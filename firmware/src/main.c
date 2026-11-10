/*
 * NudgeBand firmware: track movement all night, wake the wearer gently in light sleep inside the
 * window before the alarm. Status of every part: ../TODO.md.
 */
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "accel.h"
#include "activity.h"
#include "alarm.h"
#include "band.h"
#include "ble.h"
#include "board_io.h"
#include "haptics.h"
#include "led.h"
#include "pmic.h"
#include "smartwake.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

#define EPOCH_S 30

static K_MUTEX_DEFINE(lock);
static K_SEM_DEFINE(fifo_ready, 0, 1);

/* Time: UTC at the moment the phone set it, plus uptime since then. */
static uint32_t utc_at_set;
static int64_t uptime_at_set_ms;
static int16_t tz_offset_min;
static bool time_set;

static struct nb_alarm_cfg alarm_cfg;
static uint32_t next_alarm_utc;
static enum nb_state state = NB_STATE_IDLE;
static uint8_t repeats_left;
static enum nb_wake_reason last_wake_reason;
static uint32_t last_wake_utc;

static struct smartwake sw;
static struct activity_acc acc;

static void repeat_fn(struct k_work *w);
static K_WORK_DELAYABLE_DEFINE(repeat_work, repeat_fn);

uint32_t band_now_utc(void)
{
	if (!time_set) {
		return 0;
	}
	return utc_at_set + (uint32_t)((k_uptime_get() - uptime_at_set_ms) / 1000);
}

static void rearm_locked(void)
{
	struct smartwake_cfg cfg;
	uint32_t now = band_now_utc();

	next_alarm_utc = now ? alarm_next_utc(&alarm_cfg, now, tz_offset_min) : 0;
	if (!next_alarm_utc) {
		smartwake_disarm(&sw);
		state = NB_STATE_IDLE;
		return;
	}
	smartwake_default_cfg(&cfg);
	cfg.epoch_s = EPOCH_S;
	cfg.window_s = (alarm_cfg.flags & NB_ALARM_FLAG_SMARTWAKE) ? alarm_cfg.window_min * 60u : 0;
	smartwake_arm(&sw, &cfg, next_alarm_utc);
	state = NB_STATE_TRACKING;
	LOG_INF("next alarm at %u (UTC), window %u min", next_alarm_utc, cfg.window_s / 60);
}

void band_set_time(const struct nb_time *t)
{
	k_mutex_lock(&lock, K_FOREVER);
	utc_at_set = t->utc;
	uptime_at_set_ms = k_uptime_get();
	tz_offset_min = t->tz_offset_min;
	time_set = true;
	if (state == NB_STATE_IDLE || state == NB_STATE_TRACKING) {
		rearm_locked();
	}
	k_mutex_unlock(&lock);
	ble_status_changed();
}

void band_get_time(struct nb_time *t)
{
	t->utc = band_now_utc();
	t->tz_offset_min = tz_offset_min;
	t->reserved = 0;
}

void band_get_alarm(struct nb_alarm_cfg *cfg)
{
	k_mutex_lock(&lock, K_FOREVER);
	*cfg = alarm_cfg;
	k_mutex_unlock(&lock);
}

void band_set_alarm(const struct nb_alarm_cfg *cfg)
{
	k_mutex_lock(&lock, K_FOREVER);
	alarm_cfg = *cfg;
	/* TODO(TODO.md 3.5): keep the alarm in flash (settings) so a reset doesn't lose it. */
	if (state != NB_STATE_WAKING && state != NB_STATE_WAIT_REPEAT) {
		rearm_locked();
	}
	k_mutex_unlock(&lock);
	ble_status_changed();
}

void band_get_status(struct nb_status *st)
{
	k_mutex_lock(&lock, K_FOREVER);
	st->version = NB_STATUS_VERSION;
	st->state = state;
	st->battery_pct = pmic_battery_pct();
	st->flags = (pmic_docked() ? NB_FLAG_DOCKED : 0) | (time_set ? NB_FLAG_TIME_SET : 0) |
		    (next_alarm_utc ? NB_FLAG_ALARM_ARMED : 0) | (sw.n ? NB_FLAG_LOG_HAS_DATA : 0);
	/* TODO(TODO.md 2.1): NB_FLAG_CHARGING from the BQ25125 status register. */
	st->next_alarm_utc = next_alarm_utc;
	st->fw_major = FW_MAJOR;
	st->fw_minor = FW_MINOR;
	st->last_wake_reason = last_wake_reason;
	st->reserved = 0;
	st->last_wake_utc = last_wake_utc;
	st->stored_epochs = sw.n; /* RAM only for now (TODO.md 3.4) */
	k_mutex_unlock(&lock);
}

static void buzz_locked(void)
{
	(void)haptics_start(alarm_cfg.intensity, alarm_cfg.pattern, alarm_cfg.ramp_s,
			    alarm_cfg.buzz_s);
	state = NB_STATE_WAKING;
	/* After the buzz, wait repeat_min, then buzz again (until dismissed or out of repeats). */
	k_work_reschedule(&repeat_work, K_SECONDS(alarm_cfg.buzz_s));
}

static void repeat_fn(struct k_work *w)
{
	ARG_UNUSED(w);
	k_mutex_lock(&lock, K_FOREVER);
	if (state == NB_STATE_WAKING) {
		if (repeats_left == 0 || alarm_cfg.repeat_min == 0) {
			rearm_locked(); /* done: on to the next alarm */
		} else {
			repeats_left--;
			state = NB_STATE_WAIT_REPEAT;
			k_work_reschedule(&repeat_work, K_MINUTES(alarm_cfg.repeat_min));
		}
	} else if (state == NB_STATE_WAIT_REPEAT) {
		buzz_locked();
	}
	k_mutex_unlock(&lock);
	ble_status_changed();
}

static void wake_locked(enum nb_wake_reason why)
{
	last_wake_reason = why;
	last_wake_utc = band_now_utc();
	repeats_left = alarm_cfg.max_repeats;
	smartwake_disarm(&sw);
	LOG_INF("wake: reason %d", why);
	buzz_locked();
}

enum nb_cp_result band_test_buzz(uint8_t intensity_pct, uint8_t seconds)
{
	if (intensity_pct > 100 || seconds < 1 || seconds > 10) {
		return NB_CP_INVALID;
	}
	if (state == NB_STATE_WAKING) {
		return NB_CP_BUSY;
	}
	return haptics_start((uint8_t)(intensity_pct * 255u / 100u), 0, 1, seconds) ? NB_CP_BUSY
										     : NB_CP_OK;
}

void band_stop_buzz(void)
{
	haptics_stop();
}

void band_dismiss(void)
{
	k_mutex_lock(&lock, K_FOREVER);
	haptics_stop();
	k_work_cancel_delayable(&repeat_work);
	if (state == NB_STATE_WAKING || state == NB_STATE_WAIT_REPEAT ||
	    state == NB_STATE_IN_WINDOW) {
		/* TODO(TODO.md 3.3): dismissing during the window should skip today's alarm only. */
		rearm_locked();
	}
	k_mutex_unlock(&lock);
	ble_status_changed();
}

void band_identify(void)
{
	/* TODO(TODO.md 2.4): blink twice from a work item instead of a fixed on-time. */
	(void)led_set(0, 0, 64);
	k_msleep(300);
	(void)led_set(0, 0, 0);
}

/* Called once per epoch with that epoch's activity. */
static void end_of_epoch(uint16_t activity)
{
	enum smartwake_result r;
	uint32_t now;
	bool changed = false;

	k_mutex_lock(&lock, K_FOREVER);
	now = band_now_utc();
	r = now ? smartwake_feed(&sw, now, activity) : SMARTWAKE_NONE;
	if (state == NB_STATE_TRACKING && sw.armed && now + sw.cfg.window_s >= sw.alarm_s) {
		state = NB_STATE_IN_WINDOW;
		changed = true;
	}
	if (r == SMARTWAKE_LIGHT_SLEEP) {
		wake_locked(NB_WAKE_LIGHT_SLEEP);
		changed = true;
	} else if (r == SMARTWAKE_DEADLINE) {
		wake_locked((alarm_cfg.flags & NB_ALARM_FLAG_SMARTWAKE) ? NB_WAKE_DEADLINE
									 : NB_WAKE_EXACT);
		changed = true;
	}
	k_mutex_unlock(&lock);
	if (changed) {
		ble_status_changed();
	}
}

static struct gpio_callback acc_cb;

static void acc_int1_isr(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
	k_sem_give(&fifo_ready);
}

int main(void)
{
	static struct accel_sample batch[32];
	int64_t epoch_end_ms;
	int err;

	LOG_INF("NudgeBand firmware %d.%d", FW_MAJOR, FW_MINOR);

	nb_alarm_cfg_default(&alarm_cfg);
	err = board_io_init();
	if (err) {
		LOG_ERR("board_io_init failed (%d)", err);
		return 0;
	}
	(void)pmic_init();
	(void)led_init();
	(void)haptics_init();
	err = accel_init();
	(void)ble_init();

	if (err == 0) {
		gpio_pin_interrupt_configure_dt(&io_acc_int1, GPIO_INT_EDGE_TO_ACTIVE);
		gpio_init_callback(&acc_cb, acc_int1_isr, BIT(io_acc_int1.pin));
		gpio_add_callback_dt(&io_acc_int1, &acc_cb);
		activity_reset(&acc);
		(void)accel_start();
	}

	epoch_end_ms = k_uptime_get() + EPOCH_S * 1000;
	for (;;) {
		/* The FIFO interrupt normally wakes us every 2 s; the timeout covers a missed one. */
		(void)k_sem_take(&fifo_ready, K_SECONDS(3));

		int n = accel_read_fifo(batch, ARRAY_SIZE(batch));

		if (n > 0) {
			activity_add(&acc, batch, (uint32_t)n);
		}
		/* TODO(TODO.md 3.1): mark epochs as "no data" (0xFFFF) while docked or off the wrist. */
		while (k_uptime_get() >= epoch_end_ms) {
			end_of_epoch(activity_end_epoch(&acc));
			epoch_end_ms += EPOCH_S * 1000;
		}
	}
	return 0;
}
