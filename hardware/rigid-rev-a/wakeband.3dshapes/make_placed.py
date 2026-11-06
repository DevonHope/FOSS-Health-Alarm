"""Cell and LRA placed in the board's STEP frame (KiCad x, -y; F.Cu side up),
with leads routed to their hand-solder pads.  usage: make_placed.py OUT_DIR"""
import sys
from pathlib import Path
from build123d import Compound, Location, export_step
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_models as mm  # noqa: E402

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

F_SURF = 0.796          # top of F.Cu parts' seat in kicad-cli's STEP
Z0 = F_SURF + 1.1 + 0.2  # tallest F part 1.1 mm + 0.2 mm gap
PAD = F_SURF


def placed(parts, loc):
    return [p.moved(loc) for p in parts]


def keep(parts, label, extra, name):
    c = Compound(children=parts + extra)
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
cell = labelled(placed(src, Location((115.5, -107.5, Z0))), src)
zc = Z0 + mm.CELL_T / 2
red = mm.wire([(123.6, -103.0, zc + 0.6), (125.75, -103.0, zc + 0.6),
               (125.75, -101.6, zc + 0.6), (125.75, -101.6, PAD + 0.4)],
              mm.WIRE_D, "BAT+ lead to TP201 (red)", mm.RED)
blk = mm.wire([(123.6, -105.0, Z0 + 0.4), (124.5, -105.0, Z0 + 0.4),
               (124.5, -102.5, Z0 + 0.4), (128.86, -102.5, Z0 + 0.4),
               (128.86, -101.6, Z0 + 0.4), (128.86, -101.6, PAD + 0.4)],
              mm.WIRE_D, "BAT- lead to TP202 (black)", mm.WIRE_BLACK)
keep(cell, "LiPo 60 mAh (placed)", [red, blk], "wakeband-cell-60mah-placed.step")

# LRA: centre (128.75, 107.5), lead tab turned 60 deg towards TP501
src = mm.lra(stubs=False)
lra = labelled(placed(src, Location((128.75, -107.5, Z0), (0, 0, 60))), src)
zl = Z0 + 0.5
r = 0.15
p = mm.wire([(131.27, -102.14, zl), (131.7, -101.5, zl), (131.7, -101.5, PAD + r)],
            0.3, "LRA+ lead to TP501 (red)", mm.RED)
n = mm.wire([(132.13, -102.64, zl), (132.6, -103.2, zl), (132.6, -103.2, 1.9),
             (132.6, -113.0, 1.9), (131.9, -113.5, 1.9), (131.9, -113.5, PAD + r)],
            0.3, "LRA- lead to TP502 (black)", mm.WIRE_BLACK)
keep(lra, "VG0832012 LRA (placed)", [p, n], "wakeband-lra-vg0832012-placed.step")
