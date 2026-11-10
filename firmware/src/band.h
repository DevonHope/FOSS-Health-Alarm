/* The band's shared state and the actions the Bluetooth service can ask for (main.c). */
#ifndef NUDGEBAND_BAND_H
#define NUDGEBAND_BAND_H

#include <stdbool.h>
#include <stdint.h>

#include "protocol.h"

#define FW_MAJOR 0
#define FW_MINOR 1

/* UTC now, or 0 if the phone has not set the time since power-up. */
uint32_t band_now_utc(void);

void band_set_time(const struct nb_time *t);
void band_get_time(struct nb_time *t);

void band_get_alarm(struct nb_alarm_cfg *cfg);
void band_set_alarm(const struct nb_alarm_cfg *cfg); /* already validated */

void band_get_status(struct nb_status *st);

enum nb_cp_result band_test_buzz(uint8_t intensity_pct, uint8_t seconds);
void band_stop_buzz(void);
void band_dismiss(void);
void band_identify(void);

#endif
