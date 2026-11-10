/* LIS2DW12 motion sensor: low-power sampling into its FIFO, read in batches. */
#ifndef NUDGEBAND_ACCEL_H
#define NUDGEBAND_ACCEL_H

#include <stdint.h>

#include "activity.h"

#define ACCEL_ODR_HZ   12.5
#define ACCEL_FIFO_WTM 25 /* samples per batch: one wake every 2 s */

int accel_init(void);

/* Start sampling; INT1 fires each time ACCEL_FIFO_WTM samples are waiting. */
int accel_start(void);
int accel_stop(void);

/* Read every sample in the FIFO (up to max), in mg. Returns the count or a negative error. */
int accel_read_fifo(struct accel_sample *out, int max);

#endif
