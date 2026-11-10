/*
 * Movement measure for one sleep epoch (pure C, no Zephyr; unit-tested on the host).
 *
 * Each accelerometer sample is compared with the one before it. The change on x, y and z is
 * added up (|dx| + |dy| + |dz|, in mg), a small deadband is taken off to ignore sensor noise,
 * and what is left is summed over the epoch. Gravity cancels out because only changes count,
 * so the band's orientation on the wrist does not matter.
 */
#ifndef NUDGEBAND_ACTIVITY_H
#define NUDGEBAND_ACTIVITY_H

#include <stdbool.h>
#include <stdint.h>

/* Samples whose summed change is at or below this (mg) count as noise. */
#define ACTIVITY_DEADBAND_MG 20
/* Largest activity value; 0xFFFF means "no data" in the sleep log (docs/ble-protocol.md). */
#define ACTIVITY_MAX   0xFFFEu
#define ACTIVITY_NONE  0xFFFFu

struct accel_sample {
	int16_t x; /* mg */
	int16_t y;
	int16_t z;
};

struct activity_acc {
	struct accel_sample prev;
	bool have_prev;
	uint32_t sum; /* mg above the deadband, this epoch */
};

void activity_reset(struct activity_acc *acc);

/* Add samples (may be called many times per epoch, e.g. once per FIFO read). */
void activity_add(struct activity_acc *acc, const struct accel_sample *s, uint32_t n);

/*
 * Finish the epoch: returns its activity (saturated to ACTIVITY_MAX) and clears the sum.
 * The last sample is kept so the next epoch's first change is measured too.
 */
uint16_t activity_end_epoch(struct activity_acc *acc);

#endif
