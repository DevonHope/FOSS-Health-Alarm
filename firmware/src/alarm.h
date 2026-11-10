/*
 * When is the next alarm? (pure C, unit-tested on the host)
 *
 * The band keeps UTC and the UTC offset the phone last wrote. Daylight-saving changes are picked up
 * the next time the phone connects (TODO.md, 3.2).
 */
#ifndef NUDGEBAND_ALARM_H
#define NUDGEBAND_ALARM_H

#include <stdint.h>

#include "protocol.h"

/*
 * Next alarm time (UTC seconds) strictly after now_utc, or 0 if the alarm is disabled.
 * The smart-wake window ends at this time and starts window_min before it.
 */
uint32_t alarm_next_utc(const struct nb_alarm_cfg *cfg, uint32_t now_utc, int16_t tz_offset_min);

/* Day of week of a local-time day number (days since 1970-01-01), 0 = Monday. */
static inline uint8_t alarm_weekday(uint32_t local_day)
{
	return (uint8_t)((local_day + 3u) % 7u); /* 1970-01-01 was a Thursday */
}

#endif
