/*
 * BQ25125 (TI SLUSCF6). Plan, from the band README:
 * - Leave it in default mode as much as possible: no I2C means no 50 s host-mode watchdog to feed.
 * - /CD high only while talking to it on battery; low the rest of the time (Hi-Z, 0.7 uA) and
 *   always while docked (/CD high stops charging).
 * - I2C only for: VBMON battery reading, load-switch mode for the LED supply, ship mode.
 */
#include "pmic.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "board_io.h"

LOG_MODULE_REGISTER(pmic, LOG_LEVEL_INF);

#define ADDR 0x6A

#define REG_STATUS 0x00
#define REG_LS_LDO 0x07
#define REG_VBMON  0x0A

static bool cd_high(void)
{
	if (pmic_docked()) {
		return false; /* never stop charging to talk to it */
	}
	gpio_pin_set_dt(&io_chg_cd, 1);
	k_usleep(100);
	return true;
}

static void cd_low(void)
{
	gpio_pin_set_dt(&io_chg_cd, 0);
}

int pmic_init(void)
{
	uint8_t st;
	int err;
	bool cd = cd_high();

	/* On the dock the BQ talks I2C anyway (VIN present), so this works either way. */
	err = i2c_reg_read_byte(i2c_bus, ADDR, REG_STATUS, &st);
	if (cd) {
		cd_low();
	}
	if (err) {
		LOG_ERR("no answer at 0x%02x (%d)", ADDR, err);
		return err;
	}
	LOG_INF("BQ25125 status 0x%02x, %s", st, pmic_docked() ? "docked" : "on battery");
	return 0;
}

bool pmic_docked(void)
{
	return gpio_pin_get_dt(&io_dock_pg) == 1; /* active low in the devicetree */
}

uint8_t pmic_battery_pct(void)
{
	/*
	 * TODO(TODO.md 2.1): write VBMON_READ in reg 0x0A, wait, read back and convert range + threshold
	 * bits to percent of VBATREG using the datasheet table; then map voltage to charge with a LiPo
	 * curve. Check whether a VBMON read alone puts the chip in host mode.
	 */
	return 0xFF;
}

int pmic_led_supply(bool on)
{
	/*
	 * TODO(TODO.md 2.1): write reg 0x07 for load-switch mode (VLED follows PMID), then drive LS_CTRL.
	 * The 50 s watchdog undoes it without I2C, so re-write while the LED is in use.
	 */
	gpio_pin_set_dt(&io_ls_ctrl, on ? 1 : 0);
	return 0;
}
