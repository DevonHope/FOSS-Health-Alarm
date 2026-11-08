# Independent verification: WakeBand band rigid rev B (fix commits 3bfb257 and c4c6c1e)

Date: 2026-11-08. Repo HEAD is c4c6c1e. Compared against 25262a1. Read-only. KiCad was not available, so I parsed the board files with Python (sexpdata + shapely). The scripts are in `scratch/verify-revb/` (kp.py is the parser; t1-t14 are the checks).

## Summary

| Item | Result |
|---|---|
| 1. RF void, In2 reference, I2C reroute, feed reference, shunt vias, C6, feed vias | **PASS** |
| 2. B-L4 hole-to-copper / B-L6 mask dams | **PASS** |
| 3. B-L3 ESD part choice, pinout, placement and case fit | **PASS** (one Minor, two Notes) |
| 4. Regressions: parity, clearance, keep-out, connectivity, fab, panel, README | **PASS** (Minor: title block and Gerber job still say rev A) |

No Blockers and no Majors.

---

## 1. RF (B-L1, B-L5, B-L7): PASS

**The void**
- The zone "Nordic ref (In1 only): RF filter void" is on In1.Cu only. Its settings: keep-out, no pour, no tracks, vias allowed.
- Its outline is exactly the expected 10-point polygon (symmetric difference area 0.0).

**Fill under the void** (my parse of the stored fills over the 3.43 mm² void):

| Layer | GND fill inside the void |
|---|---|
| In1 | 0.000 mm² (void is clean) |
| In2 | 3.4285 mm² (100 %, solid GND) |
| B.Cu | 3.4285 mm² (100 %, solid GND) |

- The only other In1 rule area is Nordic's small C9-island void. The In2 copy of that void has been removed.

**Signals near the filter**
- No track on In1, In2 or B.Cu touches the box x 102.5-106.9, y 103.8-106.6.
- The I2C_SDA B.Cu path is now at y 102.6-103.6 (track edge at y 103.675). I2C_SCL drops to B.Cu at (101.3, 104.6) and crosses under the feed at y 108.7, which is outside the box.
- Both I2C nets are still single connected nets.
- The only non-GND item touching the box is the existing Nordic /DECA via at (106.56, 106.775). Its edge enters the box by 0.075 mm. It is a via, not a track, and it is unchanged from the old board.

**Feed reference**
- Every 0.36 mm RF_50 and ANT_FEED segment has 100 % In1 (and In2) coverage, up to the antenna keep-out edge at y 109.1. The part inside the keep-out is unreferenced, as before.
- The only RF_50 copper over the void is the 0.25 mm stub from the L4/C11 node at (103.79, 105.2) to (103.25, 105.2). Its x 103.5-103.79 part (47 %) sits over the void. That stub is the filter node, and the clip at x 103.5 intends this.

**Shunt-cap GND vias** (in the ladder area)
- All of them reach In2 and B.Cu fill.
- The vias inside the void lose In1, as intended:
  - (104.405, 104.63)
  - the C9-island vias (104.9, 104.21) and (105.41, 104.64)
- The C9-island vias connect to the F.Cu island zone through tracks.
- The connectivity check found no split nets.

**C6 (B-L5)**
- Nordic's C6, mapped by 180° about U1, lands at (106.832, 105.707). C6 on rev B is at (106.83, 105.707), a 0.002 mm difference.
- L2, L3, L4, C9 and C13 are also within 0.002 mm of Nordic. C11 is still on the other side, as documented.
- Pad gap L2.1 (/ANT) to C6.1 (/GND) is 0.207 mm (was 0.10). No mask web under 0.1 mm anywhere on the board.

**Feed stitching vias (B-L7)**
- Eight new 0.4/0.2 /GND vias:
  - (103.5, 105.75)
  - (103.45, 106.75), (103.45, 107.25), (103.45, 107.75), (103.45, 108.25)
  - (102.15, 105.2), (102.15, 105.7), (102.15, 106.2)
- They sit 0.57-0.79 mm from the feed centre line. Each connects to the GND fill on all four layers.
- None of them is in the antenna keep-out: the lowest is at y 108.25 and the keep-out starts at y 109.1.
- 9 GND vias are within 1 mm of the feed, which matches the README.
- The antenna keep-out holds only AE1's pads and the ANT_FEED track: no vias and no fill on any layer.

## 2. B-L4 / B-L6: PASS

**Hole-to-copper (B-L4)**
- I checked every via hole and every PTH against different-net copper on all four layers, including zone fills.
- Inner-layer vias with `remove_unused_layers` were treated as holes only.
- 18 hits are under 0.2 mm. **All of them are the 0.25/0.15 via-in-pad vias:** VIN (120.8, 104.6), PMIC_INT (120.8, 105.8), TS (121.2, 105.4), DOCK_PG (121.6, 105.8), PMID (127.15, 113.5). Their minimum is 0.15 mm.
- The two 0.45/0.3 vias the reviewer flagged are now ≥ 0.2 mm on every layer:
  - VLED, moved to (122.55, 106.05)
  - VBAT (123.95, 111.35)
- The .kicad_dru courtyard rules now require `A.Hole < 0.16mm`, in both the board and panel DRU files.

**Mask dams (B-L6)**
- U201 balls are 0.23 mm with a 0.03 mm margin, giving 0.29 mm openings. The minimum dam is 0.110 mm.
- No pad-to-pad mask web on the board is under 0.10 mm.
- The panel copies carry the 0.03 mm margin too.

## 3. B-L3 ESD at the dock contacts: PASS

**D601 = ESD5681N07-2/TR (Will Semi, C240204), from the datasheet via LCSC / elecfans / szlcsc**

| Parameter | Value |
|---|---|
| Direction, package | Unidirectional, DFN1006-2L |
| VRWM | 7 V |
| VBR at 1 mA | 8.0 / 9.0 / 10.0 V (min / typ / max) |
| IR at VRWM | ≤ 1 µA (10 nA typ) |
| Clamp | 11 V at 8 kV ESD; 16 V at 27 A, 8/20 µs |
| CJ | 140 pF typ |
| Max height | 0.53 mm |

- A newer szlcsc datasheet revision lists VBR 7.5-9.5 V, 250 pF and 40 A. The conclusion is the same either way.
- **Standoff margin:** 7 V standoff and ≥ 7.5-8 V breakdown, against 5 V nominal and 5.25 V worst case. That is ≥ 1.75 V of margin, with negligible leakage at 5 V.
- **Clamp vs charger:** both clamps (11 V and 16 V) are below the BQ25125 IN absolute maximum of 20 V. The SMF12A's rated clamp was 19.9 V, so this is better.

**Polarity**
- The schematic symbol is Device:D_Zener (pin 1 = K) with pin 1 on /VIN.
- The footprint is KiCad Diode_SMD:D_SOD-882, where pad 1 = cathode. On the board, pad 1 is on /VIN at (131.25, 110.45) and pad 2 is on /GND.
- So the cathode is on VIN. This matches the README CPL table ("cathode bar towards y 100").
- The datasheet text has a "cathode marking" but the extracted text doesn't name which pin it is. Confirm the bar in JLC's preview, which the README already lists as a check.

**Dropping the SMF12A**
- Not a meaningful loss. The SMF12A was 200 W at 10/1000 µs. The ESD5681 is 450 W at 8/20 µs, and its 27 A at 16 V clamps lower.
- The only source is the dock, which has an SMF6.0A and a 0.21 A SY6280 limit (dock/rev-b/pcb/README.md). Long surges cannot reach the band at high current.
- **Note:** if the dock fails high in the 8-20 V range, the BQ25125's OVP would have ridden it out. Now the DFN1006 conducts up to about 0.21 A × 9 V ≈ 2 W and may fail short. That is fail-safe, but the TVS dies.

**Paths from the landing to the clamp** (my measurement)

| Net | Contact via | Path to the clamp pad |
|---|---|---|
| SWDCLK | (131.2, 101.7) | 0.42 + 1.65 = 2.07 mm F.Cu to D602.1 |
| SWDIO | (131.35, 102.65) | 1.37 mm F.Cu to D603.1 |
| VIN | (132.0, 113.3) | 3.40 mm F.Cu to D601.1 |

- Add 0.67-0.78 mm from the landing centre to the via. The README's 2.7 / 2.0 / 4.2 mm figures agree.
- Each contact via touches its landing, and each net continues only from the clamp pad.
- The GND vias are 0.6 mm (D602) and 0.4 mm (D603, shared with C502). D601's GND via sits inside the GND landing.
- D602 and D603 are TPD1E10B06 (C48260), unchanged part.

**Case fit** (rev A shell geometry with rev B's LAND at x ≥ 127.6, y < 103.2)

| Part | Clearance to the case |
|---|---|
| D602 body | 0.30 mm below the land |
| D603 body | 0.35 mm below the land |
| D601 body | 0.16-0.2 mm left of the post (x ≥ 131.75, y 110.8-114.6) |
| C502 | clear of the land and post |
| TP705 pad (now at 127.1, 101.6) | 0.1 mm left of the land |

- Under the post, only the VIN F.Cu track and the via at (132.0, 113.3) sit there, under mask. Moving TP705 also clears the old B-L12 post overlap.
- Nothing is in the LED window except D702, and nothing is near the antenna-end posts.
- No courtyard overlaps, and no new pad-to-pad gap under 0.25 mm.

**Heights:** D601 is 0.53 mm max, TPD1E10B06 (DPY) about 0.4 mm max, and C502 (0402) about 0.55 mm. All are ≤ 1.1 mm.

## 4. Regressions: PASS

**Schematic vs PCB parity** (my own parse)
- I mapped the labels in the schematic (218 labels, all at pins) through the lib-symbol pin positions to each (ref, pin).
- 0 net mismatches, 0 unlabelled pins, 0 missing parts.
- Value, Footprint and LCSC fields match for every part. D601 is ESD5681N07 / D_SOD-882 / C240204 in both the schematic and the PCB.

**Clearance**
- 0 copper pairs under 0.1 mm on any layer, including the stored zone fills.
- Minimum copper-to-edge is 0.30 mm (J601.3 landing, unchanged).

**Connectivity:** 46 nets with pads. 0 split nets. No floating track or via islands.

**Trace audit:** the same 3 short interior jogs and the same 1 non-45° segment as 25262a1. Nothing new. Totals: 517 segments, 172 vias, 87 GND vias. These match the README.

**Panel**
- All 69 footprints appear exactly once in each of the 4 copies, at the board position plus offsets (13.5, −63), (50.5, −63), (13.5, −41), (50.5, −41), with the same rotation, footprint and value. This covers moved C6, D601, D602, D603, C502 and TP705.
- All 2068 segments (517 × 4) and 688 vias (172 × 4) are present.
- The In1 void zone is in all 4 copies. Fills are about 4× the board's, less the tab cuts.

**pos.csv**
- 220 rows. All match the panel footprints (x, −y, rotation).
- D601_0..3 are at 270, D602 at 270, D603 at 0, C502 at 0, C6 at y 105.707.

**bom.csv**
- The designator sets match pos.csv. Comment, footprint and LCSC match the panel.
- The new D601 line is ESD5681N07, D_SOD-882, C240204.
- C14 and C15 are DNP and absent from both files, as intended.

**gerbers.zip** (KiCad 10.0.3, 2026-11-08 11:27)
- The PTH drill has 688 hits, which match the panel vias.
- The D601 pad flashes are present at (144.75, −47.45/−48.15). C6 is flashed at its new y (−42.707).
- In1 and In2 have no region vertices inside any of the 4 void copies.

**README:** updated. Routing, the RF void section, ESD clamps, ground stitching (9 vias within 1 mm), the CPL table row for D601, the parts table and the status are all current. The stale "In1 is unbroken" line is gone.

## New or remaining problems

- **Minor: B-L10 is still open.**
  - The board title block still says "WakeBand rigid rev A", rev "A", 2026-11-03, "mounts parts-side down".
  - The Gerber job and the ProjectId in the Gerbers carry Revision "A".
  - Harmless for fabrication, but confusing on a rev B order.
- **Minor: vias inside the dock landings.**
  - D601's GND via (131.25, 111.75) is 0.255 mm from the centre of the J601.2 landing, inside the Ø1.07 plunger footprint.
  - The other three contact vias sit at the landing rims, 0.67-0.78 mm out.
  - These are fine only if the board is ordered with filled and capped vias (POFV, all vias), which the README specifies. Without POFV, the plunger rides on an open or tented via.
- **Note: D601 land pattern.** It uses KiCad's generic D_SOD-882 (pads 0.4 × 0.7, pitch 0.7). The Will Semi datasheet's recommended land values (0.55 / 0.60 / 0.30 / 0.85 / 1.40) could not be mapped reliably from the text extraction. Worth checking against the PDF drawing, but low risk for a 0.65 mm-pitch DFN1006.
- **Note: dock overvoltage behaviour.** A dock fault in the 8-20 V range now goes into D601 (≈ 2 W at the 0.21 A limit) instead of being survived by the charger's OVP behind the SMF12A. Accept or document.
- **Note:** B-L2 (CPL rotations, preview gating) and B-L8 (panel tabs) are still handled only in documentation, as the fix-advisor recommended. The D601 orientation check is now in the README table.
