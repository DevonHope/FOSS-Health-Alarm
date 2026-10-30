# WakeBand flex rev A (KiCad project)

Schematic for the first custom board: a 2-layer flex PCB that folds once around
a 12 x 30 mm, 110 mAh cell (pod about 23.5 x 40 x 8 mm). The design plan is in
[docs/flex-pcb-schematic-plan.md](../../docs/flex-pcb-schematic-plan.md) and the
module pinout and GPIO plan are in
[docs/flex-rev-a-pinout.md](../../docs/flex-rev-a-pinout.md).

Open `flex-rev-a.kicad_pro` in KiCad 10. All sheets, the symbol library and the
footprint library are saved in KiCad 10 format. `flex-rev-a.pdf` is a plot of
the current sheets and `bom.csv` is the bill of materials.

| Sheet | Status |
| --- | --- |
| `power` | nPM1304 (QFN32) from Nordic's reference circuit "configuration 2": VBUS from dock VIN, cell pads through a cut-able current jumper, 10k NTC, BUCK1 2.0 V on VDD_2V0 (VSET1 68k), BUCK2 and load switches unused, SHPHLD on the internal 50k pull-up with a test pad (extra pull-up and button DNP), PMIC_INT on GPIO3, the bus's 4.7k I2C pull-ups. |
| `mcu` | ISP2454-LX placed, all 48 signal pins wired to global labels or marked no-connect. Pad 10 (P1.10) is no-connect (lower outer row, not routable without via-in-pad). GND pads 12, 14, 16, 18 stay unconnected on the board pending Insight SiP's OK (noted on the sheet). |
| `sensors` | LIS2DW12 on VDD_2V0 with 100 nF on each supply pin plus 10 uF bulk, I2C address 0x19 (CS and SA0 strapped high), INT1 to ACC_INT1, INT2 to a test pad. |
| `haptics` | DRV2605L on VSYS with 1 uF on VDD and REG, EN from the SoC, IN/TRIG tied to GND (effects triggered over I2C), OUT+/OUT- to two LRA lead pads. Footprint TSSOP-10_3x3mm (KiCad's land pattern for TI's DGS package). |
| `dock` | Six pogo pads (2 mm pitch, 1.2 x 3.0 mm), SMF18A TVS (18 V standoff) on VIN and TPD1E10B06 on each data pad, 100 ohm series on the four data lines, 100k pull-down on UART_RX. |
| `debug` | 0.8 mm test pads on nRESET, I2C, VDD_2V0, VSYS, VBAT, GND; DNP debug LED on LED_DBG. |

Every sheet lists its open items as **(check)** in a note. The main ones:
the nPM1304 exposed-pad size against Nordic's reference layout, TVS leakage
at 2.0 V on the data pads (TPD1E0B04 is a lower-leakage alternative), the
SMF18A's surge clamp (29.2 V) against VBUS's 22 V rating, the LIS2DW12 land
pattern, the inductor land pattern, and the GPIO used for PMIC_INT.

Reference designators are numbered per sheet (power 2xx, sensors 4xx,
haptics 5xx, dock 6xx, debug 7xx; the module is U1).

Project libraries: `wakeband.kicad_sym` (ISP2454-LX, nPM1304-QEAA and
LIS2DW12 symbols) and `wakeband.pretty` (ISP2454 footprint with its antenna
keep-out, 6-pad dock strip, 0.8 mm test pad, LRA lead pad). Sheets connect
through global labels, so the top sheet has no wires.

## BOM

`bom.csv` uses JLCPCB's column names (Comment, Designator, Footprint, LCSC)
plus MPN, Qty and DNP. Test pads, dock pads, LRA pads, the solder jumper and the
net tie are excluded (copper only). Delete the DNP rows before uploading for
assembly. LCSC numbers were checked on lcsc.com on 2026-10-30. Two parts have
none: the ISP2454-LX module and the nPM1304-QEAA (LCSC only lists the
nPM1304-EK), so they need another source or consignment.

## Review fixes (2026-10-30)

- BUCK1 raised from 1.8 V to 2.0 V (R202 47k -> 68k); the global net is now
  VDD_2V0 on every sheet. At -5 % the rail is 1.9 V, well above the
  ISP2454's 1.7 V minimum.
- DRV2605L IN/TRIG tied to GND and ISP2454 pad 10 left unconnected.
- VIN TVS changed to Littelfuse SMF18A (LCSC C409420) so a wrong 9-12 V
  supply does not destroy it.
- 10 uF bulk cap added at the LIS2DW12 VDD pin (C403).
- MCU sheet uses the GND power symbol instead of a GND global label.

## ERC status (KiCad 10.0.5, 2026-10-30)

`kicad-cli sch erc flex-rev-a.kicad_sch`: **0 errors, 0 warnings.**

- nRESET has only a test pad (the nRF54L15 has an internal pull-up). The
  passive test pad satisfies KiCad's "input not driven" check, so no
  exclusion is needed.
- The ISP2454 symbol's ground pins were renamed from VSS to GND so they no
  longer clash with the GND label (same pin numbers and connections).
- PWR_FLAGs mark the off-board sources: dock VIN (dock sheet), the cell
  (VBAT and GND, power sheet), and PVSS1, which reaches GND only through the
  net tie.

## Layout hand-off (step 8, first pass, 2026-10-30)

The sections from here to "Fold and assembly orientation" record earlier
passes. The current layout is described under "Layout review rework" below.

`flex-rev-a.kicad_pcb` holds the unfolded flex with every footprint placed
and **no routing yet**. `flex-rev-a-layout.pdf` is a plot of it.

- Outline (Edge.Cuts), all corners rounded 1 mm: island A x 96-132,
  y 100-118 (36 x 18 mm); neck x 132-140, 5 mm wide; island B x 140-176,
  y 99-119 (36 x 20 mm). Fold line at x = 136. Pod about 22 x 40 mm.
- Both islands grew 4 mm (2026-10-30, option 1). The antenna shadow on
  island B mirrors island A's far end, so lengthening island B alone would
  not move it: island A grew too and the module moved to its new far end.
  The shadow is now x 171-176, and the 30 mm cell bay (x 140.5-170.5) ends
  0.5 mm before it.
- Layers: User.1 Stiffener.Top (unused), User.2 Stiffener.Bottom (FR4 0.4 mm
  under island A and the LRA pad, PI 0.2 mm behind the dock pads),
  User.3 Bend.Zone, User.4 Antenna.Keepout. Dwgs.User has the cell, LRA and
  fab notes.
- Rule areas: BEND_ZONE (no vias, pads or footprints) and ANTENNA_SHADOW_B
  (no copper at all), the module's keep-out mirrored onto island B across the
  fold. The module carries its own keep-out rule area.
- Design rules: 0.12 mm board, 0.1 mm min track and clearance, 0.3 / 0.55 mm
  vias, 0.3 mm copper-to-edge. Default net class 0.15 mm tracks.
- Placement: ISP2454 in the far corner of island A, antenna 1 mm from the
  edge; PMIC, sensor, haptic driver and test pads on island A. Island B has
  the battery tabs at the neck end, the LRA pad, the six dock pads with
  their TVS and series resistors, and the NTC under the cell bay.
- DRC: no shorts, clearance, courtyard or keep-out errors. The 125
  unconnected items are the unrouted nets. The rest (117) are silkscreen
  overlaps to tidy during layout.

Open questions for layout:

- About 11 nets cross the 5 mm neck (VIN, GND, VBAT/BATT_P, NTC, four
  dock lines, two LRA lines); this fits at 0.1/0.1 mm, but the power lines
  want 0.3 mm or more.
- The NTC sits on island B's outer face, so it senses the cell through the
  0.12 mm flex, not in direct contact.

## Routing (complete, 2026-10-30)

**DRC: 0 errors, 0 warnings, 0 unconnected** (7 documented exclusions, below).
Pad nets match the schematic netlist; ERC 0/0.

How it was routed: Freerouting 1.9.0 (Specctra DSN/SES) for the bulk, a small
scripted grid router for the last VSYS link and two GND links, then scripted
post-processing (pours, teardrop flags, neck staggering, silkscreen).

- Placement changes for routing: R601-R604 moved from island B to island A
  next to the neck (TVS stay at the dock pads); U501 (DRV2605L) group moved
  to the lower right of island A and U401 (LIS2DW12) group next to the
  module, so the PMIC's power pins face a clear path to the neck; PMIC caps
  regrouped around U201. Neck widened from 5 to 7 mm (y 105.5-112.5).
- Net classes: Power 0.3 mm (VIN, VSYS, VBAT, BATT_P, SW1, PVSS1), Motor
  0.25 mm (LRA), Rail 0.2 mm (VDD_2V0), GND 0.2 mm, signals 0.12 mm;
  clearance 0.13 mm so via holes stay 0.25 mm from other copper.
- Neck / fold zone: no vias; every trace is straight and perpendicular to
  the fold; top and bottom traces staggered (no trace sits over another);
  hatched GND on the top layer only. The stagger jogs at the neck ends are
  45-degree corners, not arcs.
- GND: solid top pour on island A and island B, hatched in the neck. No
  bottom pour: island B allows no vias off its stiffeners, and on island A the
  bottom layer is mostly tracks, so a bottom pour only left floating slivers.
- No copper in either antenna keep-out (module rule area on island A,
  ANTENNA_SHADOW_B on island B), on any layer.
- Vias only on stiffened areas, at least 0.5 mm inside the stiffener edges
  (no-via rule areas everywhere else); 0.32 mm no-track bands along the
  outline. 65 vias in total.
- ISP2454: only outer-row pads are routed (plus the pad 20-22 ANT_LINK
  trace in the outer row). Pads 8 and 24 join 7 and 25 with short traces.
  Pads 12, 14, 16, 18 (trapped lower row) and 21, 23 (inner) stay
  unconnected.
- nRESET is **not routed**: pad 13 is an inner-row pad. TP701 stays on the
  board for a bodge wire; SWD can reset the chip.
- Teardrops are enabled on every pad and via. KiCad 10's Python API cannot
  generate them, so the saved board has none; `kicad-cli pcb export gerbers
  --check-zones` (used for `fab/`) refills the zones and adds them to the
  Gerbers. Refill the zones in the KiCad GUI (B) to see them in the editor,
  and check them there before ordering.
- Silkscreen: reference designators moved to F.Fab (assembly drawing); the
  footprint outlines stay on silk.

Narrower than the net class (all short, at pins): VSYS 0.15 mm on the
2 mm link from U201 pin 20 to C205 (0.3 mm cannot leave a 0.5 mm-pitch QFN
pin between its neighbours), and a few VIN, SW1 and VSYS segments at 0.25 mm
next to the PMIC.

DRC exclusions (stored in `flex-rev-a.kicad_pro`, each with a comment): six
"unconnected" items between the reserved ISP2454 GND pads, and the nRESET
pad 13 to TP701 connection.

## Fold and assembly orientation (fixed 2026-10-30)

Island B folds **under** island A along x = 136.

- Island A's F side, with every SMT part, faces up, away from the wrist.
- Island B's F side faces down to the case floor, so the dock pads (J601)
  face the dock.
- The cell and the LRA sit on island B's **B side** (inner face, between
  the islands). Their pads are on B.Cu: cell tabs TP201 (+) / TP202 (-) at
  the neck end, LRA leads TP501 (+) / TP502 (-) just outside the LRA
  stiffener. The LRA tapes onto the FR4 stiffener in the 8 mm motor strip
  beside the cell. These four pads are hand-soldered after assembly.
- The NTC (TH201) stays on F and senses the cell through the 0.12 mm flex.
- All SMT parts are on F: single-sided assembly.

BATT_P, LRA+, LRA- and the TP202 GND link were rerouted to the B-side pads
with the scripted router (BATT_P and the GND link at 0.3 mm, LRA at 0.25 mm).
In the neck the LRA pair moved up on F.Cu to stay clear of VIN and BATT_P on
B.Cu; LRA+ steps there with 45-degree jogs 0.75 mm either side of the fold
line, so it does not cross LRA-. No trace sits over another at the fold line.

## Layout review rework (2026-10-30, current layout)

**DRC: 0 violations, 0 unconnected, 0 footprint errors** (7 documented
exclusions: the six reserved ISP2454 GND pads and nRESET pad 13 to TP701).
Pad nets match the schematic netlist; ERC 0/0.

- Outline: both islands 21.5 mm wide (y 98.25-119.75), island A x 96-132,
  island B x 140-176, neck x 132-140 and 9 mm wide (y 104.5-113.5), 1 mm
  corner fillets. Folded pod about 23.5 x 40 mm.
- Island B across its width: 0.3 mm edge, 12 mm cell bay, 0.5 mm gap, 8 mm
  LRA/dock strip, 0.7 mm edge. The LRA no longer overlaps the cell.
- Neck: every trace inside x 132-140 is one straight, locked segment along
  x: 7 on F.Cu, 4 on B.Cu, at least 0.5 mm in y between any F and B lane, no
  vias. All jogs and layer changes are on the islands. Hatched GND on F.Cu
  only.
- Stiffeners (User.2, FR4 0.4 mm): all of island A, and one merged strip on
  island B (x 140.6-175.4, y 110.75-119.25) under the dock pads, D601-D605
  and TH201, with no hinge gap at TP501/TP502. Windows 0.3 mm larger than
  each B-side pad. Vias only on stiffened areas, 0.5 mm inside their edges.
- Hand-solder pads (B.Cu): cell tabs TP201 (+) / TP202 (-) and LRA leads
  TP501 / TP502 sit in the motor strip near the neck, outside the cell bay
  and clear of the LRA. 0.5 mm clearance to other nets, coverlay opening
  pad + 0.1 mm.
- Battery path: BATT_P and the TP202 GND run 0.4 mm and straight on B.Cu
  (about 13 mm per side) to their neck lanes, with no vias on island B. On
  island A every battery-path layer change (VBAT/BATT_P) uses two vias.
- No via touches an SMD pad, except the 4 intended vias in the nPM1304
  exposed pad (pad 33). Vias moved off ISP2454 pads 1 and 25 sit at least
  0.15 mm clear and join with short traces.
- Ground: top pour on both islands, bottom pour on island A, 24 stitching
  vias on island A, solid (not thermal) connection on ISP2454 GND pads 1, 7,
  25 and 31. 98 vias in total (41 on GND).
- Stackup in the board file: polyimide core 25 um, 18 um copper, polyimide
  coverlay 25 um each side, ENIG.

Remaining compromises:

- Narrow segments at fine-pitch pins: VSYS at U501 0.25 mm, the GND link
  from C203 to U201 pad 33 at 0.2 mm, VDD_2V0 into U201 pin 12 at 0.2 mm,
  VSET1 at 0.15 mm.
- The top-pour pieces on island A are joined through the bottom pour by
  stitching vias, not by 0.5 mm top-layer links.
- ANT_LINK (pads 20-22) is a short manual trace. The top pour cannot
  surround it (antenna keep-out on one side, reserved pads on the other);
  the bottom pour is under it.
- TH201 (NTC) sits on the stiffened strip at the edge of the cell bay and
  senses the side of the cell.
- nRESET is still unrouted (inner pad 13); TP701 stays for a bodge wire.
- Teardrops are only added at Gerber export (`--check-zones`); refill zones
  in the KiCad GUI to see them in the editor.

## Fab package (`fab/`)

`fab/flex-rev-a-fab.zip` holds the same files as `fab/gerbers/`,
`fab/bom_jlcpcb.csv` and `fab/cpl_jlcpcb_top.csv`. `fab/README.md` has the
stackup, the coverlay-opening note and the JLCPCB rotation checks.

- Gerbers: F/B copper, mask, paste and silkscreen, Edge.Cuts, the bottom
  stiffener (User.2 `Stiffener_Bottom`), bend zone (User.3), antenna
  keep-out (User.4), drawings/notes (Dwgs.User) and F.Fab. Exported with
  `--check-zones`, so zones are refilled and teardrops included. User.1 (top
  stiffener) is not exported and the job file does not list it.
- Drill: Excellon, plated and non-plated separate, with Gerber drill maps.
- `cpl_jlcpcb_top.csv`: JLCPCB columns (Designator, Mid X, Mid Y, Layer,
  Rotation), F side only, 31 fitted parts.
- `bom_jlcpcb.csv`: fitted parts only (no DNP, no pads).
- The stiffener mapping (User.2 = FR4 0.4 mm) must be confirmed with JLCPCB
  before ordering.
