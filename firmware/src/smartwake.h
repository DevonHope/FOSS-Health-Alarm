/*
 * Smart-wake decision (pure C, no Zephyr; unit-tested on the host).
 *
 * Fed one activity value per epoch (see activity.h). Inside the wake window before the alarm it
 * looks for light sleep: at least `confirm_epochs` of the last `confirm_span` epochs above a
 * threshold. The threshold adapts to the night: it is `factor` times the median activity of the
 * epochs recorded so far, but never below `min_threshold`. That keeps a restless sleeper from
 * being woken the moment the window opens, and a single twitch from counting as light sleep.
 * If light sleep never shows up, it wakes at the alarm time.
 *
 * Times are seconds on any monotonic clock (the firmware uses unix time set by the phone).
 */
#ifndef NUDGEBAND_SMARTWAKE_H
#define NUDGEBAND_SMARTWAKE_H

#include <stdbool.h>
#include <stdint.h>

#define SMARTWAKE_MAX_EPOCHS 1440 /* 12 h of 30 s epochs */
#define SMARTWAKE_HIST_SPAN 8     /* longest confirm_span supported */
/* Below this many epochs (10 min) there is too little night to adapt to: use min_threshold. */
#define SMARTWAKE_MIN_HISTORY 20

enum smartwake_result {
	SMARTWAKE_NONE = 0,
	SMARTWAKE_LIGHT_SLEEP, /* wake now: light sleep inside the window */
	SMARTWAKE_DEADLINE,    /* wake now: alarm time reached */
};

struct smartwake_cfg {
	uint32_t epoch_s;       /* 30 */
	uint32_t window_s;      /* 1800 = 30 min before the alarm */
	uint16_t min_threshold; /* activity that always counts as movement */
	uint16_t factor_x10;    /* threshold = median * factor_x10 / 10 */
	uint8_t confirm_epochs; /* epochs above threshold needed ... */
	uint8_t confirm_span;   /* ... within this many recent epochs */
};

struct smartwake {
	struct smartwake_cfg cfg;
	uint32_t alarm_s; /* alarm (latest wake) time */
	bool armed;
	uint16_t n;                         /* epochs in the log (stops at SMARTWAKE_MAX_EPOCHS) */
	uint32_t fed;                       /* epochs fed since arming */
	uint16_t recent[SMARTWAKE_HIST_SPAN]; /* last epochs, newest at fed % SPAN - 1 */
	uint16_t log[SMARTWAKE_MAX_EPOCHS]; /* also the night's sleep log for the app */
};

/* Defaults tuned on nothing yet: revisit after real nights (firmware/TODO.md, phase 4). */
void smartwake_default_cfg(struct smartwake_cfg *cfg);

void smartwake_arm(struct smartwake *sw, const struct smartwake_cfg *cfg, uint32_t alarm_s);
void smartwake_disarm(struct smartwake *sw);

/* Current threshold, from the night so far. */
uint16_t smartwake_threshold(const struct smartwake *sw);

/*
 * Record the epoch that ended at `now_s` with the given activity and decide.
 * Returns SMARTWAKE_NONE while not armed. After a wake result the caller disarms.
 */
enum smartwake_result smartwake_feed(struct smartwake *sw, uint32_t now_s, uint16_t activity);

#endif
