# WakeBand band rigid rev A: layout / manufacturing / fit review (Advisor 2)

Read-only review of `hardware/band/rev-a/pcb` (rigid-rev-a.kicad_pcb, .kicad_dru, .kicad_pro, fab/), `hardware/band/rev-a/case/case_rev_a.py` and `hardware/band/rev-a/contact-carrier`. KiCad was not available. I parsed the .kicad_pcb with sexpdata and checked geometry with shapely (pads, tracks, vias, filled zones). I parsed the Gerbers and drill files with my own scripts. The scripts are in `scratchpad/adv2-layout/`.

JLCPCB limits used: 4-layer 0.09/0.09 mm trace/space, via 0.25/0.15 mm minimum, 0.2 mm copper to edge, 0.1 mm green mask dam. These come from memory and were **not re-checked against JLCPCB's page today**.

No Blockers found. The board is routed, connected and short-free by my own checks, and the fab package matches the board.

## Findings

### A-L1: Reference text for C208, U202 and D702 is plotted 110-230 mm off the board (Minor)
- **What:** For these three parts, the footprint `property "Reference"` positions hold absolute board coordinates in a format where they are relative to the footprint. They plot far outside the outline. The F_Silkscreen Gerber has 338 stroke points outside the board:
  - "C208" at about (238.3, 14-17.7) in Gerber coordinates;
  - "U202" and "D702" at about (249-262, -229).
- **Evidence:** rigid-rev-a.kicad_pcb line 620 C208 `(at 128.1 110.2 90)`, line 5016 U202 `(at 124 115.7 0)`, line 10191 D702 `(at 130.225 115.9 0)`. Other parts use small relative offsets, e.g. C207 `(at 0 -1.43 0)`. Rendered strokes read "C208", "U202" and "D702". `fab/gerbers/rigid-rev-a-F_Silkscreen.gto` lines 66-404.
- **Effect:** The three parts have no refdes on the board. Off-outline legend can trigger a JLCPCB DFM query or confuse the viewer. The board size comes from Edge.Cuts, so the order is not blocked.
- **Fix:** Set the three Reference positions to small relative offsets (or move them to F.Fab like the other refs), then re-plot.
- **Confidence:** high.

### A-L2: 0402 GND pads with a solid zone connection: tombstoning risk (Minor)
- **What:** These pads override to `zone_connect 2` (solid), while the other pad of each part is a 0.12-0.2 mm track:
  - R202.2, C401.2, R605.2 (0402);
  - C403.2 (0603).

  The F GND pour otherwise uses 0.25 mm thermal spokes. My copper-around-pad estimate for C401.2 is 0.81 mm² against about 0.33 mm² on pad 1. R605.2 is 0.57 against 0.19.
- **Evidence:** zone_connect overrides in the .kicad_pcb (pads listed above, plus U1 1/7/25/31, U201 EP, U202 EP and U501 4/8, which are fine).
- **Fix:** Use thermal relief (zone_connect 1 or the default) on the 0402/0603 GND pads. Keep solid only on the EPs and module pads.
- **Confidence:** medium. This is a risk, not a certainty; JLCPCB's reflow profile usually copes.

### A-L3: U202 (KTD2026 UTDFN-8) exposed-pad paste is 100% (Minor)
- **What:** The F_Paste aperture for U202.9 is the full 1.45 x 0.8 mm rectangle, flashed at (126.55, 113.2). The gap from the EP to the pin pads is only 0.125 mm. Full paste on a 1.5 mm DFN EP risks the part floating or tilting and bridging to pins 1-8.
- **Fix:** Use a paste margin or ratio of about -30 to -40% on pad 9, or split the aperture into 2 windows (about 50-65% coverage). The U201 EP is already done this way: 9 x 0.93 mm windows, about 65%.
- **Confidence:** medium-high.

### A-L4: DNP parts still get paste apertures (Note/Minor)
- **What:** R201 (124.09/125.11, 111.2), D701 and R701 have `dnp` but keep F.Paste. The stencil will print paste on bare pads, which reflows into solder bumps. R201's pads are VBAT and SHPHLD.
- **Fix:** Remove the paste layer from DNP footprints for the stencil, or accept the bumps.
- **Confidence:** high that the apertures exist; low that this harms anything.

### A-L5: SWDCLK dock landing pad has its via in the centre, where the spring pin lands (Minor)
- **What:** Via 84 (0.45/0.3 mm) is at (131.5, 101.1), exactly at the J601.3 pad centre on B.Cu, so the plunger presses on the POFV cap. VIN (132.35, 114.0) and GND (132.35, 111.3) put their vias at the pad edge instead.
- **Effect:** Cap dimple or plating variation sits under the contact point. The LRA vibrates the pod, so there is fretting wear on a static, thin-gold ENIG contact.
- **Fix:** Move the via to the pad edge like VIN and GND.
- **Confidence:** high on the geometry; the reliability effect is unverified.

### A-L6: Docs out of step with the board: wrong via-in-pad list and other stale statements (Minor, ordering/doc)
- **TP704 and TP705 have no via in the pad.**
  - TP704's VDD_2V0 via is at (119.35, 100.95), beside the pad.
  - TP705 has no via within 1 mm.
  - `pcb/README.md` (Placement, Routing) says TP704 has a filled via in its pad and that VSYS reaches D702 "from a via in TP705's pad".
  - `fab/README.md` lists "the VDD_2V0 via in test pad TP704" among the via-in-pad reasons for POFV.
- **My via-in-pad list from geometry** is 30 vias:
  - U1 pads 1, 7, 8, 12, 13, 14, 16, 18, 21, 23, 24, 25, 31;
  - U201 EP (9 vias);
  - C201.1, C205.1, D601.1, TP701, TP202, TP501, JP201.2;
  - J601.1, J601.2, J601.3.
- **Mask on TP202:** `fab/README.md` says TP201, TP202, TP501 and TP502 open 0.1 mm larger. TP202 has mask equal to the pad (1.5 x 1.5 in B_Mask).
- **Title block:** comment 1 says "mounts parts-side down". The README says parts-side out.
- **Via table:** README "GND, stitching and vias" totals 136. The board has 140 (129 x 0.45/0.3 and 11 x 0.3/0.2), as the header table says.
- **Case script angles:** `case_rev_a.py` says the lead tab is at 300 deg. `make_placed.py` puts the tab at about 250 deg in the KiCad frame, towards TP501.
- **Fix:** Correct the text. POFV is still needed: the conclusion stands.
- **Confidence:** high.

### A-L7: CPL rotations left at KiCad values (Note, ordering risk)
- **What:** The CPL matches the board exactly; positions and rotations were checked by script. The rotations are raw KiCad values. Polarized parts:
  - D601 SOD-123F: cathode = pad 1 = VIN.
  - D702 1615 RGB: pin 1 (anode) at top-right (131.1, 112.65).
  - U401, U501 at 90°.
  - Consigned U1 at 270°, U201 at 0°, U202 at 0°.

  All depend on the JLCPCB preview check that `fab/README.md` describes.
- **Fix:** Before paying, confirm each polarized part in the DFM preview. Attach `u1-pin1-drawing.pdf` and pin-1 notes for U201 and U202.
- **Confidence:** unverified. I could not check JLCPCB's library zero orientations.

### A-L8: Ground under the module joins the rest of In1 only through necks under 1 mm (Note, RF)
- **What:** In1 is one polygon with 58 voids. Eroding it by 0.5 mm splits off the U1 ground region (x 105.5-109.4). The module escape-via antipads at x ≈ 108.8-110.4 merge into a near-continuous slot. The necks are about 0.6-1.0 mm wide.
- **Other voids:**
  - 2.75 mm² at x 117.5-120.2, y 109.7-112.4, under PMIC pins 9-16;
  - 2.37 mm² at x 106.0-108.8, y 101.7-103.6.

  B-side tracks crossing these voids have only In2 as reference.
- **Effect:** DC is fine: the module has 12 GND pads with vias, and F/B pours. The antenna ground reference and return paths are weakened.
- **Fix:** If you rework, spread the escape vias so 0.3 mm or more of In1 copper stays between antipads. Check antipad merging under U1 and U201.
- **Confidence:** medium (geometry high, RF effect unquantified).

### A-L9: Antenna surroundings (Note; README compromise 1 confirmed)
- **Keep-out is clean:** rule area x 100-105, y 98.5-116.5, all four layers. No track, via or fill intersects it; every fill's min x is 105.0. Only mechanical pads 49-62 are inside. Module edge x = 101 is 1 mm from the board edge, as the ISP2454 datasheet asks (per docs/flex-rev-a-pinout.md).
- **Near-field material:**
  - Cell envelope starts at x 107: 2 mm from the keep-out and under the module's digital half.
  - Nearer magnet edge at x 111.
  - Shell posts (x 100.15-100.95) and the 3.6 mm PETG end wall touch the antenna strip.
  - Shell roof is 0.2 mm over the module.

  Plastic in contact will detune it slightly.
- **ANT_LINK** is 0.65 mm on F over In1. No 50 Ω feed is needed.
- **Fix:** Run the RSSI test in the closed pod, as the README says.
- **Confidence:** high on geometry.

### A-L10: Spring-pin barrel to LRA clearance is about 0.02-0.27 mm (Minor, fit)
- **What:** SWDIO (131.5, 103.3) and GND (131.5, 111.7) pins are 5.02 mm from the LRA centre (128.75, 107.5).
  - Barrel radius 0.75 at z 2.7-5.0 overlaps the can's z range 3.25-6.5.
  - Gap to the Ø8.0 can is 0.27 mm.
  - Gap to the Ø8.5 envelope (can plus lead) is 0.02 mm.
  - The locating arcs sit only on the left (110-145° and 215-280°). On the pin side, the LRA can shift by the 0.15 mm arc clearance plus hand placement.
- **Effect:** The can may touch a pin barrel, causing rattle or buzz. The metal can rubbing on GND or SWDIO barrels is probably electrically harmless.
- **Fix:** Add a locating arc or rib on the +X side between the pins (around 330-30°), or move the pin column 0.3 mm to +X if the edge clearance allows.
- **Confidence:** medium. Mill-Max 0906-2 dimensions are taken from the case script, not verified against the datasheet. The README's clash check found no overlap at nominal.

### A-L11: Small height margin under the shell roof (Note)
- **What:** ROOF_IN = F + 1.1 + 0.2. The tallest parts at datasheet maximum are:
  - DRV2605L DGS: 1.1 mm;
  - SMF12A SOD-123FL: about 1.0-1.1 mm (unverified);
  - ISP2454: 1.0 mm.

  Add about 0.03-0.05 mm of solder, and FDM roof tolerance against a 0.05 mm press-fit land.
- **Note on the README:** the pcb README table says "tallest F part (L201, 0603 caps, SOD-123F) + 0.2 = 1.3". The case uses 1.1 + 0.2.
- **Fix:** Check the actual SMF12A and DGS maximum heights. Consider ROOF_IN + 0.1.
- **Confidence:** medium.

### A-L12: Board-in-pocket clearance against JLCPCB outline tolerance (Note)
- **What:** The case pocket is the board outline ±0.15 mm. JLCPCB's routed-outline tolerance is about ±0.2 mm (from memory). A board on the high side, plus FDM over-extrusion, can jam.
- **Fix:** Measure the boards before printing, or set CLR to 0.2.
- **Confidence:** medium.

### A-L13: Copper 0.30 mm from the edge, including the VIN landing pad (Note)
- **What:** The J601.1 VIN landing pad is 0.3 mm from the bottom edge. Every pour is also 0.3 mm from the edge.
- **JLCPCB:** this is OK for routing. As `fab/README.md` already says, it is too close for V-score.
- **Fix:** When choosing rails, ask for tabs or mouse bites away from x 129-133 on both long edges (the dock pads and the TP201 corner).
- **Confidence:** high.

### A-L14: Magnets near the LRA (Note, unverified)
- **What:**
  - The N42 Ø3 x 1 mm magnet at (120.5, 107.5) is about 8 mm from the LRA centre and about 5 mm below the can's level.
  - The other magnet is about 6.3 mm below L201.
  - My estimated field at L201 is about 4 mT, which is negligible.

  An LRA's moving magnet is sensitive to external static fields only at much higher levels. This is probably fine.
- **Fix:** Compare vibration strength with the magnets fitted at bring-up.
- **Confidence:** low (estimate only).

## Checked and OK
- **Connectivity:** union-find over pads, tracks, vias and filled zones on 4 layers. 67 nets, 0 split, 0 shorts. No dangling track ends. Every via connects copper on 2 or more layers.
- **Pours:** every F/B/In2 fill fragment carries a GND via or GND pad. The smallest are an F fragment on U201.16 and F slivers at the top edge with 1 via each. No floating islands.
- **Clearances** (my own check, matching the .kicad_dru):
  - 0 violations of 0.10 mm signal clearance, 0.2 mm to zones, 0.2 mm via to other copper on inner layers, and 0.5 mm around TP201/202/501/502.
  - Minimum gaps: 0.12 mm track-track (F), 0.107 mm pad-track (U201.17), 0.139 mm track-via.
  - Minimum hole-to-hole 0.285 mm (same net).
  - Copper to edge at least 0.30 mm.
- **JLCPCB 4-layer limits:** tracks 0.12/0.15/0.2-0.5 mm; vias 0.45/0.3 and 0.3/0.2 (0.05 mm annular ring, aspect 4:1). The mask dam minimum is 0.125 mm at U202, with 0 openings closer than 0.1 mm between different nets on F or B. All are within the limits from memory.
- **POFV:** `filling yes` and `capping yes` are set in the board setup. They are required by the via-in-pad list in A-L6.
- **Power widths:**

  | Net | Width and layer |
  | --- | --- |
  | VBAT | 0.4 mm F |
  | BATT_P | 0.5 mm B |
  | VIN | 0.3 mm F/In2 (17.9 mm on In2, about 70 mΩ) |
  | VSYS | 0.2-0.3 mm (two 0.2 mm In2 under the EP, about 0.45 A combined at 10 °C rise) |
  | LRA± | 0.3 mm |
  | SW1 | 0.3 mm |
  | PVSS1 | 0.4 mm |

  Adequate for 30-100 mA charge and LRA drive.
- **Fab package:**
  - The zip equals gerbers/ plus the BOM and CPL byte for byte.
  - Job file: 4 layers, 0.8 mm, ENIG, size 33.05 x 15.05 mm.
  - Edge.Cuts is a 33 x 15 mm outline with R1 corners.
  - The PTH drill has 140 holes, identical to the board vias (0.2 and 0.3 mm). NPTH is empty.
  - The .kicad_pcb has not changed since the Gerber export; it was renamed in fa05ef9, 100% similarity.
- **BOM vs CPL vs board:** designators identical. CPL positions and rotations equal the footprint data (Y negated, matching the Gerbers). DNP parts R201, D701 and R701 are excluded. Consigned U1, U201 and U202 have a blank LCSC field. LCSC stock and availability were **not verified**.
- **Silk:** KiCad clears legend over every F and B pad (LPC flashes). No dark legend is within 0.15 mm of the edge, apart from A-L1.
- **Paste:**
  - B_Paste is empty (single-sided assembly).
  - No paste on test pads, dock or UART pads, or hand-solder pads.
  - U201 EP paste is about 65% in 9 windows.
- **Dock coordinates agree in all three sources:** J601.1-4 at x 131.5, y 113.9 (VIN), 111.7 (GND), 101.1 (SWDCLK), 103.3 (SWDIO).
  - PCB: Ø1.6 mm B pads, mask Ø1.7 mm.
  - `case_rev_a.py` SP_X/SP_Y.
  - Contact-carrier P1-P4: Ø1.4 mm pads, 0.6 mm PTH, 0.4 mm copper to edge, no traces.

  Nets match the order. Both landing pairs are outside the LRA envelope.
- **Case vs board:**
  - LED_XY (130.225, 113.2) is the D702 footprint centre. The 2.4 x 2.3 mm pocket with 0.4 mm skin covers the 1.6 x 1.5 mm body.
  - The shell land (x 119.8-133.15, y up to 103.2) and the bottom-right post (x ≥ 131.75) touch only TP704, J601.5/6 and TP705 copper, not parts. The post is 0.22 mm from D702 pad 1/4 copper.
  - Antenna-end posts (y 101.1-103.2 and 111.8-113.9) are clear of the module body (y 103.5-111.5).
  - The screw boss is outside the board (x 133.8-139.4).
  - The cell envelope (x 107-124) and LRA (x ≥ 124.5) don't overlap. The B hand-solder pads are outside both.
- **JP201:** its bridge copper (B.Cu fp_poly, net-tie group) is present in B_Cu, so VBAT reaches BATT_P.
