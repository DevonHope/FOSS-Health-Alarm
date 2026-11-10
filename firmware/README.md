# NudgeBand firmware

Firmware for the NudgeBand wristband (band **rev C**, nRF54L10). It tracks movement through the
night and, in the window before your alarm, buzzes gently at a moment of light sleep.

> **Status:** early. Not yet run on hardware (the boards are on order). The plan and progress are in
> [`TODO.md`](TODO.md). The Bluetooth contract with the Android app is
> [`docs/ble-protocol.md`](../docs/ble-protocol.md).

## Layout

```
firmware/
├── TODO.md                  the plan, phase by phase
├── CMakeLists.txt, prj.conf  Zephyr application
├── west.yml                 manifest for building with upstream Zephyr (used by CI)
├── boards/nudgeband/        board definition: pins, crystals, DC/DC, I2C (target nudgeband/nrf54l10/cpuapp)
├── dts/bindings/            devicetree binding for the board's GPIO signals
├── src/
│   ├── main.c               state machine: track, smart wake, buzz, repeat
│   ├── smartwake.c/.h       smart-wake decision            (pure C, host-tested)
│   ├── activity.c/.h        movement per 30 s epoch        (pure C, host-tested)
│   ├── alarm.c/.h           next alarm time from the config (pure C, host-tested)
│   ├── protocol.c/.h        Bluetooth byte layouts          (pure C, host-tested)
│   ├── ble.c                Bluetooth service
│   ├── accel.c              LIS2DW12 motion sensor
│   ├── haptics.c            DRV2605L motor driver
│   ├── led.c                IS31FL3193 LED driver
│   ├── pmic.c               BQ25125 charger
│   └── board_io.c           board GPIOs
└── tests/host/              unit tests that run on a PC
```

## Run the unit tests (any PC with gcc or clang)

```sh
make -C firmware/tests/host
```

## Build

With upstream Zephyr (what CI does):

```sh
mkdir nudgeband-ws && cd nudgeband-ws
git clone https://github.com/DevonHope/NudgeBand nudgeband
west init -l nudgeband --mf firmware/west.yml
west update
west build -b nudgeband/nrf54l10/cpuapp nudgeband/firmware
```

This needs the Zephyr SDK (ARM toolchain) and Zephyr's Python requirements; see Zephyr's
[Getting Started guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html).

With nRF Connect SDK (v3.1 or later), from an NCS workspace:

```sh
west build -b nudgeband/nrf54l10/cpuapp path/to/NudgeBand/firmware
```

## Flash and read logs

The band has no USB and no UART. Put it on the dock: the dock is a CMSIS-DAP debug probe on the
band's SWD pins, and the firmware logs over SEGGER RTT through the same pins. The exact flashing and
RTT commands are still to be worked out on the first boards (TODO.md, 0.4 and 0.5).
