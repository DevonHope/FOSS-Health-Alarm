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
| nPM1304 PMIC | **BQ25125** (C2871567) | Same family and pinout as the BQ25120A (C2866577, only 4 at JLC). 4.2 V charge, 30 mA set by R202, 1.8 V buck on at power-up (unused here), LS/LDO switches the LED's supply. **No fuel gauge** (the nPM1304 had one): firmware estimates charge from the BQ's VBMON battery-voltage reading. |
| KTD2026 LED driver | **IS31FL3193** (C2653363) | Stocked; its I2C inputs work on the 2.0 V bus (VIH 1.4 V). |
| 2.0 V rail (nPM1304 buck) | **2.0 V from a TPS7A0220 LDO** (U203, C2860934) on PMID | The BQ25125 buck is 1.8 V +/- 2.5 % (1.755 V worst case), too close to the nRF54L10's 1.75 V power-on-reset minimum, and a board that fails reset can't run firmware to fix it. The LDO is 2.0 V +/- 1.5 % (1.97 V minimum), draws 25 nA, and sits in a 1 x 1 mm X2SON. The buck stays fitted but unloaded (VSYS). A BQ2512x with a higher default (BQ25121A, 2.5 V) has 1 in stock. |
| DRV2605L on VSYS | DRV2605L on **VBAT** | Straight from the cell (2.0-5.2 V). |
| UART pads beside the dock landings, debug LED D701 | **removed** (J601 has the 4 dock landings only) | No routing room at the dock end. Logs go over **SEGGER RTT through the SWD dock pins** (see Firmware setup). |
| I2C/2.0 V test pads TP702-TP704 | removed | Probe R203/R204 and any 2.0 V capacitor instead. |
| R209, R210 (/INT and /PG pull-ups) | removed | No routing room; use the nRF54L10's internal pull-ups on P1.05 and P1.06. |
| KTD2026 on VSYS | IS31FL3193 VCC on **PMID** | Always powered on battery, so its I2C inputs (rated to VCC + 0.3 V) never clamp the shared bus. |

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
| 25 / 26 / 30 | SWDIO / SWDCLK / nRESET | dock pins 3/4; TP701 |
| 1 / 2 | XL1 / XL2 | 32.768 kHz crystal X1 |
| 34 / 35 | XC1 / XC2 | 32 MHz crystal X2 |

The pins were chosen for the layout: each signal leaves the QFN on the side facing where it goes.
P1.02/P1.03 (NFC), P2.07/P2.08 and P1.09 (rev A's UART and debug LED) and the other GPIOs are unconnected.

I2C addresses: LIS2DW12 0x19, DRV2605L 0x5A, IS31FL3193 0x68, BQ25125 0x6A.

## Firmware setup

### Logs: SEGGER RTT, no UART

Rev B has no UART pads. Log over **RTT** through the SWD dock pins (J601 3/4) with any J-Link or
the nRF54L DK's on-board debugger: in Zephyr set `CONFIG_USE_SEGGER_RTT=y`, `CONFIG_LOG_BACKEND_RTT=y`
and `CONFIG_UART_CONSOLE=n` (or `CONFIG_RTT_CONSOLE=y`), then read with `JLinkRTTViewer` or
`west rtt`. RTT works on the dock while the band charges. Disable it in release builds so the
debug domain powers down.

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
- **PMIC_INT (P1.05):** enable the internal pull-up (no external resistor). /INT is open drain; with
  EN_INT cleared it only pulses low for 128 us on events.
- **DOCK_PG (P1.06):** enable the internal pull-up (about 13 kOhm; there's no external
  resistor). /PG is open drain and low only while docked, so the pull-up draws about 140 uA
  from the dock and nothing on battery.

### BQ25125

- **/CD:** the BQ25125 talks I2C on battery only while /CD is high.
  - Drive CHG_CD high to configure it. Drive it low to idle: that is Hi-Z mode, where the BQ draws 0.7-0.75 uA. The 2.0 V rail comes from U203 on PMID, so it is unaffected.
  - The buck's 1.8 V output (VSYS) powers nothing, but **leave it on**: the BQ's /CD and LSCTRL input
    thresholds are 0.25 / 0.75 x VSYS, so with SYS off the nRF couldn't reliably drive them. (The I2C
    threshold is 0.75 x the pull-up voltage, 1.5 V on the 2.0 V bus; /CD at 2.0 V is above 0.75 x 1.8 V.)
  - Also drive it low while docked (DOCK_PG low), because /CD high stops charging.
- **Defaults:** without I2C the charger already does the right thing.
  - 1.8 V buck on (unused).
  - 4.2 V charge.
  - 30 mA from R202 (6.65 k) in default mode.
  - 2 mA termination (IPRETERM to GND).
  - 100 mA input limit (ILIM to GND).
  - NTC (TS) enabled.
- **After the first I2C write it is in host mode**, and its 50 s watchdog applies. Write, then re-write at least every 50 s while /CD is high:
  - Charge current 30 mA (reg 0x03, as for the BQ25120A).
  - Termination.
  - EN_INT = 0 in reg 0x02, so /INT pulses instead of staying low through the whole charge.
- **LED supply:** the LED anode (VLED) is on the BQ25125's LS/LDO output, which powers up as a
  1.8 V LDO, too low to light the LED. Write reg 0x07 for load-switch mode (VLED then follows PMID),
  then raise LS_CTRL. The watchdog undoes this after 50 s without I2C in host mode: the LED just
  goes dark, nothing is damaged.
- **Battery level:** read VBMON (reg 0x0A): the battery voltage as a percentage of VBATREG, in 2 % steps.
- **Ship mode:** with VIN absent, /CD high and /MR high, write EN_SHIPMODE. The cell then sees about 2 nA (the DRV2605L on VBAT adds its shutdown current). The dock (VIN) or shorting TP203 (/MR) to GND wakes it; the nRF54L10 then starts from reset.

### IS31FL3193

- **Shutdown by default:** it starts in software shutdown (reg 0x00). Write EN = 1, SSD = 0, set the current with reg 0x03 (e.g. 5 mA), then write PWM and the update register 0x07.
- **Channels:** OUT1 is green, OUT2 blue, OUT3 red (assigned for routing).
- **Supply:** VCC is on PMID (always up on battery), so the I2C bus is never clamped by an
  unpowered driver. Drive LED_EN (SDB) high to wake it. The LED anode is on VLED, which needs
  LS_CTRL on in load-switch mode (see above).

## Antenna tuning

The radio output runs: ANT pin -> Nordic's low-pass ladder (L2 2.7 nH, C6 1.5 pF, L3 3.5 nH, C9 2.0 pF,
L4 3.5 nH, C11 0.3 pF; their exact 0201 parts and placement) -> RF_50 -> **tuning network** -> antenna:

| Part | Position | Fitted | Role |
| --- | --- | --- | --- |
| C14 (0402) | RF_50 to GND, at the ladder end | not fitted | pi shunt 1 |
| R2 (0402) | series, RF_50 to ANT_FEED | 0 ohm | pi series (a 0402 inductor or capacitor) |
| C15 (0402) | ANT_FEED to GND, at the antenna side | not fitted | pi shunt 2 |

The antenna (AE1) sits in a 4.2 x 5.9 mm corner (x 100-104.2, y 109.1-115) with no copper on any
layer (rule area "Antenna keep-out"); the 50-ohm feed (0.36 mm on F.Cu over the In1 ground, 0.16 mm
gap) enters it from the ground edge. Johanson's evaluation board uses 6.5 x 6.5 mm and its own
match, so this board needs its own values. Expect less range than the datasheet until it is tuned.

**Tune with the cell, case, strap and wrist (or a hand) in place:** the plastic, the cell and the
body all pull the antenna down in frequency.

With a VNA (best):
1. Cut the feed at R2: lift R2 and solder a 0402-pad pigtail (a short 1.13 mm coax, shield to the
   C15/C14 ground pads, centre to the AE1 side of R2). Calibrate at the coax end (port extension).
2. Measure S11 of the antenna from 2.3 to 2.6 GHz with the band assembled and on the wrist.
3. Use a Smith-chart tool (e.g. SimSmith or Johanson's own) to pick an L-match with C15 and R2 (or
   a pi with C14) that moves 2.44 GHz to 50 ohm; Murata LQP03/LQG15 inductors and GJM capacitors
   come in 0.1 nH / 0.1 pF steps. Typical starting points for this antenna: series 2-4 nH, shunt
   0.5-1.5 pF.
4. Fit the parts, put R2 back as the series part and re-measure. Aim for S11 below -10 dB across
   2.402-2.480 GHz.

Without a VNA (RSSI method):
1. Start as built: R2 = 0 ohm, C14 and C15 not fitted.
2. Run the nRF54L10 as a constant-carrier transmitter at 2.440 GHz, 0 dBm (Nordic's radio test
   sample / `radio_test` in nRF Connect SDK).
3. Put a receiver (an nRF52/nRF54 DK running the same sample in RX, or a phone app that shows BLE
   RSSI) 1-2 m away, fixed, and note the RSSI averaged over a few seconds with the band on the wrist.
4. Try one change at a time: R2 as 1.0 / 1.5 / 2.2 / 3.3 nH; then C15 (or C14) as 0.5 / 1.0 /
   1.5 pF. Keep the change that raises the RSSI; 3 dB is a real gain, 1 dB is noise.
5. Re-check the ends of the band (2.402 and 2.480 GHz).

## Power budget

Average current drawn from the cell (60 mAh) in normal use (asleep most of the day, logging motion
at night, one wake buzz). Datasheet typicals; the stage 0 bench measurement replaces these.

| Load | Average | Notes |
| --- | --- | --- |
| BQ25125 in Hi-Z (/CD low) | 0.7 uA | buck idling with no load; 0.75 uA with it on |
| TPS7A0220 LDO (2.0 V rail) | 0.025 uA | plus the rail's own loads at the cell's current (no buck gain) |
| nRF54L10 System ON idle, LFXO + GRTC running | about 2 uA | DC/DC on |
| LIS2DW12 low-power mode, 12.5-25 Hz | about 1-2 uA | |
| DRV2605L shut down (EN low), on VBAT | up to 4 uA | datasheet max; typical is lower |
| IS31FL3193 hardware shutdown (SDB low), on PMID | up to 2.5 uA | datasheet max |
| Waking once a minute to read the accelerometer FIFO | a few uA | |
| BLE: an occasional sync or advertising burst | a few uA | |
| **Sleep floor** | **about 5-15 uA** | **0.1-0.35 mAh a day** |
| Wake buzz: about 60 mA for 30 s each morning | | about 0.5 mAh a day |
| **Total** | | **about 0.7-1 mAh a day** |

A 60 mAh cell lasts about two months between charges. The charge LED is off when the band
is off the dock. The LS/LDO output (VLED) is switched off, so neither the LED nor its driver's
outputs draw anything; the driver itself sits in hardware shutdown on PMID. Ship mode (about
2 nA plus the DRV2605L and IS31 shutdown currents, which then have no supply because PMID
drops) is for storage.

**PMID and the LDO:** off the dock the BQ25125 runs PMID from the cell through its battery FET (at
most 160 mV drop at 400 mA; microvolts at our currents), in active and Hi-Z modes alike. The BQ cuts
the cell off at BUVLO (3.0 V default), so the LDO input never goes below about 2.9 V. The TPS7A0220
needs well under 0.1 V of headroom at a few mA, so the 2.0 V rail holds until the BQ shuts the system
down. In ship mode the battery FET is off and PMID is discharged (20 kOhm), so the LDO, the nRF54L10
and everything on PMID are unpowered, as intended. The dock (VIN) or shorting TP203 (/MR) to GND
brings it back.

**Logic rail margin:** the 2.0 V LDO is +/- 1.5 % (1.97 V minimum), against the nRF54L10's
1.7 V operating minimum and 1.75 V power-on-reset requirement (datasheet v1.0, Table 92 and
section 11.14.1; brown-out 1.56-1.64 V). The LDO needs about 0.3 V of headroom, so the rail holds
down to a cell at about 2.3 V; the BQ25125 cuts the battery off well above that (BUVLO 3.0 V
default). Every I2C part reads 2.0 V as high: BQ25125 (thresholds 0.75 x its 1.8 V SYS), IS31FL3193
(VIH 1.4 V), DRV2605L (1.3 V), LIS2DW12 (0.8 x its own 2.0 V supply).

## Source

The schematic and the placed board (with the hand-laid radio and charger copper) are generated by `scripts/build.sh`; the rest of the routing was done with the grid router in `scripts/route/` and then checked by hand (see Routing):
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
