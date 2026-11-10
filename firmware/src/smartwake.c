#include "smartwake.h"

#include <string.h>

void smartwake_default_cfg(struct smartwake_cfg *cfg)
{
	cfg->epoch_s = 30;
	cfg->window_s = 30 * 60;
	cfg->min_threshold = 300;
	cfg->factor_x10 = 30;
	cfg->confirm_epochs = 2;
	cfg->confirm_span = 3;
}

void smartwake_arm(struct smartwake *sw, const struct smartwake_cfg *cfg, uint32_t alarm_s)
{
	sw->cfg = *cfg;
	if (sw->cfg.confirm_span > SMARTWAKE_HIST_SPAN) {
		sw->cfg.confirm_span = SMARTWAKE_HIST_SPAN;
	}
	if (sw->cfg.confirm_span == 0) {
		sw->cfg.confirm_span = 1;
	}
	if (sw->cfg.confirm_epochs == 0) {
		sw->cfg.confirm_epochs = 1;
	}
	if (sw->cfg.confirm_epochs > sw->cfg.confirm_span) {
		sw->cfg.confirm_epochs = sw->cfg.confirm_span;
	}
	sw->alarm_s = alarm_s;
	sw->armed = true;
	sw->n = 0;
	sw->fed = 0;
}

void smartwake_disarm(struct smartwake *sw)
{
	sw->armed = false;
}

/* Median by partial counting: values are bucketed in 16 mg steps up to 4095, enough here. */
static uint16_t median(const uint16_t *v, uint16_t n)
{
	enum { BUCKETS = 256, STEP = 16 };
	uint16_t hist[BUCKETS];
	uint16_t half = (uint16_t)((n + 1) / 2);
	uint32_t seen = 0;

	if (n == 0) {
		return 0;
	}
	memset(hist, 0, sizeof(hist));
	for (uint16_t i = 0; i < n; i++) {
		uint32_t b = v[i] / STEP;

		hist[b < BUCKETS ? b : BUCKETS - 1]++;
	}
	for (uint16_t b = 0; b < BUCKETS; b++) {
		seen += hist[b];
		if (seen >= half) {
			return (uint16_t)(b * STEP + STEP / 2);
		}
	}
	return (uint16_t)(BUCKETS * STEP);
}

uint16_t smartwake_threshold(const struct smartwake *sw)
{
	uint32_t t = 0;

	if (sw->n >= SMARTWAKE_MIN_HISTORY) {
		t = (uint32_t)median(sw->log, sw->n) * sw->cfg.factor_x10 / 10;
	}

	if (t < sw->cfg.min_threshold) {
		t = sw->cfg.min_threshold;
	}
	return t > UINT16_MAX ? UINT16_MAX : (uint16_t)t;
}

enum smartwake_result smartwake_feed(struct smartwake *sw, uint32_t now_s, uint16_t activity)
{
	uint16_t thr;
	uint8_t above = 0;
	uint16_t span;

	if (!sw->armed) {
		return SMARTWAKE_NONE;
	}

	/* Threshold from the night before this epoch, so a burst can't raise its own bar. */
	thr = smartwake_threshold(sw);

	if (sw->n < SMARTWAKE_MAX_EPOCHS) {
		sw->log[sw->n++] = activity;
	}
	sw->recent[sw->fed % SMARTWAKE_HIST_SPAN] = activity;
	sw->fed++;

	if (now_s >= sw->alarm_s) {
		return SMARTWAKE_DEADLINE;
	}
	if (now_s + sw->cfg.window_s < sw->alarm_s) {
		return SMARTWAKE_NONE; /* window not open yet */
	}

	/* Light sleep: enough of the recent epochs inside the window are above the threshold. */
	span = sw->cfg.confirm_span;
	for (uint32_t i = 0; i < span && i < sw->fed; i++) {
		/* epoch i back ended at now - i*epoch; only count epochs inside the window */
		uint32_t ended = now_s - (uint32_t)i * sw->cfg.epoch_s;

		if (ended + sw->cfg.window_s < sw->alarm_s) {
			break;
		}
		if (sw->recent[(sw->fed - 1 - i) % SMARTWAKE_HIST_SPAN] >= thr) {
			above++;
		}
	}
	return above >= sw->cfg.confirm_epochs ? SMARTWAKE_LIGHT_SLEEP : SMARTWAKE_NONE;
}
