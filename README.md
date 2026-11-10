# NudgeBand

**A small, open-source wristband that wakes you up gently.**

Set a wake-up time, and NudgeBand watches how you move in your sleep. During the 30 minutes before
your alarm, it waits for a moment of light sleep and wakes you with a soft vibration on your wrist,
with no sound and no phone needed. If you never reach light sleep, it still wakes you at your set time.

Everything is open: the circuit boards, the 3D-printed case, the charging dock and the strap pattern.
You can build one yourself.

> **Status:** prototype PCBs ordered (November 2026). Nothing has been built or tested yet.
> See [Current status](#current-status).

---

## How it works

1. **You wear it to bed.** A low-power motion sensor (accelerometer) measures how much you move.
2. **It estimates your sleep stage.** Less movement usually means deeper sleep, and small movements
   usually mean light sleep.
3. **It picks the best moment.** In the 30-minute window before your alarm, it waits for light sleep,
   because waking from light sleep feels easier than waking from deep sleep.
4. **It nudges you awake.** A tiny vibration motor ramps up gently instead of buzzing suddenly.
5. **You put it on the dock.** The dock charges the band and is also used to load new firmware.

The band has no screen and no USB port. It is sealed except for four small gold contacts on the
underside that touch spring pins in the dock.

## What's in it

| Part | What it does |
| --- | --- |
| Nordic nRF54L10 | The main chip, with Bluetooth Low Energy built in |
| Motion sensor (accelerometer) | Tracks movement through the night |
| DRV2605L + 8 mm vibration motor | Gentle, ramped vibration |
| TI BQ25125 | Charges the battery |
| 60 mAh LiPo battery | Expected to last about a month per charge (estimate, not yet measured) |
| RGB LED | Shows status through a thin window in the case, with no hole |

- **Board:** 33 x 15 mm, 4-layer, assembled by JLCPCB
- **Case:** about 45 x 19 x 10 mm, 3D-printed in PETG, held shut by one M2 screw
- **Dock:** USB-C, magnets to hold the band in place, and a built-in programmer (RP2040 running `debugprobe`)
- **Strap:** 16 mm wide, sewn from a free pattern (Velcro or elastic with a buckle)

## Current status

*Last updated: 10 November 2026*

| Area | Status |
| --- | --- |
| Hardware design | ✅ Done. Band and dock **rev C** finished and reviewed (DRC/ERC clean) |
| PCBs | 📦 **Ordered.** Waiting for delivery |
| Case and dock housing | ✅ Designed. Ready to print and test-fit |
| Strap | ✅ Sewing patterns ready |
| Firmware | 🛠️ **Started.** Plan in [`firmware/TODO.md`](firmware/TODO.md); smart-wake logic written and unit-tested, drivers drafted, not yet run on hardware |
| Android app | 🧪 **First version** in [`android/`](android/). Works with a simulated band; Bluetooth spec in [`docs/ble-protocol.md`](docs/ble-protocol.md) |
| Testing | ⏳ Waits for boards. First checks: power-up, charging, radio range, vibration |

**Up next:** assemble the first boards when they arrive, print the case, bring up the firmware
(charger setup, motion sensor, vibration), then test smart-wake on real nights.

**Known limitations:**
- The radio and antenna are not certified (FCC, IC or CE). Treat it as a personal project, not a product.
- The antenna may need tuning on the first boards.
- Battery life is a datasheet estimate until it is measured.

## Repository layout

```
hardware/
├── band/      the wristband: PCB, case and contact carrier for each revision (build rev C)
├── dock/      the charging and programming dock: PCB and housing for each revision (build rev C)
├── strap/     strap sewing patterns (PDF)
├── reviews/   design reviews of the boards
└── tools/     helper scripts (e.g. printability check)
android/       the Android companion app (and a simulated band for testing)
firmware/      band firmware (Zephyr): plan in TODO.md, source, unit tests
docs/          roadmap, parts research, design notes and the Bluetooth protocol
```

Older revisions (A and B) are kept for reference. Each folder has its own README with details.
[`hardware/README.md`](hardware/README.md) lists exactly what to order and what to print.

## Building one

1. **Order the boards.** Use the fab files in `hardware/band/rev-c/pcb/fab/` and `hardware/dock/rev-c/pcb/fab/`
   (JLCPCB with assembly), plus the small contact-carrier board.
2. **Buy the extras.** Spring pins, magnets, battery and motor are listed in
   [`BUY-LIST.md`](hardware/band/rev-a/contact-carrier/BUY-LIST.md).
3. **Print the case and dock** in PETG. Print notes are in each `case/` folder.
4. **Sew the strap** from the pattern in `hardware/strap/`.
5. **Flash the firmware** through the dock (see [`firmware/README.md`](firmware/README.md); not ready yet).

Design tools: KiCad 10 for the PCBs, Python scripts for the case models.

## License

[MIT](LICENSE). Use it, change it and share it.
