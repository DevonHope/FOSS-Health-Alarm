#include "protocol.h"

void nb_alarm_cfg_default(struct nb_alarm_cfg *cfg)
{
	cfg->version = NB_ALARM_VERSION;
	cfg->flags = NB_ALARM_FLAG_SMARTWAKE; /* not enabled until the app sets a time */
	cfg->days = 0;
	cfg->hour = 7;
	cfg->minute = 0;
	cfg->window_min = 30;
	cfg->intensity = 150;
	cfg->pattern = 0;
	cfg->ramp_s = 20;
	cfg->buzz_s = 30;
	cfg->repeat_min = 2;
	cfg->max_repeats = 5;
}

bool nb_alarm_cfg_valid(const struct nb_alarm_cfg *cfg)
{
	return cfg->version == NB_ALARM_VERSION &&
	       (cfg->flags & ~(NB_ALARM_FLAG_ENABLED | NB_ALARM_FLAG_SMARTWAKE)) == 0 &&
	       cfg->days < 0x80 && cfg->hour < 24 && cfg->minute < 60 && cfg->window_min <= 60 &&
	       cfg->pattern <= 2 && cfg->ramp_s <= 60 && cfg->buzz_s >= 5 && cfg->buzz_s <= 120 &&
	       cfg->max_repeats <= 10;
}
