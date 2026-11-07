# WakeBand rigid rev B (KiCad 10 project)

Rev B is rev A rebuilt so that **JLCPCB assembles every part** (no consigned module). It keeps rev
A's 33 x 15 mm outline, 4-layer 0.8 mm stackup (JLC04081H-7628), case, dock, contact carrier and
strap: the four B-side dock landings (J601 1-4 at x 131.5), the LED position (D702) and the cell and
LRA lead pads (TP201/TP202, TP501/TP502, JP201) are where rev A had them.

**Not FCC/IC (or CE) certified.** The radio is a bare nRF54L10 with a chip antenna on our own board,
so the module certification rev A could lean on does not apply. Build it for personal use and
experiments only; don't sell or distribute it as a product.

STATUS_PLACEHOLDER

## What changed from rev A

| Rev A | Rev B | Why |
| --- | --- | --- |
| ISP2454 module (radio + antenna) | **nRF54L10-QFAA** (C44800139) + Nordic's QFN48 reference circuit + Johanson **2450AT18A0100001E** chip antenna (C17430588) | Module not stocked at JLC. The nRF54L15 (C42458750) is out of stock at JLC and LCSC (0 on 2026-11-07); the L10 has the same package, pins and reference circuit, with 1 MB RRAM / 192 KB RAM. An nRF54L05 or nRF54L15 drops in unchanged. |
| nPM1304 PMIC | **BQ25125** (C2871567) | Same family and pinout as the BQ25120A (C2866577, only 4 at JLC). 4.2 V charge, 30 mA set by R202, 1.8 V buck on at power-up, LS/LDO switches the LED driver. **No fuel gauge** (the nPM1304 had one): firmware estimates charge from the BQ's VBMON battery-voltage reading. |
| KTD2026 LED driver | **IS31FL3193** (C2653363) | Stocked; its I2C inputs work at 1.8 V (VIH 1.4 V). |
| 2.0 V rail | **1.8 V** rail | The buck's power-up default. The charger's I2C watchdog puts every register back to default after 50 s without I2C, so a raised voltage would not hold. 1.8 V is inside the nRF54L10 (1.7-3.6 V; 1.75 V needed at power-on reset), LIS2DW12 and DRV2605L logic ranges. |
| DRV2605L on VSYS | DRV2605L on **VBAT** | Straight from the cell (2.0-5.2 V); the 1.8 V buck can't run it. |
| UART pads beside the dock landings | UART pads (J601 5/6) on F above the SWD landings | Freed room for the charger. |
| I2C/1.8 V test pads TP702-TP704 | removed | Probe R203/R204 and any 1.8 V capacitor instead. |

Unchanged: LIS2DW12, DRV2605L, ESD (TPD1E10B06 x4, SMF12A), the dock series resistors.

## nRF54L10 pin map

| Pin | Port | Net | Notes |
| --- | --- | --- | --- |
| 5 | P1.04 | I2C_SCL | clock-capable pin (TWIM needs both lines on clock pins) |
| 9 | P1.08 | I2C_SDA | clock-capable |
| 6 | P1.05 | PMIC_INT | BQ25125 /INT, wake from System OFF (P1) |
| 7 | P1.06 | DOCK_PG | BQ25125 /PG: low while the dock supplies VIN |
| 8 | P1.07 | HAPT_EN | DRV2605L EN |
| 27 | P0.02 | ACC_INT1 | LIS2DW12 INT1, wake (P0) |
| 24 | P0.01 | ACC_INT2 | LIS2DW12 INT2, wake; also TP401 |
| 38 | P1.10 | LED_EN | IS31FL3193 SDB (R211 pulls it low) |
| 39 | P1.11 | CHG_CD | BQ25125 /CD |
| 13 | P2.02 | LS_CTRL | BQ25125 LSCTRL (LED driver supply) |
| 18 / 19 | P2.07 / P2.08 | UART_RX / UART_TX | UARTE21; J601 pads 5/6 (bench only) |
| 37 | P1.09 | LED_DBG | debug LED D701 (not fitted) |
| 25 / 26 / 30 | SWDIO / SWDCLK / nRESET | dock pins 3/4; TP701 |
| 1 / 2 | XL1 / XL2 | 32.768 kHz crystal X1 |
| 34 / 35 | XC1 / XC2 | 32 MHz crystal X2 |

The pins were chosen for the layout: each signal leaves the QFN on the side facing where it goes.
P1.02/P1.03 (NFC) and the other GPIOs are unconnected.

I2C addresses: LIS2DW12 0x19, DRV2605L 0x5A, IS31FL3193 0x68, BQ25125 0x6A.

## Firmware setup

### nRF54L10

- **DC/DC:** the board has Nordic's DC/DC inductor (L1 4.7 uH), and all of Nordic's current figures
  assume DC/DC. Turn it on early (`REGULATORS.VREGMAIN.DCDCEN = 1`; in Zephyr set
  `regulator-initial-mode = <NRF5X_REG_MODE_DCDC>` on `&vregmain`).
- **Clocks:** both crystals use the chip's internal load capacitors (no external caps).
  - X1, 32.768 kHz: CL 9 pF.
  - X2, 32 MHz: CL 8 pF.
  - Set `&lfxo` / `&hfxo` to `load-capacitance = "internal"` with the value for each crystal's CL (datasheet INTCAP formula).
  - Use the LFXO as the LF clock source: only the LFXO keeps the GRTC running in System OFF.
- **RF:** the matching network is the board's own (see "Antenna tuning"); leave TX power at 0 dBm
  until it is tuned.
- **NFC pins:** unused; leave NFC disabled.

### BQ25125

- **/CD:** the BQ25125 talks I2C on battery only while /CD is high.
  - Drive CHG_CD high to configure it. Drive it low to idle: that is Hi-Z mode, where the 1.8 V buck stays on and the BQ draws 0.75 uA.
  - Also drive it low while docked (DOCK_PG low), because /CD high stops charging.
- **Defaults:** without I2C the charger already does the right thing.
  - 1.8 V buck on.
  - 4.2 V charge.
  - 30 mA from R202 (6.65 k) in default mode.
  - 2 mA termination (IPRETERM to GND).
  - 100 mA input limit (ILIM to GND).
  - NTC (TS) enabled.
- **After the first I2C write it is in host mode**, and its 50 s watchdog applies. Write, then re-write at least every 50 s while /CD is high:
  - Charge current 30 mA (reg 0x03, as for the BQ25120A).
  - Termination.
  - EN_INT = 0 in reg 0x02, so /INT pulses instead of staying low through the whole charge.
- **LED supply:** the BQ25125's LS/LDO output powers up as a 1.8 V LDO, too low for the IS31FL3193 (2.7 V minimum).
  - Write reg 0x07 for load-switch mode, then raise LS_CTRL to power the LED driver.
  - The watchdog undoes this after 50 s without I2C: the LED driver just browns out, nothing is damaged.
- **Battery level:** read VBMON (reg 0x0A): the battery voltage as a percentage of VBATREG, in 2 % steps.
- **Ship mode:** with VIN absent, /CD high and /MR high, write EN_SHIPMODE. The cell then sees about 2 nA (the DRV2605L on VBAT adds its shutdown current). The dock (VIN) or shorting TP203 (/MR) to GND wakes it.

### IS31FL3193

- **Shutdown by default:** it starts in software shutdown (reg 0x00). Write EN = 1, SSD = 0, set the current with reg 0x03 (e.g. 5 mA), then write PWM and the update register 0x07.
- **Channels:** OUT1 is green, OUT2 blue, OUT3 red (assigned for routing).
- **Supply:** LED_EN high, and VLED needs LS_CTRL on (see above).

## Antenna tuning

ANTENNA_PLACEHOLDER

## Power budget

POWER_PLACEHOLDER

## Source

The schematic and board are generated from `scripts/` (`build.sh` runs it all):
- `parts.py` is the netlist and BOM source.
- `mksym.py` builds the project symbols and `mkfp.py` the DSBGA-25 footprint.
- `fixnordic.py` tidies the footprints imported from Nordic's reference layout.
- `nordic_place.py` places the nRF54L10 support parts exactly as in Nordic's QFAA reference layout v0.8 (`nordic_ref_qfaa_0_8.kicad_pcb`, imported from Nordic's Altium files), rotated 180 degrees.
- `gen_sch.py`, `gen_pcb.py` and `placement.json` build the schematic and board.
- `transplant.py` copies Nordic's vias, no-pour areas and the C9 ground island.
- `hand_cluster.py` and `hand_bq.py` lay the radio cluster and the charger fan-out by hand.
- `zones.py` adds the pours and the antenna keep-out.
- `mkpro.py` restores the design rules after each board save.
- `mkfab.py` builds the fab package.
