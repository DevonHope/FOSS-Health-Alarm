# Fix advisor: verdicts on the 2026-11-08 "Fix before ordering" list

I checked every claim against the design files in the repo, read-only. I parsed the files with Python and sexpdata. Coordinates are KiCad board mm, with y pointing down.

## Verdict table

| # | Item | Verdict | One-line reason |
|---|------|---------|-----------------|
| 1 | Dock PCB: vias in pads (D-L1) | **APPLY-MODIFIED**: dog-bone in the `.kicad_pcb`, not in `gen_pcb.py`. Paid POFV is an acceptable alternative. | The claim holds: 16 vias have their centre in a pad, and 12 more leave their drill partly inside the pad's mask opening. Each 0.3 mm barrel holds about 3x the paste on an 0402 pad. 26 of the 28 vias can move by 0.3-1.55 mm along 0/45/90 degrees with no new clearance problems found. |
| 2 | Band rev B: Nordic In1/In2 void (B-L1) | **SKIP for this order, DOCUMENT**. Do not copy the void as it is. | The claim about the void is correct. But copying it onto In1+In2 would leave the RF ladder sitting right over B.Cu **I2C_SDA**, which runs under L3/C9/L4 at y 105.2. Nordic's void belongs to their own CPWG, which uses the bottom layer as its reference. On rev B the added capacitance is about 0.04-0.08 pF per node (4-13 %), a small detune. |
| 3 | Band rev B: CPL rotations (B-L2) | **APPLY-MODIFIED**: no blanket regex corrections. Check in JLC's preview, then pin each confirmed value per designator. | No rev B part is a SOT-23. The Nordic QFN name doesn't match `^QFN-`. Only U501 (TSSOP) and U202 (DFN) have a known correction, and even those aren't certain. For the 1-2 parts that really decide the board (X2, AE1, U1, U201, U401, U203, D702, D601), only the JLC preview can tell. |
| 4 | Dock case: plate on the pin barrels (D-L2) | **APPLY-MODIFIED**: one slot per pin pair, 1.9 mm wide x 0.6 mm deep. Ø2.1 holes don't work. | The geometry claim is exactly right: the barrel top is at -2.05, which equals PLATE_Z0, and the bore is Ø1.50 for a Ø1.499 barrel. But the pins are on a 2.2 mm pitch, so Ø2.1 counterbores would leave a 0.1 mm web. The plate keeps 1.45 mm of material, and the magnets are 11 mm away. |
| 5 | Band rev A: C203 spoke, U202 footprint | **DOCUMENT-ONLY** | Rev A is a reference and won't be ordered. Changing its Gerbers just changes the reference. Add a "known issues before ordering rev A" note. |
| D-L3 | Dock PCB has no front-to-back stop | **APPLY**: two rear ribs in `make_tray()` | Cheap and low risk. The case is being reprinted anyway, and the clash check will verify it. |
| C-E1/C-L1/C-L2 | Plunger lands on the solder tail | **APPLY the documentation change now. WAIT for a test print** before changing REC_CLR or the window. | Reflowing the pins with paste stops the wicking and costs nothing. A 0.15 mm FDM fit clearance can't be checked until something is printed. |

---

## 1. Dock PCB vias in pads (D-L1). APPLY-MODIFIED

**How the board was built.** `scripts/gen_pcb.py` only places footprints, draws the outline and adds the four GND zones. It contains no tracks or vias. The README says routing was done with "a grid router plus a hand-laid QSPI fan-out" and that the router's leftovers were re-laid by hand. So the 352 segments and 88 vias exist only in `dock-pcb-rev-b.kicad_pcb`. **Re-running gen_pcb.py would throw all the routing away.** The fix has to be an edit to the board file, either with a pcbnew script on the Mac or by hand in the GUI. Rev A's board file is byte-identical apart from the title block, so either repeat the fix there or mark rev A as superseded.

**Verified geometry.** The setup has `capping no`, `filling no` and `pad_to_mask_clearance 0`, and vias are tented on both sides. Every via is 0.45/0.3 mm.

Vias with their centre in a pad (16): C4.1, C12.1, C13.1, C15.1, R1.1, R7.1, R10.2, R12.1, D2.2, F1.2, SW1.1, U3.5, U6.4, U8.1, U8.3, U8.5.

Edge overlaps where the 0.3 mm drill reaches into the pad's mask opening (12): U5.3, U6.5, C20.1, D1.2, U3.2, Y1.4, C11.2, C14.2, U6.2, U7.2, C19.1, R9.2. In four other cases only the via land touches the pad (C8.1, U3.4, C6.1, SW1.2). Those are harmless.

**Does this cause defects at JLC?** Yes, it's a real risk. An open 0.3 x 1.6 mm barrel holds about 0.11 mm³. An 0402 pad with a 0.10-0.12 mm stencil gets about 0.03-0.04 mm³ of paste. The bottom of each via is mask-tented, which limits how far solder flows down, but the trapped air and flux then outgas and leave voids or solder balls. Per joint the defect rate is modest (a guess of 5-20 %), but 16-28 joints on each of 5 boards makes some starved or tombstoned 0402s likely. JLC's PCBA DFM review usually flags open via-in-pad and asks you to accept the risk.

**Dog-bone feasibility.** I searched for spots at 0/45/90 degrees, 0.3-2.0 mm away, at least 0.1 mm clear of the pad. Each spot had to keep at least 0.12 mm to other-net copper on the outer layers and 0.2 mm to inner tracks (the `.kicad_dru` rule), at least 0.25 mm hole-to-hole, and the new stub on each layer the via connects to had to stay clear too.

| Via (pad) | Net | Move to (x, y) | Distance and angle | Min clearance |
|---|---|---|---|---|
| C12.1 (111.3,113.2) | +3V3 | (111.76,112.74) | 0.65 @315 | 0.127 |
| C13.1 (110.35,109.75) | +3V3 | (109.50,109.75) | 0.85 @180 | 1.07 |
| C4.1 (102.05,108.3) | +3V3 | (101.35,108.30) | 0.70 @180 | 0.55 |
| R7.1 (111.95,100.35) | +3V3 | (111.55,100.35) | 0.40 @180 | 0.37 |
| R10.2 (121.74,103.09) | SWDIO_3V3 | (122.59,103.09) | 0.85 @0 | 0.235 |
| R1.1 (121.95,99.55) | XOUT | (122.85,99.55) | 0.90 @0 | 0.37 |
| C15.1 (110.3,111.7) | +1V1 | (109.50,111.70) | 0.80 @180 | 0.225 |
| D2.2 (117.1,122.7) | LED_ACT | (116.40,122.70) | 0.70 @180 | 0.125 |
| U8.3 (124.7,105.1) | SWDIO_1V8 | (125.45,105.10) | 0.75 @0 | 0.22 |
| R12.1 (128.7,103.3) | SWDIO_1V8 | (128.70,103.95) | 0.65 @90 | 0.245 |
| U8.5 (126.2,104.4) | +1V8 | (127.75,104.40) | 1.55 @0 | 0.237 |
| U8.1 (124.45,103.4) | +1V8 | (123.45,103.40) | 1.00 @180 | 0.20 |
| U6.4 (128.2,120.25) | VBUS_F | (127.75,120.25) | 0.45 @180 | 0.40 |
| F1.2 (101.6,112.25) | VBUS_F | (101.60,113.10) (under the body, tented) | 0.85 @90 | 0.325 |
| SW1.1 (119.75,122.2) | BOOT | (119.10,122.20) | 0.65 @180 | 0.93 |
| U5.3 edge (104.9,102.55) | +3V3 | (105.25,102.55) | 0.35 @0 | 0.90 |
| C20.1 edge (123.35,105.5) | +3V3 | (123.35,106.10) | 0.60 @90 | 0.41 |
| D1.2 edge (133.3,122.1) | LED_USB | (133.00,122.10) | 0.30 @180 | 0.126 |
| U3.2 edge (106.0125,113.0) | GND | (106.3125,113.0) | 0.30 @0 | 0.34 |
| Y1.4 edge (119.05,99.05) | GND | (119.35,99.05) | 0.30 @0 | 0.225 |
| C11.2 edge (111.08,108.75) | GND | (111.73,108.75) | 0.65 @0 | 0.17 |
| U6.2 edge (127.2125,119.3) | GND | (127.5125,119.3) | 0.30 @0 | 0.22 |
| U7.2 edge (125.2125,100.6) | GND | (125.5125,100.6) | 0.30 @0 | 0.34 |
| C19.1 edge (126.7375,98.05) | +1V8 | (126.7375,97.75) | 0.30 @270 | 0.53 |
| U6.5 edge (128.45,118.65) | VBUS_F | (128.804,119.004) | 0.50 @45 | 0.155 |
| R9.2 edge (114.35,116.8) | BOOT | (114.65,116.80) | 0.30 @0 | 0.545 |
| **U3.5** (107.55,113.05) | VBUS | no clean 45-degree spot. One at any angle: ≈(108.94,113.0), 1.4 mm | by hand | 0.16 |
| **C14.2** edge (111.08,110.95) | GND | no clean spot. Delete it (a GND via; the pad's other GND paths and the pour remain) or place by hand | by hand | n/a |

These numbers come from my own approximate checker. KiCad DRC is the authority, and zones refill afterwards.

**Implementation as a pcbnew script, run once on the board file:**
1. For each via above, move it to the new point.
2. On every layer where a track ended at the old via centre (In2/B.Cu), add a stub track from the old point to the new point. Use the same width and net as the existing track there.
3. On F.Cu, keep or add a track from the pad centre to the new via, 0.2-0.25 mm wide for signals and 0.3 mm on VBUS/VBUS_F/+3V3. Vias that had only In2/B.Cu tracks (C4, D2, R12, SW1, U3.5) have no F.Cu track yet, so add one. Keep the stubs at 0/45/90 degrees and end every track on a via or pad centre, so the README's trace-audit rules stay true.
4. Refill zones. Run DRC with schematic parity and require 0/0/0, with `track_not_centered_on_via` as an error. Then re-plot Gerbers, the drill file and the PDFs, and rebuild `fab/dock-pcb-rev-b-fab.zip`. The CPL doesn't change.

Effort is about 1-2 hours including DRC iteration. **Risk of the fix is low.** All moves are short, DRC catches any clearance mistake, and the electrical effect is nil: 0.3-1.5 mm extra on decoupling and LED paths. On XOUT (R1.1) the extra is 0.9 mm on a route that is already poor (D-L4).

**POFV instead?** JLC's documents only promise free resin-filled and capped vias on 6+ layer boards. For 4-layer they publish no price. It's a paid option at best, and its availability and cost have to be checked in the quote. It needs no copper change and would also cover the RP2040 EP vias (D-L8). If the user prefers it, set `(filling yes)` and `(capping yes)` in the stackup and add a fab note, and skip the dog-bones. I'd still dog-bone, because it is free, fab-independent, and permanent for re-orders. The RP2040 EP vias (D-L8) can stay as they are: the EP has no paste on the pad, so leave them for now.

## 2. Band rev B Nordic In1/In2 void (B-L1). SKIP for this order, DOCUMENT

**Claim verified.** Nordic's U1 is at (147.501, 105.988). The In1 and In2 rule areas are both at x 151.67-156.00, y 105.00-106.58, which is +4.17..+8.50 mm from U1. `transplant.py` copies a zone only if every point is inside BOX x ≤ +8.0, so this one was skipped without a message. Mapped into rev B (rotated 180 degrees about U1 at (111, 105)) it becomes: (106.832,105.961) (106.832,104.793) (104.495,104.793) (104.114,104.412) (102.5,104.412) (102.5,105.986) (103.809,105.986) (104.19,105.605) (106.197,105.605) (106.197,105.961). Rev B only has the small C9-island void on In1/In2 (x 104.0-105.83, y 103.8-104.8).

**Why Nordic voids it.** Nordic's board is 1.56 mm thick. Their RF output is a **0.762 mm** F.Cu trace that runs to the board edge (x 156), and the void runs all the way out with it. A 0.76 mm line is 50 Ω only as a CPWG referenced to the bottom-layer GND with the inner layers cut away. So the void is part of Nordic's stackup-specific 50 Ω design, and the filter got the same "no plane close underneath" treatment. Rev B made a different choice. It is 0.8 mm JLC04081H-7628 with In1 0.21 mm below the top, and its 0.36/0.16 CPWG is calculated to 50 Ω over In1. The two RF environments differ either way: even with the void copied, rev B's next plane (In2 at 0.47 mm, or B.Cu at 0.72 mm) is much closer than Nordic's.

**Why copying it as it is would make things worse.** Rev B has **B.Cu I2C_SDA running straight under the ladder**: (106.25,105.2)→(104.0,105.2)→(102.0,103.2), directly under the L3/C9/L4 line at y 105.2. In2 SWDCLK also runs at x 107.15, 0.3 mm outside the void edge, alongside L2/C6/C13. Today the solid In1 GND shields the RF ladder from both. Voiding In1+In2 would make B.Cu the ladder's reference with a digital line under it. Some of the shunt-cap GND vias (104.405,104.63), (105.41,104.64), (104.65,105.86) and (105.64,105.86) would also lose their In1/In2 connection.

**Size of the effect if left alone.** A 0.25 mm trace 0.21 mm over In1 has about 0.11 pF/mm, against roughly 0.03-0.05 pF/mm to the coplanar pour alone. That adds about +0.06 pF at the ANT node, +0.07 pF at RF1 (C6 1.5 pF, ~5 %), +0.08 pF at RF2 (C9 2.0 pF, ~4 %) and +0.04 pF at RF_50 (C11 0.3 pF, ~13 %). The 0201 pads add about 15-25 fF each. Expect a few percent shift in the filter or match, which probably means a few tenths of a dB of TX power. That is small next to the antenna detuning already expected from the 4.2 x 5.9 mm clearance (B-L9). **On the feed:** if the void had been copied, it would have reached the first ~0.8 mm of the RF_50 line (to y 105.986). That is about 1 % of a wavelength, negligible, and leaving In1 alone changes nothing on the CPWG.

**What to do.**
1. Change the rev B README line "In1 is unbroken under the radio" so it states the departure from Nordic and the reason (I2C_SDA on B.Cu, shielding).
2. Fix `transplant.py` so it at least *prints* the zones it skips. Don't change its BOX.
3. Optional, next spin only: void In1 only, using the polygon above but ending at x ≥ 103.5 so the CPWG stays over In1. Also move B.Cu I2C_SDA out of x 102.5-106.9, y 103.8-106.6, so In2 (solid GND, 0.47 mm) becomes the ladder's reference. Do this only if bring-up shows weak TX power or harmonics.

## 3. Band rev B CPL rotations (B-L2). APPLY-MODIFIED

`panelfab.py` writes `rot % 360` as it is, and there are four panel copies (_0.._3), all with the same rotation. The dock's ROT_FIX table (`^SOT-23` +180, `^SOIC-` +270, `^QFN-` +270) is the kicad-jlcpcb-tools default set. **On rev B it would match nothing useful.** There are no SOT-23 or SOIC parts, and U1's footprint is `Nordic_QFN40P600X600X90-48N`, which doesn't match `^QFN-`. Even on the dock those values were never confirmed: its README still says to check in the preview.

| Part | Footprint, KiCad rot | Expected pin-1 position (board view, from the body centre) | Correction |
|---|---|---|---|
| U1 nRF54L10 QFN48 (C44800139) | Nordic QFN, 180 | pin 1 (XL1) bottom-right (+3.03,+2.20) | +270 is the usual QFN fix, but JLC's library entry for this new part is unknown. **Preview only.** |
| U201 BQ25125 DSBGA-25 | 0 | A1 (GND) top-left (-0.8,-0.8) | BGA libraries are usually A1 top-left, so probably 0. **Preview only.** |
| U202 IS31FL3193 DFN-10 3x3 | 180 | pin 1 (LED_EN) bottom-right | kicad-jlcpcb-tools `^DFN-` +270. Likely but not certain. Preview. |
| U203 TPS7A02 X2SON-4 | 90 | pin 1 (VDD_2V0) bottom-left | **Preview only.** |
| U401 LIS2DW12 LGA-12 | 0 | pin 1 (I2C_SCL) top-left | No rule applies (`^Bosch_LGA-` doesn't match). **Preview only.** |
| U501 DRV2605L (DGS, MSOP-10) | `TSSOP-10_3x3mm`, 270 | pin 1 (REG) top-right | `^TSSOP-`/`^MSOP-` +270 is the best-established entry. Still confirm. |
| D702 RGB 1615 | 0 | pin 1 (VLED, anode) top-right | **Preview only.** |
| X2 32 MHz 2016 4-pad | 270 | pin 1 (XC1) top-left | 180 is harmless (1↔3); 90 kills the HFXO. **Preview only.** |
| X1 32.768 kHz 2012 2-pad | 270 | non-polar | No correction. Just check it isn't turned 90. |
| AE1 Johanson | 270 | pin 1 (ANT_FEED) top, y 111.1 | A 180 error swaps feed and NC. **Preview only.** |
| D601 SMF12A SOD-123F (unidirectional TVS) | 0 | pin 1 = cathode on VIN, left (-x) | Usually 0. Check the cathode band is on the left. |
| D602/D603 TPD1E10B06 | 0 | bidirectional | none |
| L201, L1-L4, FB1, all passives | n/a | non-polar | none |

**Recommended approach.**
1. Keep pos.csv raw. Don't add regex corrections.
2. Make the JLC preview check a gating step. For each part in the table, check the pin-1 marker sits at the corner listed. Rotate any wrong part in JLC's UI, and remember that **all four panel copies (_0.._3) must be rotated separately**.
3. Afterwards, write the confirmed deltas into a per-designator dict in `panelfab.py` (`ROT_FIX = {'U1': ..}`), so re-orders reproduce them.
4. Put the table above in the README.

Risk: none, since nothing gets guessed into the file.

## 4. Dock case: plate on the barrels (D-L2). APPLY-MODIFIED

**Verified.** In `dock_rev_a.py`: TAIL_TIP 0.55, PCB_TOP = 0.55 + 0.70 - 5.99 = -4.74, barrel from PCB_TOP+0.40 to PCB_TOP+2.69 = **-2.05**. `dock_rev_b.py` has PLATE_Z0 = -2.05, and the bores are `case.cyl(SP_X, y, 0.75, ...)`, which is Ø1.50 against a Ø1.50 barrel. The tolerance stack-up (PCB ±0.16, pin length ±0.15, solder under the flange ~0.05, print ~0.1) can lift the barrel by up to about 0.45 mm.

**Material.** The pins (x 131.5, y 101.1/103.3/111.7/113.9) sit under the band recess, which cuts the plate from z 0 to 1.2. So the plate there runs from -2.05 to 0, which is 2.05 mm. A 0.6 mm counterbore leaves 1.45 mm. The magnet pockets are at x 112.5/120.5, 11 mm away; the LED pockets, USB pocket, locating holes and strap channels are all far away too. **But** the pins are on a 2.2 mm pitch, so Ø2.1 counterbores at 101.1/103.3 and 111.7/113.9 would leave a 0.1 mm web that can't be printed. Use one slot per pair instead.

Put this in `make_top()` after the plunger bores:
```python
SP_CB_W, SP_CB_D = 1.9, 0.6     # barrel Ø1.50 -> 0.2 mm radial; 0.6 mm rise allowed
for ya, yb in ((case.SP_Y[0], case.SP_Y[1]), (case.SP_Y[2], case.SP_Y[3])):
    t -= case.box(case.SP_X - SP_CB_W/2, case.SP_X + SP_CB_W/2, ya, yb, PLATE_Z0 - 1, PLATE_Z0 + SP_CB_D)
    for y in (ya, yb):
        t -= case.cyl(case.SP_X, y, SP_CB_W/2, PLATE_Z0 - 1, PLATE_Z0 + SP_CB_D)
```
This gives two stadium slots, x 130.55-132.45, y 100.15-104.25 and 110.75-114.85, from z -2.05 to -1.45. The plate prints underside-down, so each slot is a first-layer pocket with a short 1.9 mm roof bridge, which is fine. Re-run the script with the dock PCB STEP. Expect the solid count to be 1 and the clash check to show 0 overlaps. Then re-export the STEP/STL/previews. Update the docstring and README to say the plate no longer touches the barrels. Note that the PCB is now held down only by the docked band's spring force and the 0.25 mm gap over the USB shell, which is acceptable.

## 5. Band rev A (C203 spoke, U202 footprint). DOCUMENT-ONLY

Rev A isn't being built. Fixing it means editing, refilling and re-plotting a reference design nobody will order, and re-validating it. Add a "Before ordering rev A" box to `band/rev-a/pcb/README.md` listing: C203 pad 2 needs ≥2 GND spokes (refill after loosening the local clearance or adding a stub); U202 should use KiCad's DFN-10 EP 0.7x1.2 (or equivalent) with paste windows at about 50-60 %; and A-L1, the silkscreen ref text 110-230 mm off-board.

## Other items

**D-L3: rear stops. APPLY.** Verified: the cavity runs y 96.1-124.0, the PCB y 97.5-124.0, so there is 1.4 mm free at the back, and the corner stops sit outside the PCB's x range. In `make_tray()` after the corner stops:
```python
for x0, x1 in ((PCB[0] + 2.0, PCB[0] + 6.0), (PCB[1] - 6.0, PCB[1] - 2.0)):   # rear stops, 0.2 mm clearance
    t += case.box(x0, x1, PCB[2] - 1.45, PCB[2] - 0.2, TRAY_Z0 + FLOOR_T - 0.01, PCB_TOP + 0.6)
```
These are ribs at x 102-106 and 134-138, y 96.05-97.3, up to z -4.14. Nothing on the PCB overhangs the rear edge (the nearest parts are at y ≥ 97.8, inside the board), and the ribs are 2 mm below the plate. That leaves 0.2 mm of total y float, with the front staying line-to-line at 124.0. Re-run the clash check. Optional: a printed backstop behind the USB shell is better, but it is more work.

**Contact carrier (C-E1/C-L1/C-L2).**
- **APPLY now (documentation)** in `band/rev-a/case/README.md` Home build, steps 3-6, and the carrier README, which rev B reuses. Before the carrier goes into the cover: put paste on the top pads, insert the pins, reflow on a hotplate with the carrier on a holed spacer so the tails hang free, clean with IPA, and check under magnification that every tail end is free of solder and flux. Only then lay the carrier in the cover and glue it. Add to step 6 / bring-up: dock the band with a deliberate ~0.3 mm side push in each direction and check all 4 contacts with a meter.
- **WAIT for a test print:** REC_CLR 0.3 → 0.15. If you do it, add a local `REC_CLR = 0.15` in `dock_rev_b.py`; don't edit `dock_rev_a.py`, which rev A also uses. A 0.15 mm clearance between two FDM parts may simply not fit. Measure the printed band and recess first. The straight Ø1.7-1.8 bore at tail depth (z 0.4-0.7) in the band cover is also a test-print decision.

## Sources
- JLCPCB POFV guide: https://jlcpcb.com/help/article/via-in-pad-pofv-guide
- JLCPCB free via-in-pad (6+ layers): https://api.jlcpcb.com/blog/jlcpcb-free-via-in-pad
- JLCPCB via covering options: https://jlcpcb.com/help/article/pcb-via-covering
