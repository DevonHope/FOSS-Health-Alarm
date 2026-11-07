# WakeBand rigid rev B (work in progress)

Rev B is rev A rebuilt so that **JLCPCB can assemble every part**. It keeps rev A's 33 x 15 mm
outline, 4-layer 0.8 mm stackup, case and dock: the four B-side dock landings, the LED
position and the cell and LRA lead pads are in the same places.

**Status (2026-11-07):**
- Done: schematic (ERC 0), placement (fits; courtyards clear).
- Next: routing, zones, fab package.

## What changed from rev A

| Rev A | Rev B | Why |
| --- | --- | --- |
| ISP2454 module (radio + antenna) | **nRF54L10-QFAA** (C44800139) + Nordic's QFN48 reference circuit + Johanson **2450AT18A0100001E** chip antenna (C17430588) | Module not stocked at JLC. The nRF54L15 (C42458750) is out of stock at JLC and LCSC; the L10 has the same package, pins and reference circuit, with 1 MB RRAM / 192 KB RAM. An nRF54L05 or nRF54L15 drops in unchanged when stocked. |
| nPM1304 PMIC | **BQ25125** (C2871567) | Same family and pinout as the BQ25120A (C2866577, only 4 at JLC). 4.2 V charge, 30 mA set by R202, 1.8 V buck on by default, LS/LDO for the LED driver. No fuel gauge (rev A's nPM1304 had one): firmware estimates charge from the battery voltage. |
| KTD2026 LED driver | **IS31FL3193** (C2653363) | Stocked; I2C inputs work at 1.8 V (VIH 1.4 V). |
| 2.0 V rail | **1.8 V** rail | The buck's power-on default. The charger's I2C watchdog resets its registers after 50 s without I2C, so a raised voltage would not hold. |

Unchanged: LIS2DW12, DRV2605L (now powered straight from the cell), ESD parts, test pads.

## Antenna (to be expanded)

- **Clear area:** the chip antenna sits in a 4.6 x 5.9 mm corner (bottom-left) with no copper on any layer. Johanson asks for 6.5 x 6.5 mm, so expect less range than their eval board.
- **Matching:**
  - The nRF54L10's RF output runs through Nordic's 3-stage low-pass filter: their exact 0201 parts, L2 / C6 / L3 / C9 / L4 / C11.
  - It then goes through a tuning network: C14 shunt, R2 series (0 Ω to start), C15 shunt.
  - Tune with the cell, case and strap fitted.
- **Case:** the antenna is 1.3 mm tall, so the shell roof needs a pocket over it.

Not FCC/IC certified; for personal use only.

## Source

The schematic and board are generated from `scripts/`:
- `parts.py` is the netlist and BOM source.
- `mksym.py` and `mkfp.py` build the project symbols and the DSBGA-25 footprint.
- `gen_sch.py`, `gen_pcb.py` and `placement.json` build the schematic and board.
- `mkpro.py` restores rev A's design rules after each board save.
