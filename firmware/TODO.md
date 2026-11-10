# NudgeBand firmware to-do

The plan for the band's firmware, from first power-up to nightly use. Tick items off as they land.
Numbers (like **2.1**) are referenced from `TODO(...)` comments in the code.

**Where things stand (10 November 2026):** boards are ordered, nothing has run on hardware yet.
The hardware-independent parts are written and unit-tested on a PC (smart-wake decision, movement
measure, alarm times, Bluetooth byte layouts), and the whole firmware builds in CI. The rest of
`src/` is a first draft that follows the
band README, written before any board existed: expect fixes at bring-up.

- Target board: band **rev C** (`hardware/band/rev-c/pcb`, pin map and part notes in its README).
- Chip: nRF54L10 (1 MB RRAM, 192 KB RAM). Parts on one I2C bus: LIS2DW12 motion sensor 0x19,
  DRV2605L motor driver 0x5A, IS31FL3193 LED driver 0x68, BQ25125 charger 0x6A.
- Bluetooth contract with the Android app: [`docs/ble-protocol.md`](../docs/ble-protocol.md)
  (owned jointly with the app; change both sides together).
- Smart wake runs **on the band**. The phone only sets it up and reads the history.

Legend: `[x]` done, `[~]` drafted (written, never run on hardware), `[ ]` not started.

---

## 0. Tools and project setup

- [x] **0.1** Zephyr application in `firmware/` with its own board definition
  (`boards/nudgeband`, target `nudgeband/nrf54l10/cpuapp`).
- [x] **0.2** Host unit tests for the pure-C code (`make -C firmware/tests/host`), run in CI.
- [x] **0.3** CI build of the firmware with upstream Zephyr v4.2 (`.github/workflows/firmware.yml`,
  manifest `firmware/west.yml`). The whole app (drivers, Bluetooth) compiles; the `.hex` is a CI
  artifact. CMake is pinned to 3.x because Zephyr v4.2 breaks under CMake 4.
- [ ] **0.4** Flash and debug through the dock. The dock is a CMSIS-DAP probe (RP2040 running
  `debugprobe`). Find the runner that handles the nRF54L10 over CMSIS-DAP (pyOCD with the nRF54L
  pack, or OpenOCD), including erase and recovery of a locked chip. Fallback: a J-Link or an
  nRF54L15 DK's on-board debugger wired to the dock pins.
- [ ] **0.5** Read logs over RTT through the dock (`pyocd rtt` or OpenOCD's RTT server). Write the
  exact commands into `firmware/README.md`.
- [ ] **0.6** Decide upstream Zephyr vs nRF Connect SDK for releases. The code is written to build
  with both. NCS brings Nordic's SoftDevice Controller (better tested Bluetooth on nRF54L) and its
  power tooling; upstream is lighter. Add an NCS build to CI either way.
- [ ] **0.7** Before bring-up, practise on an nRF54L15 DK (as an nRF54L10, the
  `nrf54l15dk/nrf54l10/cpuapp` target) with breakout boards for the LIS2DW12 and DRV2605L. This
  shakes out most of the drivers before the bands arrive.

## 1. Board bring-up (first boards, on the bench)

Do these on one board at a time, in order, powered from the dock.

- [ ] **1.1** Power: check the 2.0 V rail (U203) and PMID with the dock on and with a cell only.
  Check the dock's SWD level shifters (band side at 1.8 V) talk to the band's 2.0 V logic.
- [ ] **1.2** SWD connects; flash a minimal "hello" image and see the RTT log.
- [ ] **1.3** Clocks: confirm both crystals start with the internal load capacitors (LFXO 17 pF,
  HFXO 15 pF in the board file, copied from the nRF54L15 DK which uses the same crystal CL values).
  Measure the 32.768 kHz error over a few hours against the phone's time and adjust.
- [ ] **1.4** DC/DC regulator on (board file sets it); compare current with it on and off.
- [ ] **1.5** I2C scan: all four addresses answer (0x19, 0x5A, 0x68, 0x6A).
- [ ] **1.6** Sleep current: everything idle, radio off. Target from the power budget is 5-15 uA
  total. Measure with a Power Profiler Kit (or a uCurrent) between the cell and the board.
- [ ] **1.7** Antenna tuning and range: run Nordic's `radio_test` sample and follow "Antenna tuning"
  in the band README (RSSI method if there is no VNA). Keep TX power at 0 dBm until tuned.

## 2. Part drivers (`src/`)

- [~] **2.1** BQ25125 charger (`pmic.c`).
  - [x] Plan: stay in default mode (it already charges at 4.2 V / 30 mA), keep /CD low (Hi-Z,
    0.7 uA) and only raise it on battery to talk I2C. Never raise /CD while docked.
  - [~] Docked detection from /PG (DOCK_PG, internal pull-up).
  - [ ] Battery percent from VBMON (reg 0x0A): conversion table from the datasheet, then a LiPo
    voltage-to-charge curve. Find out whether a VBMON read alone starts host mode and its 50 s
    watchdog.
  - [ ] Charging flag from the status register for the app.
  - [ ] Load-switch mode for the LED supply (reg 0x07 + LS_CTRL), re-written while the LED is on.
  - [ ] Ship mode for storage (EN_SHIPMODE with VIN absent, /CD and /MR high).
  - [ ] /INT (PMIC_INT) handling: fault logging, wake from System OFF if used.
- [~] **2.2** LIS2DW12 motion sensor (`accel.c`): low-power 12-bit, 12.5 Hz, +/-2 g, FIFO
  watermark of 25 samples on INT1 (a wake every 2 s).
  - [ ] Check the mg scaling against a still board (gravity should read about 1000 mg).
  - [ ] Measure the current of the 2 s FIFO wakes; try a lower rate (e.g. 6.25 Hz with 31-sample
    batches) if the budget needs it, and re-check the smart-wake thresholds if the rate changes.
  - [ ] Off-wrist / not-moving-for-hours detection (stationary for a long time = on the table).
- [~] **2.3** DRV2605L motor driver (`haptics.c`): real-time playback with the firmware ramping the
  strength; patterns soft ramp, slow pulses and heartbeat; EN low between buzzes.
  - [ ] Auto-calibration for the VG0832012 LRA (rated voltage, overdrive clamp, drive time from
    its resonant frequency, from the motor datasheet). Run once at first boot, store the result.
  - [ ] Check the motor actually runs from VBAT across the cell's range (3.0-4.2 V).
  - [ ] Tune what "gentle" means: start level, ramp length, the floor where it can't be felt.
- [~] **2.4** IS31FL3193 LED driver (`led.c`): register writes are a guess from the README.
  - [ ] Check every register bit against the datasheet; pick the current for about 5 mA.
  - [ ] Status colours: charging (on the dock), charged, low battery, pairing, identify (blink).
    Off the dock the LED stays off to save power.
- [ ] **2.5** Brown-out and low battery: stop tracking and buzzing below a safe voltage; the BQ
  cuts off at 3.0 V by itself.

## 3. Core application

- [~] **3.1** Movement tracking: FIFO batches into the movement measure (`activity.c`, tested),
  one value per 30 s epoch.
  - [ ] Mark epochs as "no data" (0xFFFF) while docked, off the wrist or before the time is set.
- [~] **3.2** Timekeeping: UTC from the phone plus uptime (GRTC on the LFXO).
  - [ ] Keep time across a reset where possible (retained RAM).
  - [ ] Daylight-saving changes overnight when the phone is not connected: have the app send the
    next offset change (time and new offset), or accept that DST nights rely on the phone.
- [~] **3.3** Alarm and wake sequence (`alarm.c` tested, `main.c` drafted): next alarm from
  hour, minute, repeat days and the UTC offset; buzz, pause, repeat up to the limit.
  - [ ] Dismiss on the band. The spec says double tap, but tap detection needs the sensor at
    400 Hz or more, and the motor shaking the sensor will look like taps. Options: listen for taps
    only in the pauses between buzzes (sensor switched to a fast rate then), or treat sustained
    movement after the buzz as "awake". Decide on real hardware.
  - [ ] Dismissing during the window should skip only today's alarm (today it re-arms the same alarm).
  - [ ] A one-off alarm (no repeat days) switches itself off after it fires.
- [x] **3.4a** Smart-wake decision (`smartwake.c`, host-tested). See "Smart-wake algorithm" below.
- [ ] **3.4** Sleep log storage: keep the last 7 nights of epochs (about 2 KB per night) in RRAM
  (ZMS or a small ring buffer partition), with wake and dock events, for the app to download.
- [ ] **3.5** Keep settings (alarm, UTC offset, motor calibration) in flash so a reset doesn't lose
  them.
- [ ] **3.6** Power states: sleep between FIFO batches; on the dock, stop tracking and only charge;
  System OFF with wake on the dock (/PG) for long storage.
- [ ] **3.7** Watchdog (WDT) so a hang can't leave the band dead or the motor running.

## 4. Bluetooth (contract: `docs/ble-protocol.md`)

- [~] **4.1** Advertising as `NudgeBand-XXXX` with the service UUID, about 1 s apart.
  - [ ] Tune the interval for battery; advertise faster for 30 s after leaving the dock.
  - [ ] Stop advertising at night after the phone has set things up (optional, saves power).
- [~] **4.2** Security: LE Secure Connections, Just Works, one bond kept in settings; config
  writes need an encrypted link.
  - [ ] Clear the bond (from the dock: a command over RTT, or a button if a later rev has one).
- [~] **4.3** NudgeBand service: Time, Alarm config, Status (notify), Control point (indicate)
  drafted in `ble.c`; byte layouts in `protocol.h` are size-checked against the spec.
  - [ ] Status notifications on battery changes of 5 % or more.
- [ ] **4.4** Sleep log transfer: `LOG_READ` streams DATA, EVENT and END packets sized to the ATT
  MTU (5 epochs per packet at MTU 23, 117 at MTU 247); `LOG_CLEAR`.
- [~] **4.5** Battery and Device Information services (Zephyr's BAS and DIS); feed BAS from 2.1.
- [ ] **4.6** Updates over the air: MCUboot + MCUmgr SMP over Bluetooth. Signed images; keep the
  dock (SWD) as the recovery path.
- [ ] **4.7** Test against the app with nRF Connect for Mobile first, then the NudgeBand app.

## 5. Testing on real nights

- [ ] **5.1** Wear it for a week with logging on and no smart wake; download the logs and compare
  with how the nights felt (and with Somn's phone-based log on the same nights if possible).
- [ ] **5.2** Tune the smart-wake numbers (threshold floor, factor, confirm epochs) from those logs.
  Add the real nights to the host tests as fixtures.
- [ ] **5.3** Battery life: measure a full week's drain and check against the 0.7-1 mAh a day budget.
- [ ] **5.4** Failure checks: reset in the middle of the night, flat battery, lost phone
  connection, docked overnight, alarm while charging.

## 6. Releases

- [ ] **6.1** Version numbers (`VERSION` file), shown in Status and Device Information.
- [ ] **6.2** CI attaches the built `.hex` and the signed update image to GitHub releases.
- [ ] **6.3** Flashing guide for builders in `firmware/README.md` (dock + one command).
- [ ] **6.4** Release builds turn RTT logging off so the debug domain powers down.

---

## Smart-wake algorithm (what the code does today)

Per 30 s epoch, at 12.5 Hz, the band adds up `|dx| + |dy| + |dz|` between consecutive samples, in
mg, ignoring changes of 20 mg or less. That is the epoch's **activity** (0-65534; 0xFFFF = no data).

- The **threshold** is 3 x the median activity of the night so far, but never below 300. During the
  first 10 minutes of a night (fewer than 20 epochs) it is just 300.
- **Light sleep** = at least 2 of the last 3 epochs at or above the threshold (only epochs inside
  the window count), so a single twitch does not wake you.
- Inside the window (default 30 min before the alarm), the first light-sleep epoch starts the wake.
  If none comes, it wakes at the alarm time.
- With smart wake turned off in the alarm config, the window is 0 and it simply wakes at the alarm.

All of these numbers are first guesses, to be tuned from real nights (5.2).
