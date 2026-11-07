# WakeBand rigid rev A fab package

Generated 2026-11-07 from `../rigid-rev-a.kicad_pcb` with kicad-cli 10.0.3
(Gerbers exported with `--check-zones`; the previous package used 10.0.5). See `../README.md` for the stackup,
orientation, placement and the list of compromises.

`rigid-rev-a-fab.zip` holds every file in `gerbers/` plus `bom_jlcpcb.csv` and
`cpl_jlcpcb_top.csv`. `u1-pin1-drawing.pdf` is the pin-1 drawing for the
consigned ISP2454 (F.Fab outline with pin-1 mark, pads numbered, board edge).

## JLCPCB order options

| Option | Value |
| --- | --- |
| Layers | 4 |
| Size | 33 x 15 mm (1 mm corner radius) |
| Thickness | 0.8 mm |
| Stackup | JLC04081H-7628 (7628 prepreg 0.21 mm, core 0.26 mm; matches the job file) |
| Copper | 1 oz outer, 0.5 oz inner |
| Finish | ENIG |
| Via covering | **Epoxy filled and capped (POFV) - paid option, must be selected** |
| Min via | 0.3 mm pad / 0.2 mm hole (11 vias); the other 131 are 0.45 / 0.3 |
| Min track / space | 0.12 / 0.10 mm |
| Impedance control | not needed (ANT_LINK is two module pads joined on F.Cu, 0.65 mm) |
| Assembly | top side only; the bottom has no parts, only the hand-solder pads TP201/TP202/TP501/TP502 and the bridged jumper JP201 (no paste) |

**POFV is not optional.** There are vias in pads: the ISP2454 GND pads 1, 7,
8, 12, 14, 16, 18, 21, 23, 24, 25, 31 and nRESET pad 13; nine vias in the
nPM1304 exposed pad; the nRESET via in test pad TP701; the VIN via in C201.1,
the VSYS via in C205.1 the VDD_2V0 via in test pad TP704, the VSYS via in test pad TP705, the GND via in dock pad 2 (J601), the
VBAT via in JP201 pad 2 and the LRA- via in TP502. Without filling
and capping, solder wicks down these vias and the module and PMIC joints
starve. With POFV every via on the board is filled and plated over.

The board is narrow (15 mm). If the assembly quote asks for edge rails or a
panel, choose rails added by JLCPCB, joined by **tabs or mouse bites, not
V-cut**: copper comes within 0.30 mm of the board edge, too close for a
V-score.

Mask: openings equal the pads (0 expansion), except the hand-solder pads
TP201, TP202 (cell) and TP501, TP502 (LRA), which open 0.1 mm larger.

Since the 2026-11-06 rework F.Cu is the pod's outer face: the parts and the
six dock pads (J601, top edge) are on F, and B.Cu faces the cell and the
LRA. B carries signal tracks under green mask; put kapton over B before the
cell goes on (compromise 6 in `../README.md`).

## Placement rotation checks (JLCPCB preview)

`cpl_jlcpcb_top.csv` gives KiCad's rotations. JLCPCB's zero orientation
differs per package, so check each of these in the placement preview. The
"Expected at JLCPCB" column comes from the rotation-correction tables that
the JLCKicadTools and KiBot exporters apply for JLCPCB (QFN, TSSOP, DFN: +270).
Neither table has an entry for SOD-123F, a generic LGA or the TI DPY
package, so those stay at the KiCad value until the preview shows otherwise.
The CPL itself is left at KiCad's values, so fix rotations in the preview,
not in the file.

| Ref | Part | Package | CPL | Expected at JLCPCB | What to check in the preview |
| --- | --- | --- | --- | --- | --- |
| U201 | nPM1304-QEAA (consigned) | QFN-32 | 0 | 270 (QFN rule), but it is consigned, so JLCPCB may model it from the drawing | pin 1 dot at the VDD_2V0 corner |
| U501 | DRV2605L | TSSOP-10 (TI DGS) | 90 | 0 (90 + 270, TSSOP rule) | pin 1 (REG) at board coordinates (127.6, 109.65) |
| U401 | LIS2DW12 | LGA-12 2 x 2 mm | 0 | 0 (no rule) | pin 1 mark on the correct corner |
| D601 | SMF12A (unidirectional TVS, LCSC C207255) | SOD-123F | 0 | 0 (no rule); flip 180 if the band shows on GND | cathode band on pad 1 = VIN (left) |
| D602-D605 | TPD1E10B06DPYR | X1SON DPY (1.0 x 0.6 mm) | 0 | 0 (no rule) | bidirectional, so 0 or 180 both work; body must sit across both pads, not at 90 |
| L201 | DFE201610E-2R2M | 2016 inductor | 180 | 0 or 180 (non-polar) | body across both pads |
| U202 | KTD2026EWE-TR (consigned) | UTDFN-8 1.5 x 1.5 mm | 0 | 270 (DFN rule), but it is consigned | pin 1 (ST) at the bottom-left corner, board coordinates (125.95, 113.95); the I2C pins face up |
| D702 | TJ-S1615SW6TGLCCYRGB-A5 (LCSC C273610) | 1615 RGB LED | 0 | 0 (no rule) | pin 1 (anode, corner mark) at the top-right pad, (131.1, 112.65), the pad joined to VSYS |
| U1 | ISP2454-LX (consigned) | LGA-62 module | 270 | 270 (enter it by hand) | attach `u1-pin1-drawing.pdf` |

Sources: [KiBot position notes (internal rotation list)](https://kibot.readthedocs.io/en/latest/notes_position.html),
[JLCKicadTools rotation database](https://github.com/matthewlai/JLCKicadTools/blob/master/jlc_kicad_tools/cpl_rotations_db.csv).

The passives are non-polar, but check them in the preview anyway.

L201's footprint (0.55 x 1.6 mm pads at +/-0.725 mm, 0.9 mm gap) matches
Murata's recommended land pattern for the DFE201610E; see compromise 8 in
`../README.md`.

## Consigned and unassembled parts

- **U1 (ISP2454-LX), U201 (nPM1304-QEAA) and U202 (KTD2026EWE-TR, from
  Digi-Key)** have no LCSC part number and must be consigned (or sourced
  another way). Send the U1 pin-1 drawing with the consignment.
- **Not assembled:** R201, D701 and R701 are DNP (not in the BOM or CPL).
  SW201 was removed from the design on 2026-11-07. The 60 mAh cell (BT1) and the 8 mm LRA are hand-soldered to
  TP201/TP202 and TP501/TP502 on B.Cu after assembly (TP201 and JP201 bottom
  right, TP202 and TP501 top right, TP502 bottom right; all outside the cell
  and LRA outlines).
- Test pads, the dock pads (J601), the I_BAT solder jumper (JP201, bridged
  in copper) and the net tie NT201 are copper only.
