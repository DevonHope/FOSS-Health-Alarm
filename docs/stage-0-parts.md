# Stage 0 parts list

Dev-kit prototype from the [hardware roadmap](hardware-roadmap.md#stage-0-dev-kit-prototype).
Goal: prove the motion-based wake logic and measure real battery life, with no
custom board.

Prices and stock were checked on the store pages on **2026-10-28** (USD).
They change, so re-check before ordering. Items marked "unconfirmed" could not
be fully verified.

## Order list

### Required

| # | Part | Qty | Price | Store |
| --- | --- | --- | --- | --- |
| 1 | Seeed Studio XIAO nRF54L15 Sense (SKU 101991422) | 1 | $15.99 | [Seeed](https://www.seeedstudio.com/XIAO-nRF54L15-Sense-p-6494.html) |
| 2 | Adafruit DRV2605L Haptic Motor Controller, STEMMA QT (ID 2305) | 1 | $7.95 | [Adafruit](https://www.adafruit.com/product/2305) |
| 3 | Vybronics VG0832012 coin LRA, 8 mm | 2 | about $8 to $10 each (unconfirmed) | [Digi-Key](https://www.digikey.com/en/products/detail/vybronics-inc/VG0832012/7364317) · [datasheet](https://www.vybronics.com/coin-vibration-motors/lra/v-g0832012) |
| 4 | Adafruit LiPo 3.7 V 400 mAh, protected (ID 3898) | 1 | $6.95 | [Adafruit](https://www.adafruit.com/product/3898) |
| 5 | JST PH 2-pin cable, male header, 200 mm (ID 3814) | 2 | $0.75 | [Adafruit](https://www.adafruit.com/product/3814) |
| 6 | STEMMA QT / Qwiic JST SH 4-pin to male header cable, 150 mm (ID 4209) | 1 | $0.95 | [Adafruit](https://www.adafruit.com/product/4209) |
| 7 | Nordic Power Profiler Kit II (nRF-PPK2, Mouser 949-NRF-PPK2) | 1 | $93.43 | [Mouser](https://www.mouser.com/en/ProductDetail/Nordic-Semiconductor/nRF-PPK2?qs=hd1VzrDQEGilgnS3iQ3EVw%3D%3D) · [Adafruit 5048, $99.95](https://www.adafruit.com/product/5048) |

**Subtotal: about $135 to $145**, about $100 of which is the PPK2. Without the
PPK2 the band parts come to about $45 with two motors.

### Optional

| Part | Price | Store | Why |
| --- | --- | --- | --- |
| Raspberry Pi Debug Probe (ID 5699) | $12.00 | [Adafruit](https://www.adafruit.com/product/5699) | SWD + UART over one USB cable. Not needed for stage 0 (the XIAO has its own debugger), but it is the same tool the stage 1 dock will use. |
| Adafruit Vibrating Mini Motor Disc, ERM (ID 1201) | $1.95 | [Adafruit](https://www.adafruit.com/product/1201) | Cheap backup motor to compare ERM against LRA. 10 mm x 2.7 mm, about 60 mA at 3 V. |
| Archer 20 mm quick-release silicone strap | $19.99 | [Archer](https://www.archerwatchstraps.com/en-us/products/quick-release-silicone-venetian-red) | Any 20 mm quick-release strap works; the printed case needs 20 mm lug holes. Unconfirmed whether spring bars are included. |
| Seeed XIAO nRF52840 Sense (SKU 102010469) | $13.99 at 10+ | [Seeed](https://www.seeedstudio.com/Seeed-XIAO-BLE-Sense-nRF52840-p-5253.html) | Fallback board if the nRF54L15 version is out of stock. Single-unit price and stock were not shown. |

### Alternatives for the LRA

If the VG0832012 is short on Digi-Key, these Vybronics coin LRAs have wire
leads and similar specs (Vybronics catalogue, stocked at Digi-Key):

- **VG0832022D**: same 8 mm size, best stock (about 12.7k).
- **VG0832013D**: same 8 mm size (about 2.4k in stock).
- **VG0825001U**: 8 x 2.55 mm, thinner, 1.2 Vrms, 240 Hz (about 1.7k in stock).

Adafruit and SparkFun do not currently sell a coin LRA.

## What each part does, and checked specs

**XIAO nRF54L15 Sense**: the whole controller for stage 0.
- 21 x 17.8 mm, 3.3 V I/O, USB-C.
- Onboard LSM6DS3TR-C 6-axis IMU (I2C address 0x6A). It sits on its own I2C
  bus (P0.04 SDA, P0.03 SCL) behind a load switch enabled by P0.01, so
  firmware can cut its power. Stage 0 uses this IMU for sleep detection; the
  low-power LIS2DW12 comes in at stage 1.
- Onboard SAMD11 CMSIS-DAP debugger: flash, debug and serial log over the
  USB-C port. No external probe needed.
- Battery pads (BAT+ / BAT-) on the underside, no connector. Charger is an
  SGM40567. The charge current works out to about 200 mA from the schematic
  (R4 = 120 kohm). Seeed does not publish this figure, so measure it before
  trusting it.
- [Wiki](https://wiki.seeedstudio.com/xiao_nrf54l15_sense_getting_started/) ·
  [schematic](https://files.seeedstudio.com/wiki/XIAO_nRF54L15/res/202004618_XIAO_nRF54L15_Sense_V1.2_SCH_260605.pdf.pdf) ·
  [Zephyr board files](https://github.com/zephyrproject-rtos/zephyr/tree/main/boards/seeed/xiao_nrf54l15)

**DRV2605L breakout**: drives the motor with smooth ramps.
- VIN 3 to 5 V; run it from the XIAO's 3.3 V so the I2C pull-ups stay at
  3.3 V. I2C address 0x5A. 25.8 x 17.8 x 4.6 mm.
- Adafruit's guide only covers ERM motors. The chip supports LRAs; set it to
  LRA mode, select the LRA effect library and run auto-calibration in
  firmware.
- [Learn guide](https://learn.adafruit.com/adafruit-drv2605-haptic-controller-breakout/pinouts)

**VG0832012 LRA**: the gentle buzz.
- 8.0 mm diameter, 3.25 mm thick, wire leads.
- 1.8 Vrms rated, 235 Hz resonance, 58 mA typical, 80 mA max.
- Order two: the wire leads are fragile.

**400 mAh LiPo (ID 3898)**: about 36 x 17 x 7.8 mm, 8.2 g, JST PH.
- Protection circuit included (overcharge, cut-off at 3.0 V, short circuit).
- Max charge 400 mA, so the XIAO's roughly 200 mA charge is a safe 0.5C.
- Why not a smaller cell: the 100 mAh (ID 1570, max 100 mA) and 150 mAh
  (ID 1317, max 150 mA) Adafruit cells would be charged faster than their
  rating by this XIAO. The 400 mAh cell is also close to the final pod's
  footprint, just thicker, which makes it a good stand-in for case design.

**JST PH pigtail (ID 3814)**: solder the bare ends to the XIAO's BAT+ / BAT-
pads so the battery plugs in and out. Check polarity before plugging in:
JST PH colour conventions are not universal. Order two in case one is needed
for the PPK2 lead.

**STEMMA QT to header cable (ID 4209)**: connects the DRV2605L to the XIAO.

**PPK2**: measures current from 200 nA to 1 A on a 0.8 to 5 V supply, which
covers both deep sleep and the motor buzz. Use source mode in place of the
battery (set it to about 3.8 V) to measure what a night costs.

## Wiring

| From | To |
| --- | --- |
| Cable 4209 red | XIAO 3V3 |
| Cable 4209 black | XIAO GND |
| Cable 4209 blue (SDA) | XIAO D4 (P1.10) |
| Cable 4209 yellow (SCL) | XIAO D5 (P1.11) |
| Cable 4209 JST SH end | DRV2605L STEMMA QT port |
| LRA wire leads | DRV2605L motor + / - terminals |
| Battery (via 3814 pigtail) | XIAO BAT+ / BAT- pads |
| PPK2 VOUT / GND (power measurements) | XIAO BAT+ / BAT- pads, with the battery unplugged |

## Before you order

- Re-check the Digi-Key price and stock for the LRA. The page could not be
  read automatically.
- Once the parts arrive, measure the XIAO's real charge current with the PPK2
  or a USB meter before leaving the battery charging unattended.
