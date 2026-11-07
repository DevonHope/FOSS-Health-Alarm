# WakeBand rigid rev A (KiCad project)

4-layer 0.8 mm rigid board that replaces the flex design (archived in
`../flex-rev-a`). Routed, DRC clean, fab package in `fab/`. Last edited with
KiCad 10.0.3 (earlier revisions used 10.0.5; the file format is the same).

| Item | Value |
| --- | --- |
| Board | 33 x 15 mm, 1 mm corner radius, 0.8 mm FR4, ENIG |
| Pod | printed case rev A in `../case-rev-a` (one M2 screw); see below for the height stack |
| DRC | 0 violations, 0 unconnected, schematic parity 0 (1 documented exclusion); off-centre via ends checked as errors |
| Traces | straight or 45-degree segments only, 45-degree bends, every end on its pad or via centre (audit 2026-11-06, below) |
| ERC | 0 errors, 0 warnings |
| Vias | 142: 131 x 0.45/0.3 mm, 11 x 0.3/0.2 mm |
| Files | `rigid-rev-a-layout.pdf` (layers), `rigid-rev-a.pdf` (schematic), `fab/` |

## Stackup

JLCPCB JLC04081H-7628, 0.8 mm (also in `fab/gerbers/rigid-rev-a-job.gbrjob`):

| Layer | Use |
| --- | --- |
| F.Cu (L1, 35 um) | all SMT parts, the six dock pads (J601, top edge), signal fan-out, GND pour |
| prepreg 7628, 0.21 mm | |
| In1.Cu (L2, 15 um) | solid GND, no tracks; no copper in the antenna keep-out |
| core 0.26 mm | |
| In2.Cu (L3, 15 um) | power jumps (VSYS, VBAT, VIN, VDD_2V0, LRA_P, nRESET) and signal routing; GND fill in the spare area |
| prepreg 7628, 0.21 mm | |
| B.Cu (L4, 35 um) | faces the cell and LRA: hand-solder pads TP201/TP202/TP501/TP502, JP201, signal routing, GND pour; no parts |

Track length by layer: F.Cu 208 mm, In2.Cu 205 mm, B.Cu 147 mm, In1.Cu 0.

## Orientation, outline and pod height

The board mounts **parts-side out** (changed 2026-11-06): F.Cu, with every
part and the six dock pads, faces the case top, the pod's outer face. B.Cu
has no parts and faces the cell and the LRA, which sit between the board and
the wrist. The dock pads J601 are a row on F along the top edge, y = 101.6,
2.0 mm pitch, Ø1.4 mm: from left to right UART_TX (x 121.75), UART_RX,
SWDIO, SWDCLK, GND, VIN (x 131.75). GND sits between VIN and the data pads.
Coordinates below are KiCad board coordinates, with the board from
(100, 100) to (133, 115). The strip round the dock row (x 120.9-132.5,
y 100.3-102.9) has no parts, so the case top can sit right on the board
there and the pogo pins only reach through the case top.

Pod height, from the outer face (case rev A):

| Layer | mm |
| --- | --- |
| case top | 1.2 |
| tallest F part (L201, 0603 caps, SOD-123F) plus 0.2 mm | 1.3 |
| board | 0.8 |
| gap (B.Cu has no parts) | 0.2 |
| cell, up to | 5.0 |
| foam | 0.5 |
| wrist cover floor | 1.0 |
| **Total** | **about 10** (9 with a 4 mm cell) |

## Envelopes (Dwgs.User)

| Envelope | Where | Notes |
| --- | --- | --- |
| ISP2454 antenna keep-out | x 100-105, full height | rule area inside the U1 footprint: no tracks, vias or pours on any layer |
| 60 mAh cell, 17 x 13.5 mm | x 107-124, y 100.75-114.25 | under B; starts 2 mm past the keep-out; PCM and lead end at x = 124 |
| Ø8 LRA (Ø8.5 envelope) | centre (128.75, 107.5), x 124.5-133 | under B, far end of the board; circle top at y 103.25, bottom at 111.75 |

## 3D models

Every part on the board has a 3D model, except the test pads, the dock
pads, NT201 and JP201, which need none. KiCad 10 has no model for two
footprints, so `wakeband.3dshapes/` holds parametric ones (build123d; rebuild
with `pip install build123d`, then from this folder
`python wakeband.3dshapes/make_models.py wakeband.3dshapes`):

| Model | Used by | Size and source |
| --- | --- | --- |
| `InsightSiP_ISP2454_LGA-62_8x8mm.step` | U1 (also set in `wakeband.pretty`) | 8 x 8 x 1.0 mm, substrate plus overmould, pin-1 dot; size from the footprint |
| `Texas_DPY0002A_0.6x1mm_P0.65mm.step` | D602-D605 | 1.0 x 0.6 x 0.375 mm X1SON-2, bottom terminals, pin-1 band; TI MPSS034C |
| `LiPo_3.7V_60mAh_401215_PCM.step` | cell (off board) | 17 x 13 x 4.0 mm pouch with folded PCM at +X, lead stubs |
| `Vybronics_VG0832012_LRA_D8x3.25mm.step` | LRA (off board) | Ø8.0 x 3.25 mm can, lead tab at +X |
| `LED_TOGIALED_1615_RGB_CommonAnode.step` | D702 | 1.6 x 1.5 x 0.6 mm body and lens, pin-1 (anode) mark |
| `Kinetic_UTDFN-8_1.5x1.5mm_P0.4mm_EP1.45x0.8mm.step` | U202 | 1.5 x 1.5 x 0.5 mm UTDFN-8, pin-1 dot, terminals |

The paths use `${KIPRJMOD}`. D602-D605 use the KiCad library footprint
`Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm`; "Update footprint from library"
puts back the library's model path, which has no file in KiCad 10.

`make_placed.py` places the cell and the LRA in the board's STEP frame,
under B.Cu with a 0.2 mm gap: the cell centred at (115.5, 107.5) with its
lead end at x = 124, and the LRA centred at (128.75, 107.5) with its lead tab
turned towards TP501. The leads run to TP201 (bottom right) and TP202 (top
right) and to TP501/TP502. A clash check against the board's STEP finds no
overlaps. The tallest F part is now 1.1 mm (SW201 was removed on
2026-11-07); the charge LED is 0.6 mm.

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
- **JP201** (I_BAT jumper) on B in the bottom-right corner, between the
  cell's lead end and TP201, outside the cell and LRA outlines, so it can
  be cut for current measurement with the cell fitted.
- **Dock pads** J601 on F along the top edge (see Orientation). Their
  protection parts stay along the bottom edge: R601-R604 and D602-D605 (TI
  DPY package) between the module and D601 (VIN TVS).
- **U501 DRV2605L** at the right end over the LRA envelope, with C501, C502.
- **Hand-solder pads** on B (the cell side), 0.5 mm to other copper and
  mask at pad + 0.1 mm, all outside the cell and LRA outlines: TP201 (BAT+)
  at (129.0, 113.5) and JP201 in the bottom-right corner below the LRA
  circle, TP202 (BAT-) at (125.3, 101.6) in the top-right corner, TP501
  (LRA+) at (131.7, 101.5) and TP502 (LRA-) at (131.9, 113.5) at the right
  edge. TP202 joins the GND via in dock pad 2; TP502 has a filled via in its
  pad. TH201 sits on F over the cell, through the board.
- **Charge LED** D702 (RGB, 1.6 x 1.5 mm) at (130.225, 113.2), in SW201's old
  place at the bottom edge below U501, with its driver U202 (KTD2026) at
  (126.55, 113.2) and C208 (1 uF, VIN) at (128.1, 112.17). See "Charge LED"
  below.
- **Test pads**: TP702 (I2C_SDA) and TP704 (VDD_2V0) at the top edge near
  TH201, TP703 (I2C_SCL) left of U501, TP706 (VBAT) beside R201, TP401
  (ACC_INT2), TP701 (nRESET), TP705 (VSYS), TP707 (GND) and TP203
  (SHPHLD; with SW201 gone, this pad is the only way to pull SHPHLD low).
  TP704 has a filled via in its pad (flat after POFV, still
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
  with test pads TP702/TP703.
- Dock lines (rework 2026-11-06): the pads moved from B (bottom edge) to F
  (top edge), and each line now runs from its pad across the board to its
  TVS and 100 ohm resistor at the bottom edge, then on to the module:
  UART_TX 28.8 mm / 3 vias, UART_RX 27.0 / 3, SWDIO 41.9 / 4 (round the
  module end), SWDCLK 27.3 / 2, VIN 23.8 mm / 3 vias to C201.1. These were
  laid by a small 3-layer grid router (F, In2, B; In1 stays solid GND) and
  then checked by DRC and the trace audit; three spots were laid by hand.
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
  four charger caps share three on their GND spine. TP202 (BAT-) on B
  joins the GND via in dock pad 2 by a short B track.
- Each data TVS (D602-D605) has its own GND via about 0.8 mm from its GND
  pad.
- Two 0.3/0.2 mm GND vias under the U501 body tie the pin 4 and pin 8 pour
  pockets to In1.

| Vias | Count |
| --- | --- |
| 0.45/0.3, signal and power | 76 |
| 0.45/0.3, GND (incl. 9 in the nPM1304 exposed pad, 4 in module corner pads, 1 in dock pad 2) | 49 |
| 0.3/0.2, GND (8 in module pads, 2 under U501) | 10 |
| 0.3/0.2, nRESET (module pad 13) | 1 |
| Total | 136 |

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
2026-11-07, after the charge LED was added and the zones refilled): 0 errors, 0
warnings, 0 unconnected items, 0 parity issues, no isolated copper or
starved thermals. One warning is excluded in `rigid-rev-a.kicad_pro` with a
comment: D701 differs from its library copy because its silk dot (clipped by
the board edge) was removed on purpose. `track_not_centered_on_via` is now
an error (it was set to ignore, which is how off-centre via ends passed DRC
before). ERC: 0 errors, 0 warnings.

## Trace audit (2026-11-06)

**Charge LED (2026-11-07).** U202, D702 and C208 were placed and routed, and
SW201 with its SHPHLD stub removed. Same checks, whole board: no new
findings (only the eight nPM1304 exposed-pad stubs, as before). LED_R and
LED_G run side by side under U202's bottom pins along the board edge (U202
moved 0.2 mm up so both fit at 0.10 mm clearance and 0.3 mm from the edge);
I2C_SCL reaches the bus on In2 (3 vias), VSYS to D702's anode on In2 (2
vias), and U202's GND pin and exposed pad join the F.Cu GND pour (solid
connection). DRC with parity: 0 / 0 / 0. ERC: 0. Segments 465, vias 142.

**Dock rework (later on 2026-11-06).** After the dock pads moved to F and
the lead pads to B, the same checks were run again by script on the whole
board: every segment at 0, 45 or 90 degrees, every bend 45 degrees, no
segment under 0.1 mm outside a pad, no zig-zag step, no overlapping
same-net tracks, every end on a pad or via centre (the eight nPM1304
exposed-pad stubs below excepted, as before). DRC with schematic parity:
0 violations, 0 unconnected, 0 parity. ERC: 0. Segments 432, vias 136.

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

## Charge LED (D702, U202)

An RGB LED that shows charging through a 0.4 mm skin in the case top (no
opening; see `../case-rev-a`).

| Ref | Part | Notes |
| --- | --- | --- |
| D702 | TOGIALED TJ-S1615SW6TGLCCYRGB-A5, LCSC C273610 (JLCPCB extended) | 1.6 x 1.5 x 0.6 mm, top view, common anode. Pin 1 A, 2 B, 3 G, 4 R |
| U202 | Kinetic KTD2026EWE-TR, UTDFN-8 1.5 x 1.5 mm | 3-channel I2C LED driver, 0.125-24 mA current sinks. Digi-Key KTD2026EWE-TR; no LCSC listing found, so consign it |
| C208 | 1 uF 25 V X5R 0402, LCSC C52923 | U202 VIN decoupling, beside pin 5 |

- **Why a driver.** The module's GPIOs run at 2.0 V. Green and blue need
  about 2.8-3.6 V, so a GPIO can't light them. U202 sinks each colour to
  GND from the anode on VSYS.
- **Wiring.** Anode and U202 VIN on VSYS. D1 = blue, D2 = green, D3 = red.
  ST (pin 1) is not connected.
- **I2C.** On the existing bus (R203/R204 4.7 k to VDD_2V0) at address
  **0x30**. No clash with the nPM1304 (0x6B), DRV2605L (0x5A) or LIS2DW12
  (0x18/0x19). U202's VIH min is 1.2 V, so the 2.0 V bus drives it.
- **Power.** U202 starts in shutdown (about 0.1 uA). The LED is off until
  firmware turns it on, and only needs to be on while on the dock.
- **Brightness.** While docked VSYS is fed from the dock supply, so all
  three colours have headroom. On battery VSYS follows the cell, so blue
  and green get dim or go out as the cell runs down; use red for low-battery
  signals.

**Firmware.** The nPM1304 doesn't drive this LED. Firmware reads the
charger status from the nPM1304 over I2C and sets U202 to match, for
example amber while charging, green when done, red blinking on a fault.
Charging itself must still be enabled by firmware (see "Firmware charger
requirements" above).

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
6. **The cell and LRA sit on B.Cu signal tracks.** B carries 147 mm of
   tracks, 128 mm of them under the cell and LRA outlines (87 mm before the
   dock rework; the dock lines added 41 mm). They are under solder mask, but
   put a layer of kapton tape over B.Cu (or on the cell) before fitting the
   cell, and fit the cell and LRA with foam or adhesive pads, not bare.
   The F side, now the outer face, carries the parts; the case top covers
   it except the six dock windows, sealed round each window.
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
9. **SW201 removed (2026-11-07).** The ship-mode button was DNP and too tall
   for the case. Its place now holds the charge LED. SHPHLD is still on
   TP203 for bring-up.
10. **NTC** runs a long way round (In2 beside the charger caps, 18.5 mm
    from TH201 to pin 18). It is a DC thermistor line, so this is only a layout tidiness
    issue.
11. **Dock lines are long.** The TVS diodes D602-D605 and D601 stay at the
   bottom edge, 11-20 mm (along the copper 24-42 mm) from the dock pads at
   the top edge, so an ESD hit travels that far before it is clamped. The
   lines are under the case and mask, and the series resistors are still
   between the TVS and the module. Moving the protection parts to the top
   edge needs a re-route of the MCU-side nets.
12. **Bring-up test pads** TP702 and TP704 stay on F, under the case top.
13. **U202 (KTD2026) has no LCSC listing.** Consign it with U1 and U201.
