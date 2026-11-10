#include "board_io.h"

#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(board_io, LOG_LEVEL_INF);

#define IO DT_NODELABEL(nudgeband_io)

const struct gpio_dt_spec io_pmic_int = GPIO_DT_SPEC_GET(IO, pmic_int_gpios);
const struct gpio_dt_spec io_dock_pg = GPIO_DT_SPEC_GET(IO, dock_pg_gpios);
const struct gpio_dt_spec io_acc_int1 = GPIO_DT_SPEC_GET(IO, acc_int1_gpios);
const struct gpio_dt_spec io_acc_int2 = GPIO_DT_SPEC_GET(IO, acc_int2_gpios);
const struct gpio_dt_spec io_hapt_en = GPIO_DT_SPEC_GET(IO, hapt_en_gpios);
const struct gpio_dt_spec io_led_en = GPIO_DT_SPEC_GET(IO, led_en_gpios);
const struct gpio_dt_spec io_chg_cd = GPIO_DT_SPEC_GET(IO, chg_cd_gpios);
const struct gpio_dt_spec io_ls_ctrl = GPIO_DT_SPEC_GET(IO, ls_ctrl_gpios);

const struct device *const i2c_bus = DEVICE_DT_GET(DT_NODELABEL(i2c21));

int board_io_init(void)
{
	const struct gpio_dt_spec *in[] = {&io_pmic_int, &io_dock_pg, &io_acc_int1, &io_acc_int2};
	/* All outputs start low: motor driver off, LED driver in shutdown, charger Hi-Z (/CD low,
	 * which also lets it charge on the dock), LED supply off. */
	const struct gpio_dt_spec *out[] = {&io_hapt_en, &io_led_en, &io_chg_cd, &io_ls_ctrl};
	int err;

	if (!device_is_ready(i2c_bus)) {
		LOG_ERR("I2C bus not ready");
		return -ENODEV;
	}
	for (size_t i = 0; i < ARRAY_SIZE(in); i++) {
		err = gpio_pin_configure_dt(in[i], GPIO_INPUT);
		if (err) {
			return err;
		}
	}
	for (size_t i = 0; i < ARRAY_SIZE(out); i++) {
		err = gpio_pin_configure_dt(out[i], GPIO_OUTPUT_INACTIVE);
		if (err) {
			return err;
		}
	}
	return 0;
}
