# Hardware roadmap

This band does one thing: it watches wrist motion during the night and, inside a
30 minute window before your alarm, buzzes gently when you are in light sleep.
If it never sees light sleep, it buzzes at the set time. The wake logic runs on
the band, so it works with no phone. A FOSS Android app comes later and is only
for settings and history.

That narrow job is what lets the hardware be small. There is no screen, no
heart rate sensor and no GPS; the parts list is a Bluetooth chip, an
accelerometer, a vibration motor and its driver, a small battery, and a charger.

## Size target

The reference point is the Google Fitbit Air pod: 34.9 x 17 x 8.3 mm, 5.2 g,
with a 34.5 mAh cell (see the
[earlier research doc](https://claude.ai/artifact/C2vRboE4HNkBdYpmuuvmsz)).
The Air also runs heart rate, SpO2 and a gyroscope; this band does not, so it
can match that size with a similar or bigger battery and last longer.

Targets for the final pod:

| Item | Target |
| --- | --- |
| Pod size | 35 x 18 x 8 mm or smaller |
| Battery life | 2 weeks or more per charge |
| Charging | Sealed case, contact pads + magnets on a dock |
| Radio | Bluetooth LE, for settings and logs only |

### Power budget (estimate)

| Load | Rough average |
| --- | --- |
| SoC asleep with RTC, waking about once a minute to read the accelerometer FIFO | a few uA |
| Accelerometer in low-power mode (25 to 100 Hz) | about 1 to 4 uA |
| Occasional BLE advertising / sync | a few uA averaged |
| Motor: about 60 mA for about 30 s per morning | about 0.5 mAh per day |

That is roughly 1 mAh per day, so a 40 mAh cell should last a month and a
100 mAh cell much longer. These are datasheet-level guesses; stage 0 exists to
measure the real number.

### Thickness stack-up (estimate)

| Layer | mm |
| --- | --- |
| Case top wall | 0.8 |
| PCB (0.6 mm) + tallest part (8 x 8 x 1 mm SiP module) | 1.6 |
| Clearance and foam | 0.3 |
| Battery (3 mm pouch) | 3.0 |
| Clearance and adhesive | 0.2 |
| Case bottom wall with charge pads | 0.8 |
| **Total** | **about 6.7** |

The 8 mm coin LRA (2.55 to 3.25 mm thick) sits beside the battery in the
battery layer, not on top of it, so it does not add height. Footprint is the
tighter constraint: a 12 x 30 mm cell plus an 8 mm motor fits in about
20 x 35 mm.

## Parts shortlist

Figures come from vendor product pages and should be re-checked against the
current datasheet before ordering. Items marked "check" were not fully
confirmed.

### Bluetooth SoC or module

| Option | Size | Notes |
| --- | --- | --- |
| Insight SiP **ISP2454** (nRF54L15) | 8 x 8 x 1 mm | Newest Nordic chip, lowest power, antenna and crystals inside. Pin-compatible with Insight SiP's nRF52 modules. Launched late 2024, production 2025 (check stock). |
| Insight SiP **ISP1807** (nRF52840) | 8 x 8 x 1 mm | Same footprint family, mature chip, same family as Bangle.js 2. Good fallback if ISP2454 stock is thin. |
| Raytac MDBT50Q (nRF52840) | about 10 x 15 x 2.2 mm (check) | Cheaper, easy to source and to assemble, but more than twice as thick. Fine for stage 1, too tall for the final pod. |
| Bare nRF54L15 or nRF52840 chip | QFN / WLCSP | Smallest and cheapest in volume, but you design the antenna, RF match and crystals yourself. Only worth it after stage 2 if the module is the size bottleneck. |

**Pick:** nRF54L15 as the main target, with the nRF52840 as a fallback. Use a
SiP module so the RF work and certification are already done.

### Accelerometer

| Part | Package | Current | Notes |
| --- | --- | --- | --- |
| ST **LIS2DW12** | 2.0 x 2.0 x 0.7 mm LGA | under 1 uA low-power, 50 nA off | Wake-up and activity/inactivity interrupts, FIFO. Well supported in Zephyr. |
| ST LIS2DUX12 | 2.0 x 2.0 x 0.74 mm LGA | about 3 uA (check per data rate) | 128-sample FIFO, on-chip machine learning core that could run a simple sleep/awake classifier. |
| ADI ADXL367 | 2.2 x 2.3 x 0.87 mm | 0.89 uA at 100 Hz | Lowest current, 512-sample FIFO. |
| Bosch BMA400 | 2 x 2 x 0.95 mm | 0.8 to 14.5 uA by mode | Thicker, 1 kB FIFO. |
| Bosch BMA530 | 1.2 x 0.8 x 0.55 mm | 18 uA at 100 Hz low-power | Smallest available, but uses more current. |

**Pick:** LIS2DW12 for stage 1 because it is common and easy to buy, with
ADXL367 as the low-power upgrade. A large FIFO lets the SoC sleep for most of
each minute.

### Vibration motor

| Part | Size | Drive | Notes |
| --- | --- | --- | --- |
| Vybronics **VG0825003D** (LRA) | 8.0 mm x 2.55 mm | 1.2 Vrms, 240 Hz, 48 mA typ | Thinnest coin LRA found. |
| Vybronics VG0832012 (LRA) | 8.0 mm x 3.25 mm | 1.8 Vrms, 235 Hz, 58 mA typ | Common, well documented, and comes on hobby breakout boards. |
| Precision Microdrives C08-005 (LRA) | 8 mm x 3.3 mm | 1.8 Vrms, 233 Hz, 75 mA typ | Good datasheet. |
| Vybronics VL120628H (rectangular LRA) | 12 x 6 x 2.8 mm | 2.0 Vrms, 200 Hz | Option if the layout suits a long, thin part. Check its vibration axis. |
| Vybronics VCLP1020B002L (coin ERM) | 10 mm x 2.1 mm | 3 V DC, 27 mA | Simplest option: one MOSFET and PWM, no driver IC. Buzzier and slower to start. |

**Pick:** a coin LRA (VG0832012 for prototypes, VG0825003D for the slim pod).
An LRA gives a smooth, quiet buzz and pairs with a driver that has ready-made
soft ramps.

### Haptic driver

| Part | Package | Notes |
| --- | --- | --- |
| TI **DRV2605L** | DSBGA-9 (about 1.75 mm sq) or VSSOP-10 | I2C, LRA auto-resonance, built-in effect library with smooth ramp-up effects. 4 uA shutdown. Cheap breakout boards exist. |
| TI DRV2625 | DSBGA-9 (about 1.4 mm sq) | 0.1 uA shutdown, auto-resonance, 123 built-in effects including 48 ramps, and a sequencer that can loop. Best fit for the final pod. |
| TI DRV2603 | 2 x 2 x 0.75 mm WQFN | PWM input only, no library, auto-resonance. Simplest; the SoC makes the ramp itself. |

**Pick:** DRV2605L in stages 0 and 1 (breakouts, simple package), DRV2625 for the
slim pod (smaller and lower shutdown current).

### Battery

Pouch cell names give thickness, width and length: a 401230 is 4.0 x 12 x 30 mm.

| Cell | Size (mm) | Capacity | Notes |
| --- | --- | --- | --- |
| 301230-class pouch | 3 x 12 x 30 | about 60 to 80 mAh (estimate) | Best fit for the Air-sized footprint. No authoritative listing found yet; check suppliers. |
| Akyga LP401230 | 4.0 x 12 x 30 | 110 mAh, protection circuit included | Easy to buy, 1 mm thicker. |
| Akyga LP302030 | 3.0 x 20 x 30 | 140 mAh, protection circuit included | Wider pod, but thin with lots of capacity. |
| VARTA CoinPower CP1254 | 12.1 dia x 5.4 | about 74 mAh | Rigid steel can, robust, but thick. |
| LIR2032 coin | 20 dia x 3.2 | about 45 mAh | Cheap for prototypes, but awkward in a slim band. |

Many cells from vendors such as EEMB ship bare, with no protection circuit.
Either buy cells with protection included or rely on a charger/PMIC with
protection, and check the cell's charge rate (usually 0.5C to 1C, so 20 to
50 mA for a small cell).

**Pick:** a 3 mm pouch cell of about 50 to 110 mAh with a protection circuit.
The final pick depends on the case layout in stage 2.

### Charger and power

| Part | Package | Notes |
| --- | --- | --- |
| Nordic **nPM1304** | check datasheet | PMIC made for small batteries: 4 to 100 mA charging, two buck converters, load switches, and a fuel gauge drawing 8 uA when active and zero in sleep. Pairs with the Nordic SoC (check nRF Connect SDK support). Announced July 2025. |
| TI BQ25120A | 2.5 x 2.5 mm WCSP | Charger (5 to 300 mA) + buck + LDO + button wake, 700 nA quiescent, under 50 nA ship mode. Made for wearables. |
| TI BQ25100 | 1.6 x 0.9 mm WCSP | Bare-minimum linear charger, 10 to 250 mA, 75 nA battery leakage. Smallest option. |
| Microchip MCP73831 | SOT-23-5 | Common on hobby boards; fine for stage 1, not small. |

**Pick:** nPM1304 for the slim pod (charger, regulator and fuel gauge in one).
Fall back to BQ25100 plus the SoC's internal DC-DC if board space is tight.

### Charging contacts

Put the spring pins in the dock, not the band. The band gets two flat gold
pads on its underside plus two small magnets that pull it onto the dock. This
keeps the case sealed and adds almost no height, which is how the Fitbit Air
puck works. Off-the-shelf magnetic pogo connectors (for example Mill-Max
Maxnetic, at about 10.9 mm stack height) are too tall for the band itself but
are fine to build the dock from. Low-profile Mill-Max 836/838 pogo pins (2 mm
pitch, about 5 mm tall) suit the dock side.

## Custom PCB options

| Option | Thickness | Pros | Cons |
| --- | --- | --- | --- |
| Rigid FR4, 2 or 4 layers | 0.4 to 0.8 mm (JLCPCB minimum 0.4 mm) | Cheapest, fastest, easy assembly | Flat only; very thin boards can flex during assembly |
| Flex (polyimide), 1/2/4 layers | 0.07 to 0.45 mm (JLCPCB) | Can wrap around the battery or follow the wrist; very thin | Needs stiffeners under parts; no impedance control at JLCPCB |
| Flex + stiffeners | flex plus 0.1 to 0.6 mm stiffener | Rigid islands for parts, flexible links between them | Stiffener choice matters: steel is slightly magnetic (keep it away from the magnets and pads) |
| Rigid-flex | varies | Best mechanics for a folding design | Expensive; JLCPCB does not offer it yet; PCBWay and others do (check current capabilities) |

JLCPCB flex details worth knowing: 2-layer flex is 0.11 to 0.2 mm thick, the
minimum trace/space is about 3 to 4 mil, and stiffeners come in polyimide
(0.1 to 0.25 mm), FR4 (0.1 to 1.6 mm) and stainless steel (0.1 to 0.3 mm).

**Pick:** a 4-layer rigid board at 0.6 mm for stages 1 and 2, assembled at the
fab. Move to flex with stiffeners only if the rigid pod can't hit the size
target, for example to fold the board around the battery.

### Tools

- **KiCad 10** (released March 2026) for schematic and layout. It exports STEP
  models for the case design and has design blocks and a graphical DRC rule
  editor. Rigid-flex is not a first-class feature yet, so flex boards are drawn
  as flat outlines with stiffener notes on a user layer.
- **FreeCAD** (with the KiCad StepUp workbench) or another CAD tool for the
  case and dock, using KiCad's STEP export.
- **Zephyr / nRF Connect SDK** for firmware; it has drivers for the
  LIS2DW12 and Nordic's PMICs (check DRV2605/DRV2625 support for the chosen
  version, or drive them over I2C directly).
- **Nordic Power Profiler Kit II** (or a similar current meter) to measure
  real battery life in stage 0.

### Open hardware to learn from

- [ZSWatch](https://github.com/ZSWatch/Watch-HW): open smartwatch, nRF5340,
  designed in KiCad, GPL-3.0. The best reference for layout and enclosure.
- [PineTime](https://pine64.org/documentation/PineTime/Further_information/Specifications):
  nRF52832 watch with a published schematic (PDF only, no layout source).
- [Bangle.js Sleep Phase Alarm](https://git.noordstar.me/FOSS/BangleApps/src/branch/master/apps/sleepphasealarm/README.md):
  the open-source wake logic to port.

## Staged roadmap

### Stage 0: dev-kit prototype

Goal: prove the wake algorithm and measure power, with no custom board.

- **Seeed XIAO nRF54L15 Sense** (nRF54L15, LSM6DS3TR-C 6-axis IMU, built-in
  LiPo charging). The XIAO nRF52840 Sense is the fallback, same idea.
- **DRV2605L breakout** + **VG0832012 coin LRA**.
- A small LiPo with a protection circuit (any 100 mAh-class pouch).
- 3D-printed wrist case and a strap.

Done when: the band logs motion all night, buzzes with a soft ramp inside the
window, and a measured power budget shows at least two weeks on the chosen
cell.

### Stage 1: first custom board

Goal: a wearable board with the real parts, sized for comfort but not yet slim.

- 4-layer, 0.8 mm rigid board, assembled by the fab (JLCPCB or PCBWay).
- Module (ISP2454, or MDBT50Q if easier to source), LIS2DW12, DRV2605L,
  MCP73831 or BQ25100, a protected 401230 cell, VG0832012 LRA.
- SWD test pads, a current-measure jumper, and an LED for debugging.
- Charge through pads with a simple pogo-pin dock.

Done when: it runs the stage 0 firmware unchanged except for pin mapping, and
battery life matches the stage 0 estimate.

### Stage 2: slim pod

Goal: hit the size target.

- 4-layer, 0.6 mm rigid board, parts on one side only, battery on the other.
- ISP2454 SiP (8 x 8 x 1 mm), DRV2625, nPM1304, ADXL367 or LIS2DW12.
- 3 mm pouch cell (50 to 110 mAh) and VG0825003D LRA beside it.
- Sealed case with gold contact pads and magnets; magnetic pogo dock.
- Remove debug LEDs and jumpers; keep SWD as pads under the battery.

Done when: the pod is about 35 x 18 x 8 mm or smaller and lasts two weeks.

### Stage 3: optional refinements

- Flex PCB with stiffeners folded around the battery, if stage 2 is still too
  big.
- Bare nRF54L15 chip instead of the module, only if size or cost requires it.
- Optional PPG heart rate sensor, powered only during the 30 minute window, if
  motion alone proves too coarse.

## Open questions

- Does motion alone give a good enough wake, or will heart rate be needed?
  Stage 0 answers this before any board is designed.
- Is the ISP2454 easy to buy in single quantities? If not, stage 2 uses the
  ISP1807 (same footprint) or a bare chip.
- Which 3 mm pouch cell has a reliable supplier at small quantities?
