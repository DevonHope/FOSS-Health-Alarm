/* Host tests for protocol.c and alarm.c */
#include <stdio.h>

#include "alarm.h"
#include "protocol.h"
#include "test.h"

/* 2026-11-10 (a Tuesday) 02:00:00 UTC */
#define TUE_0200_UTC 1794276000u

static void test_alarm(void)
{
	struct nb_alarm_cfg c;
	uint32_t t;

	printf("alarm\n");
	CHECK(alarm_weekday(TUE_0200_UTC / 86400) == 1); /* Tuesday */

	nb_alarm_cfg_default(&c);
	CHECK(alarm_next_utc(&c, TUE_0200_UTC, 0) == 0); /* disabled */

	c.flags |= NB_ALARM_FLAG_ENABLED;
	c.hour = 7;
	c.minute = 30;
	/* UTC, one-off: today 07:30 */
	CHECK(alarm_next_utc(&c, TUE_0200_UTC, 0) == TUE_0200_UTC + 5u * 3600u + 1800u);

	/* EST (-300): local now is Mon 21:00, so next 07:30 local = Tue 12:30 UTC */
	t = alarm_next_utc(&c, TUE_0200_UTC, -300);
	CHECK(t == TUE_0200_UTC + 10u * 3600u + 1800u);

	/* Exactly at the alarm time: the next one is tomorrow */
	t = alarm_next_utc(&c, TUE_0200_UTC + 5u * 3600u + 1800u, 0);
	CHECK(t == TUE_0200_UTC + 29u * 3600u + 1800u);

	/* Weekdays only (Mon-Fri = 0x1f), asked on Friday after the alarm: Monday */
	c.days = 0x1f;
	{
		uint32_t fri_0900 = TUE_0200_UTC + 3u * 86400u + 7u * 3600u;
		uint32_t mon_0730 = TUE_0200_UTC + 6u * 86400u + 5u * 3600u + 1800u;

		CHECK(alarm_weekday(fri_0900 / 86400) == 4);
		CHECK(alarm_next_utc(&c, fri_0900, 0) == mon_0730);
	}

	/* Sunday only (bit 6), from Tuesday */
	c.days = 0x40;
	t = alarm_next_utc(&c, TUE_0200_UTC, 0);
	CHECK(alarm_weekday(t / 86400) == 6);
	CHECK(t == TUE_0200_UTC + 5u * 86400u + 5u * 3600u + 1800u);

	/* Positive offset (+60) crossing midnight local */
	c.days = 0;
	c.hour = 0;
	c.minute = 30;
	t = alarm_next_utc(&c, TUE_0200_UTC, 60); /* local Tue 03:00 -> Wed 00:30 local = Tue 23:30 UTC */
	CHECK(t == TUE_0200_UTC + 21u * 3600u + 1800u);
}

static void test_cfg(void)
{
	struct nb_alarm_cfg c;

	printf("protocol\n");
	nb_alarm_cfg_default(&c);
	CHECK(nb_alarm_cfg_valid(&c));
	c.hour = 24;
	CHECK(!nb_alarm_cfg_valid(&c));
	nb_alarm_cfg_default(&c);
	c.buzz_s = 4;
	CHECK(!nb_alarm_cfg_valid(&c));
	nb_alarm_cfg_default(&c);
	c.window_min = 61;
	CHECK(!nb_alarm_cfg_valid(&c));
	nb_alarm_cfg_default(&c);
	c.days = 0x80;
	CHECK(!nb_alarm_cfg_valid(&c));
	nb_alarm_cfg_default(&c);
	c.flags = 0x04;
	CHECK(!nb_alarm_cfg_valid(&c));
	nb_alarm_cfg_default(&c);
	c.version = 2;
	CHECK(!nb_alarm_cfg_valid(&c));

	CHECK(nb_log_epochs_per_packet(23) == 5);
	CHECK(nb_log_epochs_per_packet(247) == 117);
}

void test_protocol(void)
{
	test_cfg();
	test_alarm();
}
