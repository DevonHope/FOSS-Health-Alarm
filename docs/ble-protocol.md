# NudgeBand Bluetooth protocol (v1, draft)

This is the contract between the band firmware (`firmware/`) and the Android app (`android/`).
Both sides must change together. Bump `version` fields when a layout changes.

**Status:** draft, written before the first boards arrived. Nothing here has run on real hardware.
The app's simulated band (`android/protocol/.../MockBand.kt`) implements this spec so the app can be
tested now.

## Big picture

- **Smart wake runs on the band.** The band keeps time, logs movement all the time, and decides when
  to vibrate. The phone does not need to be nearby at night.
- **The app is for setup and history:** set the clock, set the alarm and wake window, test the
  vibration, read the battery and status, and download the movement log to show past nights.
- All multi-byte numbers are **little-endian**. Times are **UTC Unix seconds** (`u32`). The band works
  out local time from the UTC offset the app writes.

## Advertising

| Field | Value |
| --- | --- |
| Name (scan response) | `NudgeBand-XXXX` (last 2 bytes of the device address, hex) |
| Advertised service | NudgeBand service UUID (128-bit), in the advertising packet |
| Interval | about 1 s when not connected (tune for battery later), faster for 30 s after leaving the dock |
| Connectable | yes |

## Security

- Pair with **LE Secure Connections, Just Works**, and bond on first connect.
- All NudgeBand characteristics except Status need an **encrypted** link for writes.
- The band keeps one bond. A long press on the dock button (or `LOG_CLEAR` with a flag, TBD) clears it.

## Services

| Service | UUID | Use |
| --- | --- | --- |
| Battery (standard) | `0x180F` | Battery Level `0x2A19` (read, notify) |
| Device Information (standard) | `0x180A` | Firmware Revision `0x2A26`, Hardware Revision `0x2A27`, Model Number `0x2A24` |
| NudgeBand | `a56e0001-a414-4c37-89d9-4dcc3036748e` | Everything below |
| MCUmgr SMP (later) | `8d53dc1d-1db7-4cd3-868b-8a527460aa84` | Firmware updates over the air |

NudgeBand UUIDs share the base `a56eXXXX-a414-4c37-89d9-4dcc3036748e`:

| Characteristic | Short | Properties | Size |
| --- | --- | --- | --- |
| Time | `0x0002` | read, write | 8 |
| Alarm config | `0x0003` | read, write | 12 |
| Status | `0x0004` | read, notify | 18 |
| Control point | `0x0005` | write, indicate | 1 to 20 |
| Sleep log | `0x0006` | notify | up to MTU - 3 |

The app asks for an ATT MTU of 247. Everything must still work at the default MTU of 23.

### Time (`0x0002`)

| Offset | Type | Field |
| --- | --- | --- |
| 0 | u32 | UTC Unix seconds |
| 4 | i16 | UTC offset in minutes (e.g. -300 for EST) |
| 6 | u16 | reserved, 0 |

The app writes this on every connection. The band sets `time_set` in Status once it has a time.

### Alarm config (`0x0003`)

| Offset | Type | Field | Notes |
| --- | --- | --- | --- |
| 0 | u8 | version | 1 |
| 1 | u8 | flags | bit 0 enabled, bit 1 smart wake (0 = buzz exactly at the alarm time) |
| 2 | u8 | days | bit 0 Monday ... bit 6 Sunday. 0 = one-off, next occurrence only |
| 3 | u8 | hour | local time, 0 to 23 |
| 4 | u8 | minute | 0 to 59 |
| 5 | u8 | window minutes | 0 to 60, default 30. The window ends at the alarm time |
| 6 | u8 | intensity | motor drive, 0 to 255, default 150 |
| 7 | u8 | pattern | 0 soft ramp, 1 slow pulses, 2 heartbeat; default 0 |
| 8 | u8 | ramp seconds | soft start, 0 to 60, default 20 |
| 9 | u8 | buzz seconds | how long one wake attempt lasts, 5 to 120, default 30 |
| 10 | u8 | repeat minutes | pause before buzzing again if not dismissed, 0 = never, default 2 |
| 11 | u8 | max repeats | 0 to 10, default 5 |

The band rejects a write with out-of-range values (ATT error `0x13`, value not allowed).

Dismiss: the `DISMISS` command from the app always works. Dismissing on the band itself is TBD
(tap in the pauses between buzzes, or sustained movement): double-tap detection needs a 400 Hz+
sample rate, the band samples at 12.5 Hz, and the motor's shaking looks like taps.

### Status (`0x0004`)

| Offset | Type | Field | Notes |
| --- | --- | --- | --- |
| 0 | u8 | version | 1 |
| 1 | u8 | state | 0 idle, 1 tracking, 2 in wake window, 3 waking (buzzing), 4 waiting to repeat |
| 2 | u8 | battery percent | from the BQ25125 VBMON reading, 2 % steps (no fuel gauge) |
| 3 | u8 | flags | bit 0 docked, bit 1 charging, bit 2 time set, bit 3 alarm armed, bit 4 log has data |
| 4 | u32 | next alarm UTC | 0 if none; the end of the next wake window |
| 8 | u8 | firmware major | |
| 9 | u8 | firmware minor | |
| 10 | u8 | last wake reason | 0 none, 1 light sleep, 2 window ended (deadline), 3 test buzz, 4 exact alarm |
| 11 | u8 | reserved | 0 |
| 12 | u32 | last wake UTC | 0 if none |
| 16 | u16 | stored log epochs | number of 30 s epochs in flash |

The band notifies Status when it changes (state, flags, battery change of 5 % or more).

### Control point (`0x0005`)

Write with response. The band answers each command with an **indication**:
`0x80, request opcode, result` and optional data.

| Opcode | Command | Parameters |
| --- | --- | --- |
| `0x01` | TEST_BUZZ | u8 intensity percent, u8 seconds (1 to 10) |
| `0x02` | STOP_BUZZ | none |
| `0x03` | LOG_READ | u32 from UTC (0 = everything stored) |
| `0x04` | LOG_CLEAR | none |
| `0x05` | DISMISS | none (stops today's alarm) |
| `0x06` | IDENTIFY | none (blink the LED twice) |

| Result | Meaning |
| --- | --- |
| 0 | OK |
| 1 | opcode not supported |
| 2 | invalid parameter |
| 3 | busy (e.g. log transfer already running) |
| 4 | not ready (e.g. time not set) |

`LOG_READ` answers OK first, then streams Sleep log notifications, ending with an END packet.
Until the flash log exists in the firmware, `LOG_READ` and `LOG_CLEAR` answer 1 (not supported).

### Sleep log (`0x0006`)

Each notification starts with a type byte and a `u16` sequence number (starting at 0 for each transfer).

**DATA (`0x01`)**

| Offset | Type | Field |
| --- | --- | --- |
| 0 | u8 | type = 1 |
| 1 | u16 | sequence |
| 3 | u32 | UTC of the first epoch in this packet |
| 7 | u8 | epoch length in seconds (30) |
| 8 | u8 | count N |
| 9 | N x u16 | activity per epoch |

Activity is the raw movement for that 30 s epoch: the accelerometer is sampled at 12.5 Hz, and for
each sample the band adds `|dx| + |dy| + |dz|` (change from the previous sample, in mg) when it is above
a 20 mg deadband. The sum is in mg and saturates at 65534. `0xFFFF` means no data (band off the wrist,
on the dock, or not running). About 960 epochs (1.9 KB) per 8-hour night.

N fits the MTU: N = (MTU - 3 - 9) / 2, so 5 at the default MTU of 23 and 117 at MTU 247.

**EVENT (`0x02`)**

| Offset | Type | Field |
| --- | --- | --- |
| 0 | u8 | type = 2 |
| 1 | u16 | sequence |
| 3 | u32 | UTC |
| 7 | u8 | event: 1 window started, 2 woke in light sleep, 3 woke at window end, 4 dismissed, 5 docked, 6 undocked, 7 exact alarm |
| 8 | u8 | argument (event specific, 0 if unused) |

**END (`0x03`)**

| Offset | Type | Field |
| --- | --- | --- |
| 0 | u8 | type = 3 |
| 1 | u16 | sequence |
| 3 | u16 | number of packets sent before this one |

The app checks that sequence numbers have no gaps and that the END count matches; if not, it asks
again.

## Smart-wake rule

This is the firmware's rule (`firmware/src/smartwake.c`). The app mirrors it to draw past nights and
to drive the simulated band, so change both together.

1. Each 30 s epoch, take the activity value (epochs with no data are skipped).
2. **Threshold** = max(300, 3 x the median activity of the night so far). While the night has fewer
   than 20 epochs, the threshold is just 300.
3. **Light sleep** = at least 2 of the last 3 epochs are at or above the threshold. For waking, those
   epochs must be inside the wake window.
4. Wake at the first light-sleep epoch in the window; otherwise wake at the alarm time.
5. Smart wake off, or a window of 0, means an exact alarm at the set time.

The app also shows **awake** when the last 3 epochs average 3000 mg or more. That is for the
sleep chart only; the band does not use it.

All numbers are first guesses and will be tuned from real nights.

## Change log

- v1 draft (2026-11-10): first version, agreed between the app and firmware threads: 30 s epochs,
  u16 activity in mg, intensity 0-255 plus pattern id, firmware version and last wake in Status.
  Smart-wake rule replaced with the firmware's median-threshold rule; band-side dismiss is TBD.
