"""WakeBand case rev A for the rigid rev A board (parts side out): an outer
shell over F.Cu and a wrist cover holding the cell and the LRA, joined by a
stepped lip all round, two press-fit pins at the antenna end and one M2
countersunk screw into a heat-set insert at the LRA end.

Design frame: x and y are KiCad board coordinates, z = 0 is the wrist face
and +z points away from the wrist. Stack: wrist cover floor, cell and LRA,
0.2 mm gap, board (B.Cu at BOARD_B, F.Cu up), parts, shell top.
The finished parts are mirrored in y (y_step = -y_kicad) so they line up
with the board's KiCad STEP export lifted by BOARD_B:
    (x, y, z)_out = (x, y, z + BOARD_B)_step

usage (needs `pip install build123d`):
    python case_rev_a.py OUT_DIR [BOARD_STEP CELL_STEP LRA_STEP]
Writes wakeband-case-rev-a-{shell,cover}.{step,stl}. With the three STEP
files (KiCad STEP coordinates) it also runs the clash check.
"""
import math
import sys
from pathlib import Path

from build123d import (Align, Axis, Box, Circle, Color, Cone, Cylinder, Kind,
                       Plane, Polygon, Pos, RectangleRounded, Rot, SlotOverall, chamfer,
                       export_step, export_stl, extrude, fillet, import_step,
                       mirror, offset)

# ------------------------------------------------------------------ inputs
BOARD = (100.0, 133.0, 100.0, 115.0)  # Edge.Cuts
BOARD_R = 1.0
BOARD_T = 0.8
CLR = 0.15
CELL_MAX, FOAM, GAP = 5.0, 0.5, 0.2
F_PARTS = 1.1                         # tallest F part (DNP SW201 left out)
CELL_ENV = (107.0, 124.0, 100.75, 114.25)
LRA_C, LRA_R, LRA_H = (128.75, 107.5), 4.0, 3.25
LRA_ENV_R = 4.25                      # Ø8.5 envelope incl. the lead round the can
DOCK_X = [121.75 + 2.0 * i for i in range(6)]
DOCK_Y = 101.6
WIN_D = 1.2                           # dock windows (pads are Ø1.4)

WALL = 2.0          # side walls: lip 0.95 + 0.15 + skirt 0.9
LIP_W = 0.95        # cover lip (inner part of the wall)
LIP_H = 0.7         # how far the cover lip rises into the shell
END_A = 3.6         # antenna end wall: holds the two press-fit pins
ROOF = 1.2
FLOOR = 1.0
LEDGE = 0.5         # cover ledge under the board edge (B side)

BOARD_B = FLOOR + FOAM + CELL_MAX + GAP          # 6.7  B.Cu face = split
BOARD_F = BOARD_B + BOARD_T                      # 7.5
ROOF_IN = BOARD_F + F_PARTS + 0.2                # 8.8
TOP = ROOF_IN + ROOF                             # 10.0
Z_SKIRT = BOARD_B - LIP_H                        # 6.0  shell skirt bottom
PART_FACE = BOARD_B - GAP                        # 6.5  cell/LRA board-side face

CAV = (BOARD[0] - CLR, BOARD[1] + CLR, BOARD[2] - CLR, BOARD[3] + CLR)
X_A = CAV[0] - END_A                             # 97.05
SCREW = (136.6, 107.5)
BOSS_R, BOSS_Z0 = 2.8, 3.5                       # shell boss reaches down to z 3.5
INSERT_D, INSERT_DEPTH = 3.2, 4.0                # M2 x 3 heat-set insert
X_E = SCREW[0] + BOSS_R + 0.15 + 1.5             # 141.05
Y0, Y1 = CAV[2] - WALL, CAV[3] + WALL
YC = (Y0 + Y1) / 2
CORNER = 3.0

STRAP_W, STRAP_T = 16.0, 2.0
SLOT_L, SLOT_W = STRAP_W + 0.6, STRAP_T + 0.2
BAR = 2.4
LUG_W = SLOT_L + 2 * 1.9
LUG_L = SLOT_W + BAR
LUG_H = 3.0

# dock land: solid from the shell top down onto F.Cu round the pad row
LAND = (119.8, CAV[1], CAV[2], 103.2)
# antenna end: two press-fit pins from the shell skirt into the cover's end wall
PIN_D, PIN_L = 1.4, 2.0
PIN_X = X_A + 1.25                               # middle of the skirt (X_A .. X_A + 2.5)
PIN_Y = (102.5, 112.5)


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def rrect(x0, x1, y0, y1, r):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2) * RectangleRounded(x1 - x0, y1 - y0, r)


def slab(face, z0, z1):
    return Pos(0, 0, z0) * extrude(face, z1 - z0)


def cyl(cx, cy, r, z0, z1):
    return Pos(cx, cy, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def prism_xz(pts, y0, y1):
    return extrude(Plane.XZ.offset(-y0) * Polygon(*pts, align=None), y1 - y0, dir=(0, 1, 0))


def sector(cx, cy, r0, r1, a0, a1, z0, z1):
    ring = cyl(cx, cy, r1, z0, z1) - cyl(cx, cy, r0, z0 - 1, z1 + 1)
    pts = [(cx, cy)] + [(cx + 2 * r1 * math.cos(math.radians(a)), cy + 2 * r1 * math.sin(math.radians(a)))
                        for a in [a0 + (a1 - a0) * i / 8 for i in range(9)]]
    return ring & slab(Polygon(*pts, align=None), z0 - 1, z1 + 1)


def bb_hit(a, b):
    p, q = a.bounding_box(), b.bounding_box()
    return all(getattr(p.min, i) < getattr(q.max, i) and getattr(q.min, i) < getattr(p.max, i) for i in "XYZ")


def soften(solid, z, first, second, label):
    """45 deg chamfer on the outer loop at height z, then a round between the
    chamfer and the wall: nothing overhangs past 45 deg."""
    loop = solid.edges().filter_by_position(Axis.Z, z - 1e-3, z + 1e-3)
    out = chamfer(loop, first)
    z2 = z + first if z == 0 else z - first
    if second:
        try:
            out = fillet(out.edges().filter_by_position(Axis.Z, z2 - 1e-3, z2 + 1e-3), second)
        except Exception as exc:
            print(f"{label}: round {second} failed ({exc}); chamfer only")
    return out


BODY = rrect(X_A, X_E, Y0, Y1, CORNER)
POCKET = rrect(*CAV, BOARD_R + CLR)                       # board pocket in the shell
LIP_OUT = offset(POCKET, LIP_W, kind=Kind.ARC)            # outside of the cover lip
SKIRT_IN = offset(POCKET, LIP_W + CLR, kind=Kind.ARC)     # inside of the shell skirt


# ------------------------------------------------------------------ shell
def make_shell():
    s = slab(BODY, Z_SKIRT, TOP)
    s = soften(s, TOP, 1.0, 1.5, "shell top edge")
    s = chamfer(s.edges().filter_by_position(Axis.Z, Z_SKIRT - 1e-3, Z_SKIRT + 1e-3), 0.3)
    s -= slab(SKIRT_IN, Z_SKIRT - 1, BOARD_B)             # room for the cover lip
    s -= slab(POCKET, BOARD_B - 1, ROOF_IN)               # board and parts
    # dock land onto F.Cu (0.05 mm press) and the six windows
    s += box(*LAND, BOARD_F - 0.05, ROOF_IN + 0.1) & slab(POCKET, 0, TOP)
    for x in DOCK_X:
        s -= cyl(x, DOCK_Y, WIN_D / 2, BOARD_F - 1, TOP + 1)
        s -= Pos(x, DOCK_Y, TOP - 0.2) * Cone(WIN_D / 2, WIN_D / 2 + 0.2, 0.2,
                                               align=(Align.CENTER, Align.CENTER, Align.MIN))
    # posts onto F.Cu in the antenna keep-out strip (no copper or parts there)
    for y0, y1 in ((101.1, 103.2), (111.8, 113.9)):
        s += box(CAV[0] + 0.3, BOARD[0] + 0.95, y0, y1, BOARD_F, ROOF_IN + 0.1)
    # antenna end: two press-fit pins down into the cover's end wall
    for y in PIN_Y:
        s += cyl(PIN_X, y, PIN_D / 2, Z_SKIRT - PIN_L, Z_SKIRT + 0.01)
        s = chamfer(s.edges().filter_by_position(Axis.Z, Z_SKIRT - PIN_L - 1e-3, Z_SKIRT - PIN_L + 1e-3).filter_by_position(
            Axis.Y, y - PIN_D, y + PIN_D), 0.2)
    # LRA end: screw boss down into the cover, heat-set insert from below
    s += cyl(*SCREW, BOSS_R, BOSS_Z0, Z_SKIRT + 0.01)
    s -= cyl(*SCREW, INSERT_D / 2, BOSS_Z0 - 1, BOSS_Z0 + INSERT_DEPTH)
    return s


# ------------------------------------------------------------------ cover
def make_cover():
    lugs = [rrect(X_A - LUG_L - 0.1, X_A + 1.0, YC - LUG_W / 2, YC + LUG_W / 2, 2.0),
            rrect(X_E - 1.0, X_E + LUG_L + 0.1, YC - LUG_W / 2, YC + LUG_W / 2, 2.0)]
    outline = offset(offset(BODY + lugs[0] + lugs[1], 1.5, kind=Kind.ARC), -1.5, kind=Kind.ARC)
    # base: the whole outline (body and strap loops) up to LUG_H, wrist edge
    # softened, top edge rounded, strap slots cut
    base = slab(outline, 0, LUG_H)
    base = soften(base, 0, 0.8, 2.0, "wrist edge")
    try:
        base = fillet(base.edges().filter_by_position(Axis.Z, LUG_H - 1e-3, LUG_H + 1e-3), 0.8)
    except Exception as exc:
        print(f"loop top round failed ({exc})")
    for x0 in (X_A - SLOT_W, X_E):
        slot = Pos(x0 + SLOT_W / 2, YC) * Rot(0, 0, 90) * SlotOverall(SLOT_L, SLOT_W)
        base -= slab(slot, -1, LUG_H + 1)
        for z, d, op in ((0, 0.4, chamfer), (LUG_H, 0.4, fillet)):
            ring = [e for e in base.edges().filter_by_position(Axis.Z, z - 1e-3, z + 1e-3)
                    if x0 - 1e-3 <= e.center().X <= x0 + SLOT_W + 1e-3
                    and YC - SLOT_L / 2 - 0.01 <= e.center().Y <= YC + SLOT_L / 2 + 0.01]
            try:
                base = op(ring, d)
            except Exception:
                try:  # bed side: a 0.3 mm round if the chamfer won't build
                    base = fillet(ring, 0.3)
                except Exception as exc:
                    print(f"slot edge z={z}: {exc}")
    # body above the loops: 0.01 mm inside the outline, overlapping the base by
    # 1.2 mm so it fills the base's top round along the body
    upper = slab(offset(BODY, -0.01, kind=Kind.ARC), LUG_H - 1.2, Z_SKIRT)
    upper = chamfer(upper.edges().filter_by_position(Axis.Z, Z_SKIRT - 1e-3, Z_SKIRT + 1e-3), 0.3)
    c = base.fuse(upper)
    c += slab(LIP_OUT - POCKET, Z_SKIRT - 0.01, BOARD_B)
    # cavity: cell, LRA (with its lead) and the lead pads; a LEDGE under the board edge
    inner = rrect(BOARD[0] + LEDGE, BOARD[1] - LEDGE, BOARD[2] + LEDGE, BOARD[3] - LEDGE, 0.5)
    lra_c = Pos(*LRA_C) * Circle(LRA_ENV_R + CLR)
    c -= slab(inner + lra_c, FLOOR, BOARD_B + 1)
    # cell seat: side ribs and an end stop (envelope x 107-124, y 100.75-114.25)
    c += box(109.0, 121.0, BOARD[2] + LEDGE - 0.01, CELL_ENV[2] - CLR, FLOOR, FLOOR + 2.0)
    c += box(109.0, 121.0, CELL_ENV[3] + CLR, BOARD[3] - LEDGE + 0.01, FLOOR, FLOOR + 2.0)
    c += box(105.6, 106.8, 102.0, 113.0, FLOOR, FLOOR + 1.5)
    # LRA: pedestal to its adhesive face and two locating arcs (angles in the
    # KiCad frame): clear of the lead tab (300 deg), the lead round the can
    # (300 to 62 deg), the cell's PCM end (145 to 215 deg) and the BAT+ lead
    c += cyl(*LRA_C, LRA_R, FLOOR, PART_FACE - LRA_H)
    for a0, a1 in ((110, 145), (215, 280)):
        c += sector(*LRA_C, LRA_R + CLR, LRA_R + 0.95, a0, a1, FLOOR, PART_FACE - LRA_H + 1.35)
    # antenna end: holes for the shell's press-fit pins (0.05 mm interference)
    for y in PIN_Y:
        c -= cyl(PIN_X, y, PIN_D / 2 - 0.05, Z_SKIRT - PIN_L - 0.3, Z_SKIRT + 1)
    # screw: pocket for the shell boss, clearance hole, countersink 0.2 mm below flush
    c -= cyl(*SCREW, BOSS_R + CLR, BOSS_Z0 - 0.15, Z_SKIRT + 1)
    c -= cyl(*SCREW, 1.2, -1, BOSS_Z0)
    c -= cyl(*SCREW, 2.2, -1, 0.2)
    c -= Pos(*SCREW, 0.2) * Cone(2.2, 1.2, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c


def to_step_frame(shape):
    """Design frame (KiCad y) to the output frame (STEP y = -KiCad y)."""
    return mirror(shape, about=Plane.XZ)


def assembly_in_design_frame(paths):
    """Board, cell and LRA STEPs (KiCad STEP frame) moved into the design frame."""
    out = []
    for f in paths:
        for s in import_step(f).solids():
            s2 = mirror(s.translate((0, 0, BOARD_B)), about=Plane.XZ)
            bb = s2.bounding_box()
            # SW201 is DNP: leave it out (it is in the board STEP)
            if 126.0 < bb.min.X < 127.0 and 111.5 < bb.min.Y < 112.5 and bb.max.Z > BOARD_F + 1.2:
                continue
            out.append((s2, Path(f).stem))
    return out


def clash(parts, asm):
    hits = []
    for name, part in parts:
        for s, src in asm:
            if not bb_hit(part, s):
                continue
            r = part & s
            v = r.volume if r is not None else 0
            if v > 1e-4:
                bb = s.bounding_box()
                hits.append((name, src, round(v, 4), [round(t, 2) for t in bb.min], [round(t, 2) for t in bb.max]))
    return hits


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    print(f"z: B.Cu {BOARD_B:.2f}, F.Cu {BOARD_F:.2f}, roof inside {ROOF_IN:.2f}, top {TOP:.2f}")
    shell, cover = make_shell(), make_cover()
    for part, name in ((shell, "shell"), (cover, "cover")):
        assert len(part.solids()) == 1 and part.is_valid, f"{name}: {len(part.solids())} solids, valid {part.is_valid}"
        bb = part.bounding_box()
        print(f"{name}: valid {part.is_valid}, volume {part.volume:.0f} mm3, "
              f"bbox {[round(v, 2) for v in bb.min]} .. {[round(v, 2) for v in bb.max]}")
    ov = shell & cover
    print("shell vs cover overlap:", round(ov.volume if ov is not None else 0, 4))
    for part, name, col in ((shell, "shell", Color(0.20, 0.22, 0.25)), (cover, "cover", Color(0.55, 0.60, 0.65))):
        p = to_step_frame(part)
        p.label, p.color = ("case shell" if name == "shell" else "case wrist cover"), col
        export_step(p, str(out / f"wakeband-case-rev-a-{name}.step"))
        export_stl(p, str(out / f"wakeband-case-rev-a-{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    if len(sys.argv) > 4:
        asm = assembly_in_design_frame(sys.argv[2:5])
        hits = clash((("shell", shell), ("cover", cover)), asm)
        print(f"clash check: {len(asm)} assembly solids (SW201 left out), {len(hits)} overlaps")
        for h in hits:
            print("  ", h)
