/*
 * DRV2605L register-level driver (TI SLOS854). The motor is driven in real-time playback (RTP)
 * mode so the firmware can ramp the strength itself. EN is held low between buzzes (shutdown).
 */
#include "haptics.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "board_io.h"

LOG_MODULE_REGISTER(haptics, LOG_LEVEL_INF);

#define ADDR 0x5A

#define REG_STATUS    0x00
#define REG_MODE      0x01
#define REG_RTP       0x02
#define REG_LIBRARY   0x03
#define REG_FEEDBACK  0x1A
#define REG_CONTROL3  0x1D

#define MODE_RTP          0x05
#define MODE_STANDBY      BIT(6)
#define LIBRARY_LRA       0x06
#define FEEDBACK_LRA      BIT(7)
#define CONTROL3_RTP_UNSIGNED BIT(3)

#define STEP_MS 50

static struct k_work_delayable step_work;
static uint32_t elapsed_ms;
static uint32_t ramp_ms;
static uint32_t total_ms;
static uint8_t target;
static uint8_t pat;
static bool running;

static int wr(uint8_t reg, uint8_t val)
{
	return i2c_reg_write_byte(i2c_bus, ADDR, reg, val);
}

/* Strength at this moment of the pattern, 0-255. */
static uint8_t level_now(void)
{
	uint32_t lvl = target;

	if (elapsed_ms < ramp_ms) {
		lvl = lvl * elapsed_ms / ramp_ms;
	}
	switch (pat) {
	case 1: /* slow pulses: 1 s on, 1 s off */
		return (elapsed_ms / 1000) % 2 ? 0 : (uint8_t)lvl;
	case 2: /* heartbeat: two short beats every 1.2 s */
	{
		uint32_t t = elapsed_ms % 1200;

		return (t < 150 || (t >= 300 && t < 450)) ? (uint8_t)lvl : 0;
	}
	default:
		return (uint8_t)lvl;
	}
}

static void power_down(void)
{
	(void)wr(REG_RTP, 0);
	(void)wr(REG_MODE, MODE_STANDBY);
	gpio_pin_set_dt(&io_hapt_en, 0);
	running = false;
}

static void step(struct k_work *work)
{
	ARG_UNUSED(work);
	if (!running) {
		return;
	}
	if (elapsed_ms >= total_ms) {
		power_down();
		return;
	}
	(void)wr(REG_RTP, level_now());
	elapsed_ms += STEP_MS;
	k_work_reschedule(&step_work, K_MSEC(STEP_MS));
}

int haptics_init(void)
{
	uint8_t st;
	int err;

	k_work_init_delayable(&step_work, step);

	gpio_pin_set_dt(&io_hapt_en, 1);
	k_msleep(1);
	err = i2c_reg_read_byte(i2c_bus, ADDR, REG_STATUS, &st);
	if (err) {
		LOG_ERR("no answer at 0x%02x (%d)", ADDR, err);
		gpio_pin_set_dt(&io_hapt_en, 0);
		return err;
	}
	LOG_INF("DRV2605L status 0x%02x (device id %u)", st, st >> 5);
	/*
	 * TODO(TODO.md 2.3): auto-calibrate for the VG0832012 (rated voltage, overdrive clamp,
	 * drive time from its resonant frequency) and store the result; until then the chip's LRA
	 * defaults apply.
	 */
	power_down();
	return 0;
}

int haptics_start(uint8_t intensity, uint8_t pattern, uint8_t ramp_s, uint8_t buzz_s)
{
	int err;

	gpio_pin_set_dt(&io_hapt_en, 1);
	k_msleep(1);
	err = wr(REG_FEEDBACK, FEEDBACK_LRA);
	err = err ?: wr(REG_LIBRARY, LIBRARY_LRA);
	err = err ?: wr(REG_CONTROL3, CONTROL3_RTP_UNSIGNED);
	err = err ?: wr(REG_RTP, 0);
	err = err ?: wr(REG_MODE, MODE_RTP);
	if (err) {
		gpio_pin_set_dt(&io_hapt_en, 0);
		return err;
	}
	target = intensity;
	pat = pattern;
	ramp_ms = (uint32_t)ramp_s * 1000;
	total_ms = (uint32_t)buzz_s * 1000;
	elapsed_ms = 0;
	running = true;
	k_work_reschedule(&step_work, K_NO_WAIT);
	return 0;
}

void haptics_stop(void)
{
	running = false;
	k_work_cancel_delayable(&step_work);
	power_down();
}

bool haptics_busy(void)
{
	return running;
}
