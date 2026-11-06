"""Cell and LRA placed in the board's STEP frame (KiCad x, -y; F.Cu side up,
B.Cu at z = 0), under B.Cu with a 0.2 mm gap, with leads routed to their
hand-solder pads on B.  usage: make_placed.py OUT_DIR"""
import math
import sys
from pathlib import Path
from build123d import Axis, Compound, export_step
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_models as mm  # noqa: E402

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

B_SURF = 0.0          # B.Cu face of the board in kicad-cli's STEP
GAP = 0.2             # B.Cu has no parts: cell and LRA sit 0.2 mm off it
Z0 = B_SURF - GAP     # their board-side face
CELL_C = (115.5, -107.5)
LRA_C = (128.75, -107.5)
LRA_TAB = 60.0        # lead tab towards TP501 (KiCad (131.7, 101.5))
TP201, TP202 = (129.0, -113.5), (125.3, -101.6)   # BAT+, BAT- (on B)
TP501, TP502 = (131.7, -101.5), (131.9, -113.5)   # LRA+, LRA- (on B)


def flip_place(shape, c, turn=0.0):
    """Local part frame (board-side face at z = 0, part along +z) to the
    board's STEP frame under B.Cu: turn about z, half turn about x, move."""
    return shape.rotate(Axis.Z, turn).rotate(Axis.X, 180).translate((c[0], c[1], Z0))


def local_to_world(p, c, turn=0.0):
    a = math.radians(turn)
    x, y, z = p
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (c[0] + x, c[1] - y, Z0 - z)


def keep(parts, label, name):
    c = Compound(children=parts)
    c.label = label
    export_step(c, str(out / name))
    bb = c.bounding_box()
    print(name, [round(v, 3) for v in bb.min], [round(v, 3) for v in bb.max])


def labelled(shapes, src):
    for s, o in zip(shapes, src):
        s.label, s.color = o.label, o.color
    return shapes


# cell: centre (115.5, 107.5) in KiCad, lead end at x = 124
src = mm.cell(stubs=False)
cell = labelled([flip_place(p, CELL_C) for p in src], src)
zc = Z0 - mm.CELL_T / 2
zw = B_SURF - mm.WIRE_D / 2          # wire centre when it lies on a B pad
red = mm.wire([(123.6, -112.6, zc), (128.1, -112.6, zc), (TP201[0], TP201[1], zc),
               (TP201[0], TP201[1], zw)], mm.WIRE_D, "BAT+ lead to TP201 (red)", mm.RED)
blk = mm.wire([(123.6, -102.3, zc), (TP202[0], -102.3, zc), (TP202[0], TP202[1], zc),
               (TP202[0], TP202[1], zw)], mm.WIRE_D, "BAT- lead to TP202 (black)", mm.WIRE_BLACK)
keep(cell + [red, blk], "LiPo 60 mAh (placed)", "wakeband-cell-60mah-placed.step")

# LRA: centre (128.75, 107.5), lead tab turned towards TP501
src = mm.lra(stubs=False)
turn = -LRA_TAB       # the half turn about x mirrors the angle
lra = labelled([flip_place(p, LRA_C, turn) for p in src], src)
r = 0.1         # LRA leads: thin enamelled wire, 0.2 mm modelled
tip_p = local_to_world((mm.LRA_D / 2 + 1.9, 0.5, 0.5), LRA_C, turn)
tip_n = local_to_world((mm.LRA_D / 2 + 1.9, -0.5, 0.5), LRA_C, turn)
pos = mm.wire([tip_p, (TP501[0], TP501[1], tip_p[2]), (TP501[0], TP501[1], B_SURF - r)],
              2 * r, "LRA+ lead to TP501 (red)", mm.RED)
# LRA-: round the far side of the can at r = 4.15, mid height, to TP502
zm = Z0 - mm.LRA_H / 2
arc = [(LRA_C[0] + 4.15 * math.cos(math.radians(a)), LRA_C[1] + 4.15 * math.sin(math.radians(a)), zm)
       for a in range(48, -62, -10)]
neg = mm.wire([tip_n, (arc[0][0], arc[0][1], tip_n[2])] + arc +
              [(TP502[0], TP502[1], zm), (TP502[0], TP502[1], B_SURF - r)],
              2 * r, "LRA- lead to TP502 (black)", mm.WIRE_BLACK)
keep(lra + [pos, neg], "VG0832012 LRA (placed)", "wakeband-lra-vg0832012-placed.step")
