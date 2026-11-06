"""WakeBand rigid rev A: parametric 3D models for parts with no KiCad model.

Footprint models (U1, D602-D605) use KiCad's model frame: origin at the
footprint origin, z = 0 on the board surface, +Y = KiCad -Y.
Cell and LRA use their own frame: origin at the centre of the face that
sits towards the board, the part extending along +Z.

usage: python make_models.py OUT_DIR
"""
import sys
from pathlib import Path
from build123d import (Box, Cylinder, Sphere, Compound, Color, Pos, Rot, Align,
                       fillet, chamfer, Axis, export_step, Vector)

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
MIN = (Align.CENTER, Align.CENTER, Align.MIN)

BLACK = Color(0.10, 0.10, 0.10)
DARKGREY = Color(0.22, 0.22, 0.24)
GREEN = Color(0.10, 0.35, 0.18)
GOLD = Color(0.85, 0.68, 0.30)
SILVER = Color(0.78, 0.79, 0.80)
TIN = Color(0.70, 0.72, 0.74)
WHITE = Color(0.92, 0.92, 0.92)
KAPTON = Color(0.90, 0.62, 0.10)
RED = Color(0.80, 0.08, 0.06)
WIRE_BLACK = Color(0.06, 0.06, 0.06)
FOAM = Color(0.25, 0.25, 0.28)


def part(shape, name, color):
    shape.label = name
    shape.color = color
    return shape


def save(children, name, label):
    c = Compound(children=children)
    c.label = label
    export_step(c, str(OUT / name))
    bb = c.bounding_box()
    print(f"{name}: {len(children)} bodies, bbox {bb.min} .. {bb.max}")


def wire(points, d, name, color):
    """A round wire along a polyline: cylinders with spheres at the joints."""
    r = d / 2
    pieces = []
    pts = [Vector(*p) for p in points]
    for a, b in zip(pts, pts[1:]):
        v = b - a
        L = v.length
        cyl = Cylinder(r, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # turn +Z onto v
        z = Vector(0, 0, 1)
        axis = z.cross(v)
        if axis.length > 1e-9:
            import math
            ang = math.degrees(math.acos(max(-1, min(1, z.dot(v) / L))))
            cyl = cyl.rotate(Axis((0, 0, 0), axis.normalized()), ang)
        elif v.Z < 0:
            cyl = cyl.rotate(Axis.X, 180)
        pieces.append(cyl.translate(a))
    for p in pts[1:-1]:
        pieces.append(Sphere(r).translate(p))
    w = pieces[0]
    for p in pieces[1:]:
        w = w.fuse(p)
    return part(w.clean(), name, color)


# ---------------------------------------------------------------- U1
# Insight SiP ISP2454: 8 x 8 x 1.0 mm LGA module (footprint descr; datasheet
# not on disk). Substrate plus overmould, pin-1 dot at KiCad (-3.475,-3.475),
# i.e. model (-x, +y).
def isp2454():
    sub_t, total = 0.30, 1.00
    sub = Box(8.0, 8.0, sub_t, align=MIN)
    mould = Box(7.9, 7.9, total - sub_t, align=MIN).translate((0, 0, sub_t))
    mould = fillet(mould.edges().filter_by(Axis.Z), 0.15)
    dot_r, dot_d = 0.25, 0.04
    dot = Cylinder(dot_r, dot_d, align=MIN).translate((-3.1, 3.1, total - dot_d))
    mould = mould - dot
    pin1 = Cylinder(dot_r, dot_d, align=MIN).translate((-3.1, 3.1, total - dot_d))
    save([part(sub, "ISP2454 substrate", GREEN),
          part(mould, "ISP2454 overmould", DARKGREY),
          part(pin1, "ISP2454 pin 1 mark", WHITE)],
         "InsightSiP_ISP2454_LGA-62_8x8mm.step", "ISP2454")


# ---------------------------------------------------------------- D60x
# TI DPY0002A (X1SON-2): 1.0 x 0.6 mm, 0.375 mm tall (KiCad footprint descr,
# TI MPSS034C). Bottom terminals at x = +/-0.35; pin 1 at -x, marked by a
# light band on top.
def dpy0002a():
    h = 0.375
    term_w, term_l, term_t = 0.45, 0.25, 0.02
    body = Box(1.0, 0.6, h - term_t, align=MIN).translate((0, 0, term_t))
    t1 = Box(term_l, term_w, term_t, align=MIN).translate((-0.35, 0, 0))
    t2 = Box(term_l, term_w, term_t, align=MIN).translate((0.35, 0, 0))
    band = Box(0.12, 0.6, 0.005, align=MIN).translate((-0.38, 0, h - 0.005))
    body = body - band
    save([part(body, "DPY0002A body", BLACK),
          part(t1, "DPY0002A pin 1", TIN),
          part(t2, "DPY0002A pin 2", TIN),
          part(band, "DPY0002A pin 1 band", WHITE)],
         "Texas_DPY0002A_0.6x1mm_P0.65mm.step", "DPY0002A")


# ---------------------------------------------------------------- cell
# 3.7 V 60 mAh protected LiPo, 401215 class: pouch about 14 x 13 x 4 mm plus
# a folded PCM at one end, 17 x 13.5 mm envelope. Lead end at +X. Two short
# wire stubs (red +, black -) leave the PCM end; the JST-PH plug is cut off
# because the cell is hand-soldered to TP201/TP202.
CELL_L, CELL_W, CELL_T = 17.0, 13.0, 4.0
PCM_L = 2.6
STUB = 2.0
WIRE_D = 0.8


def cell(stubs=True):
    pouch_l = CELL_L - PCM_L
    pouch = Box(pouch_l, CELL_W, CELL_T, align=MIN)
    pouch = fillet(pouch.edges().filter_by(Axis.X), 0.6)
    pouch = pouch.translate((-CELL_L / 2 + pouch_l / 2, 0, 0))
    # sealed flange where the tabs leave the pouch, then the PCM folded on it
    pcm = Box(PCM_L, CELL_W - 0.6, 2.6, align=MIN)
    pcm = pcm.translate((CELL_L / 2 - PCM_L / 2, 0, (CELL_T - 2.6) / 2))
    parts = [part(pouch, "LiPo pouch", SILVER),
             part(pcm, "LiPo PCM (Kapton wrapped)", KAPTON)]
    if stubs:
        z = CELL_T / 2
        x0 = CELL_L / 2
        for y, nm, col in ((3.0, "BAT+ lead (red)", RED),
                           (1.6, "BAT- lead (black)", WIRE_BLACK)):
            parts.append(wire([(x0 - 0.3, y, z), (x0 + STUB, y, z)], WIRE_D, nm, col))
    return parts


# ---------------------------------------------------------------- LRA
# Vybronics VG0832012: Ø8.0 x 3.25 mm coin LRA, wire leads. Can with a
# Ø6 adhesive pad on the far face, a small lead-exit tab at +X.
LRA_D, LRA_H = 8.0, 3.25


def lra(stubs=True):
    can = Cylinder(LRA_D / 2, LRA_H - 0.1, align=MIN)
    can = chamfer(can.edges(), 0.2)
    pad = Cylinder(3.0, 0.1, align=MIN).translate((0, 0, LRA_H - 0.1))
    tab = Box(1.6, 2.0, 0.4, align=MIN).translate((LRA_D / 2 + 0.3, 0, 0.3))
    parts = [part(can, "LRA can", SILVER), part(pad, "LRA adhesive pad", FOAM),
             part(tab, "LRA lead exit", BLACK)]
    if stubs:
        for y, nm, col in ((0.5, "LRA+ lead (red)", RED),
                           (-0.5, "LRA- lead (black)", WIRE_BLACK)):
            parts.append(wire([(LRA_D / 2 + 0.6, y, 0.5),
                               (LRA_D / 2 + 0.6 + STUB, y, 0.5)], 0.3, nm, col))
    return parts


if __name__ == "__main__":
    isp2454()
    dpy0002a()
    save(cell(), "LiPo_3.7V_60mAh_401215_PCM.step", "LiPo 60 mAh")
    save(lra(), "Vybronics_VG0832012_LRA_D8x3.25mm.step", "VG0832012")
