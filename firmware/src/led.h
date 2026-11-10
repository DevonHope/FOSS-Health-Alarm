/* IS31FL3193 RGB LED driver (OUT1 green, OUT2 blue, OUT3 red). */
#ifndef NUDGEBAND_LED_H
#define NUDGEBAND_LED_H

#include <stdint.h>

int led_init(void);
int led_set(uint8_t r, uint8_t g, uint8_t b); /* all zero = off and shut down */

#endif
