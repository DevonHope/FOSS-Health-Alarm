/*
 * LIS2DW12 register-level driver. Register map: ST DS12086.
 * Low-power mode 1 (12-bit), 12.5 Hz, +/-2 g, FIFO in continuous mode with a watermark on INT1.
 */
#include "accel.h"

#include <zephyr/logging/log.h>
#include <zephyr/sys/byteorder.h>

#include "board_io.h"

LOG_MODULE_REGISTER(accel, LOG_LEVEL_INF);

#define ADDR 0x19

#define REG_WHO_AM_I    0x0F
#define WHO_AM_I_VALUE  0x44
#define REG_CTRL1       0x20
#define REG_CTRL2       0x21
#define REG_CTRL4_INT1  0x23
#define REG_CTRL6       0x25
#define REG_OUT_X_L     0x28
#define REG_FIFO_CTRL   0x2E
#define REG_FIFO_SAMPLES 0x2F

#define CTRL1_ODR_12HZ5    (0x2 << 4)
#define CTRL1_ODR_OFF      (0x0 << 4)
#define CTRL1_LP_MODE1     0x00 /* MODE = low power, LP_MODE = 1 (12-bit) */
#define CTRL2_SOFT_RESET   BIT(6)
#define CTRL2_BDU          BIT(3)
#define CTRL2_IF_ADD_INC   BIT(2)
#define CTRL4_INT1_FTH     BIT(1)
#define CTRL6_FS_2G        (0x0 << 4)
#define FIFO_MODE_BYPASS   (0x0 << 5)
#define FIFO_MODE_CONT     (0x6 << 5)
#define FIFO_SAMPLES_MASK  0x3F

static int wr(uint8_t reg, uint8_t val)
{
	return i2c_reg_write_byte(i2c_bus, ADDR, reg, val);
}

int accel_init(void)
{
	uint8_t id;
	int err = i2c_reg_read_byte(i2c_bus, ADDR, REG_WHO_AM_I, &id);

	if (err) {
		LOG_ERR("no answer at 0x%02x (%d)", ADDR, err);
		return err;
	}
	if (id != WHO_AM_I_VALUE) {
		LOG_ERR("WHO_AM_I 0x%02x, expected 0x%02x", id, WHO_AM_I_VALUE);
		return -ENODEV;
	}
	err = wr(REG_CTRL2, CTRL2_SOFT_RESET);
	k_msleep(5);
	err = err ?: wr(REG_CTRL2, CTRL2_BDU | CTRL2_IF_ADD_INC);
	err = err ?: wr(REG_CTRL6, CTRL6_FS_2G);
	err = err ?: wr(REG_CTRL4_INT1, CTRL4_INT1_FTH);
	return err;
}

int accel_start(void)
{
	int err = wr(REG_FIFO_CTRL, FIFO_MODE_BYPASS); /* clears the FIFO */

	err = err ?: wr(REG_FIFO_CTRL, FIFO_MODE_CONT | ACCEL_FIFO_WTM);
	err = err ?: wr(REG_CTRL1, CTRL1_ODR_12HZ5 | CTRL1_LP_MODE1);
	return err;
}

int accel_stop(void)
{
	return wr(REG_CTRL1, CTRL1_ODR_OFF);
}

int accel_read_fifo(struct accel_sample *out, int max)
{
	uint8_t level;
	int n;
	int err = i2c_reg_read_byte(i2c_bus, ADDR, REG_FIFO_SAMPLES, &level);

	if (err) {
		return err;
	}
	n = MIN((int)(level & FIFO_SAMPLES_MASK), max);
	for (int i = 0; i < n; i++) {
		uint8_t raw[6];

		err = i2c_burst_read(i2c_bus, ADDR, REG_OUT_X_L, raw, sizeof(raw));
		if (err) {
			return err;
		}
		/* 12-bit, left-aligned; at +/-2 g one LSB of the 12-bit value is 0.976 mg */
		out[i].x = (int16_t)(((int32_t)(int16_t)sys_get_le16(&raw[0]) >> 4) * 976 / 1000);
		out[i].y = (int16_t)(((int32_t)(int16_t)sys_get_le16(&raw[2]) >> 4) * 976 / 1000);
		out[i].z = (int16_t)(((int32_t)(int16_t)sys_get_le16(&raw[4]) >> 4) * 976 / 1000);
	}
	return n;
}
