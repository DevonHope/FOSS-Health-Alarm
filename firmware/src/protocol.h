/*
 * Byte layouts of the NudgeBand Bluetooth service. The spec is docs/ble-protocol.md (shared with
 * the Android app); keep the two in step. Pure C, little-endian target, unit-tested on the host.
 */
#ifndef NUDGEBAND_PROTOCOL_H
#define NUDGEBAND_PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>

#define NB_PACKED __attribute__((packed))

/* Service a56e0001-a414-4c37-89d9-4dcc3036748e; characteristics share the base. */
#define NB_UUID_BASE_W32 0xa56e0000u
#define NB_UUID_SERVICE  0x0001
#define NB_UUID_TIME     0x0002
#define NB_UUID_ALARM    0x0003
#define NB_UUID_STATUS   0x0004
#define NB_UUID_CONTROL  0x0005
#define NB_UUID_LOG      0x0006

struct NB_PACKED nb_time {
	uint32_t utc;
	int16_t tz_offset_min;
	uint16_t reserved;
};

#define NB_ALARM_VERSION        1
#define NB_ALARM_FLAG_ENABLED   0x01
#define NB_ALARM_FLAG_SMARTWAKE 0x02

struct NB_PACKED nb_alarm_cfg {
	uint8_t version;
	uint8_t flags;
	uint8_t days; /* bit 0 Monday ... bit 6 Sunday; 0 = next occurrence only */
	uint8_t hour; /* local */
	uint8_t minute;
	uint8_t window_min;
	uint8_t intensity;
	uint8_t pattern; /* 0 soft ramp, 1 slow pulses, 2 heartbeat */
	uint8_t ramp_s;
	uint8_t buzz_s;
	uint8_t repeat_min;
	uint8_t max_repeats;
};

enum nb_state {
	NB_STATE_IDLE = 0,
	NB_STATE_TRACKING = 1,
	NB_STATE_IN_WINDOW = 2,
	NB_STATE_WAKING = 3,
	NB_STATE_WAIT_REPEAT = 4,
};

#define NB_STATUS_VERSION      1
#define NB_FLAG_DOCKED         0x01
#define NB_FLAG_CHARGING       0x02
#define NB_FLAG_TIME_SET       0x04
#define NB_FLAG_ALARM_ARMED    0x08
#define NB_FLAG_LOG_HAS_DATA   0x10

enum nb_wake_reason {
	NB_WAKE_NONE = 0,
	NB_WAKE_LIGHT_SLEEP = 1,
	NB_WAKE_DEADLINE = 2,
	NB_WAKE_TEST = 3,
	NB_WAKE_EXACT = 4,
};

struct NB_PACKED nb_status {
	uint8_t version;
	uint8_t state;
	uint8_t battery_pct;
	uint8_t flags;
	uint32_t next_alarm_utc;
	uint8_t fw_major;
	uint8_t fw_minor;
	uint8_t last_wake_reason;
	uint8_t reserved;
	uint32_t last_wake_utc;
	uint16_t stored_epochs;
};

/* Control point opcodes and results */
#define NB_CP_TEST_BUZZ 0x01
#define NB_CP_STOP_BUZZ 0x02
#define NB_CP_LOG_READ  0x03
#define NB_CP_LOG_CLEAR 0x04
#define NB_CP_DISMISS   0x05
#define NB_CP_IDENTIFY  0x06
#define NB_CP_RESPONSE  0x80

enum nb_cp_result {
	NB_CP_OK = 0,
	NB_CP_UNSUPPORTED = 1,
	NB_CP_INVALID = 2,
	NB_CP_BUSY = 3,
	NB_CP_NOT_READY = 4,
};

/* Sleep log notifications */
#define NB_LOG_DATA  0x01
#define NB_LOG_EVENT 0x02
#define NB_LOG_END   0x03

struct NB_PACKED nb_log_data_hdr {
	uint8_t type;
	uint16_t seq;
	uint32_t first_epoch_utc;
	uint8_t epoch_s;
	uint8_t count;
	/* followed by count x u16 activity */
};

struct NB_PACKED nb_log_event {
	uint8_t type;
	uint16_t seq;
	uint32_t utc;
	uint8_t event;
	uint8_t arg;
};

struct NB_PACKED nb_log_end {
	uint8_t type;
	uint16_t seq;
	uint16_t packets;
};

_Static_assert(sizeof(struct nb_time) == 8, "Time is 8 bytes");
_Static_assert(sizeof(struct nb_alarm_cfg) == 12, "Alarm config is 12 bytes");
_Static_assert(sizeof(struct nb_status) == 18, "Status is 18 bytes");
_Static_assert(sizeof(struct nb_log_data_hdr) == 9, "Log DATA header is 9 bytes");
_Static_assert(sizeof(struct nb_log_event) == 9, "Log EVENT is 9 bytes");
_Static_assert(sizeof(struct nb_log_end) == 5, "Log END is 5 bytes");

/* Defaults from the spec. */
void nb_alarm_cfg_default(struct nb_alarm_cfg *cfg);

/* True if every field is in range (the band answers ATT 0x13 otherwise). */
bool nb_alarm_cfg_valid(const struct nb_alarm_cfg *cfg);

/* Activity values that fit one DATA packet at this ATT MTU. */
static inline uint8_t nb_log_epochs_per_packet(uint16_t mtu)
{
	uint32_t n = (mtu - 3u - sizeof(struct nb_log_data_hdr)) / 2u;

	return n > 255u ? 255u : (uint8_t)n;
}

#endif
