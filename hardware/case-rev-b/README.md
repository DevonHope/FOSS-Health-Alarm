# WakeBand case rev B (for the rigid rev B board)

Rev A's case (`../case-rev-a`) with two shell changes. The cover, contact carrier, spring pins,
magnets, dock and strap are unchanged; print or reuse the rev A cover.

1. **Antenna pocket:** the Johanson chip antenna (AE1 at 102.15, 112.55; 3.2 x 1.6 x 1.3 mm)
   stands 0.2 mm taller than the space rev A leaves over the top side. The roof gets a pocket over
   it to z 9.05, leaving 0.95 mm of roof and 0.15 mm of air over the antenna.
2. **Dock land:** rev A's solid land over the top spring-pin pair started at x 119.8. Rev B's
   charger parts sit under the start of it, so it now starts at x 127.6 and covers only the pin pair
   at x 131.5 (pads and solder mask).

| File | What |
| --- | --- |
| `wakeband-case-rev-b-shell.step` / `.stl` | outer shell (print this) |
| `case_rev_b.py` | builds the shell from `../case-rev-a/case_rev_a.py` |

    python case_rev_b.py OUT_DIR BOARD_STEP CELL_STEP LRA_STEP

**Clash check (2026-11-08):** the rev B board STEP (KiCad export, all part models), the 60 mAh cell
and the LRA (the placed models from rev A's `make_placed.py`; rev B keeps the lead pads where they
were) against the shell and cover: 469 solids, **0 overlaps**. Shell against cover: 0.77 mm3, the
same intended 0.05 mm press fit as rev A.

Two parts have no 3D model in KiCad's library: the TPD1E10B06 ESD diodes (D602, D603; 0.6 x 1.0 x
0.4 mm) and the TPS7A0220 LDO (U203; 1 x 1 x 0.4 mm). At 0.4 mm tall they sit well under the 1.1 mm
the shell leaves over the top side.

Sand the panel tab nubs off the board's long edges before fitting (see the board README).
