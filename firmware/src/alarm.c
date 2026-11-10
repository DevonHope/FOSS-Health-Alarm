#include "alarm.h"

uint32_t alarm_next_utc(const struct nb_alarm_cfg *cfg, uint32_t now_utc, int16_t tz_offset_min)
{
	int64_t off = (int64_t)tz_offset_min * 60;
	int64_t local_now = (int64_t)now_utc + off;
	int64_t day = local_now / 86400;
	int64_t tod = (int64_t)cfg->hour * 3600 + (int64_t)cfg->minute * 60;

	if (!(cfg->flags & NB_ALARM_FLAG_ENABLED)) {
		return 0;
	}
	for (int64_t d = day; d <= day + 7; d++) {
		int64_t local = d * 86400 + tod;

		if (local <= local_now) {
			continue;
		}
		if (cfg->days != 0 && !(cfg->days & (1u << alarm_weekday((uint32_t)d)))) {
			continue;
		}
		return (uint32_t)(local - off);
	}
	return 0; /* not reached: some day in the next week always matches */
}
