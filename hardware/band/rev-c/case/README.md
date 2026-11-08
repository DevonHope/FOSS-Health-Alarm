# WakeBand case rev C (for the rigid rev C board)

> **Same geometry as the rev B case** ([`../../rev-b/case`](../../rev-b/case)); only the file names
> changed (`wakeband-case-rev-c-*`, `case_rev_c.py`). Rev C's board keeps rev B's outline, dock landings,
> LED and antenna positions, and its moved ESD parts (0.4-0.5 mm tall) clear the shell: clash check
> 2026-11-08 against the rev C board, cell and LRA, 0 overlaps. The text below is the rev B case's.

Rev A's case (`../../rev-a/case`) with two shell changes. The cover, contact carrier, spring pins,
magnets, dock and strap are unchanged; print or reuse the rev A cover.

1. **Antenna pocket:** the Johanson chip antenna (AE1 at 102.15, 112.55; 3.2 x 1.6 x 1.3 mm)
   stands 0.2 mm taller than the space rev A leaves over the top side. The roof gets a pocket over
   it to z 9.05, leaving 0.95 mm of roof and 0.15 mm of air over the antenna.
2. **Dock land:** rev A's solid land over the top spring-pin pair started at x 119.8. Rev B's
   charger parts sit under the start of it, so it now starts at x 127.6 and covers only the pin pair
   at x 131.5 (pads and solder mask).

**Charge LED window (from rev A, unchanged):** rev B's LED D702 is at (130.225, 113.2), where rev A's
was. The shell keeps rev A's blind pocket over it: 2.4 x 2.3 mm, cut from inside, leaving a **0.4 mm
skin** on the outer face (the roof is 1.2 mm elsewhere). The LED shines through that thin spot with no
opening, so the case stays sealed. Checked on the built rev B shell: solid from z 9.6 to 10.0 over the
LED, against 8.8 to 10.0 beside it. Print in a light or translucent colour; through dark filament the
LED is hard to see (see `../../rev-a/case/README.md`, Charge LED).

**Printing:** shell **top face down** (as rev A's), no supports; print the cover from this folder
(`wakeband-case-rev-c-cover.stl`, the same part as rev A's), wrist face down, pausing at z 1.25 mm for the magnets. **Print check (2026-11-08, `../../../tools/printcheck.py`):** one solid, no
overhang past 45 degrees, no bridges, no knife edges; the only wall under 0.8 mm besides the 0.4 mm LED
skin is 0.75 mm, for 0.7 mm of height, between the M2 heat-set insert hole and the shell's inside face
below the board (both fit-critical; the insert melts into it anyway).

| File | What |
| --- | --- |
| `wakeband-case-rev-c-shell.step` / `.stl` | outer shell (print this) |
| `wakeband-case-rev-c-cover.step` / `.stl` | wrist cover (print this; identical to rev A's cover) |
| `case_rev_c.py` | builds the shell from `../../rev-a/case/case_rev_a.py` |

    python case_rev_c.py OUT_DIR BOARD_STEP CELL_STEP LRA_STEP

**Clash check (2026-11-08):** the rev B board STEP (KiCad export, all part models), the 60 mAh cell
and the LRA (the placed models from rev A's `make_placed.py`; rev B keeps the lead pads where they
were) against the shell and cover: 469 solids, **0 overlaps**. Shell against cover: 0.77 mm3, the
same intended 0.05 mm press fit as rev A.

Re-checked after the review re-layout (board at c4c6c1e, ESD parts moved next to the dock contacts): 128
solids (KiCad 10.0.3 packs the models into fewer solids), **0 overlaps**; shell against cover unchanged.

Two parts have no 3D model in KiCad's library: the TPD1E10B06 ESD diodes (D602, D603; 0.6 x 1.0 x
0.4 mm) and the TPS7A0220 LDO (U203; 1 x 1 x 0.4 mm). At 0.4 mm tall they sit well under the 1.1 mm
the shell leaves over the top side.

Sand the panel tab nubs off the board's long edges before fitting (see the board README).
