/* Board GPIOs from the devicetree node "nudgeband-io" (boards/nudgeband). */
#ifndef NUDGEBAND_BOARD_IO_H
#define NUDGEBAND_BOARD_IO_H

#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/i2c.h>

extern const struct gpio_dt_spec io_pmic_int;
extern const struct gpio_dt_spec io_dock_pg;
extern const struct gpio_dt_spec io_acc_int1;
extern const struct gpio_dt_spec io_acc_int2;
extern const struct gpio_dt_spec io_hapt_en;
extern const struct gpio_dt_spec io_led_en;
extern const struct gpio_dt_spec io_chg_cd;
extern const struct gpio_dt_spec io_ls_ctrl;

/* The one I2C bus: LIS2DW12 0x19, DRV2605L 0x5A, IS31FL3193 0x68, BQ25125 0x6A. */
extern const struct device *const i2c_bus;

int board_io_init(void);

#endif
