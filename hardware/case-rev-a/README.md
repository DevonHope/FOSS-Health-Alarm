# WakeBand case rev A

Two printed parts for the [rigid rev A board](../rigid-rev-a/README.md),
joined by a stepped ridge all round and held by one M2 screw. Since the
2026-11-06 board rework the board mounts **parts side out**:

- the **shell** covers F.Cu, with the parts and the six dock pads;
- the **wrist cover** holds the cell and the LRA under B.Cu.

| Part | File | Size (x, y, z) |
| --- | --- | --- |
| Outer shell | `wakeband-case-rev-a-shell.step` / `.stl` | 44.8 x 19.3 x 4.0 mm, plus the screw boss down to z 3.5 |
| Wrist cover with strap loops | `wakeband-case-rev-a-cover.step` / `.stl` | 54.2 x 20.4 x 6.7 mm |
| Assembled | | **44.8 x 19.3 x 10.0 mm** body, 54.2 x 20.4 mm with the strap loops |

![iso](wakeband-case-rev-a-preview-iso.png)
![outer face](wakeband-case-rev-a-preview-top.png)
![wrist face](wakeband-case-rev-a-preview-wrist.png)

`case_rev_a.py` (build123d) makes both parts. From this folder:

    pip install build123d
    python case_rev_a.py OUT_DIR BOARD_STEP CELL_STEP LRA_STEP

The three STEP files are optional. Pass them to also check the case for
clashes against the board, the cell and the LRA. Use the board's KiCad STEP
export, plus the cell and LRA files from
`../rigid-rev-a/wakeband.3dshapes/make_placed.py`.

The script designs in KiCad x/y with z = 0 at the wrist face. It then
mirrors y, so the parts land on the board's STEP export lifted by
z = 6.7 mm.

## Stack as worn

| Layer | z (mm) |
| --- | --- |
| shell top, outer face (dock windows) | 10.0 |
| inside of the shell top (F parts up to 1.1 mm, plus 0.2 mm) | 8.8 |
| F.Cu, parts up | 7.5 |
| B.Cu, the split between shell and cover | 6.7 |
| cell and LRA, 0.2 mm below B.Cu | 6.5 |
| room for a cell up to 5.0 mm, plus 0.5 mm foam | 1.0 |
| wrist face | 0 |

## Openings

Only the necessary ones:

1. **Six dock windows**, Ø1.2 mm, with a 0.2 mm lead-in, over the dock pads
   J601 (pads Ø1.4 mm, 2.0 mm pitch, y = 101.6, x 121.75-131.75). Round the
   row, the shell is solid all the way down onto the board (the dock land).
   It presses 0.05 mm on the solder mask, so each window is closed off from
   the parts. The pogo pins reach 2.5 mm down through the shell top.
2. **The screw hole** in the wrist face. It is countersunk, and the head
   sits 0.2 mm below flush.

The strap slots go through the strap loops only, outside the closed body.

## Joint (the ridge)

All round the parting line, the inner 0.95 mm of the cover wall stands
0.7 mm proud. It fits inside a 0.9 mm skirt on the shell with 0.15 mm
clearance, so the two halves slot together and can't slide sideways.

Below the ridge, a 0.5 mm ledge on the cover holds the board's B side at its
edge. The dock land and two posts in the antenna keep-out strip press on the
F side. Together they clamp the board.

## Fixing

- **One M2 x 6 countersunk screw** (ISO 10642 / DIN 7991, A2 stainless),
  from the wrist face at the LRA end (x = 136.6).
- It goes into a **brass M2 heat-set insert**, 3.0 mm long, in a Ø3.2 mm
  hole (for example Ruthex RX-M2x3). The insert sits in a Ø5.6 mm boss that
  hangs down from the shell into a pocket in the cover.
- **Self-tapping option:** set `INSERT_D = 1.6` and use an M2 x 6
  countersunk screw straight into the boss.
- **Antenna end:** two printed **press-fit pins** (Ø1.4 x 2.0 mm, 0.05 mm
  interference) go from the shell's skirt into the cover's end wall. This
  is the only metal-free way to hold that end: the ISP2454 keep-out is
  x 100-105, and the screw and insert sit 30 mm away from it.
- **When worn,** the strap pulls the cover onto the wrist and the shell
  presses down onto it, so the joint stays closed.

## Hardware

| Item | Spec |
| --- | --- |
| Screw | M2 x 6 countersunk, ISO 10642 / DIN 7991, A2 stainless |
| Insert | M2 brass heat-set insert, 3.0 mm long, Ø3.2 mm hole |
| Foam | foam tape under the cell: 1.5 mm for a 4 mm cell, 0.5 mm for a 5 mm cell |
| Kapton | one layer over B.Cu under the cell and LRA (board README, compromise 6) |
| Strap | 16 mm velcro or fabric strap, up to 2 mm thick |

## Printing

| Setting | Value |
| --- | --- |
| Material | PETG (or ASA). PLA creeps at skin temperature |
| Nozzle / layer | 0.4 mm / 0.12-0.16 mm |
| Walls | 4 perimeters (side walls 2.0 mm, top 1.2 mm, floor 1.0 mm) |
| Infill | 100 % |
| Supports | none |
| Shell | outer face (top) down on the bed |
| Cover | wrist face down on the bed |

Every edge that sits on the bed has a 45-degree chamfer with a round above
it. Nothing overhangs more than 45 degrees, and nothing needs a bridge. The
Ø1.2 mm dock windows print slightly small: open them with a 1.2 mm drill.
The two pins print standing up on the shell, so print them at 100 % infill.

## Assembly

1. Press the insert into the shell's boss from below with a soldering
   iron at about 230 C, flush with the end of the boss.
2. Solder the cell to TP201 (+) and TP202 (-), and the LRA to TP501 (+) and
   TP502 (-). All four pads are on B. Put kapton over B.Cu.
3. Optional: run a thin bead of silicone round the six windows on the
   inside of the shell top. Then lay the board in the shell, parts first.
4. Stick the LRA's adhesive face onto the cover's pedestal between the two
   arcs, lead tab towards TP501. Put foam tape in the cell bay.
5. Lower the cover straight onto the shell. The ridge locates it, and the
   two pins press into the cover's end wall.
6. Fit the screw from the wrist side and stop when it's snug.
7. Thread the strap through both loops.

## Checks (2026-11-06)

- **Clash check** against the board STEP (all part models except SW201,
  which is DNP), the cell, the LRA and their leads: no overlaps.
- **Shell against cover:** the only overlap is the intended 0.05 mm press
  fit of the two pins (0.77 mm³).
- **Wall thickness**, sampled by rays from several thousand surface points
  per part:
  - shell: top and land at least 1.0 mm; the ridge skirt 0.9 mm (0.6 mm at
    its edge chamfer); window webs 0.8 mm; boss wall 1.2 mm;
  - cover: floor 1.0 mm; the ridge lip and the board ledge 0.5 mm; about
    0.6 mm round the pin holes (0.33 mm at the seam chamfer); 0.5 mm web
    between the LRA bay and the screw-boss pocket; LRA arcs 0.5-0.8 mm.
- **Assembly path:** the cover lowered straight onto the shell touches
  nothing but the two pins, over their last 1.9 mm.
- Both parts are single, valid solids, and SolidCraft imports them as
  closed bodies.

## Compromises

1. **Bigger than the README budget** of about 35 x 17 x 9 mm. The body is
   44.8 x 19.3 x 10.0 mm because of:
   - 2.0 mm side walls, which carry the ridge;
   - room for a 5 mm cell plus foam (`CELL_MAX = 4.0` makes it 9.0 mm tall);
   - 0.2 mm clearances over the F parts and under B;
   - the screw boss past the LRA end;
   - the 3.6 mm antenna end wall that holds the pins.
2. **The pogo pins reach through 2.5 mm** of shell to the dock pads.
   Making that shallower needs a pocket in the outer face, which prints as
   a bridge.
3. **The antenna end is held by friction pins.** A tilt-in hook, as in the
   first version of this case, doesn't fit now that the board sits right at
   the joint. If the end gaps when the band is off the wrist, the next step
   is a second screw or a snap arm.
4. **A printed case is not waterproof.** Seal the windows with silicone or
   conformal coat, as in assembly step 3.
5. **SW201 (DNP) must not be fitted:** at 1.6 mm it is taller than the
   1.1 mm the shell allows for.
6. **The strap loops are wider than the body** (20.4 mm against 19.3 mm),
   because a 16 mm strap needs a 16.6 mm slot.
