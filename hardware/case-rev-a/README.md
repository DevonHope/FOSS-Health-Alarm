# WakeBand case rev A

Two printed parts for the [rigid rev A board](../rigid-rev-a/README.md), held
together by one M2 screw.

| Part | File | Size (x, y, z) |
| --- | --- | --- |
| Outer shell (over B.Cu) | `wakeband-case-rev-a-shell.step` / `.stl` | 42.65 x 18.3 x 6.8 mm |
| Wrist cover with strap loops | `wakeband-case-rev-a-cover.step` / `.stl` | 52.05 x 20.4 x 3.0 mm (inner features to 7.75) |
| Assembled | | **42.65 x 18.3 x 9.8 mm** body, 52.05 x 20.4 mm with the strap loops |

![iso](wakeband-case-rev-a-preview-iso.png)
![wrist face](wakeband-case-rev-a-preview-wrist.png)

`case_rev_a.py` (build123d) makes both parts. From this folder:

    pip install build123d
    python case_rev_a.py OUT_DIR ../../path/to/wakeband-rigid-rev-a-full.step \
        wakeband-cell-60mah-placed.step wakeband-lra-vg0832012-placed.step

The board and part STEP files are optional. When given (see
`../rigid-rev-a/wakeband.3dshapes/make_placed.py`), the script also checks
the case against the board, cell and LRA for clashes.

## Orientation as worn

Coordinates are KiCad board coordinates in x and y, z = 0 is the wrist face.

| Layer | z (mm) |
| --- | --- |
| shell roof, outer face (dock windows) | 9.8 |
| B.Cu against the roof | 8.6 |
| F.Cu, parts face down | 7.8 |
| cell and LRA, 0.2 mm below the tallest F part | 6.5 |
| room for a cell up to 5.0 mm plus 0.5 mm foam | 1.0 |
| wrist face | 0 |

The cell and the LRA stay on the F side. The six dock pads (J601) are on B
at y = 113, x 111.25-123.75, inside the cell's outline, so B must face out to
the dock. The cell leads land on F pads, and the LRA sits next to the wrist.

## Parts and features

- **Shell.** Covers B.Cu except six Ø1.6 mm windows over the dock pads, with
  a 0.2 mm lead-in for the pogo pins. Round each window, a rim stands 0.1 mm
  proud of the roof and presses on the solder mask. The board sits in a
  pocket with 0.15 mm clearance, and eight small ribs (0.03 mm clear) stop it
  rattling. The LRA end holds the M2 heat-set insert. The antenna end wall
  (2.0 mm) has the pocket for the cover's hook. Roof edge: 1.0 mm chamfer at
  45 deg with an R1.5 blend.
- **Wrist cover.** 1.0 mm floor. Wrist edge: 0.8 mm chamfer at 45 deg with an
  R2 blend, and an R0.5 round on the seam. It also carries:
  - **Antenna end:** a tongue with a hook that drops into the shell's pocket,
    and two posts that hold the board's F face in the keep-out strip
    (x 100-101.15, which has no copper or parts).
  - **LRA end:** a column and ledge that hold the board edge (x 132.3-133).
  - **Screw:** an ISO 10642 countersink, with the head 0.2 mm below flush.
  - **Cell:** side ribs and an end stop.
  - **LRA:** a pedestal for its adhesive face, plus three locating arcs.
  - **Strap:** loops at both ends, 16.6 x 2.2 mm slots for a **16 mm**
    strap up to 2 mm thick (velcro or fabric). The slots are rounded on the
    loop side and chamfered on the wrist side.
- No metal near the antenna. The screw and insert sit at x = 137, past the
  board's LRA end; the ISP2454 keep-out is x 100-105.

## Hardware

| Item | Spec |
| --- | --- |
| Screw | M2 x 6 countersunk, ISO 10642 / DIN 7991, A2 stainless |
| Insert | M2 brass heat-set insert, 3.0 mm long, for a Ø3.2 mm hole (e.g. Ruthex RX-M2x3) |
| Self-tapping option | set `INSERT_D = 1.6` and use an M2 x 6 countersunk screw straight into the plastic (fine for a few openings) |
| Foam | 1.5 mm foam tape under a 4 mm cell, 0.5 mm under a 5 mm cell |
| Strap | 16 mm velcro or fabric strap, up to 2 mm thick |

## Printing

| Setting | Value |
| --- | --- |
| Material | PETG (or ASA). PLA creeps at skin temperature |
| Nozzle / layer | 0.4 mm / 0.12-0.16 mm |
| Walls | 4 perimeters (all side walls are 1.5 mm, other walls at least 1.2 mm) |
| Top / bottom | 6 layers |
| Infill | 100 % (the parts are small) |
| Supports | none |
| Shell orientation | roof (outer face with the windows) down on the bed |
| Cover orientation | wrist face down on the bed |

Every bed-side edge is a 45 deg chamfer with the round above it, so no
overhang is past 45 deg. The two overhangs that are left are the hook (45 deg
underside) and the pocket it fits in (45 deg roof). The Ø1.6 mm dock windows
print slightly small: open them with a 1.6 mm drill.

## Assembly

1. Press the insert into the shell's boss from the open side with a
   soldering iron at about 230 C, flush with the split face.
2. Solder the cell to TP201 (+) and TP202 (-), and the LRA to TP501 / TP502.
3. Drop the board into the shell, B side first, so the dock pads line up
   with the windows. For a sweat seal, run a thin bead of silicone round the
   window rims first, or conformal-coat B.Cu apart from the six pads (README
   compromise 6).
4. Stick the LRA's adhesive face onto the cover's pedestal, inside the three
   arcs, with its lead tab towards TP501. Put the foam tape in the cell bay.
5. Hook the cover's tongue into the antenna end pocket, then swing the LRA
   end down so the column slides into its slot.
6. Fit the screw from the wrist side. Stop when it's snug.
7. Thread the strap through both loops.

## Checks (2026-11-06)

- **Clash check:** against the board STEP (all 35 part models), the cell,
  the LRA and their leads. No overlaps, except the intended 0.1 mm press of
  the six window rims into the board. The shell and the cover don't overlap.
- **Wall thickness:** sampled by rays from about 6000 surface points per
  part. Structural walls are 1.2 mm or more, the floor 1.0 mm, the roof
  1.2 mm. Thinner, on purpose: the webs between dock windows (0.9 mm), the
  window rims, the hook tip, the LRA arcs (0.8 mm), the cell side ribs
  (0.7 mm) and the board ledge.

## Compromises

1. **Bigger than the README budget** (about 35 x 17 x 8-9 mm). The body is
   42.65 x 18.3 x 9.8 mm because of:
   - walls of 1.5 mm and roof/floor of 1.2/1.0 mm, instead of 0.8 mm;
   - room for a 5 mm cell plus foam (`CELL_MAX = 4.0` makes it 8.8 mm tall);
   - the screw block and board column past the LRA end (+7.5 mm);
   - the 2.0 mm antenna end wall that holds the hook pocket.
2. **The strap loops** add 4.6 mm at each end, and are 20.4 mm wide (the body
   is 18.3) because a 16 mm strap needs a 16.6 mm slot. Each loop hangs on two
   short necks (about 0.85 mm plus the corner rounds, 3 mm tall). That is fine
   for a velcro strap. Pull-test a print.
3. **A printed case is not waterproof.** The window rims only press on the
   solder mask. Seal with silicone or conformal coat (step 3).
4. **The cover must flex slightly** for the hook to engage. Check the fit on
   the first print; the hook depth (0.7 mm) is a parameter.
5. **The LRA end support is small** (1.0 mm column, 0.6 mm ledge), because
   the LRA reaches x = 132.75 and the board ends at 133.
