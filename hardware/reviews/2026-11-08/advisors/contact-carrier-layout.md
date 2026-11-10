# Contact carrier review: layout, manufacturing, mechanical fit (Advisor 2)

Scope: `hardware/band/rev-a/contact-carrier` (rev-b copy is byte-identical: same .kicad_pcb, same zips, md5 checked),
`band/rev-a/case/case_rev_a.py`, `band/rev-b/case/case_rev_b.py` (imports rev A's cover unchanged),
`band/rev-{a,b}/pcb/rigid-rev-{a,b}.kicad_pcb` (J601), `dock/rev-b/pcb/dock-pcb-rev-b.kicad_pcb`, `dock/rev-b/case/dock_rev_b.py`
(+ `dock/rev-a/case/dock_rev_a.py` it imports). Nothing was built (no KiCad/build123d here): geometry is from the
script constants, the .kicad_pcb text and the gerbers. Mill-Max data: web datasheets for 0906-2/-4-15-20-75-14-11-0
and the Mill-Max catalogue p.25 (023-028.pdf). JLCPCB: jlcpcb.com/capabilities/pcb-capabilities.

Prompt correction: the band magnets are Ø3 x 1 mm (case script `MAG_D, MAG_T = 3.0, 1.0`); Ø4 x 1.5 mm is the rev B dock's.

## Findings

### C-L1 — Major — Flange-side solder joint has no pad to fillet to; joint is on the "wrong" side for this pin
- **What:** The assembly solders the pin from the flange (top) side, in the cover (case README "Home build" step 5;
  carrier README). The top pad is Ø1.4 mm, the 0906 flange is Ø1.83 mm, so the flange completely covers the pad:
  there is no exposed copper outside the flange for a fillet. Solder fed at the flange edge either balls on the
  flange/mask or wicks by capillary under the flange and down the 0.6 mm plated hole (0.08 mm radial gap round the
  0.43 mm tail). Anything that runs through comes out on the bottom pad, right at the 0.15 mm tail stub that is the
  dock contact surface and on the PETG at the window apex (0.7 mm floor under the carrier). The iron also heats the
  carrier while it sits on the 0.7 mm PETG floor step. Mill-Max specify this part as a through-hole solder tail
  ("Solder mount in .020 min. mounting hole"), i.e. soldered from the tail side.
- **Evidence:** `contact-carrier.pretty/SpringPin_Mill-Max_0906_PTH_D1.4mm_Drill0.6mm.kicad_mod` pad `size 1.4 1.4`,
  `drill 0.6`; F.Mask opening Ø1.5 (gerber `%ADD10C,1.500000*%`); case_rev_a.py L51 `SP_FLANGE_D 1.83`, L45 `CARRIER_Z 0.7`.
  Plunger wicking itself is low risk (plunger exits the barrel 2.69 mm above the flange; the tail is solid).
- **Fix:** Solder the pins to the carrier *before* it goes in the cover: solder paste on the top pads, pins in,
  reflow on a hotplate / hot air with the carrier on a holed spacer (flange joints form under the flange and in the
  barrel, like an SMT joint), inspect that the tail ends are clean, then glue. (A top pad bigger than the flange won't fit a 2.2 mm board at 0.2 mm edge clearance, so reflow under
  the flange is the practical route.) Update the home-build steps.
- **Confidence:** High on the geometry (pad < flange); medium on how badly a hand joint will turn out.

### C-L2 — Major — Dock-to-band XY capture at the tail is only ±0.15 mm; dock recess allows ±0.3 mm
- **What:** The band's tail end is 0.55 mm up a cone window (Ø2.0 at the skin, Ø1.2 at z 0.7). At the tail
  height the cone is Ø1.37, and the dock plunger is Ø1.067, so the plunger only reaches the tail if the band is
  within (1.371 − 1.067)/2 = **0.15 mm** of the dock pin axis. The rev B dock recess clearance is 0.3 mm a side
  (`dock_rev_a.py` `REC_CLR = 0.3`, reused by `dock_rev_b.py` via `offset(A.BAND, A.REC_CLR)`). At 0.3 mm offset the
  plunger edge meets the cone at z ≈ 0.29, about 0.26 mm short of the tail: open contact unless the 4 cone walls
  push the band sideways against magnet-loaded PETG-on-PETG friction (all 4 pins are on one line x 131.5, so
  they don't constrain rotation about that line's centre well). Stacking also: carrier-in-pocket 0.1 mm, JLC routed
  outline ±0.2 mm (hole-to-edge), tail in 0.6 hole ±0.08 (±0.15 at max hole +0.13), printed cone apex (README
  already expects to drill it).
- **Evidence:** case_rev_a.py L47 `WIN_D0, WIN_D1 = 2.0, 1.2`, L244 cone 0 → 0.7; tail tip z 0.55 (L339-342);
  dock pin Ø1.07 (`dock_rev_a.py` L102); dock pin XY = band XY (dock PCB P1–P4 at 131.5 / 101.1, 103.3, 111.7,
  113.9, verified).
- **Fix:** Make the window a straight bore at the tail (e.g. Ø1.7–1.8 from z 0.4 to 0.7, cone only below), giving
  ±0.3 mm capture while the floor between pair holes (2.2 mm pitch) keeps ≥0.4 mm webs; and/or tighten the dock
  recess to 0.15 mm; and/or reduce the tail recess. Verify at bring-up by docking with deliberate side offset.
- **Confidence:** Medium (geometry certain; whether the cones self-centre in practice is unverified).

### C-L3 — Minor — Stack-up nominal is fine, worst case is thin at the low end
- **Calc (rev A and rev B identical; rev B reuses rev A's cover and constants, B.Cu 6.70 on both, both boards 0.8 mm):**
  carrier underside 0.70 + 1.60 = flange seat 2.30; 0906-2 A (Initial Height) = 5.004 → free tip 7.304; B.Cu 6.70
  → compression **0.60 mm** of 1.397 max stroke (rated mid 0.711). Force ≈ 55 g/pin (catalogue spring 75: 25 g
  initial, 60 g at mid).
- **Tolerances:** pin length ±0.15 (catalogue ±.006"), 1.6 mm FR4 ±0.16 (±10 %), printed floor step 0.7 and the
  ledge that sets B.Cu ±0.1 each (layer quantisation at 0.12–0.16 mm layers), solder/epoxy under flange or carrier
  +0–0.05. Worst case 0.60 ± 0.56 → **0.04 … 1.16 mm**: never bottoms (1.397), but at the bad corner barely touches
  (~25 g). RSS ±0.27 → 0.33…0.87, comfortable. 0906-4 would put the free tip at 8.29 → 1.59 mm compression >
  1.397 stroke: bottomed, so -2 is the right choice.
- **Datasheet inconsistency:** the web datasheet for 0906-2 gives Overall Length .246" but Initial Height .197" +
  tail .069" = .266". For 0906-4, .236 + .069 = .305 = its listed OL, so IH is measured from the flange underside and
  the -2 OL is most likely a typo — but if IH were wrong instead (tip 4.495 above the flange) compression would be
  only ~0.10 mm. The catalogue's A = .197 for -2 supports the design value.
- **Fix:** Measure flange-underside-to-tip on a received pin, the printed floor-step height, and carrier thickness
  before gluing; order the carrier with 1.6 mm (keep) and note that a 0.1 mm shim / sanding the step trims it.
- **Confidence:** High on the arithmetic; medium on the print tolerances assumed.

### C-L4 — Minor — Carrier won't drop into its pocket as drawn: 0.1 mm clearance vs ±0.2 mm routed outline, sharp panel corners and tab stubs
- **What:** Pocket = carrier + 0.1 mm a side, square corners (`box(...)` L239). JLC routed-edge tolerance is ±0.2 mm,
  printed pockets come out small, and printed inside corners are rounded by the nozzle. The README says the board
  has 0.5 mm corner radii, and the single-board Edge.Cuts has them, but the **panel** outline (the file you order)
  has square corners at all four corners of each carrier, plus a 1.2 mm tab at each end; with JLC's router radius
  the tab roots fillet out to nearly the full 2.2 mm end width, so the break stub sits across the whole end, 0.45 mm
  from the end pad (101.1 − 0.7 = 100.4 vs end 99.95).
- **Evidence:** `fab/panel/contact-carrier-rev-a-panel-Edge_Cuts.gm1` (lines only, no arcs; tab x 130.9–132.1,
  y 97.95–99.95 and 115.05–117.05); `fab/gerbers/...-Edge_Cuts.gm1` (G02 arcs r 0.5); case_rev_a.py L46 `CARRIER_CLR 0.1`.
- **Fix:** Pocket clearance 0.2–0.25 mm with corner reliefs (or Ø0.6 dog-bones) in the pocket; in the README tell
  the builder to cut tabs with flush cutters/saw (not snap) and sand ends; optionally put the 0.5 mm corner arcs into
  the panel outline. Pin XY then depends on the pocket, which feeds C-L2.
- **Confidence:** High.

### C-L5 — Minor — Rev A main board has a via in the SWDCLK landing pad, rev B a via on the SWDCLK pad edge
- **What:** Rev A: via (0.45/0.3 mm, net PAD_SWDCLK) exactly at (131.5, 101.1) — the plunger lands on an open 0.3 mm
  hole (B.Mask is open over the pad). Rev B: via at (132.1, 101.4), 0.67 mm from the pad centre (hole edge 0.52 mm
  from centre) — inside the Ø1.067 plunger footprint at ~0.0–0.2 mm XY error. Same-net, so not a short; it is a
  contact-wear / intermittent-contact issue (plunger tip sitting on a hole rim, plating cracks after cycles; solder
  that wicked into the via makes a bump). VIN vias at (132.35, 114.0) on both revs are 0.86 mm out (hole edge 0.71),
  marginal. Electrical advisor may also see these.
- **Fix:** Move the vias out of the 1.6 mm pad (≥1.1 mm from centre) or specify filled/capped vias (JLC via-in-pad).
- **Confidence:** High (coordinates read from the .kicad_pcb).

### C-L6 — Minor — Dock pin pushes the band pin up against its own solder joint
- **What:** The dock 0906-4 (-75) pushes the band tail up with ~60 g at mid-stroke; the band pin's own spring pushes
  the barrel down with ~55 g at 0.60 mm (as little as ~25 g at the C-L3 low corner). Net 5–35 g per pin is carried
  in tension by the flange solder joint and epoxy (with the fragile joint of C-L1). README step 4 already notes the
  pins lift when loose.
- **Fix:** Fine once the joint is good (C-L1); keep the epoxy bead over the flanges. Note for bring-up.
- **Confidence:** Medium (spring values from catalogue; web page lists 10 g initial, catalogue 25 g).

### C-L7 — Minor — Carrier location in −x relies on a 0.3 mm step
- **What:** The pocket starts at z 0.7 and the floor is 1.0 mm, so the long edge facing the LRA is held by only
  0.3 mm of PETG (the LRA pedestal is cut back over x ≥ 130.2, y 104–111). The ends (cover side walls) and the +x
  edge (end wall/ledge, except round y 107.5 where the LRA cavity Ø8.8 reaches x 133.15) are full height. Also the
  pocket removes the 0.5 mm board ledge at x 132.5–132.7, leaving only 0.3 mm of ledge under the board end
  along the carrier.
- **Fix:** Acceptable with epoxy; a 0.6–0.8 mm step or two printed pegs/ribs on the LRA side would locate it before
  the glue sets. Check that the board end still sits on the remaining 0.3 mm ledge.
- **Confidence:** High (from script geometry).

### C-L8 — Minor — LRA can to inner spring-pin barrels: ~0.27 mm nominal, ~0.12 mm worst case
- **What:** Inner pins (131.5, 103.3) and (131.5, 111.7) are 5.02 mm from the LRA centre (128.75, 107.5). Barrel Ø1.5
  (z 2.71–4.99) overlaps the LRA's z range (3.25–6.5). Clearance to the Ø8.0 can 0.27 mm; LRA locating arcs have 0.15
  clearance → 0.12 mm worst case; to the script's Ø8.5 "lead round the can" envelope only 0.02 mm. The pins sit at
  ±57° from the LRA axis, i.e. in the 300–62° sector the script reserves for the lead. The placed model routes the
  leads from the tab at ~250° (away from the pins), so no wire should be there — but if a builder wraps the lead
  that way an enamelled wire rubs on SWDIO/GND barrels under vibration.
- **Fix:** Say in the build notes to route the LRA leads away from the pin side; or nudge LRA_C 0.2 mm in −x.
- **Confidence:** Medium-high (no STEP boolean run here; the script's own clash check reports 0).

### C-L9 — Note — JLC ordering details
- Single carrier 2.2 x 15.1 mm is below JLC's 3 x 3 mm FR4 minimum → the 6-up customer panel is the right call.
  Panel 48.2 x 29.1 mm (job file 48.25 x 29.15), rails 3 mm (x) / 5 mm (y), 2.0 mm routed slots, 1.0 mm frame ribs
  between slots, tabs 1.2 mm without mouse bites. JLC's own panel rules (≥4 mm break tabs, 70 x 70 mm for V-cut) apply
  to JLC panelisation, not to an outline you supply; order as "Panel by Customer", 1 design, and expect possible
  engineering-query about the tabs. V-score is not possible (<70 mm panel); mouse bites don't fit a 1.2 mm tab.
- The job file says `"Finish": "None"`; README says ENIG, BUY-LIST says HASL is fine: pick one (HASL is fine;
  the board is only soldered to). Drill-map .gbr files are inside the zip: harmless, JLC ignores them.
- Thickness 1.6 mm must be selected explicitly (it is the default, and the stack-up depends on it).
- **Confidence:** High for the JLC figures as published today.

## Checked and OK
- Zips: both `contact-carrier-rev-a-fab.zip` (12 files) and `...-panel-fab.zip` (12 files) contain F/B Cu, F/B mask,
  F/B silk, Edge.Cuts, PTH + (empty) NPTH drill, job file; rev-b copies are identical (md5).
- Drill: 24 x 0.600 mm PTH in the panel, positions match the 6 carriers at 7.2 mm pitch; no slots needed.
- Hole size: 0.6 mm finished (JLC +0.13/−0.08 → 0.52–0.73) for the Ø0.432 tail; ≥ Mill-Max's .020" (0.508) min and
  ≥ .004" over the tail at the low limit.
- Annular ring 0.40 mm (JLC min 0.18–0.25). Copper-to-routed-edge 0.40 mm (long sides) / 0.45 mm (ends) vs JLC 0.2.
  Hole-to-edge 0.8 mm FR4. Mask opening 1.5 mm over the 1.4 mm pads.
- XY: carrier holes = case `SP_X/SP_Y` = rev A J601 = rev B J601 pads (B.Cu, Ø1.6) = dock rev B P1–P4, and nets agree
  (SWDCLK 101.1, SWDIO 103.3, GND 111.7, VIN 113.9). Same KiCad x/y frame in all three with +z toward the board,
  so no mirroring error. Carrier pattern is symmetric about (131.5, 107.5) and each pin is its own contact, so it
  can go in either way round. Pad Ø1.6 vs plunger Ø1.067: ±0.27 mm full-face margin.
- 0906-2 vs -4: -2 gives 0.60 mm (mid-ish) compression; -4 would bottom (C-L3). Dock 0906-4 sits at 0.70 by design.
- Clearances: screw boss pocket starts at x 133.65, countersink to x 134.4 (carrier ends x 132.6); magnets at
  x 112.5/120.5 and cell envelope x 107–124 are far away; carrier top (2.3) and flanges (to 2.71) are below the LRA
  (z ≥ 3.25); barrel tops (z 4.99) are 1.7 mm below B.Cu; only the Ø1.07 plungers reach the board, through the Ø2.3 ledge notches.
- Rev B case changes only the shell (antenna pocket, land start x 127.6); carrier, cover, pins unaffected.
