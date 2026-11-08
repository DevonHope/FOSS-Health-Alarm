# Independent verification: WakeBand band rigid rev A, commit d5355a6 (review 2026-11-08)

Board: `hardware/band/rev-a/pcb/rigid-rev-a.kicad_pcb` (33 x 15 mm, 4 layers). Baseline: 25262a1. Nothing after
d5355a6 touches `hardware/band/rev-a` (`git diff --stat d5355a6 HEAD` is empty). I made no changes to the repo.
KiCad isn't installed, so everything below comes from my own Python parsing of the board, the schematic, the
footprint library, the Gerbers, the drill file, the zip, the BOM and the CPL, using sexpdata and shapely.
Scripts: `scratch/verify-reva/`
(kp.py, geo.py, gbr.py, gnet.py, item1*.py, item2.py, item4.py, sch.py, parity.py, clr.py, conn.py, ko.py, g2b.py, gclr.py).

## Summary

| # | Item | Verdict |
|---|------|---------|
| 1 | C203 pad 2 connected to GND_L1 | **PASS** |
| 2 | U202 exposed pad, paste, library match, obsolete footprint | **PASS** (there are no EP vias, see note) |
| 3 | Reference text of C208, U202, D702; nothing outside the outline | **PASS** |
| 4 | J601.3 SWDCLK via moved off the pad centre | **PASS** |
| 5 | Regressions: parity, clearances, keep-out, fab = Gerbers = board, BOM/CPL | **PASS** (one older Minor finding) |

No Blocker or Major findings. Four Minor or informational findings are listed at the end.

## 1. C203 pad 2 (GND, 116.12, 111.22): PASS

- The pad now has `zone_connect 2` (solid). The pad's zone connection was inherited before.
- The GND_L1 F.Cu fill now covers the whole pad (0.330 of 0.330 mm²), and its whole perimeter (2.119 mm) touches fill.
  Before, 0.504 mm of the perimeter touched fill, which is one spoke.
- The fill island is 18.2 mm² and holds 4 GND vias to the inner planes, so the pad is not on a floating island.
- The Gerber F.Cu GND region also covers the whole pad (0.347 of 0.347 mm²), so the fix reached the fab files.
- The new fill keeps 0.200 mm from pad 1 (VDD_2V0). The nearest other-net copper to pad 2 is the VDD_2V0 via at
  0.237 mm and the PMIC_INT track at 0.300 mm.
- **Tombstoning:** the extra heat sinking stays close to the pad. Copper crossing a ring around the pad:
  - 0.1 mm out: 2.17 mm now, 0.50 mm before.
  - 0.5 mm out: 0.94 mm now, 0.77 mm before.
  - 0.8 mm out: 1.13 mm now, 1.13 mm before.

  So the pour's neck limits the heat path to about the conductance of a two-spoke relief (2 x 0.5 mm). That is the
  same as the review's "≥ 2 spokes" fix. Pad 1 still has three 0.2 mm tracks and an unpoured via. The imbalance grew a
  little compared with the old starved single spoke, but no more than the requested fix would add. It matches the
  solid pads R202.2, C401.2 and so on, and the README documents it. Acceptable.

## 2. U202 (KTD2026, UTDFN-8 1.5 x 1.5): PASS

- **EP size:** pad 9 is 1.2 x 0.65 mm rect at (126.55, 113.2). In the Gerber, the F.Cu flash is R 1.2 x 0.65.
- **EP to signal pads:** 0.200 mm to each of pins 1-7, the minimum by geometry (pin 8 is GND). The GND_L1 fill also
  keeps 0.200 mm from every signal pin.
- **Paste:** pad 9 has no F.Paste. There are two paste-only pads, 0.45 x 0.48 mm, at ±0.3 mm. That is 0.432 / 0.780
  = **55.4 %**, fully inside the EP. The F_Paste Gerber has exactly these two flashes plus the 8 pins.
- **GND vias in the EP:** there are none, before or after the fix: no via lies within 0.5 mm of the EP in either
  revision. Nothing can sit under a paste opening.
  - The EP connects to GND by the pin-8 track to the EP centre (it's still there).
  - It also connects solid to the GND_L1 fill, which covers 0.774 of 0.780 mm² in the Gerber. That island is
    15.7 mm² with 4 GND vias.
  - So "vias still valid" doesn't apply here, and nothing broke.
- **Library vs board:** `wakeband.pretty/Kinetic_UTDFN-8_1.5x1.5mm_P0.4mm_EP1.2x0.65mm.kicad_mod` matches the board
  instance in every pad (number, type, shape, position, size and layers), in its graphics (silk, fab and courtyard),
  and in its descr and tags.
- **Board-only fields:** pad 9 has `zone_connect 2`, the same override as before. The two paste pads have
  `thermal_bridge_angle 45`, which is harmless (see Minor M3).
- **Footprint field:** the same in the board, `power.kicad_sch`, `wakeband.kicad_sym`, `bom.csv` and
  `fab/bom_jlcpcb.csv`.
- **Obsolete footprint:** git renamed the `..._EP1.45x0.8mm.kicad_mod` file. It no longer exists, and no
  .kicad_pcb, .kicad_sch, .kicad_sym, .csv or .kicad_mod in the repo uses it. The only remaining references to the old
  name are the 3D model filename (Minor M2), the fix script and README text.
- I couldn't check the EP against the KTD2026 datasheet offline. The pin-pad geometry is unchanged.

## 3. Reference text and silkscreen: PASS

- **Before (25262a1):** the three reference texts were on F.SilkS with board-absolute numbers stored as offsets.
  They plotted at C208 (238.3, -15.9), U202 (250.6, 228.9) and D702 (260.5, 229.1).
- **Now:** all three are on F.Fab at the library offsets:
  - C208 at (126.94, 112.17)
  - U202 at (126.55, 111.60)
  - D702 at (130.22, 111.40)

  All three sit on the board next to their parts. No footprint field on F.SilkS or B.SilkS is visible any more.
  F.Fab is not in the plotted layers.
- **F_Silkscreen.gto in `fab/gerbers/` and in the zip:**
  - 318 objects, **0 outside** the 33 x 15 mm outline with 1 mm corner radius (each stroke tested exactly, aperture
    included).
  - The old file had 487 objects, 169 of them off the board. 487 − 169 = 318, so only the off-board text was removed.
- **Every other Gerber layer** (F/B Cu, In1, In2, F/B Mask, F/B Paste, B Silk) also has **0 objects outside the
  outline**. Edge_Cuts extents: 99.975..133.025 x 99.975..115.025.

## 4. J601.3 SWDCLK landing pad (B.Cu, 131.5, 101.1): PASS

- **Via position:** the via (0.45 / 0.3, F.Cu–B.Cu, net /dock/PAD_SWDCLK) is now at (130.65, 101.1), 0.85 mm from
  the pad centre. Before, it was at the centre.
- **Plunger clearance:** the drill edge is 0.70 mm from the pad centre. A Ø1.0 tip at the centre has 0 overlap with
  the drill or the via land. Before, the overlap was 0.071 mm² with the drill and 0.159 mm² with the land. The tip has
  0.20 mm margin to the drill edge, like the VIN and GND pads (0.71 and 0.79 mm).
- **Connectivity:**
  - B.Cu: the via land overlaps the Ø1.6 pad by 0.053 mm², a 0.42 mm chord.
  - F.Cu: the existing track (128.25 → 130.65, 101.1, 0.12 mm) ends exactly on the via centre, with no stub.
  - My net-connectivity check (pads, tracks, vias and fills joined per net) finds **0 split nets out of 67**.
- **Clearances:** 0.201 mm from the via to the GND fill on F.Cu and In1, and 0.200 mm from the pad to GND_L4. The
  via hole is at least 0.275 mm from other-net copper.
- **Fab files:** the drill file has the hole at (130.65, -101.1) and none at 131.5. The B_Cu and F_Cu Gerbers show
  the via pad there.
- Part of the drill (0.70–1.00 mm from the centre) is inside the 1.6 mm mask opening, as with the VIN and GND pads.
  The board already requires POFV (`filling yes`, `capping yes`), and B has no paste.

## 5. Regressions: PASS

### Net parity, from my own netlist

I built the netlist from the six sheets: wires, T-connections, local and global labels, and power symbols, with
PWR_FLAG excluded.

- 53 schematic symbols on the board and 53 footprints, with no reference missing on either side.
- **201 pins, 0 pin-partition differences, 0 net-name mismatches.** Footprint fields and values match for every
  reference.
- The 31 single-pin schematic nets are all `unconnected-*` on the board.
- U1 pads 49-62 have no net and no symbol pin, the same as in the baseline: they are the module's antenna-area pads.

### Clearances (all copper, per layer, different nets; net tie and bridged jumper excluded)

| Check | Result |
|---|---|
| F.Cu minimum | 0.107 mm (U201.17 to NTC track) |
| In1.Cu minimum | 0.2005 mm |
| In2.Cu minimum | 0.180 mm |
| B.Cu minimum | 0.139 mm |
| Items under 0.1 mm | **none** |
| Inner-layer via to other-net copper under 0.2 mm (`.kicad_dru`) | none |
| Hand-solder pads under 0.5 mm | none |
| Via hole to other-net copper, minimum | 0.214 mm |
| Hole to hole, minimum | 0.285 mm |

These numbers are identical to 25262a1, so the fix introduced no new near-misses. At the changed features:

- C203.2: 0.237 mm
- C203.1 to the new fill: 0.200 mm
- U202.9 to its pins: 0.200 mm
- SWDCLK via: 0.201 mm

### Antenna keep-out (x 100-105, y 98.5-116.5, all layers)

- 0 tracks, vias, zone fill or other footprints' courtyards.
- Only U1's own unnetted pads 49-62 are inside, and the keep-out allows pads. The same holds in the baseline.
- In the Gerbers, the inner and B copper starts at x ≥ 105.0.

### Fab zip = Gerbers = board

- **Zip vs files:** all 18 files in `rigid-rev-a-fab.zip` are byte-identical to `fab/gerbers/*` (16 files) and to
  `fab/bom_jlcpcb.csv` and `fab/cpl_jlcpcb_top.csv`.
- **Drill:** 140 holes, the same positions and sizes as the board's 140 vias. NPTH is empty.
- **Flashes:** the flash positions match the board's pads and vias on F.Cu (345), B.Cu (150), In1 (140), In2 (140),
  F.Paste (201), F.Mask (203) and B.Mask (10). The only differences are 0.001 mm rounding at x 111.6625.
- **Zone fills:**
  - In1 and In2 fill areas equal the Gerber region areas exactly (352.329 and 228.194 mm²).
  - On F.Cu and B.Cu they match at the changed spots: C203 fill vs Gerber within 0.008 mm²; U202 and J601.3 within
    0.006 and 0.0003 mm².
  - Elsewhere they differ slightly because of the teardrops (Minor M1).

### BOM vs CPL vs board

- 34 BOM designators equal the 34 CPL designators, and all are on the board's top side.
- CPL X, Y and rotation match the board for every part (Y is negated, as KiCad's pos export does).
- BOM footprints match the board footprints.
- The 19 board footprints that are not in the BOM are all DNP (D701, R201, R701) or `exclude_from_bom`/`pos` (J601,
  JP201, NT201, TPs).

## Findings

**Blocker:** none. **Major:** none.

**Minor**

- **M1 (older than this commit): the Gerbers carry about 86 teardrops and a re-poured fill that the board file
  doesn't have.**
  - Counts: 84 non-GND conductor regions on F.Cu and 2 on B.Cu.
  - Cause: `scripts/mkfab.py` exports with `kicad-cli ... --check-zones`. That refills the zones in memory and adds
    teardrops, because the pads have teardrops enabled. This is the effect the fix script warns about for
    `--refill-zones`. So the F.Cu and B.Cu copper you order is not exactly the copper that the 0/0/0 DRC checked.
  - It is unchanged from 25262a1: the region counts are 103/9/1/9 in both.
  - I re-ran the clearance check on the Gerbers themselves, by net from the X2 attributes, teardrops included:
    minimums are F.Cu 0.107, B.Cu 0.139, In1 0.2005 and In2 0.180 mm. Nothing is under 0.1 mm, so it is harmless.
  - Suggest: either drop `--check-zones` (the saved fill is already current), or turn teardrops off in the pads or
    board setup, so that the Gerbers equal the DRC'd board.
- **M2: the U202 3D model is still named `..._EP1.45x0.8mm.step`.** Both the library footprint and the board
  reference it. The README's 3D-model table says so, and the package itself didn't change. Cosmetic only. Rename it
  when the models are next regenerated.
- **M3: the board's two U202 paste-only pads carry `(thermal_bridge_angle 45)`; the library copy doesn't.** pcbnew
  added the value when the script created the pads. It has no effect, because the pads have no copper. I couldn't
  confirm in KiCad whether `lib_footprint_mismatch` compares this value. The author reports DRC 0 with library checks,
  so it probably doesn't.
- **M4 (informational): there were never any vias in U202's EP.** The review item's wording assumed some. The EP's
  GND path is the pin-8 track plus the solid GND_L1 pour, which is fine for a KTD2026.
