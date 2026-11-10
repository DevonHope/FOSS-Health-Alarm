/*
 * IS31FL3193 (Lumissil). Register addresses from the band README; check every bit against the
 * datasheet at bring-up (TODO.md, 2.4) before trusting this.
 */
#include "led.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "board_io.h"
#include "pmic.h"

LOG_MODULE_REGISTER(led, LOG_LEVEL_INF);

#define ADDR 0x68

#define REG_SHUTDOWN 0x00
#define REG_CURRENT  0x03
#define REG_PWM1     0x04 /* OUT1 green */
#define REG_PWM2     0x05 /* OUT2 blue */
#define REG_PWM3     0x06 /* OUT3 red */
#define REG_UPDATE   0x07
#define REG_LED_CTRL 0x1D

int led_init(void)
{
	return 0; /* stays in hardware shutdown (LED_EN low) until used */
}

int led_set(uint8_t r, uint8_t g, uint8_t b)
{
	int err;

	if (!r && !g && !b) {
		gpio_pin_set_dt(&io_led_en, 0);
		return pmic_led_supply(false);
	}
	err = pmic_led_supply(true);
	gpio_pin_set_dt(&io_led_en, 1);
	k_usleep(100);
	/* TODO(TODO.md 2.4): confirm the EN/SSD bits of reg 0x00 and the current code for ~5 mA. */
	err = err ?: i2c_reg_write_byte(i2c_bus, ADDR, REG_SHUTDOWN, 0x20);
	err = err ?: i2c_reg_write_byte(i2c_bus, ADDR, REG_CURRENT, 0x00);
	err = err ?: i2c_reg_write_byte(i2c_bus, ADDR, REG_LED_CTRL, 0x07);
	err = err ?: i2c_reg_write_byte(i2c_bus, ADDR, REG_PWM1, g);
	err = err ?: i2c_reg_write_byte(i2c_bus, ADDR, REG_PWM2, b);
	err = err ?: i2c_reg_write_byte(i2c_bus, ADDR, REG_PWM3, r);
	err = err ?: i2c_reg_write_byte(i2c_bus, ADDR, REG_UPDATE, 0x00);
	if (err) {
		LOG_WRN("LED write failed (%d)", err);
	}
	return err;
}
