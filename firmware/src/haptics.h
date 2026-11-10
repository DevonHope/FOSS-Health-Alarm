/* DRV2605L + VG0832012 LRA: gentle ramped vibration. */
#ifndef NUDGEBAND_HAPTICS_H
#define NUDGEBAND_HAPTICS_H

#include <stdbool.h>
#include <stdint.h>

int haptics_init(void);

/*
 * Buzz in the background: ramp from nothing to `intensity` (0-255) over ramp_s seconds, then hold
 * until buzz_s seconds have passed in total. pattern: 0 soft ramp, 1 slow pulses, 2 heartbeat.
 */
int haptics_start(uint8_t intensity, uint8_t pattern, uint8_t ramp_s, uint8_t buzz_s);
void haptics_stop(void);
bool haptics_busy(void);

#endif
