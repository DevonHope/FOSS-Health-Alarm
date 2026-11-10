/* Host unit tests for the pure-C parts of the firmware. Run: make -C tests/host */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "activity.h"
#include "smartwake.h"
#include "test.h"

int failures;
int checks;

#define EPOCH   30u
#define ALARM   (8u * 3600u) /* alarm 8 h after "midnight" = 0 */
#define BEDTIME 0u

static struct smartwake sw; /* big: keep it off the stack */

/* Feed epochs ending at t = BEDTIME + EPOCH, ... until a wake result; return the wake time. */
static uint32_t run_night(uint16_t (*activity_at)(uint32_t t), enum smartwake_result *why)
{
	struct smartwake_cfg cfg;

	smartwake_default_cfg(&cfg);
	smartwake_arm(&sw, &cfg, ALARM);
	for (uint32_t t = BEDTIME + EPOCH; t < ALARM + 3600; t += EPOCH) {
		enum smartwake_result r = smartwake_feed(&sw, t, activity_at(t));

		if (r != SMARTWAKE_NONE) {
			*why = r;
			return t;
		}
	}
	*why = SMARTWAKE_NONE;
	return 0;
}

static uint16_t still(uint32_t t)
{
	(void)t;
	return 0;
}

static uint16_t calm_with_rare_noise(uint32_t t)
{
	return (t / EPOCH) % 17 == 0 ? 40 : 5;
}

/* Turning over 10 min into the window: 3 busy epochs. */
#define MOVE_AT (ALARM - 20u * 60u)
static uint16_t moves_in_window(uint32_t t)
{
	return (t >= MOVE_AT && t < MOVE_AT + 3 * EPOCH) ? 2000 : 10;
}

/* Lots of movement, but all of it before the window opens. */
static uint16_t moves_before_window(uint32_t t)
{
	return (t >= ALARM - 60u * 60u && t < ALARM - 40u * 60u) ? 2000 : 10;
}

/* One big twitch in the window, nothing around it: not light sleep. */
static uint16_t single_twitch(uint32_t t)
{
	return t == ALARM - 15u * 60u ? 5000 : 10;
}

/* Restless sleeper: 400 every epoch all night (above the 300 floor), real move 5 min before. */
static uint16_t restless(uint32_t t)
{
	if (t >= ALARM - 5u * 60u && t < ALARM - 5u * 60u + 2 * EPOCH) {
		return 3000;
	}
	return 400;
}

static void test_smartwake(void)
{
	enum smartwake_result why;
	uint32_t t;

	printf("smartwake\n");

	t = run_night(still, &why);
	CHECK(why == SMARTWAKE_DEADLINE);
	CHECK(t == ALARM);

	t = run_night(calm_with_rare_noise, &why);
	CHECK(why == SMARTWAKE_DEADLINE);
	CHECK(t == ALARM);

	t = run_night(moves_in_window, &why);
	CHECK(why == SMARTWAKE_LIGHT_SLEEP);
	/* epoch ending at MOVE_AT + EPOCH is the first busy one; the second confirms */
	CHECK(t == MOVE_AT + EPOCH * 1);

	t = run_night(moves_before_window, &why);
	CHECK(why == SMARTWAKE_DEADLINE);
	CHECK(t == ALARM);

	t = run_night(single_twitch, &why);
	CHECK(why == SMARTWAKE_DEADLINE);

	t = run_night(restless, &why);
	CHECK(why == SMARTWAKE_LIGHT_SLEEP);
	CHECK(t >= ALARM - 5u * 60u && t < ALARM);
	CHECK(smartwake_threshold(&sw) > 400); /* adapted above the restless baseline */

	/* Not armed: never wakes. */
	smartwake_disarm(&sw);
	CHECK(smartwake_feed(&sw, ALARM + 10, 9999) == SMARTWAKE_NONE);

	/* Armed late (inside the window, no history): two busy epochs still wake. */
	{
		struct smartwake_cfg cfg;

		smartwake_default_cfg(&cfg);
		smartwake_arm(&sw, &cfg, ALARM);
		CHECK(smartwake_feed(&sw, ALARM - 600, 1000) == SMARTWAKE_NONE);
		CHECK(smartwake_feed(&sw, ALARM - 570, 1000) == SMARTWAKE_LIGHT_SLEEP);
	}

	/* Log keeps the night for the app, capped at SMARTWAKE_MAX_EPOCHS. */
	{
		struct smartwake_cfg cfg;

		smartwake_default_cfg(&cfg);
		smartwake_arm(&sw, &cfg, 100000u);
		for (uint32_t i = 1; i <= SMARTWAKE_MAX_EPOCHS + 50; i++) {
			smartwake_feed(&sw, i * EPOCH, (uint16_t)i);
		}
		CHECK(sw.n == SMARTWAKE_MAX_EPOCHS);
		CHECK(sw.log[0] == 1);
	}
}

static void fill(struct accel_sample *s, uint32_t n, int16_t x, int16_t y, int16_t z)
{
	for (uint32_t i = 0; i < n; i++) {
		s[i].x = x;
		s[i].y = y;
		s[i].z = z;
	}
}

static void test_activity(void)
{
	struct activity_acc acc;
	struct accel_sample s[375]; /* 30 s at 12.5 Hz */

	printf("activity\n");

	/* Lying still, any orientation: gravity alone gives nothing. */
	activity_reset(&acc);
	fill(s, 375, 0, 0, 1000);
	activity_add(&acc, s, 375);
	CHECK(activity_end_epoch(&acc) == 0);
	fill(s, 375, 707, -707, 0);
	activity_reset(&acc);
	activity_add(&acc, s, 375);
	CHECK(activity_end_epoch(&acc) == 0);

	/* Noise inside the deadband: nothing. */
	activity_reset(&acc);
	for (uint32_t i = 0; i < 375; i++) {
		s[i].x = (int16_t)(i % 2 ? 5 : -5);
		s[i].y = 0;
		s[i].z = (int16_t)(1000 + (i % 3 ? 4 : -4));
	}
	activity_add(&acc, s, 375);
	CHECK(activity_end_epoch(&acc) == 0);

	/* One 100 mg step on x: counted once (100 - deadband). */
	activity_reset(&acc);
	fill(s, 10, 0, 0, 1000);
	fill(s + 10, 10, 100, 0, 1000);
	activity_add(&acc, s, 20);
	CHECK(activity_end_epoch(&acc) == 100 - ACTIVITY_DEADBAND_MG);

	/* Split over two calls gives the same as one call. */
	activity_reset(&acc);
	activity_add(&acc, s, 12);
	activity_add(&acc, s + 12, 8);
	CHECK(activity_end_epoch(&acc) == 100 - ACTIVITY_DEADBAND_MG);

	/* Step across an epoch boundary still counts (the last sample carries over). */
	activity_reset(&acc);
	activity_add(&acc, s, 10);
	CHECK(activity_end_epoch(&acc) == 0);
	activity_add(&acc, s + 10, 10);
	CHECK(activity_end_epoch(&acc) == 100 - ACTIVITY_DEADBAND_MG);

	/* Saturates instead of wrapping. */
	activity_reset(&acc);
	for (uint32_t i = 0; i < 375; i++) {
		int16_t v = (int16_t)(i % 2 ? 2000 : -2000);

		s[i].x = v;
		s[i].y = v;
		s[i].z = v;
	}
	activity_add(&acc, s, 375);
	CHECK(activity_end_epoch(&acc) == ACTIVITY_MAX);
}

int main(void)
{
	test_activity();
	test_smartwake();
	test_protocol();
	printf("%d checks, %d failed\n", checks, failures);
	return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
