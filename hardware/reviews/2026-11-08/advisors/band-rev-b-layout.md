# WakeBand band rigid rev B: layout, manufacturing and fit review (Advisor 2)

Scope: `hardware/band/rev-b/pcb/` (board, DRU, fab package, panel, Nordic reference), `case/`, `contact-carrier/`.
Method: KiCad is not installed, so I parsed the `.kicad_pcb` files with a small s-expression parser and shapely.
I rebuilt copper per layer (pads, tracks, vias, stored zone fills) and ran my own clearance, connectivity,
hole-to-copper, mask-dam, paste and edge checks. I mapped Nordic's QFAA v0.8 reference into the rev B frame
(rotated 180 degrees about U1: x' = 258.5011 - x, y' = 210.9876 - y) and checked JLC limits against
jlcpcb.com/capabilities/pcb-capabilities. I did not modify the repo.

Severity counts: **0 Blocker, 3 Major, 5 Minor, 5 Note.**

---

## Findings

### B-L1 · Major · Nordic's In1/In2 void under the RF ladder and RF output was not copied
- **What:** In Nordic's reference, In1 **and** In2 are cut out under the whole ANT → L2 → L3 → L4 → C11 → RF-out run. Rev B only copied the small void under the C9 island. In1 is a solid GND plane 0.21 mm under every 0201 pad and trace of the ladder.
  - This adds shunt capacitance to the filter/match. Nordic's values (2.7 nH, 1.5 pF, 3.5 nH, 2.0 pF, 3.5 nH, 0.3 pF) were tuned without it.
  - C11 is only 0.3 pF, so tens of fF per node is not negligible.
  - The ladder can't be re-tuned with the C14/R2/C15 antenna network.
- **Evidence:**
  - `scripts/nordic_ref_qfaa_0_8.kicad_pcb` has keep-out (no-pour) zones on In1.Cu and on In2.Cu. Their outline in rev B coordinates is (106.832,105.961) (106.832,104.793) (104.495,104.793) (104.114,104.412) (102.5,104.412) (102.5,105.986) (103.809,105.986) (104.19,105.605) (106.197,105.605) (106.197,105.961), i.e. x 102.5–106.83, y 104.41–105.99.
  - In rev B, the In1 GND fill is one polygon of 402 mm² and covers all ANT/RF1/RF2/RF_50 copper: I measured 0 % of those tracks off In1.
  - Cause: `scripts/transplant.py` copies only zones whose points all lie inside `BOX = (-7.9, -6.6, 8.0, 5.0)`. Nordic's void reaches x = +8.5 mm from U1, out to their board edge, so it was skipped silently. The README line "In1 is unbroken under the radio and the RF line" describes this departure as if it were a feature.
- **Fix:** Add rule areas (no pour) on In1 and In2 matching Nordic's polygon, ending at the L4/C11 node (x ≈ 102.9–103.5). Leave In1 solid under the 50 Ω CPWG that follows. Alternatively, ask Nordic (DevZone) whether the ladder values hold over a 0.21 mm reference plane. Also stack In2 GND under the void so B.Cu becomes the reference, as in Nordic's design.
- **Confidence:** High that the geometry differs from Nordic. Medium on the size of the RF effect (no simulation).

### B-L2 · Major · CPL rotations have no JLC corrections, unlike the dock PCB fixed the same day
- **What:** `fab/jlcpcb/pos.csv` is KiCad rotation as-is (`panelfab.py`, `rot % 360`). Commit a5e8671 ("Dock PCB CPL: JLCPCB rotation fixes for SOT-23, SOIC and QFN parts") found that QFN needed +270 on the dock board. Rev B applies the equivalent of none of these.
  - **Usual KiCad→JLC offsets for these packages:**
    - U1: Nordic QFN48, CPL 180. Pin 1 is top-left, as in KiCad's QFN.
    - U202: KiCad `DFN-10-1EP_3x3mm`, CPL 180.
    - U501: KiCad `TSSOP-10_3x3mm`, CPL 270.
  - **Orientation-critical parts where a wrong turn breaks the board:**
    - X2 (`Nordic_BT-XTAL_2016`): pin 1 is **bottom-left** in the local frame (−0.725, +0.575), and pins 1/3 are the crystal. A 90° error puts XC1/XC2 on the GND pads and the HFXO is dead.
    - AE1: the feed must land on pad 1 at y 111.1, the ground side. The body is nearly symmetric, so a 180° error swaps feed and NC.
    - D702 (RGB, common anode).
    - U201 (DSBGA, A1).
    - U203 (X2SON).
    - U401 (LGA-12).
- **Evidence:** pos.csv rows U1_* 180.0, U202_* 180.0, U501_* 270.0, X2_* 270.0, AE1_* 270.0. The dock fix is in `hardware/dock-pcb-rev-a/scripts/gen_cpl.py` (ROT_FIX).
- **Fix:** Generate the CPL with the same ROT_FIX table (add `^DFN-`, `^TSSOP-` and the Nordic QFN name), or confirm each part in JLC's placement preview before paying. The README already asks for that check; making it a gating step would close this. Pay special attention to X2 and AE1.
- **Confidence:** Medium. JLC's per-part library orientation varies, and only the preview is authoritative.

### B-L3 · Major · ESD/TVS parts sit 12–15 mm from the exposed dock contacts
- **What:** The spring-pin tails are bare contacts on the wrist face, in contact with skin all night. The dock nets are routed across most of the board before they reach any protection:
  - PAD_SWDCLK: 22.1 mm (F 4.4 / In2 3.6 / B 14.1).
  - PAD_SWDIO: 23.3 mm (F 5.5 / In2 4.7 / B 13.1).
  - VIN: 42 mm in total, of which 30.3 mm is on In2.
  
  An ESD current therefore flows through a long trace next to other signals (under U1 and the cell) before it is clamped. That defeats much of the purpose of D602/D603/D601.
- **Evidence:** J601.3/4/1 are at (131.5, 101.1/103.3/113.9). D602.1 is at (118.4, 111.0), D603.1 at (115.9, 111.0), R601/R602 at (117.3/115.3, 112.5), and D601.1 at (119.6, 113.8). The README notes "No routing room at the dock end".
- **Fix:** Move D602/D603 (0.6 × 1.0 mm) and D601 next to J601, on F.Cu over the pads with short GND vias. The case land at x ≥ 127.6 only bears on y < 103.2, and the area beside it is free. If room is truly gone, at least put the series resistors R601/R602 at the dock end so the long run is behind 100 Ω.
- **Confidence:** Medium-high on the geometry. ESD severity is engineering judgement.

### B-L4 · Minor · Courtyard-scoped POFV rules relax every via in U201/U202 courtyards, and hole-to-copper is below JLC's 0.2 mm
- **What:** The `.kicad_dru` rules `bga_hole_clearance` and `dfn_via_in_pad` (hole_clearance 0.15, clearance 0.1) apply to any via inside the courtyard, not only the via-in-pad ones. As a result, two ordinary 0.45/0.3 vias have 0.175 mm hole-to-GND-pour on **all four layers**:
  - VLED at (122.7, 106.2), inside U201's courtyard edge (119.65–122.75).
  - VBAT at (123.95, 111.35), inside U202's courtyard.
  
  The eight 0.25/0.15 via-in-pad vias (VIN 120.8,104.6; TS 121.2,105.4; PMIC_INT 120.8,105.8; DOCK_PG 121.6,105.8; PMID 127.15,113.5; …) have 0.15 mm hole-to-copper to the In1/In2/B.Cu GND pour.
  
  JLC lists inner via-hole-to-copper as 0.2 mm and outer via-hole-to-track as 0.2 mm. Filling and capping doesn't change drill registration on inner layers.
- **Evidence:** My hole-to-copper check (the stored fill polygons sit 0.325 mm from the via centres). The courtyard extents come from the board file.
- **Fix:** Restrict the rules to via size, e.g. `A.Type == 'Via' && A.Drill < 0.16mm && A.insideCourtyard(...)`. Then refill, which pushes the pour back to ≥ 0.2 mm from the holes, and move the two 0.45 mm vias out of the courtyards or shrink them. All the offending copper is GND pour, so JLC CAM would probably just pull it back (low electrical risk), but expect a DFM query.
- **Confidence:** High on the geometry.

### B-L5 · Minor · C6 moved 0.107 mm toward L2: 0.1 mm ANT-to-GND pad gap and a 0.05 mm mask dam
- **What:** Nordic's C6 is at (106.832, 105.707) in the rev B frame. Rev B has it at (106.83, 105.6).
  - **Result:** the pad gap between L2.1 (/ANT) and C6.1 (/GND) is 0.10 mm, and the mask web between their openings is 0.05 mm. JLC can't make that web (minimum 0.10 mm on green), so it will be removed.
  - **Risk:** a solder bridge on 0201s here shorts the radio output to ground. It is the only pair of placed parts on the board closer than 0.2 mm.
- **Evidence:** My pad-to-pad and mask-dam checks. This is the only C6/L2 deviation from Nordic placement besides C11 (see B-L10).
- **Fix:** Put C6 back at Nordic's y (gap 0.2 mm). If a track forced the move, re-route the track.
- **Confidence:** High.

### B-L6 · Minor · BQ25125 DSBGA mask dams are 0.09 mm (JLC minimum 0.10 mm)
- **What:** All 40 neighbouring U201 ball openings are 0.09 mm apart (pads 0.25 mm + 0.04 mm margin). JLC will gang-relieve the BGA. The balls carry filled-and-capped vias, so the risk is low, but solder can flow along exposed fan-out tracks.
- **Fix:** Use a mask margin of 0.035 mm or less on that footprint, or accept the gang opening knowingly.
- **Confidence:** High on the geometry.

### B-L7 · Minor · Sparse via fence on the 50 Ω CPWG feed; README's "12 GND vias within 1 mm" not reproduced
- **What:** The 0.36/0.16 mm CPWG (RF_50 → R2 → ANT_FEED, x = 102.75, y 105.7–109.1, ≈ 3.4 mm long) has **no** GND via within 1.0 mm. The nearest are (103.76,106.24) at 1.01 mm, (100.77,107.44) at 1.07, (100.77,108.46) at 1.11 and (104.015,108.12) at 1.27.
  - Across the whole RF chain (ladder included) I count 8 GND vias within 1.0 mm.
  - Johanson's datasheet says ground vias are "highly recommended".
- **Evidence:** My distance check over all /GND vias.
- **Fix:** Add 0.4/0.2 GND vias at about 0.45 mm from the trace edge, about 1 mm pitch, on both sides of the CPWG. There is F.Cu ground on both sides. Correct the README count.
- **Confidence:** High on the counts.

### B-L8 · Minor · Panel tabs: mouse-bite holes 0.05 mm from GND pour, and a 10 µF MLCC 1 mm from a break line
- **What:**
  - **Hole-to-copper:** the mouse-bite holes (0.5 mm NPTH, centred on the board edge) come within 0.05 mm of the GND pour on F/In1/In2/B. The pour stops 0.3 mm in, and the holes reach 0.25 mm in. JLC lists NPTH-to-copper as 0.2 mm, so expect exposed or burred copper at the tab nubs that you then sand.
  - **Crack risk:** C206 (10 µF 0603 on PMID, rot 90, so its terminals are perpendicular to the edge, the worst orientation for bend strain) is 1.03 mm from the top tab line (board x 120.6–124.6, y 100). C205 is at 1.67 mm and L201 at 1.8 mm. Snapping the tab can crack C206, and a crack shorts PMID to GND.
- **Evidence:** `fab/jlcpcb/gerbers.zip` NPTH.drl (T1 C0.500, 76 holes). Panel offsets (13.5, −63), (50.5, −63), (13.5, −41), (50.5, −41).
- **Fix:**
  - Add copper keep-outs of ≥ 0.5 mm at the tab spans, or use KiKit's mousebite offset (−0.25 mm) so the holes sit outside the board.
  - Move the top tab away from C206/C205, e.g. to x ≈ 112–116 on the top edge, if the case allows.
  - Tell the assembler to cut the tabs (nibbler or saw) rather than snap them.
- **Confidence:** High on the geometry. Medium on the crack risk.

### B-L9 · Note · Antenna clearance and surroundings are tighter than Johanson's evaluation board (in-case tuning is essential)
- **What:**
  - **Clearance:** 4.2 × 5.9 mm, against 6.5 × 6.5 mm on Johanson's evaluation board. The antenna body is 1.25 mm from the ground edge at x 104.2, and the feed pad is 1.4 mm from the ground edge at y 109.1.
  - **Nearby material:**
    - PETG post at x 100.15–100.95, 0.3 mm from the AE1 pads.
    - The antenna pocket.
    - A 3.6 mm end wall with press-fit pins.
    - The cell envelope from x 107 (2.8 mm from the keep-out, 4.05 mm from the antenna body; the README says ~2 mm).
  - **What checks out:** the keep-out holds on all 4 layers (only AE1's pads and the feed in it), and the feed end of AE1 faces the ground.
- **Fix:** None needed beyond the README's tuning procedure. Keep the C14/R2/C15 pi network.

### B-L10 · Note · Documentation and labelling drift
- **Board metadata still says rev A:** the title block reads "WakeBand rigid rev A", rev "A", date 2026-11-03, with the comment "mounts parts-side down" (the case has parts side out). The gerber job file says `Revision: "A"`. The board has no rev B silkscreen mark.
- **README overstatements:**
  - "In1 is unbroken under the radio": there is a C9-island void on In1 and In2 (correct per Nordic, but the claim is wrong).
  - "12 GND vias within 1 mm": see B-L7.
- **Case docstring is stale:** `case_rev_b.py` says the antenna pocket is "0.35 mm deep (0.85 mm of roof left)". The code gives POCKET_TOP = 9.05, a depth of 0.25 below ROOF_IN 8.8, leaving 0.95 mm of roof. The case README's 0.95 is right.
- **C11 position:** C11 sits on the opposite side of the RF line from Nordic's (GND pad at y 104.63, not 105.89). This is electrically equivalent if its GND via is short (vias at 0.55 and 0.79 mm).

### B-L11 · Note · Silkscreen below JLC minimums
- **What:**
  - Footprint silk lines are 0.12 mm wide (JLC minimum 0.15). 0402/LGA silk is 0.09–0.10 mm from the pads (JLC wants 0.15). JLC will clip or thin it.
  - The board has no silk text. The panel has one text with "JLCJLCJLCJLC" ✓.
- **Fix:** Optional: widen to 0.15 mm, or ignore.

### B-L12 · Note · Case post over the TP705 edge
- **What:** The shell post `box(131.75, CAV[1], 110.8, 114.6)` overlaps the TP705 (PMID test pad, Ø0.8 at 131.6, 110.5) by 0.005 mm². That is a pad edge pressed by plastic. It is harmless, but the pad can't be probed with the board in the case.

### B-L13 · Note · Spring-pin body to LRA envelope is 0.02 mm (carried over from rev A)
- **What:** The pin bodies (Ø1.5) at (131.5, 103.3/111.7) are 5.02 mm from the LRA centre (128.75, 107.5), against an LRA envelope radius of 4.25 + 0.75. The can itself (r 4.0) has about 0.27 mm. The case README's clash check reports 0 overlaps.
- **Fix:** Nothing for rev B. Keep it in mind if the LRA lead dress changes.

---

## Checked and found OK

**Board outline and stackup**
- 33 × 15 mm, R1 corners. It matches `case_rev_a.py` BOARD (100–133, 100–115), BOARD_R 1.0 and BOARD_T 0.8.
- Stackup: 0.035 / 0.2104 (7628, εr 4.4) / 0.0152 / 0.26 / 0.0152 / 0.2104 / 0.035, ENIG. Filling and capping are set in the board file.

**Copper, vias and connectivity**
- **Clearances:** my copper clearance is ≥ 0.10 mm everywhere on all layers (JLC 0.09). Tracks are ≥ 0.10 mm wide.
- **Vias:** 0.25/0.15, 0.4/0.2, 0.45/0.3, 0.5/0.25 and 0.66/0.33, all through-vias and all within JLC's 0.15–0.55 mm POFV range. Every via is ≥ 0.1 mm larger than its drill. Hole-to-hole is ≥ 0.25 mm.
- **Copper to edge:** ≥ 0.30 mm (J601.3 is at exactly 0.30). JLC requires ≥ 0.2 mm on routed edges.
- **Connectivity:** every net is one connected component, counting tracks, vias, pads and stored zone fills. No unconnected items, no isolated fill islands, 0 dangling track ends, and no via left touching fewer than 2 layers. The panel has 4× the board's fills (172 = 4 × 43), so the fills are present in the fab data.
- **Pour fragments:** a few 0.02–0.05 mm GND-pour slivers touch the C9 island zone and merge with it. The C9 island stays separate from the main F.Cu pour (0.16 mm gap), as in Nordic's design.

**RF section**
- **50 Ω feed:** the 0.36 mm trace with 0.16 mm gaps over In1 at 0.2104 mm computes to **50.0 Ω** CPWG (conformal mapping, εr 4.4; about 48 Ω with mask). In1 is solid under the whole feed up to the keep-out edge.
- **Keep-out:** the antenna keep-out holds on F/In1/In2/B, with no pour and no vias.
- **Placement vs Nordic:** U1 support parts are within 0.03 mm of Nordic's placement, except C6 (B-L5) and C11 (B-L10).
- **Lengths vs Nordic:**

  | Net | Nordic (mm) | Rev B (mm) |
  | --- | --- | --- |
  | ANT | 0.86 | 0.86 |
  | RF1 | 0.94 | 0.93 |
  | RF2 | 1.02 | 1.08 |
  | XC1 / XC2 | 3.61 / 3.58 | 3.59 / 3.59 |
  | XL1 / XL2 | 2.10 / 1.93 | 2.09 / 1.94 |
  | DCC | 2.82 | 2.67 |

  The X2 no-pour area was copied.
- **Under the crystals:** only In1 GND lies directly beneath X1, X2 and L1; signals on In2/B.Cu are shielded by In1.
- **Paste:** U1 EP paste is 59 % with 16 filled 0.66/0.33 vias; U202 EP 63 %; U203 EP 62 %; DSBGA paste 0.06 mm² per ball. Test pads and dock pads have no paste.

**Power tracks**
- VBAT is mostly 0.4 mm, LRA ± 0.3 mm, VLED 0.2–0.25 mm. VIN and PMID include 0.15 mm runs, VIN partly on In2 at 0.5 oz (about 7.5 mΩ/mm).
- Fine for 30 mA charge, a 100 mA input limit and about 60 mA of LRA drive.

**Fab package**
- **Gerbers vs board:** `gerbers.zip` holds 4 copper layers, mask, paste, silk, Edge_Cuts, PTH/NPTH drill and the job file, all from commit cafbbe5 together with the board. PTH via count 640 = 4 × 160. The panel's sub-boards match the board exactly (69 footprints, 510 segments, 160 vias each, same rotations).
- **Panel:**
  - 70.1 × 71.1 mm, with two 15 mm rails.
  - 3 top fiducials (1 mm copper, 2 mm mask opening), placed asymmetrically.
  - 3 tooling holes of 1.152 mm.
  - Mouse bites of 0.5 mm holes at 0.8 mm pitch.
  - All boards at rotation 0.
  - Tab positions match the README.
- **pos.csv:** coordinates equal the panel footprint positions with y negated. Every placed footprint's origin is its pad-centroid (within 0.02 mm).
- **BOM vs CPL vs board:** 40 lines and 220 designators. BOM = CPL designator set. Value, footprint and LCSC number match the board fields for every part. The DNP C14/C15 and the test, dock and jumper pads are excluded.

**Mechanical**
- **Dock pads:** J601 at x 131.5, y 101.1 (SWDCLK) / 103.3 (SWDIO) / 111.7 (GND) / 113.9 (VIN). This matches the case `SP_X`/`SP_Y`, the order in its comment, and the contact carrier's P1–P4 holes and nets exactly. Pads are Ø1.6 against a Ø1.07 plunger.
- **Case land and posts:** the land (x ≥ 127.6, y ≤ 103.2) and the antenna-end posts touch no pads or courtyards (only traces and tented vias under mask).
- **LED:** D702 (130.225, 113.2) sits centred under the 2.4 × 2.3 mm LED pocket.
- **Antenna pocket:** it fully clears the AE1 body (pocket 2.2 × 3.8 mm, 1.55 mm above F.Cu, against a 1.3 mm part).
- **Hand-solder pads:** the B-side pads TP201/TP202/TP501/TP502 keep ≥ 0.5 mm to other nets. They lie outside the cell envelope (x ≤ 124) and the LRA envelope. JP201 is outside both.

## Not verified
- LCSC part numbers, stock, and basic vs extended status (the LCSC API was blocked by the proxy; only C2965582 was confirmed as a YXC 32 MHz part).
- JLC's per-part library orientations (see B-L2).
- Johanson's exact recommended land and clearance dimensions: the datasheet's drawing values (2.6, 4.2, 1.6, 1.9, 0.4, 13.5, 6.5, 39.5, 6.5, 4) could not be tied to features from the text.
- Nordic's reference stackup: the imported file has no stackup, so the reference's L1–L2 spacing is unknown.
- I did not render the Gerbers; I checked consistency through the panel `.kicad_pcb`, the drill files and the job file.
- 3D clash: I relied on the case README's clash check and only cross-checked coordinates.

Sources: [Johanson 2450AT18A0100001E datasheet](https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf), [JLCPCB PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [LCSC C2965582](https://www.lcsc.com/product-detail/C2965582.html?s_z=t_HRS).
