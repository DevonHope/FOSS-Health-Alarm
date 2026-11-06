"""WakeBand case rev A for the rigid rev A board: an outer shell and a wrist
cover, held by one M2 countersunk screw into a heat-set insert.

Frame ("worn"): x and y are KiCad board coordinates, z = 0 is the wrist face
and +z points away from the wrist. The board sits B.Cu up against the shell
roof (dock pads J601 under six windows), F.Cu down, with the cell and the
LRA between the board and the wrist cover. The board's KiCad STEP export maps
into this frame by a half turn about X and a lift of BOARD_B:
    (x, y, z)_worn = (x, -y, BOARD_B - z)_step

usage (needs `pip install build123d`):
    python case_rev_a.py OUT_DIR [ASSEMBLY_STEP ...]
Writes wakeband-case-rev-a-{shell,cover}.{step,stl}. With assembly STEP
files (board, cell, LRA, in KiCad STEP coordinates) it also runs a clash
check and writes the worn assembly with the case.
"""
import math
import sys
from pathlib import Path

from build123d import (Align, Axis, Box, Color, Compound, Cone, Cylinder, Kind,
                       Location, Plane, Polygon, Pos, RectangleRounded, chamfer,
                       export_step, export_stl, extrude, fillet, import_step,
                       offset)

# ------------------------------------------------------------------ inputs
BOARD = (100.0, 133.0, 100.0, 115.0)  # x0, x1, y0, y1 (Edge.Cuts)
BOARD_R = 1.0                         # board corner radius
BOARD_T = 0.8
CLR = 0.15                            # clearance board / cell / LRA
CELL_MAX = 5.0                        # thickest cell the cover takes
FOAM = 0.5                            # foam tape under the cell
F_GAP = 1.1 + 0.2                     # tallest F part + gap: cell/LRA face
LRA_C, LRA_R, LRA_H = (128.75, 107.5), 4.0, 3.25
DOCK_X = [111.25 + 2.5 * i for i in range(6)]
DOCK_Y = 113.0

WALL = 1.5        # side walls (3+ perimeters at 0.4 mm)
END_A = 2.0       # antenna end wall (holds the hook pocket)
ROOF = 1.2        # over B.Cu
FLOOR = 1.0       # wrist cover floor
SPLIT = 3.0       # height of the wrist cover

# derived heights
BOARD_B = FLOOR + FOAM + CELL_MAX + F_GAP + BOARD_T     # B.Cu face, 8.6
BOARD_F = BOARD_B - BOARD_T                             # F.Cu face, 7.8
PART_FACE = BOARD_F - F_GAP                             # cell/LRA top, 6.5
TOP = BOARD_B + ROOF                                    # 9.8

# outline
CAV = (BOARD[0] - CLR, BOARD[1] + CLR, BOARD[2] - CLR, BOARD[3] + CLR)
X_A = CAV[0] - END_A                                    # antenna end, 97.85
SCREW = (137.0, 107.5)
INSERT_D, INSERT_DEPTH = 3.2, 4.0                       # M2 x 3 heat-set insert
X_E = 140.5                                             # LRA end
Y0, Y1 = CAV[2] - WALL, CAV[3] + WALL
CORNER = 3.0

STRAP_W, STRAP_T = 16.0, 2.0
SLOT_L, SLOT_W = STRAP_W + 0.6, STRAP_T + 0.2           # 16.6 x 2.2
BAR = 2.4
LUG_W = SLOT_L + 2 * 1.9                                # 20.4
LUG_L = SLOT_W + BAR                                    # 4.6
YC = (Y0 + Y1) / 2


def bb_hit(a, b):
    """True when the bounding boxes of a and b share any volume."""
    p, q = a.bounding_box(), b.bounding_box()
    return all(getattr(p.min, i) < getattr(q.max, i) and getattr(q.min, i) < getattr(p.max, i)
               for i in "XYZ")


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def rrect(x0, x1, y0, y1, r):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2) * RectangleRounded(x1 - x0, y1 - y0, r)


def cyl(cx, cy, r, z0, z1):
    return Pos(cx, cy, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def prism_xz(pts, y0, y1):
    """A polygon drawn in (x, z), extruded from y0 to y1."""
    return extrude(Plane.XZ.offset(-y0) * Polygon(*pts, align=None), y1 - y0, dir=(0, 1, 0))


def sector(cx, cy, r0, r1, a0, a1, z0, z1):
    ring = cyl(cx, cy, r1, z0, z1) - cyl(cx, cy, r0, z0 - 1, z1 + 1)
    pts = [(cx, cy)] + [(cx + 2 * r1 * math.cos(math.radians(a)),
                         cy + 2 * r1 * math.sin(math.radians(a)))
                        for a in [a0 + (a1 - a0) * i / 8 for i in range(9)]]
    wedge = extrude(Pos(0, 0, z0 - 1) * Polygon(*pts, align=None), z1 - z0 + 2)
    return ring & wedge


def soften(solid, z, first, second, label):
    """Chamfer the outer loop at height z, then fillet the new edge between
    the chamfer and the wall: a profile with no overhang past 45 deg."""
    loop = solid.edges().filter_by_position(Axis.Z, z - 1e-3, z + 1e-3)
    out = chamfer(loop, first)
    z2 = z + first if z == 0 else z - first
    if second:
        try:
            e2 = out.edges().filter_by_position(Axis.Z, z2 - 1e-3, z2 + 1e-3)
            out = fillet(e2, second)
        except Exception as exc:  # keep the chamfer if OCC can't fillet
            print(f"{label}: fillet {second} failed ({exc}); chamfer only")
    return out


# ------------------------------------------------------------------ shell
def make_shell():
    body = rrect(X_A, X_E, Y0, Y1, CORNER)
    s = Pos(0, 0, SPLIT) * extrude(body, TOP - SPLIT)
    s = soften(s, TOP, 1.0, 1.5, "shell roof edge")
    s = chamfer(s.edges().filter_by_position(Axis.Z, SPLIT - 1e-3, SPLIT + 1e-3), 0.3)
    # board / parts cavity, open towards the wrist cover
    cav = rrect(*CAV, BOARD_R + CLR)
    s -= Pos(0, 0, SPLIT - 1) * extrude(cav, BOARD_B - SPLIT + 1)
    # slot for the cover's board-support column at the LRA end
    s -= box(133.0, 134.2, 104.9, 110.1, SPLIT - 1, BOARD_F + 0.1)
    # heat-set insert hole
    s -= cyl(*SCREW, INSERT_D / 2, SPLIT - 1, SPLIT + INSERT_DEPTH)
    # hook pocket in the antenna end wall; its wrist-side face slopes 45 deg
    s -= prism_xz([(CAV[0] + 0.1, 3.9), (CAV[0] - 0.8, 4.8), (CAV[0] - 0.8, 5.3),
                   (CAV[0] + 0.1, 5.3)], 102.0, 113.0)
    # dock windows the size of the pads (0.9 mm webs at 2.5 mm pitch), with a
    # 0.2 mm lead-in for the pogo pins on the outside
    for x in DOCK_X:
        s -= cyl(x, DOCK_Y, 0.8, BOARD_B - 1, TOP + 1)
        s -= Pos(x, DOCK_Y, TOP - 0.2) * Cone(0.8, 1.0, 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # sealing rim around each window: 0.1 mm proud of the roof, presses on
    # the solder mask round the pads (the rims merge into one strip)
    for x in DOCK_X:
        s += cyl(x, DOCK_Y, 1.5, BOARD_B - 0.1, BOARD_B)
    for x in DOCK_X:
        s -= cyl(x, DOCK_Y, 0.8, BOARD_B - 1, BOARD_B + 1)
    # anti-rattle ribs at the board edge (0.03 mm clear of the board)
    for (x, y) in [(CAV[0] - 0.08, 104.0), (CAV[0] - 0.08, 111.0), (CAV[1] + 0.08, 102.5),
                   (CAV[1] + 0.08, 112.5), (112.0, CAV[2] - 0.08), (124.0, CAV[2] - 0.08),
                   (112.0, CAV[3] + 0.08), (124.0, CAV[3] + 0.08)]:
        s += cyl(x, y, 0.2, BOARD_F - 0.05, BOARD_B)
    return s


# ------------------------------------------------------------------ cover
def make_cover():
    body = rrect(X_A, X_E, Y0, Y1, CORNER)
    lugs = [rrect(X_A - LUG_L - 0.1, X_A + 1.0, YC - LUG_W / 2, YC + LUG_W / 2, 2.0),
            rrect(X_E - 1.0, X_E + LUG_L + 0.1, YC - LUG_W / 2, YC + LUG_W / 2, 2.0)]
    outline = body + lugs[0] + lugs[1]
    outline = offset(offset(outline, 1.5, kind=Kind.ARC), -1.5, kind=Kind.ARC)  # round the inside corners
    c = extrude(outline, SPLIT)
    c = soften(c, 0, 0.8, 2.0, "cover wrist edge")
    try:
        c = fillet(c.edges().filter_by_position(Axis.Z, SPLIT - 1e-3, SPLIT + 1e-3), 0.5)
    except Exception as exc:
        print(f"cover top edge: fillet failed ({exc})")
    # strap slots (rounded ends), softened on both faces
    for x0 in (X_A - SLOT_W, X_E):
        slot = rrect(x0, x0 + SLOT_W, YC - SLOT_L / 2, YC + SLOT_L / 2, SLOT_W / 2 - 0.01)
        c -= Pos(0, 0, -1) * extrude(slot, SPLIT + 2)
        for z, d in ((0, 0.4), (SPLIT, 0.6)):
            ring = c.edges().filter_by_position(Axis.Z, z - 1e-3, z + 1e-3).filter_by_position(
                Axis.X, x0 - 1e-3, x0 + SLOT_W + 1e-3)
            ring = [e for e in ring if YC - SLOT_L / 2 - 0.01 <= e.center().Y <= YC + SLOT_L / 2 + 0.01]
            try:
                c = chamfer(ring, d) if z == 0 else fillet(ring, d)
            except Exception as exc:
                print(f"slot edge at z={z}: {exc}")
    # tray for the cell and the LRA
    cav = rrect(*CAV, BOARD_R + CLR)
    c -= Pos(0, 0, FLOOR) * extrude(cav, SPLIT)
    # cell seat: side ribs and an end stop (cell envelope x 107-124, y 100.75-114.25)
    c += box(109.0, 121.0, CAV[2], 100.55, FLOOR, SPLIT)
    c += box(109.0, 121.0, 114.45, CAV[3], FLOOR, SPLIT)
    c += box(105.6, 106.8, 102.0, 113.0, FLOOR, FLOOR + 1.5)
    # LRA: pedestal to its adhesive face and three locating arcs
    c += cyl(*LRA_C, LRA_R, FLOOR, PART_FACE - LRA_H)
    for a0, a1 in ((35, 80), (100, 140), (-140, -100)):
        c += sector(*LRA_C, LRA_R + CLR, LRA_R + 0.95, a0, a1, FLOOR, PART_FACE - LRA_H + 1.35)
    # antenna end: tongue with a hook, and two posts up to the board's F face
    # (x 100-101.15 is in the antenna keep-out: no copper or parts there)
    c += box(CAV[0], CAV[0] + 0.1, 101.1, 113.9, FLOOR, SPLIT)
    c += box(CAV[0] + 0.1, CAV[0] + 1.3, 101.1, 113.9, FLOOR, 6.6)
    c += box(CAV[0] + 0.1, CAV[0] + 1.3, 101.1, 103.2, 6.6, BOARD_F - 0.05)
    c += box(CAV[0] + 0.1, CAV[0] + 1.3, 111.8, 113.9, 6.6, BOARD_F - 0.05)
    c += prism_xz([(CAV[0] + 0.1, 4.4), (CAV[0] - 0.6, 5.1), (CAV[0] - 0.6, 5.2),
                   (CAV[0] + 0.1, 5.2)], 102.5, 112.5)
    # LRA end: column beside the board edge with a ledge under it (45 deg underside)
    c += box(132.9, 133.9, 105.0, 110.0, FLOOR, BOARD_F - 0.05)
    c += prism_xz([(132.9, 6.4), (132.3, 7.0), (132.3, BOARD_F - 0.05), (132.9, BOARD_F - 0.05)],
                  105.0, 110.0)
    # screw: clearance hole, countersink for an ISO 10642 M2 head, 0.2 mm below flush
    c -= cyl(*SCREW, 1.2, -1, SPLIT + 1)
    c -= cyl(*SCREW, 2.2, -1, 0.2)
    c -= Pos(*SCREW, 0.2) * Cone(2.2, 1.2, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c


def worn(shape):
    return shape.moved(Location((0, 0, BOARD_B), (180, 0, 0)))


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    print(f"heights: B.Cu {BOARD_B:.3f}, F.Cu {BOARD_F:.3f}, part face {PART_FACE:.3f}, top {TOP:.2f}")
    shell, cover = make_shell(), make_cover()
    shell.label, shell.color = "case shell", Color(0.20, 0.22, 0.25)
    cover.label, cover.color = "case wrist cover", Color(0.55, 0.60, 0.65)
    for part, name in ((shell, "shell"), (cover, "cover")):
        bb = part.bounding_box()
        assert len(part.solids()) == 1, f"{name} is {len(part.solids())} solids"
        print(f"{name}: valid {part.is_valid}, volume {part.volume:.0f} mm3, "
              f"bbox {[round(v, 2) for v in bb.min]} .. {[round(v, 2) for v in bb.max]}")
        export_step(part, str(out / f"wakeband-case-rev-a-{name}.step"))
        export_stl(part, str(out / f"wakeband-case-rev-a-{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    if len(sys.argv) > 2:
        asm = []
        for f in sys.argv[2:]:
            c = worn(import_step(f))
            asm += [(s, Path(f).stem) for s in c.solids()]
        hits = []
        for part, name in ((shell, "shell"), (cover, "cover")):
            for s, src in asm:
                if not bb_hit(part, s):
                    continue
                r = part & s
                v = r.volume if r is not None else 0
                if v > 1e-4:
                    hits.append((name, src, s.label, round(v, 4), [round(t, 2) for t in s.bounding_box().min]))
        r = shell & cover
        v = r.volume if r is not None else 0
        if v > 1e-4:
            hits.append(("shell", "cover", "", round(v, 4), []))
        print(f"clash check: {len(asm)} assembly solids, {len(hits)} overlaps")
        for h in hits:
            print("  ", h)
