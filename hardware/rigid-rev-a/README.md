# WakeBand rigid rev A (KiCad project)

4-layer 0.8 mm rigid board that replaces the flex design (archived in
`../flex-rev-a`). Routed, DRC clean, fab package in `fab/`. Last edited with
KiCad 10.0.3 (earlier revisions used 10.0.5; the file format is the same).

| Item | Value |
| --- | --- |
| Board | 33 x 15 mm, 1 mm corner radius, 0.8 mm FR4, ENIG |
| Pod | about 35 x 17 mm outline with 1 mm side walls (estimate); height about 8-9 mm (see below) |
| DRC | 0 violations, 0 unconnected, schematic parity 0 (1 documented exclusion); off-centre via ends checked as errors |
| Traces | straight or 45-degree segments only, 45-degree bends, every end on its pad or via centre (audit 2026-11-06, below) |
| ERC | 0 errors, 0 warnings |
| Vias | 135: 124 x 0.45/0.3 mm, 11 x 0.3/0.2 mm |
| Files | `rigid-rev-a-layout.pdf` (layers), `rigid-rev-a.pdf` (schematic), `fab/` |

## Stackup

JLCPCB JLC04081H-7628, 0.8 mm (also in `fab/gerbers/rigid-rev-a-job.gbrjob`):

| Layer | Use |
| --- | --- |
| F.Cu (L1, 35 um) | all SMT parts, signal fan-out, GND pour |
| prepreg 7628, 0.21 mm | |
| In1.Cu (L2, 15 um) | solid GND, no tracks; no copper in the antenna keep-out |
| core 0.26 mm | |
| In2.Cu (L3, 15 um) | power jumps (VSYS, VBAT, VIN, VDD_2V0, LRA_P, nRESET) and signal routing; GND fill in the spare area |
| prepreg 7628, 0.21 mm | |
| B.Cu (L4, 35 um) | the six dock pads, signal routing, GND pour |

Track length by layer: F.Cu 159 mm, In2.Cu 165 mm, B.Cu 96 mm, In1.Cu 0.

## Orientation, outline and pod height

The board mounts **parts-side down**: F.Cu faces into the pod, towards the
cell and the LRA, and B.Cu is the pod's outer face, carrying the dock pads
J601 (Ø1.6 mm, 2.5 mm pitch, y = 113): VIN, GND, SWDCLK, SWDIO, UART_RX,
UART_TX from right to left in board coordinates (mirrored when you look at
the outer face). Coordinates below are KiCad board coordinates,
with the board from (100, 100) to (133, 115).

Pod height, counting both walls:

| Layer | mm |
| --- | --- |
| outer wall over B.Cu | 0.8 |
| board | 0.8 |
| tallest F-side part (L201, 0603 caps, SOD-123F) | 1.1 |
| gap | 0.2 |
| cell | 4-5 |
| floor | 0.8 |
| **Total** | **about 8-9** |

The outer wall covers B.Cu except six windows over the dock pads (see
compromise 6).

## Envelopes (Dwgs.User)

| Envelope | Where | Notes |
| --- | --- | --- |
| ISP2454 antenna keep-out | x 100-105, full height | rule area inside the U1 footprint: no tracks, vias or pours on any layer |
| 60 mAh cell, 17 x 13.5 mm | x 107-124, y 100.75-114.25 | under F; starts 2 mm past the keep-out; PCM and lead end at x = 124 |
| Ø8 LRA (Ø8.5 envelope) | centre (128.75, 107.5), x 124.5-133 | under F, far end of the board; circle top at y 103.25 |

## 3D models

Every part on the board has a 3D model, except the test pads, the dock
pads, NT201 and JP201, which need none. KiCad 10 has no model for two
footprints, so `wakeband.3dshapes/` holds parametric ones (build123d; rebuild
with `python make_models.py wakeband.3dshapes`):

| Model | Used by | Size and source |
| --- | --- | --- |
| `InsightSiP_ISP2454_LGA-62_8x8mm.step` | U1 (also set in `wakeband.pretty`) | 8 x 8 x 1.0 mm, substrate plus overmould, pin-1 dot; size from the footprint |
| `Texas_DPY0002A_0.6x1mm_P0.65mm.step` | D602-D605 | 1.0 x 0.6 x 0.375 mm X1SON-2, bottom terminals, pin-1 band; TI MPSS034C |
| `LiPo_3.7V_60mAh_401215_PCM.step` | cell (off board) | 17 x 13 x 4.0 mm pouch with folded PCM at +X, lead stubs |
| `Vybronics_VG0832012_LRA_D8x3.25mm.step` | LRA (off board) | Ø8.0 x 3.25 mm can, lead tab at +X |

The paths use `${KIPRJMOD}`. D602-D605 use the KiCad library footprint
`Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm`; "Update footprint from library"
puts back the library's model path, which has no file in KiCad 10.

`make_placed.py` places the cell and the LRA in the board's STEP frame:
they sit 1.3 mm out from F.Cu (1.1 mm tallest part plus a 0.2 mm gap), the
cell centred at (115.5, 107.5) with its lead end at x = 124, and the LRA
centred at (128.75, 107.5) with its lead tab turned towards TP501. The leads
run to TP201/TP202 and TP501/TP502. A clash check against the board's STEP
finds no overlaps. SW201 (DNP, 1.6 mm tall) is in the board STEP and sits
outside the LRA circle.

## Placement

- **U1 ISP2454** at the left end, antenna end in the keep-out strip.
- **U401 LIS2DW12** just right of the module's top corner. C401 and C402
  sit right of it, 1.0 mm of track from pins 9 and 10; their GND pads share
  one via, and U401's GND pads 5-8 share another.
- **U201 nPM1304** in the middle. The BUCK1 parts sit left of it (see
  "Buck loop" below).
- **Charger caps** stacked right of U201, each beside its pin: C206
  (VBUSOUT, pin 22), C201 (VIN, pin 21), C205 (VSYS, pin 20), C202 (VBAT,
  pin 19). Their GND pads are joined by an F.Cu spine with three vias to
  In1 between the pads. R202 (VSET1) and R201 (DNP) sit below the stack.
  C203 sits under PMIC pin 12, offset left so pins 13-15 can escape.
- **JP201** (I_BAT jumper) in the top strip between the cell area and
  TP201.
- **Dock row** along the bottom edge: R601-R604 and D602-D605 (TI DPY
  package) between the module and D601 (VIN TVS), above the B-side dock
  pads.
- **U501 DRV2605L** at the right end over the LRA envelope, with C501, C502.
- **Hand-solder pads** on F, 0.5 mm to other copper and mask at pad + 0.1 mm:
  TP201 (BAT+) at (125.75, 101.6) and TP202 (BAT-) at (128.86, 101.6),
  past the cell's lead end (pad copper starts at x 124.75 and 127.86) and
  above the LRA circle (pads end at y 102.6, the circle starts at 103.25),
  so neither solder joint sits on the cell pouch. TP501/TP502 (LRA) at the
  right edge. TH201 sits over the cell.
- **Test pads**: TP702 (I2C_SDA) and TP704 (VDD_2V0) at the top edge near
  TH201, TP703 (I2C_SCL) left of U501, TP706 (VBAT) beside R201, TP401
  (ACC_INT2), TP701 (nRESET), TP705 (VSYS), TP707 (GND) and TP203
  (SHPHLD). TP704 has a filled via in its pad (flat after POFV, still
  probeable).

## Buck loop (nPM1304 BUCK1, pins 1-4)

Laid out after Nordic's reference: input cap across PVDD/PVSS1 at the pins,
output cap between the inductor and PVSS1, PVSS1 tied to GND only at the net
tie next to pin 2.

| Path (pad centre to pad centre, along the copper) | Now | Before the review |
| --- | --- | --- |
| C204.2 (PVSS1) to pin 2 | 1.7 mm, no vias | 5.4 mm |
| C204.1 (VSYS) to pin 4 (PVDD) | 1.7 mm, no vias | 3.3 mm, 2 vias |
| C207.2 (PVSS1) to pin 2 | 4.2 mm, no vias | 7.3 mm, 2 vias |
| C207.1 to L201.2 | 2.3 mm (pad centres are 2.2 mm apart) | 2.9 mm |
| NT201.1 to pin 2 | 3.0 mm | 9.6 mm |
| L201.1 to pin 3 (SW1) | 2.9 mm | 1.1 mm |
| C205.1 (VSYS) to pin 20 | 1.5 mm | 13.0 mm |
| pin 4 to pin 20 (VSYS) | 12.4 mm, 2 vias | 23.9 mm, 4 vias |

"Now" was measured after the 2026-11-06 trace clean-up, when every track
end sits on its pad centre; the clean-up moved these paths by 0.2 mm or
less.

- C204 sits 0.7 mm from pins 2 and 4. SW1 (0.3 mm) leaves pin 3 between
  C204's pads, under its body, to L201. The edge-to-edge copper of SW1 is
  2.2 mm: longer than before, the price of putting C204 across pins 2 and 4.
- C207 sits above L201; PVSS1 runs 0.4 mm wide from C207.2 through NT201.1
  and C204.2 to pin 2.
- NT201 sits on that PVSS1 link, 1.7 mm from pin 2, with its own GND via to
  In1 0.7 mm from its GND pad.
- Pin 1 (VOUT1, sense) drops through a via to In2 and lands at the
  L201.2/C207.1 node.
- Pin 4 and C204.1 change layer through two VSYS vias to two 0.2 mm In2
  tracks under the PMIC exposed pad (one in each gap between the EP via
  rows), which end in a via in C205.1's pad next to pin 20. Pin 32 joins
  through its own via. VSYS to U501/C501 runs on F from pin 32 along the
  top of the PMIC area.

## Routing

- Power: 0.4 mm on the battery path (BATT_P 0.5 mm, VBAT), 0.3 mm on
  VIN/VSYS/SW1/LRA, 0.4 mm on PVSS1 between the caps, 0.25 mm at the PMIC
  pins, 0.2 mm VSYS under the EP, 0.25 mm on VDD_2V0 where it leaves the
  buck. VBAT changes layer with two vias at each end. Single vias remain on
  VSYS (pin 32 and the via in C205.1), VIN (the via in C201.1, at
  (123.1, 111.75) and at the dock, (122.65, 113.2)), VDD_2V0 and LRA_P at
  U501 (129.15, 106.4). Each via is good for about 1 A, well above these
  currents.
- Signals: 0.12 mm tracks, 0.10 mm clearance, VDD_2V0 and REG 0.2 mm,
  routed with a scripted grid router because Freerouting crashed on this
  board, then cleaned up (see "Trace audit" below). The router keeps vias
  out of pads. I2C runs U401 - U1 - U201 - U501
  with test pads TP702/TP703. Each dock line runs from its B-side pad through
  one via to its TVS and 100 ohm resistor on F, then on to the module.
- Rules (in `rigid-rev-a.kicad_dru` and the netclasses): 0.10 mm clearance
  on all netclasses, 0.2 mm hole clearance, 0.2 mm from vias to other copper
  on inner layers, 0.5 mm around the hand-solder pads. Zones use 0.2 mm
  clearance.
- ANT_LINK (module pads 20 and 22) is joined on F.Cu, 0.65 mm long, right at
  the keep-out edge over the solid In1 GND.
- No F.Cu tracks inside the module's or the PMIC's pad ring (nRESET and
  some signals pass under the module on In2/B, outside the keep-out).
  VDD_2V0 passes under U401 between its pads, and REG and I2C pass under
  the U501 body; all are under solder mask.

## GND, stitching and vias

- In1 is solid GND. F, B and the spare area of In2 are GND pours (0.2 mm
  clearance, islands removed).
- Each F-side GND pad has its own via to In1 where there is room, plus
  stitching vias around the board edge and at the module's top and bottom
  (outside the keep-out).
- Shared GND vias: U401 pads 5-8 share one; C401 and C402 share one; the
  four charger caps share three on their GND spine. TP202 (BAT-) has three
  GND vias around it.
- Each data TVS (D602-D605) has its own GND via about 0.8 mm from its GND
  pad.
- Two 0.3/0.2 mm GND vias under the U501 body tie the pin 4 and pin 8 pour
  pockets to In1.

| Vias | Count |
| --- | --- |
| 0.45/0.3, signal and power | 70 |
| 0.45/0.3, GND (incl. 9 in the nPM1304 exposed pad and 4 in module corner pads) | 54 |
| 0.3/0.2, GND (8 in module pads, 2 under U501) | 10 |
| 0.3/0.2, nRESET (module pad 13) | 1 |
| Total | 135 |

### Vias in pads and POFV

The ISP2454 pads that sit inside the outer ring cannot be reached by a
track on F.Cu. Their outcome:

- **Interior GND pads** 8, 12, 14, 16, 18, 24 (column x = 105.2) and 21, 23
  (column x = 105.85) each have a 0.3/0.2 mm via in the pad. The large GND
  pads 1, 7, 25, 31 have 0.45/0.3 mm vias in the pad.
- **nRESET (pad 13)** has a 0.3/0.2 via in the pad and runs on In2 to TP701.
- **Pad 10** stays NC. The other inner pads are unused nets, left
  unconnected.

Other vias in pads: nine in the nPM1304 exposed pad, TP701 (nRESET), C201.1
(VIN), C205.1 (VSYS) and TP704 (VDD_2V0). All of these need JLCPCB's
**epoxy-filled and capped (POFV)** option, which fills every via on the
board.

## DRC and ERC

`kicad-cli pcb drc --schematic-parity --severity-all` (KiCad 10.0.3,
2026-11-06, after the trace clean-up and a zone refill): 0 errors, 0
warnings, 0 unconnected items, 0 parity issues, no isolated copper or
starved thermals. One warning is excluded in `rigid-rev-a.kicad_pro` with a
comment: D701 differs from its library copy because its silk dot (clipped by
the board edge) was removed on purpose. `track_not_centered_on_via` is now
an error (it was set to ignore, which is how off-centre via ends passed DRC
before). ERC: 0 errors, 0 warnings.

## Trace audit (2026-11-06)

Every track was checked by script against the rules below, before and after
a clean-up. Vias, layers, track widths and the netlist did not change; every
net stays connected and every clearance holds (0.10 mm, 0.2 mm from vias on
inner layers, 0.2 mm to holes, 0.3 mm to the edge, 0.5 mm at the
hand-solder pads, nothing in the antenna keep-out).

| Check | Before (2ebc6fb) | After |
| --- | --- | --- |
| Segments | 599 | 399 |
| Staircase steps (short zig-zags from the grid router) | 182 | 0 |
| Segments not at 0, 45 or 90 degrees | 34 | 0 |
| Bends outside pads that are not 45 degrees (14 of them at 90 degrees) | 30 | 0 |
| Segments shorter than 0.1 mm outside pads | 142 | 0 |
| Junctions with an acute angle between branches | 3 | 0 |
| Track ends that touch a pad or via but stop off its centre | 118 | 0 |
| Tracks that join on a pad or via edge instead of its centre | 25 | 0 |
| Tracks ending on the middle of another track | 3 | 0 |
| Stubs (one dead end, one poking 0.3 mm out of a via) | 2 | 0 |
| Overlapping or crossing same-net tracks (VSYS and LRA_P on In2) | 4 | 0 |
| Other-net clearance problems | 0 | 0 |

How: each run between pads, vias and junctions was re-laid with straight and
45-degree segments only, ends moved to pad and via centres, and each new
segment checked against all other-net copper. Eight spots were laid by
hand: the nPM1304 ground pins (straight stubs from each pin centre into the
exposed pad), C401/C402 and U401 GND into their vias, the I2C_SCL branch on
B.Cu (now meets the diagonal at 90 degrees), PMIC_INT into its via (a small
loop removed), R204.1 into its via, the In2 VSYS runs (one straight run, fed
at 90 degrees) and VBAT down to R201.1.

Kept on purpose:

- 19 very short segments (0.01-0.1 mm) and 3 small jogs sit wholly inside a
  pad or via, where a pad centre is off the 45-degree line to the next point
  (for example two vias 0.45 x 0.40 mm apart). They add no copper outside
  the pad.
- Five direct pin-to-pin links: U401 pins 2-3, 2-9 (VDD), 5-6, 6-7 (GND),
  and the ISP2454 ANT_LINK between pads 20 and 22.
- The F.Cu GND bar at x = 123.025 that passes over C205.2 and C201.2: it is
  the GND spine of the charger caps.

## Firmware charger requirements

The nPM1304 starts with **charging disabled**, a **4 mA** charge current
and **4.0 V** termination. Firmware must, over I2C:

1. set the charge current to **30 mA** (0.5 C for the 60 mAh cell),
2. set the termination voltage to **4.2 V**,
3. enable charging.

Until firmware does this the cell does not charge from the dock.

## Protection parts

- **D601 (VIN TVS): Littelfuse SMF12A**, LCSC C207255, SOD-123FL. 12 V
  standoff, 13.3-14.7 V breakdown at 1 mA, 19.9 V clamp at 10.1 A, 2.5 uA
  max leakage at 12 V. It clamps below the nPM1304's 22 V VBUS absolute
  maximum and survives a wrong 12 V supply. (SMF18A, used before, clamped at
  29.2 V.)
- **D602-D605: TI TPD1E10B06DPYR** on KiCad's
  `Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm`, TI's DPY land pattern.

## Remaining compromises

1. **Antenna margin.** The cell and LRA envelopes start only 2 mm past the
   ISP2454 keep-out. That is an RF risk: do a phone RSSI test with the cell
   and LRA fitted (and in the pod) against a bare module before committing.
2. **POFV is required** (paid option) because of the vias in pads listed
   above.
3. **Single-via power layer changes** remain on VSYS, VIN, VDD_2V0 and LRA_P
   (listed under Routing). Each is fine for the current.
4. **SW1 is 2.9 mm** pad centre to pad centre (2.2 mm between pad edges),
   up from 1.1 mm, so that C204 sits right at pins 2 and 4. The VSYS link
   under the EP is two 0.2 mm tracks (the EP via rows leave no room for
   wider ones); it carries only the buck's input current.
5. **Fine routing:** 0.12 mm tracks with 0.10 mm clearance (JLCPCB's 4-layer
   minimum is 0.09/0.09).
6. **B.Cu carries signal tracks** (96 mm), so the outer face is not just
   GND and dock pads. The pod's outer wall must cover B.Cu except the six
   dock-pad windows, with the window edges sealed so sweat cannot reach the
   tracks. If the case cannot do that, conformal-coat B.Cu everywhere except
   the six pads.
7. **C403** (10 uF on VDD_2V0) is 4.5 mm from U401 pin 9; C401 (100 nF) is
   1.0 mm from it.
8. **L201 land pattern (confirmed).** L201 uses KiCad's
   `L_Murata_DFE201610P` footprint for the Murata DFE201610E-2R2M. Murata's
   DFE201610E sheet (m_dfe201610e, "Recommended patterns") gives two
   1.6 mm tall pads with a 0.9 mm gap and 2.0 mm overall span, so
   0.55 x 1.6 mm pads centred at +/-0.725 mm. That is exactly the KiCad
   footprint (and the copy on the board), and the DFE201610P sheet gives the
   same drawing. The part is 2.0 +/-0.2 x 1.6 +/-0.2 x 1.0 max mm with
   0.5 +/-0.3 mm electrodes. No change needed; the only difference is that
   KiCad rounds the pad corners (roundrect), which is normal.
9. **SW201 (DNP)** has a courtyard over the LRA envelope. Don't fit it.
10. **NTC** runs a long way round (In2 beside the charger caps, 18.5 mm
    from TH201 to pin 18). It is a DC thermistor line, so this is only a layout tidiness
    issue.
