# WakeBand rigid rev A (KiCad project)

4-layer 0.8 mm rigid board that replaces the flex design (archived in
`../flex-rev-a`). Routed, DRC clean, fab package in `fab/`.

| Item | Value |
| --- | --- |
| Board | 33 x 15 mm, 1 mm corner radius, 0.8 mm FR4, ENIG |
| Pod | about 35 x 17 mm outline with 1 mm walls (estimate); height = cell (4-5 mm) + 0.8 mm board + tallest top-side part |
| DRC | 0 violations, 0 unconnected, schematic parity 0 (3 documented exclusions) |
| ERC | 0 errors, 0 warnings |
| Vias | 143: 132 x 0.45/0.3 mm, 11 x 0.3/0.2 mm |
| Files | `rigid-rev-a-layout.pdf` (layers), `rigid-rev-a.pdf` (schematic), `fab/` |

## Stackup

JLCPCB JLC04081H-7628, 0.8 mm (also in `fab/gerbers/rigid-rev-a-job.gbrjob`):

| Layer | Use |
| --- | --- |
| F.Cu (L1, 35 um) | all SMT parts, signal fan-out, GND pour |
| prepreg 7628, 0.21 mm | |
| In1.Cu (L2, 15 um) | solid GND, no tracks; no copper in the antenna keep-out |
| core 0.26 mm | |
| In2.Cu (L3, 15 um) | power jumps (VSYS, VBAT, BATT_P, VIN, PVSS1, LRA_P, nRESET) and signal routing; GND fill in the spare area |
| prepreg 7628, 0.21 mm | |
| B.Cu (L4, 35 um) | the six dock pads, signal routing, GND pour |

Track length by layer: F.Cu 144 mm, In2.Cu 158 mm, B.Cu 107 mm, In1.Cu 0.

## Orientation and outline

The board mounts **parts-side down**: F.Cu faces into the pod, towards the
cell and the LRA, and B.Cu is the pod's outer face, carrying the dock pads
J601 (Ø1.6 mm, 2.5 mm pitch, y = 113): VIN, GND, SWDCLK, SWDIO, UART_RX,
UART_TX from right to left in board coordinates (mirrored when you look at
the outer face). Coordinates below are KiCad board coordinates,
with the board from (100, 100) to (133, 115).

## Envelopes (Dwgs.User)

| Envelope | Where | Notes |
| --- | --- | --- |
| ISP2454 antenna keep-out | x 100-105, full height | rule area inside the U1 footprint: no tracks, vias or pours on any layer |
| 60 mAh cell, 17 x 13.5 mm | x 107-124, y 100.75-114.25 | under F; starts 2 mm past the keep-out; PCM and lead end at x = 124 |
| Ø8 LRA (Ø8.5 envelope) | centre (128.75, 107.5), x 124.5-133 | under F, far end of the board |

## Placement

- **U1 ISP2454** at the left end, antenna end in the keep-out strip.
- **U401 LIS2DW12** just right of the module's top corner; C401 (turned
  90 deg, GND pad next to U401's GND pads) and C402 beside it.
- **U201 nPM1304** in the middle with L201, C204, C205, C207, NT201 to its
  left and the charger parts (C201, C202, C206, JP201, R202) to its right.
  C203 sits under PMIC pin 12, offset left so pins 13-15 can escape.
- **Dock row** along the bottom edge: R601-R604 and D602-D605 between the
  module and D601 (VIN TVS), above the B-side dock pads.
- **U501 DRV2605L** at the right end over the LRA envelope, with C501, C502.
- **Hand-solder pads** on F near the edges, 0.5 mm to other copper and mask
  at pad + 0.1 mm: TP201 (BAT+) and TP202 (BAT-) at the top edge by the cell's
  lead end; TP501/TP502 (LRA) at the right edge. TH201 sits over the cell.
- Test pads TP401, TP701-TP707 and TP203 for ACC_INT2, nRESET, I2C, VDD_2V0,
  VSYS, VBAT, GND and SHPHLD.

## Routing

- Power nets as routed before: 0.4 mm on the battery path (BATT_P, VBAT),
  0.3 mm on VIN/VSYS/PVSS1/SW1/LRA, 0.25 mm on VDD_2V0 where it leaves the
  PMIC. VSYS changes layer through two parallel In2 paths with two vias at
  each end. VBAT, BATT_P, VIN, PVSS1 and LRA_P have a second 0.45/0.3 via
  beside each layer change, joined on both layers, except three spots with
  no room: BATT_P at (121.7, 102.7), VIN's F-to-B jump at the dock (122.65,
  113.2) and LRA_P at U501 (129.15, 106.4). Each via is good for about 1 A,
  well above these currents.
- Signals: 0.12 mm tracks, 0.10 mm clearance, VDD_2V0 and REG 0.2 mm,
  routed with a scripted grid router because Freerouting crashed on this
  board. I2C runs U401 - U1 - U201 - U501 with test pads TP702/TP703. Each
  dock line runs from its B-side pad through one via to its TVS and 100 ohm
  resistor on F, then on to the module.
- Rules (in `rigid-rev-a.kicad_dru` and the netclasses): 0.10 mm clearance
  on all netclasses, 0.2 mm hole clearance, 0.2 mm from vias to other copper
  on inner layers, 0.5 mm around the hand-solder pads. Zones use 0.2 mm
  clearance.
- ANT_LINK (module pads 20 and 22) is joined on F.Cu, 0.65 mm long, right at
  the keep-out edge over the solid In1 GND.
- No F.Cu tracks inside the module's or the PMIC's pad ring (nRESET and
  some signals pass under the module on In2/B, outside the keep-out).
  VDD_2V0 passes under U401 between its pads, and REG and I2C_SCL pass under
  the U501 body; all are under solder mask.

## GND, stitching and vias

- In1 is solid GND. F, B and the spare area of In2 are GND pours (0.2 mm
  clearance, islands removed).
- Each F-side GND pad has its own via to In1 where there is room (15
  fan-out vias), plus 18 stitching vias around the board edge and 2 more at
  the module's top and bottom (outside the keep-out).
- Short GND links where no via fits beside the pad: U401 pad 8 + C402 share
  one via; C401's GND pad ties to U401's GND pads. C403, D605 and NT201 each
  have their own short stub and via: D605 0.6 mm of 0.3 mm track, NT201
  (the PVSS1 star point) 1.5 mm of 0.3 mm track.
- Two 0.3/0.2 mm GND vias under the U501 body tie the pin 4 and pin 8 pour
  pockets to In1.

| Vias | Count |
| --- | --- |
| 0.45/0.3, signal and power (incl. 8 second vias on power layer changes) | 80 |
| 0.45/0.3, GND (incl. 9 in the nPM1304 exposed pad and 4 in module corner pads) | 52 |
| 0.3/0.2, GND (8 in module pads, 2 under U501) | 10 |
| 0.3/0.2, nRESET (module pad 13) | 1 |
| Total | 143 |

### Inner module pads and POFV

The ISP2454 pads that sit inside the outer ring cannot be reached by a
track on F.Cu. Their outcome:

- **Interior GND pads** 8, 12, 14, 16, 18, 24 (column x = 105.2) and 21, 23
  (column x = 105.85) each have a 0.3/0.2 mm via in the pad. The large GND
  pads 1, 7, 25, 31 have 0.45/0.3 mm vias in the pad.
- **nRESET (pad 13)** has a 0.3/0.2 via in the pad and runs on In2 to TP701.
- **Pad 10** stays NC. The other inner pads are unused nets, left
  unconnected.

All of these are via-in-pad and need JLCPCB's **epoxy-filled and capped
(POFV)** option, which fills every via on the board. No via is left unfilled
in a pad. New vias placed during routing are all outside pads.

## DRC and ERC

`kicad-cli pcb drc --schematic-parity`: 0 violations, 0 unconnected items,
0 parity issues. Three warnings are excluded in `rigid-rev-a.kicad_pro`,
each with a comment: D605, D701 and L201 differ from their library copies
because one silk item was removed on purpose (D605's dot overlapped R605's
silk, D701's dot was clipped by the board edge, L201's segment touched U201's
outline). ERC: 0 errors, 0 warnings.

## Firmware charger requirements

The nPM1304 starts with **charging disabled**, a **4 mA** charge current
and **4.0 V** termination. Firmware must, over I2C:

1. set the charge current to **30 mA** (0.5 C for the 60 mAh cell),
2. set the termination voltage to **4.2 V**,
3. enable charging.

Until firmware does this the cell does not charge from the dock.

## Remaining compromises

1. **Antenna margin.** The cell and LRA envelopes start only 2 mm past the
   ISP2454 keep-out. That is an RF risk: do a phone RSSI test with the cell
   and LRA fitted (and in the pod) against a bare module before committing.
2. **POFV is required** (paid option) because of the via-in-pad on U1, U201
   and TP701.
3. **Three single-via power layer changes** remain where a second via does
   not fit: BATT_P at (121.7, 102.7), VIN at the dock (122.65, 113.2) and
   LRA_P at U501 (129.15, 106.4). Each is fine for the current.
4. **GND returns:** D605 and NT201 now have short 0.3 mm stubs to their own
   vias. NT201's via sits 1.5 mm from the pad because the net tie's copper
   bridge keeps vias away from its own side.
5. **Fine routing:** 0.12 mm tracks with 0.10 mm clearance (JLCPCB's 4-layer
   minimum is 0.09/0.09). B.Cu carries 107 mm of signal routing, so the
   outer-face GND pour is cut up; In1 stays solid.
6. **Placement nudges for routing:** C203 moved 0.65 mm left and C401 moved
   and turned 90 deg next to U401. Both stay next to the pins they decouple.
7. Values marked "(check)" in the schematic (L201, TPD1E10B06) are still to
   be confirmed before ordering.
