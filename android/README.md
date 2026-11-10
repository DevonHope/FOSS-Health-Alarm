# NudgeBand Android app

A small, free and open-source companion app for the NudgeBand. The band does smart wake on its own;
the app is for setting it up and looking back at past nights.

**Status:** first version, built before any band exists. It works end to end with a **simulated
band**, so you can try every screen now. Real Bluetooth code is written to the spec but untested
until the first boards are running firmware.

## What it does

- **Band tab:** find and connect to your band (or the simulated one), see battery, state, next alarm,
  last wake-up and firmware version. Test the motor, blink the LED, stop a ringing alarm.
- **Alarm tab:** alarm time, days, on/off, smart wake on/off, wake window (5 to 60 min), vibration
  pattern, strength, soft start and buzz length. Changes go to the band when you tap **Save to band**.
- **Sleep tab:** **Sync** downloads the band's movement log. Each night shows a chart of deep / light /
  awake (an estimate from movement only), when the window started, and when and why it woke you.
  History is kept on the phone.
- The app sets the band's clock every time it connects.

## Try it with the simulated band

1. Install the APK (see below) and open the app. "Use simulated band" is on by default.
2. Band tab: **Find my band**, then tap **NudgeBand-SIM1**.
3. Alarm tab: pick a time and tap **Save to band**.
4. Band tab: **Simulate last night**. This fakes a night of sleep that ends at your alarm time and
   runs the same smart-wake rule the firmware uses.
5. Sleep tab: **Sync** to download and view it.

## Get the APK

Every push that changes `android/` builds a debug APK on GitHub Actions
(workflow "Android app", artifact **nudgeband-debug-apk**). Download the zip, unzip it, and install the
`.apk` on your phone (allow installs from your browser or file manager when asked).

Requires Android 8.0 or newer. Works without Google services (tested target: /e/OS and other
de-Googled phones; no Play Services are used).

## Build it yourself

```
cd android
./gradlew :app:assembleDebug        # APK in app/build/outputs/apk/debug/
./gradlew :protocol:test            # protocol + simulated band tests (no Android SDK needed:
                                    # set NUDGEBAND_PROTOCOL_ONLY=1)
```

Needs JDK 17 and the Android SDK (Android Studio provides both).

## Layout

```
android/
├── protocol/   plain Kotlin: the Bluetooth message formats, log transfer, smart-wake rule mirror,
│               and MockBand (the simulated band). Unit-tested on any computer.
└── app/        the Android app (Jetpack Compose)
    ├── band/   BandConnection: BleBandConnection (real Bluetooth) and SimulatedBandConnection
    ├── data/   SleepStore: downloaded nights saved on the phone
    └── ui/     Band, Alarm and Sleep screens
```

The Bluetooth protocol is in [`docs/ble-protocol.md`](../docs/ble-protocol.md). It is shared with
the firmware; change both together.

## Not done yet

- Pairing and bonding with a real band (the spec asks for LE Secure Connections; Android will show
  its pairing prompt on first connect). Untested.
- Firmware updates over Bluetooth (MCUmgr), later.
- Reconnect automatically in the background, and a notification when a sync is due.
- Signed release builds and F-Droid metadata.
