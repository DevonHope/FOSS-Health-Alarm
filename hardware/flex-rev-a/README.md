# WakeBand flex rev A (KiCad project)

Schematic for the first custom board: a 2-layer flex PCB that folds once around
a 12 x 30 mm, 110 mAh cell (pod about 22 x 40 x 8 mm). The design plan is in
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

## Routing (in progress, 2026-10-30)

Partial route pushed so other machines can pull it: **DRC 0 errors**, 3
connections still open (PAD_SWDIO at R602, VBUSOUT at C206, NTC from U201 to
TH201). Warnings left: silkscreen overlaps only.

- Routed with Freerouting 1.9.0 (Specctra DSN/SES), then post-processed:
  GND pours (island A both layers, island B top, hatched top in the neck),
  ISP2454 pads 8/24 tied to 7/25, teardrops enabled on every pad and via.
- Placement changes for routing: R601-R604 moved from island B to island A
  next to the neck (TVS stay at the dock pads); neck widened from 5 to 7 mm
  (y 105.5-112.5).
- Net classes: Power 0.3 mm (VIN, VSYS, VBAT, BATT_P, SW1, PVSS1), Motor
  0.25 mm (LRA), Rail 0.2 mm (VDD_2V0), GND 0.2 mm, signals 0.12 mm;
  clearance 0.13 mm so via holes stay 0.25 mm from other copper.
- No-via rule areas everywhere except the stiffened areas, 0.5 mm inside
  their edges; 0.32 mm no-track bands along the outline.
- DRC exclusions (in the .kicad_pro): the 6 "unconnected" items on ISP2454
  GND pads 12, 14, 16, 18, 21, 23, left unconnected on purpose.
