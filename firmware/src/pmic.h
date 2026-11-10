/* BQ25125 charger. Its power-up defaults already charge correctly (4.2 V, 30 mA set by R202). */
#ifndef NUDGEBAND_PMIC_H
#define NUDGEBAND_PMIC_H

#include <stdbool.h>
#include <stdint.h>

int pmic_init(void);

/* True while the dock supplies VIN (/PG low). */
bool pmic_docked(void);

/* Battery percent from VBMON (2 % steps), or 0xFF if unknown. */
uint8_t pmic_battery_pct(void);

/* LED supply on/off (LS/LDO in load-switch mode). */
int pmic_led_supply(bool on);

#endif
