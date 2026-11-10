# Dock PCB rev B: layout, manufacturing and mechanical fit review (Advisor 2)

Scope: `hardware/dock/rev-b/pcb` (board, DRU, fab package, `gen_cpl.py`), `hardware/dock/rev-b/case/dock_rev_b.py`
(with `rev-a/case/dock_rev_a.py` and `band/rev-a/case/case_rev_a.py`, which it imports), and the band contact carrier
`band/rev-a/contact-carrier`. Review only; nothing in the repo was changed.

Method: I parsed the `.kicad_pcb` with sexpdata and built shapely geometry (roundrect radii, rotations, zone fills).
I checked connectivity (tracks, vias and pads, plus GND through the fills), copper clearances per layer, copper to
edge, vias in pads, routed lengths (Dijkstra over the track graph) and plane voids. I read the Gerber, Excellon and
job files directly, diffed the BOM and CPL against the board, and took the spring-pin dimensions from the Mill-Max
datasheet page. KiCad was not available, so no native DRC was run.
Scripts: `scratch/adv2/`.

Coordinates are KiCad board mm (y down). The case scripts use the same x/y, with z = 0 at the band's wrist face.

---

## Findings

### D-L1: Open vias in SMD pads, on 0402 passives and SOT-23 pins (Major)
- **What:** 17 vias (0.45 mm pad, 0.3 mm drill) sit fully inside SMD pads that have paste, and about 15 more overlap a
  pad edge. The mask opening equals the pad (`pad_to_mask_clearance 0`), so these vias are exposed even though vias
  are tented elsewhere. The stackup has `capping no` and `filling no`. Solder will wick down the barrels during reflow,
  which on 0402 pads (0.54 x 0.64 mm, barely larger than the 0.45 mm via land) risks opens and tombstones.
- **Evidence:** vias fully inside a pad: C12.1, C13.1, C4.1, R7.1 (+3V3); C15.1 (+1V1); R1.1 (XOUT); R10.2 (SWDIO_3V3);
  U8.1, U8.3, U8.5; R12.1; U3.5 (VBUS); U6.4, F1.2 (VBUS_F); SW1.1 (BOOT); D2.2 (LED_ACT, via at 117.1, 122.7).
  Partial overlaps include C8.1, C20.1, U5.3, D1.2, U3.2/U3.4, U6.2/U6.5, U7.2, C6.1, C11.2, C14.2, Y1.4, R9.2.
  The README's trace audit ("every track end on its pad or via centre") put these vias on pad centres on purpose.
- **Fix:** dog-bone the vias off the pads (0.15 to 0.2 mm neck, via at least 0.1 mm clear of the pad), or order
  JLCPCB's epoxy-filled and capped via-in-pad. As far as I know that is a paid option on 4-layer boards (pricing not
  verified). The RP2040 EP vias are a separate case (D-L8).
- **Confidence:** High for the geometry. Medium-high that it causes real defects at JLC.

### D-L2: Top plate sits exactly on the spring-pin barrels, with no clearance (Major)
- **What:** In the case model the barrel tops land exactly on the top plate's underside. The plunger bores are Ø1.50 mm,
  the same as the barrel (Ø1.499 mm), so the barrels can't enter them. Any upward tolerance (PCB 1.6 mm ±10%, solder
  under the flange, the Mill-Max ±0.15 mm length tolerance, print tolerance) makes the plate rest on the four barrels.
  The plate then won't seat flush (an open seam), or pressing it down preloads the PCB and the pin solder joints.
  The clash check passes only because the two solids touch with zero volume.
- **Evidence:** `dock_rev_a.py`: TAIL_TIP = 0.7 + 1.6 − 1.75 = 0.55 and PCB_TOP = 0.55 + 0.70 − 5.99 = −4.74.
  Barrel top = PCB_TOP + 2.69 = **−2.05**. `dock_rev_b.py` sets PLATE_Z0 = **−2.05**, and the bores are
  `cyl(SP_X, y, 0.75, …)` (Ø1.50). Datasheet for 0906-4-15-20-75-14-11-0: body length 0.090" + flange 0.016"
  = 2.69 mm (so the model's 2.69 is right), body Ø0.059" (1.499 mm), length tolerance ±0.006" (0.15 mm).
- **Fix:** add a Ø2.1 x 0.5 mm counterbore on the plate underside at each pin (simplest). Otherwise raise PLATE_Z0 by
  about 0.4 mm, which needs a magnet-pocket and USB-pocket recheck. The plate can still act as a hold-down if wanted.
- **Confidence:** High (computed from the scripts and the datasheet).

### D-L3: The PCB has no y stop at the back, so USB-C insertion force lands on the spring plungers (Major)
- **What:** The tray holds the PCB in x (side stops with 0.2 mm clearance) but not in y. The front edge (y 124.0) is
  line-to-line with the cavity wall (y 124.0, open at the USB notch), and behind the board (y 97.5) there is 1.4 mm of
  free space (cavity wall at 96.1). The "corner stops" lie entirely outside the board's x range, at x 98.6 to 99.8 and
  140.2 to 141.4, so they don't stop y travel. Pushing a plug in (−y, typically 5 to 20 N) slides the PCB back until
  something stops it. The plungers in their bores have 0.22 mm radial clearance, which is less than the 0.25 mm around
  the shell in its pocket. So the four Ø1.07 mm plungers take the side load first, then the 0.56 mm of shell that
  reaches into the plate pocket.
- **Evidence:** `dock_rev_b.py` `make_tray()`: cavity = `outline(WALL=1.6)`, which gives y 96.1 to 124.0. The corner-stop
  boxes use `PCB[0]-1.4..PCB[0]-0.2` and `PCB[1]+0.2..PCB[1]+1.4` in x. USB_BODY back y is 116.1 and the pocket
  is 0.25 larger. The shell top is at −1.49, against the plate underside at −2.05. The same layout is inherited from rev A.
- **Fix:** add rear stops (ribs or bosses on the tray floor behind the board edge at y about 97.3, 0.2 mm clearance),
  and 0.1 to 0.2 mm front clearance so the board drops in. Better still, give the USB shell a printed backstop or tie
  the PCB down (two M2 screws, or snap hooks).
- **Confidence:** Medium-high on the geometry. The plunger side-load risk depends on friction and is not measured.

### D-L4: SWDIO_DRV runs through the crystal footprint, and XOUT runs on In2 through two vias (Major)
- **What:** The SWDIO drive trace runs on F.Cu between Y1's XIN pad and its GND pad, then drops through a via under
  the crystal body (119.4, 100.1) and continues on B.Cu under the crystal. XOUT leaves RP2040 pin 21 through a via,
  runs 6.8 mm on In2 under Y1, and comes up through a second via into R1. Raspberry Pi's RP2040 hardware design guide
  asks for short XIN/XOUT on one layer, with no other signals near or under the crystal. An SWD edge next to XIN can
  couple into the oscillator (jitter or start-up margin).
- **Evidence:** F.Cu segment (119.4, 100.1)–(119.4, 101.1) on net SWDIO_DRV, with Y1 pads at x 117.6–119.0 (XIN) and
  119.8–121.2 (GND). B.Cu segment (119.4, 101.6)–(119.4, 100.1), also SWDIO_DRV. In2.Cu XOUT segment
  (121.95, 99.55)–(119.4, 102.1). XOUT is 8.23 mm routed with 2 vias; XIN is 3.12 mm to Y1.
- **Fix:** reroute SWDIO_DRV (GPIO17 to R10) around the crystal. Put R1 and XOUT on F.Cu next to the XOUT pad, and
  keep a GND keep-out (In1 is already solid) under Y1, C1 and C2.
- **Confidence:** High on the geometry. The electrical impact is likely small, but this goes against vendor guidance.

### D-L5: RP2040 core-regulator output cap is about 10 mm from VREG_VOUT, through two vias (Minor)
- **What:** The +1V1 path from VREG_VOUT (pin 45) to its 1 µF (C15) is 9.75 mm routed, running pin 45 → pin 50 →
  via → B.Cu → via → C15. The datasheet asks for that cap close to the pin. DVDD pin 23 has C16 at 2.1 mm (good).
  DVDD pin 50's nearest cap is C15 at 6.95 mm.
- **Evidence:** `+1V1` segments: (116, 110.85)→B.Cu→(110.3, 111.7), vias at (116, 110.85) and (110.3, 111.7). C15 pads
  are at (110.12 / 111.08, 111.7).
- **Fix:** move C15 to the bottom-edge pins 45 to 50 (about 114.5, 111.0) and route on F.Cu.
- **Confidence:** High on the numbers. The regulator usually still works, so this is Minor.

### D-L6: Some 3.3 V supply pins are more than 6 mm from their decoupling (Minor)
- **What:** Routed distance to the nearest cap is 6.85 mm for IOVDD pin 22, 6.56 mm for IOVDD pin 49 and 6.16 mm for
  USB_VDD pin 48. The other pins are 1.3 to 4 mm (pins 1, 10, 33, 42, 43 and 44 are fine).
- **Evidence:** Dijkstra over the +3V3 track graph. Pin 22 (115.8, 103.16) reaches C9 at 6.85 mm; pins 48 and 49 reach
  C17 at 6.2 to 6.6 mm.
- **Fix:** add or move a 100 nF cap next to pins 48/49 and pin 22, or shorten the routes.
- **Confidence:** High.

### D-L7: Band power runs 21 mm on a 0.3 mm inner-layer trace (Minor)
- **What:** VBUS_F (PTC to SY6280 and the LDOs) is 0.3 mm wide throughout, with 21.3 mm on In2.Cu. JLCPCB's
  standard 4-layer inner copper is 0.5 oz. By IPC-2221 internal, 0.3 mm of 0.5 oz carries about 0.30 A for a 10 °C
  rise. At the switch's 0.45 A limit plus 40 mA for the probe, that gives about 25 °C. IPC-2152 is less pessimistic.
  The drop is about 30 mV. VBUS (8.8 mm on F.Cu, 4.5 mm on In2) and VIN_BAND (F.Cu, 1 oz) are fine.
- **Fix:** widen VBUS_F to 0.5 to 0.6 mm, or keep it on F.Cu. There is space along the y 120.9 run.
- **Confidence:** Medium (the inner copper weight is JLC's default; the job file doesn't specify it).

### D-L8: RP2040 EP: all 9 thermal vias sit under paste windows (Minor)
- **What:** The EP (3.2 mm square) has a 3x3 grid of open 0.3 mm vias at pitch 1.0 (115 to 117, 105.6 to 107.6).
  The four 1.29 mm paste squares (about 65% coverage, which is fine) cover or touch every via, so paste will wick away.
- **Fix:** tent or plug the EP vias from the bottom (they are tented on B.Mask already; the In1 side is fine), or move
  the paste windows off the vias. Low risk on its own.
- **Confidence:** High on the geometry.

### D-L9: The board has no silkscreen at all (Minor)
- **What:** `gen_pcb.py` `strip_silk()` removes every footprint silk graphic and moves references to F.Fab. Both
  legend Gerbers contain only clear-polarity (LPC) flashes of the mask openings and no dark features. So the board
  has no pin-1 or polarity marks (U1, U2, D1, D2, J1), no references, no P1 to P4 labels for the hand-soldered pins,
  no revision mark and no project name. The rev A and rev B fab copper and mask are byte-identical, so the two boards
  can't be told apart.
- **Fix:** restore the library silk (or at least pin-1 dots, LED cathode bars, and P1 SWCLK, P2 SWDIO, P3 GND, P4 VIN
  labels) and add "WakeBand dock rev B" plus the date in silk or copper.
- **Confidence:** High.

### D-L10: CPL rotations and the J1 offset can't be confirmed offline (Note)
- `gen_cpl.py` applies SOT-23 +180 (U3 to U8), SOIC +270 (U2 90 → 0) and QFN +270 (U1 180 → 90). These match
  common kicad-jlcpcb-tools defaults, but the RP2040's (C2040) EasyEDA footprint orientation is not confirmed.
- J1 offset (0, −1.42) → CPL y 118.88: the code applies the frame transform correctly and the CPL row matches.
  The 1.42 mm equals the centre of J1's pad-and-hole bounding box in KiCad's frame (pads y −4.77 to legs +1.85,
  centre −1.46), which fits a bbox-centred EasyEDA origin. I couldn't fetch the EasyEDA data (easyeda.com is blocked
  by the proxy).
- D1/D2 (C2286): KiCad pad 1 (−x) is the cathode and the nets are right (pad 1 = LED_*_K to R13/R14 to GND).
  JLC's footprint polarity is unverified.
- **Action:** in JLC's DFM preview, check pin 1 of U1 and U2, pin 1 of the six SOT-23s, the J1 legs in their holes,
  and the D1/D2 cathode marks. With no silkscreen (D-L9) the preview is the only check.
- **Confidence:** Medium.

### D-L11: J1 shell legs get no paste; confirm JLCPCB solders them (Note)
- The four shell slots are plated through-holes with no paste in the footprint. If JLC treats C165948 as SMT only, the
  shell is held by the 0.3 mm signal pads alone and the plug force goes into them. Ask for, or check, THT soldering of
  the legs (or hand-solder them). The STEP suggests the legs (about 0.9 mm below the body) don't come through a
  1.6 mm board. Not verified.

### D-L12: Spring-pin hole is 0.6 mm, larger than Mill-Max's recommended 0.508 mm minimum (Note)
- The tail (Ø0.432) has 0.084 mm radial play, so alignment depends on the flange sitting flat on its pad.
  Plunger tip error is bounded by the Ø1.5 guide bores. This works, and it matches the carrier. Keep it, but solder
  each pin with the plate fitted or a jig so the pins stay square.

### D-L13: Tray support pads sit on TP1 and touch J1's rear shell pad (Minor)
- The Ø2.4 mm support pad at (102, 99.5) sits on TP1 (102, 99.6, RP_SWCLK, with an open via in the pad). The pad at
  (102, 122) comes within 0.016 mm of J1's rear-left shell annular ring (103.68, 121.35), where a bottom-side solder
  fillet would tilt the board. Spring-pin tails (0.15 mm below the board, plus a solder dome) have only the 0.3 mm
  under-board gap (GAP_UNDER) over the tray floor.
- **Fix:** move the support pads about 1 mm inboard (for example to (103, 101) and (101.5, 120)), and add Ø3 mm
  reliefs in the tray floor under P1 to P4 and the J1 legs.
- **Confidence:** High on the geometry, Low on the consequence.

### D-L14: Stale README text for rev B (Minor)
- `dock/rev-b/pcb/README.md:94` says "Hold BOOTSEL (a pin through the poke hole)", but the rev B housing has no hole.
  A blank RP2040 with empty flash boots straight into the USB bootloader, so the first flash needs no BOOTSEL; say so.
- `dock/rev-b/case/README.md:42` says "it is held by the lip", but rev B has no lip. It is held only by two Ø2.0 pins
  in Ø2.05 holes (0.05 mm clearance, no interference fit).
- **Related, unverified:** the Ø4 x 1.5 mm plate magnets are sized to pull the band down harder than 240 g of spring
  force. With the plate retained only by friction on those pins, lifting the band may lift the top plate off the tray
  with it. Check at bring-up. If it happens, add a snap or interference fit, or a screw.

### D-L15: Smaller layout notes (Note)
- **USB:** RP2040 is full-speed (12 Mb/s), so impedance and length matching don't matter. D+ is 14.7 mm on F.Cu;
  D− is 13.8 mm with 3 vias and 6.6 mm on In2. Both are 0.2 mm wide at 0.5 mm pitch. The In1 GND plane has a
  1.15 mm² void at (107.9, 114.8), where the merged antipads of the D− vias sit under the D+ trace. Harmless at FS;
  keep D+ and D− on the same layer if it is reworked.
- **QSPI:** U2 is turned so its pins 1 to 3 face away from the RP2040. SD1, SD2 and SS run 18.5, 16.7 and 26.8 mm
  against 3.6 to 4.3 mm for the others, mostly at 0.10 mm spacing to each other. At the default boot2 clock this is
  fine. Turning U2 by 180° would shorten the routes.
- **+1V1 under the QFN:** the trace runs inside U1's pad ring, 0.15 mm from the EP edge (EP copper x 114.4, trace edge
  114.25). It passes the rules and follows Pi's reference practice. The hidden short risk is low, but a 0.2 mm gap
  would be better.
- **Board finish:** the job file says "Finish: None". Choose ENIG over HASL for the 0.4 mm-pitch QFN.

---

## Checked and found OK

- **Rev A and rev B:** the `.kicad_pcb` files differ only in the title block. Copper, mask, paste, edge and both drill
  files are identical, and so are the BOM and CPL.
- **Fab zip vs loose files:** identical. The zip has every expected layer: 4 copper layers, F/B mask, F/B paste,
  F/B silk, Edge.Cuts, PTH and NPTH drill plus maps, and the job file.
- **Gerbers vs board:** F.Cu has 288 flashes, which equals 200 F-side pads plus 88 vias. Nudged parts (C3, C19, R4,
  R13) sit at their current positions. Zone fills keep exactly 0.2 mm clearance to every other-net item, so the
  fills are current.
- **Connectivity (own check):** no dangling track ends, no net mismatches, every non-GND net is one connected group,
  and GND (88 items across 4 layers and the fills) is one group. All F.Cu GND islands are stitched except one 1 mm²
  sliver at R14.2, and R14.2 is connected by track anyway.
- **JLCPCB 4-layer capability:**
  - Tracks: minimum width 0.15 mm, minimum copper spacing 0.10 mm (QSPI on F.Cu); JLC's limit is 0.09/0.09 mm.
  - Inner layers: no spacing below 0.127 mm.
  - Vias: 0.3 mm drill on 0.45 mm (0.075 mm ring, which meets the 0.15 mm pad-over-drill rule).
  - Copper to edge: at least 0.30 mm (the fill) and 0.325 mm (via 73, +1V8, at 126.74, 98.05).
  - Board size: 40 x 26.5 mm.
- **USB-C drill:**
  - Shell legs come out as plated G85 slots: 0.6 x 1.7 mm and 0.6 x 1.2 mm, a 2:1 length-to-width ratio, at
    103.68 / 112.32 and y 116.62–117.72 / 121.05–121.65.
  - The Ø0.65 mm pegs are in the NPTH file at (105.11, 117.7) and (110.89, 117.7).
  - The shell's front face sits on the board edge (KiCad fab body front at y 123.95).
- **Mask and paste:** 0.4 mm-pitch QFN pads leave 0.2 mm mask webs, and EP paste covers about 65%. The bottom side
  has no paste and no parts (test pads only), so assembly is top side only.
- **BOM and CPL:** 49 designators in each, the same set, and footprints and LCSC numbers agree with the board.
  P1 to P4 and TP1 to TP4 are correctly left out. CPL positions equal the footprint origins, except J1's intended
  −1.42 mm.
- **Spring pins vs band:**
  - Dock P1 to P4 are at (131.5; 101.1 / 103.3 / 111.7 / 113.9) as SWCLK / SWDIO / GND / VIN.
  - These match the carrier pins (SWDCLK / SWDIO / GND / VIN at the same coordinates) and `case_rev_a.SP_X/SP_Y`.
    Both boards are seen from the same side (both F sides face +z), so no mirroring applies.
  - The magnets at (112.5, 107.5) and (120.5, 107.5) match the band's MAG_XY.
- **Pin height and travel:** the free tip is 1.25 mm above the recess floor. Seated on the band tails (z 0.55),
  compression is 0.70 of 1.40 mm, mid-stroke as intended. The plunger has 0.22 mm radial clearance in its Ø1.5 bore.
- **Board in the housing:** the 40 x 26.5 board fits the tray cavity (x 98.4 to 141.6 between the end blocks, y 96.1
  to 124.0). For the y location, see D-L3.
- **USB-C opening:**
  - The notch is 13.0 mm wide, open to the full height (z −6.64 to 1.2). A ≤12.35 x 6.5 mm plug overmold centred
    on the receptacle (z −3.11) fits, with 0.28 mm above the tray floor.
  - The shell pocket has 0.25 mm clearance and a 0.25 mm gap over the shell top (z −1.49).
- **LED skins:** the LED windows sit at D1 (133.0, 122.6) and D2 (116.4, 122.8), exactly over the parts. Both are
  outside the band recess (band body y ≤ about 117.5), so they stay visible while docked, and clear of the USB notch
  and pocket.
- **Component heights:** there is 2.69 mm between the PCB top (−4.74) and the plate underside (−2.05). The SOIC-8
  (1.75 mm max) and the other parts fit. Only J1 needs a pocket, and it has one. The magnet pockets clear the
  components below them.
- **Power-path widths:** VIN_BAND and VBUS are 0.3 mm on 1 oz outer copper (fine for 0.45 A). The PTC, the SY6280
  and C7 are close together (VIN_BAND path C7 to P4 is 6.3 mm).

## Not verified
- JLC's EasyEDA footprint origins and rotations for C2040, C165948 and C2286 (EasyEDA blocked). See D-L10.
- Whether JLC solders J1's shell legs (D-L11).
- Magnet hold vs plate retention, measured forces (D-L14).
- The STEP-based z extent of the USB-C legs: I scanned raw points without placement transforms, so it is approximate.
- Native KiCad DRC and ERC (KiCad not installed).
