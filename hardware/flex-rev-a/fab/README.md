# WakeBand flex rev A fab package

Generated 2026-10-30 from `../flex-rev-a.kicad_pcb` with kicad-cli 10.0.5.
See `../README.md` ("Fab package" and "Fold and assembly orientation") for
the layer list, stiffener mapping, teardrop note and assembly orientation.

`flex-rev-a-fab.zip` holds every file in `gerbers/` plus `bom_jlcpcb.csv` and
`cpl_jlcpcb_top.csv`.

## Stackup (also in the Gerber job file)

2-layer flex, about 0.12 mm: polyimide coverlay 25 um / copper 18 um
(1/2 oz) / polyimide core 25 um / copper 18 um / polyimide coverlay 25 um.
Finish ENIG. Stiffeners (User.2 `Stiffener_Bottom`) are FR4 0.4 mm. There is
no top stiffener, and the job file lists no Stiffener_Top layer.

## Coverlay openings

The mask layers are the coverlay openings. Fine-pitch parts use 0 expansion,
so each opening equals the pad: U1 (ISP2454), U201 (nPM1304 QFN-32), U401
(LIS2DW12 LGA-12) and U501 (DRV2605L TSSOP-10). The hand-solder pads TP201,
TP202, TP501 and TP502 open 0.1 mm larger. Ask JLCPCB to confirm that their
coverlay can open these pads one by one. If it can't, they will use one
larger opening or LPI mask over those parts.

## Placement rotation checks (JLCPCB preview)

`cpl_jlcpcb_top.csv` gives KiCad's rotations. JLCPCB's zero orientation
differs per package, so check each of these in the placement preview:

| Ref | Part | Package | CPL | Check |
| --- | --- | --- | --- | --- |
| U201 | nPM1304-QEAA | QFN-32 | 0 | likely needs +270 deg; pin 1 at the dot |
| U501 | DRV2605L | TSSOP-10 | 0 | likely needs +270 deg |
| U401 | LIS2DW12 | LGA-12 | 0 | check pin 1 in the preview |
| D601 | SMF18A (unidirectional TVS) | SOD-123F | 0 | cathode band on the VIN pad, not GND |
| U1 | ISP2454-LX (consigned) | LGA-62 module | 270 | enter 270 and attach a pin-1 drawing (F.Fab has the outline and pin-1 mark) |

U1 and U201 have no LCSC part number: they need consignment or another
source. The passives and the TPD1E10B06 ESD diodes (bidirectional) are
non-polar, but check them in the preview anyway.
