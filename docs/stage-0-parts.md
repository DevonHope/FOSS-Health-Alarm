# Stage 0 parts list

Dev-kit prototype from the [hardware roadmap](hardware-roadmap.md#stage-0-dev-kit-prototype).
Goal: prove the motion-based wake logic and measure real battery life, with no
custom board.

Checked against store pages on **2026-10-28** (USD) and reviewed for
compatibility. Prices change, so re-check before ordering. Digi-Key blocks
automated reads, so Digi-Key part numbers, prices and stock marked "(via
Octopart)" come from Octopart's copy of the Digi-Key listing.

## Cart: two orders

No single store carries everything. The XIAO nRF54L15 Sense is only stocked by
Seeed, and Mouser carries no Vybronics LRAs. So the fewest-shipment cart is
**Seeed for the board, Digi-Key for everything else**.

### Order 1: Seeed

| Part | Part # | Qty | Unit | Link |
| --- | --- | --- | --- | --- |
| Seeed Studio XIAO nRF54L15 Sense (pick the pre-soldered header option to skip soldering headers) | 101991422 | 1 | $15.99 | [Seeed](https://www.seeedstudio.com/XIAO-nRF54L15-Sense-p-6494.html) |

### Order 2: Digi-Key

| Part | Digi-Key # | Qty | Unit | Link |
| --- | --- | --- | --- | --- |
| Adafruit DRV2605L haptic driver, STEMMA QT (Adafruit 2305) | 1528-1346-ND (via Octopart) | 1 | $7.95 | [Digi-Key](https://www.digikey.com/en/products/detail/adafruit-industries-llc/2305/5356831) |
| Vybronics VG0832012 coin LRA, 8 mm | 1670-VG0832012-ND (via Octopart) | 3 | $3.21 | [Digi-Key](https://www.digikey.com/en/products/detail/vybronics-inc/VG0832012/7364317) |
| Adafruit LiPo 3.7 V 400 mAh, protected (Adafruit 3898) | 1528-2731-ND | 1 | $6.95 | [Digi-Key](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3898/9685336) |
| JST PH 2-pin male cable, 200 mm (Adafruit 3814), soldered to the XIAO | 1528-2617-ND (via Octopart) | 2 | $0.75 | [Digi-Key](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3814/9380221) |
| JST PH 2-pin female cable, 100 mm (Adafruit 261), PPK2 lead | 1528-261-ND (via Octopart) | 1 | $0.75 | search "1528-261-ND" on Digi-Key |
| STEMMA QT to male header cable, 150 mm (Adafruit 4209) | 1528-4209-ND | 1 | about $0.95 | [Digi-Key](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4209/1528-4209-ND/10230003) |
| Nordic Power Profiler Kit II | NRF-PPK2 (price not readable) | 1 | about $93 to $100 | [Digi-Key](https://www.digikey.com/en/products/detail/nordic-semiconductor-asa/NRF-PPK2/13557476) |

If the VG0832012 runs short, use **1670-VG0832022D-ND** ($3.47, about 12.7k in
stock, via Octopart): same size and drive. If Digi-Key's PPK2 price is well
above $93, Mouser has it at
[$93.43 (949-NRF-PPK2)](https://www.mouser.com/en/ProductDetail/Nordic-Semiconductor/nRF-PPK2?qs=hd1VzrDQEGilgnS3iQ3EVw%3D%3D),
at the cost of a third shipment.

**Total: about $145 to $152 before shipping and tax.** Without the PPK2, about
$52. Shipments with batteries go ground only. Free-shipping thresholds were
not verified.

Digi-Key BOM upload file: [stage-0-digikey.csv](stage-0-digikey.csv).

### Bench supplies (add to the Digi-Key order if you don't have them)

| Item | Why |
| --- | --- |
| USB-C cable that carries data (not charge-only) | Flashing and serial log through the XIAO's onboard debugger |
| Half-size breadboard | Bench testing only; too bulky to wear overnight |
| Male header strip | Pins for the PPK2 lead and any loose wire ends |
| Heat-shrink, and Kapton tape or UV glue | Strain relief for the LRA's very thin leads |
| Double-sided foam tape | Fixes the LRA to a mass for calibration and wear tests |
| Temporary strap (elastic or hook-and-loop) | Wearing it overnight before a case exists |

Tools you probably already have: fine-tip soldering iron, solder and flux,
flush cutters, wire strippers, tweezers, a **multimeter** (needed for the
battery polarity check), and a micro-USB cable for the PPK2 (unconfirmed
whether one is in the box).

### Optional extras

| Part | Price | Link | Why |
| --- | --- | --- | --- |
| Raspberry Pi Debug Probe (Adafruit 5699) | $12.00 | [Adafruit](https://www.adafruit.com/product/5699) | Same SWD + UART tool the stage 1 dock will use. Not needed for stage 0. |
| Adafruit Vibrating Mini Motor Disc, ERM (Adafruit 1201) | $1.95 | [Adafruit](https://www.adafruit.com/product/1201) | Cheap ERM to compare against the LRA. 10 x 2.7 mm. |
| 20 mm quick-release silicone strap | $19.99 | [Archer](https://www.archerwatchstraps.com/en-us/products/quick-release-silicone-venetian-red) | For when the printed case exists (needs 20 mm lug holes). |

## Checked specs

**XIAO nRF54L15 Sense**: the whole controller for stage 0.
- 21 x 17.8 mm, 3.3 V I/O, USB-C.
- Onboard LSM6DS3TR-C 6-axis IMU (I2C address 0x6A) on its own I2C bus
  (P0.04 SDA, P0.03 SCL), behind a load switch on P0.01 so firmware can cut
  its power. Stage 0 uses this IMU; the low-power LIS2DW12 comes in at
  stage 1.
- Onboard SAMD11 CMSIS-DAP debugger: flash, debug and serial log over USB-C.
- Battery pads (BAT+ / BAT-) on the underside. Charger is an SGM40567; the
  schematic's R4 = 120 kohm works out to about 200 mA. Seeed doesn't publish
  this figure, so measure it.
- [Wiki](https://wiki.seeedstudio.com/xiao_nrf54l15_sense_getting_started/) ·
  [schematic](https://files.seeedstudio.com/wiki/XIAO_nRF54L15/res/202004618_XIAO_nRF54L15_Sense_V1.2_SCH_260605.pdf.pdf) ·
  [Zephyr board files](https://github.com/zephyrproject-rtos/zephyr/tree/main/boards/seeed/xiao_nrf54l15)

**DRV2605L breakout**
- VIN 3 to 5 V, no regulator; 10 kohm I2C pull-ups to VIN. Power it from the
  XIAO's 3V3, not the battery, so the I2C lines stay at 3.3 V. Address 0x5A.
- **Cut the power LED jumper on the back** before measuring sleep current;
  the always-on LED would swamp the microamp readings.
- The EN pin is not broken out, so idle current depends on the chip's
  software standby mode (a few uA). Budget for it.
- The motor's 60 to 80 mA comes from the XIAO's 3V3 rail. Watch the PPK2
  trace for dips during a buzz.
- [Learn guide](https://learn.adafruit.com/adafruit-drv2605-haptic-controller-breakout/pinouts)

**VG0832012 LRA**
- 8.0 mm diameter, 3.25 mm thick, wire leads.
- 1.8 Vrms rated, 235 Hz resonance, 58 mA typical, 80 mA max.
- Buy three: the leads are about 0.1 mm wire and break easily.

**400 mAh LiPo (Adafruit 3898)**: about 36 x 17 x 7.8 mm, 8.2 g, JST PH.
- Protection circuit included (overcharge, 3.0 V cut-off, short circuit).
- Max charge 400 mA, so the XIAO's roughly 200 mA is 0.5C. Smaller Adafruit
  cells (100 and 150 mAh) would be charged faster than their rating.
- Footprint is close to the final pod, just thicker.

**JST PH cables**: the 3814 (male) mates with the battery's plug and uses
Adafruit's matching colours. Solder it to the BAT pads, red to BAT+, and
still check polarity with a meter before the first plug-in. The 261 (female)
mates with that same 3814, so the PPK2 can plug in where the battery goes.

**PPK2**: 200 nA to 1 A on 0.8 to 5 V, covering both sleep and the buzz.

## Wiring

| From | To |
| --- | --- |
| Cable 4209 red | XIAO 3V3 |
| Cable 4209 black | XIAO GND |
| Cable 4209 blue (SDA) | XIAO D4 (P1.10) |
| Cable 4209 yellow (SCL) | XIAO D5 (P1.11) |
| Cable 4209 JST SH end | DRV2605L STEMMA QT port |
| LRA wire leads | DRV2605L motor + / - terminals |
| Battery 3898 | 3814 pigtail soldered to XIAO BAT+ / BAT- |

Solder the 3814 to the BAT pads **before** fitting headers: the pads sit
between the header rows.

## Measuring with the PPK2

- **Source mode (PPK2 is the battery):** PPK2 VOUT and GND to the 261 lead,
  plugged into the XIAO's battery socket. Unplug the battery **and USB-C**:
  with USB connected, USB powers the board and the charger may try to charge
  the PPK2. Use BLE or the PPK2's logic inputs for markers, since there's no
  USB serial log in this mode.
- **Ampere-meter mode (a real night on the real battery):** battery to PPK2
  VIN, PPK2 VOUT to BAT+, common ground.

## LRA setup in firmware

Adafruit has only tested this breakout with ERM motors, but the chip supports
LRAs. Before auto-calibration, set the LRA bit, library 6, RATED_VOLTAGE,
OD_CLAMP and DRIVE_TIME (about half the resonant period: about 2.1 ms at
235 Hz). Then run auto-calibration (mode 7, GO).
- Stick the motor to a mass (the case or your wrist) while calibrating; a
  free-hanging LRA calibrates wrong.
- The calibration results (A_CAL_COMP, A_CAL_BEMF, BEMF_GAIN) are lost at
  power-off. Save them in flash and write them back at boot.
- Zephyr has an `adafruit_drv2605l` shield and a DRV2605 haptics driver.
