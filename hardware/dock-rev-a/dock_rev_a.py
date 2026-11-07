"""WakeBand dock rev A (concept): a printed puck the band sits in face down.
Six spring pins on a small dock board touch the band's six flush gold
contacts; two Ø3 x 1 mm N52 magnets under a 0.2 mm skin pull the band's two
case magnets in, with opposite poles so the band only seats one way round.
USB-C power in at one end, a 6-pin programming/serial header at the other.

Design frame: the band's worn frame from ../case-rev-a/case_rev_a.py (KiCad
x/y, z = 0 at the wrist face, band top at z = 10.0). The dock sits on top of
the band there. Outputs:
  - *-assembly frame STEP (mirrored y like the case, docked on the band)
  - print STL/STEP turned over: base plate on the bed, recess up.

usage (needs `pip install build123d`): python dock_rev_a.py OUT_DIR
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "case-rev-a"))
import case_rev_a as case  # noqa: E402
from build123d import (Axis, Box, Color, Kind, Pos, export_step, export_stl,  # noqa: E402
                       fillet, mirror, offset, Plane)

TOP = case.TOP                     # band top face = contact plane
REC_D = 1.5                        # locating recess depth
REC_CLR = 0.3
MARGIN = 3.5                       # puck wall round the recess
SKIN = 0.4                         # recess floor over the spring pins
MAG_SKIN = 0.2
PIN_WORK = 2.24                    # Mill-Max 0965 recommended working height
PIN_EXT = 2.54                     # free height
PCB_T = 0.8
PCB = (113.0, 140.0, 98.4, 107.6)  # dock board outline (x0, x1, y0, y1)
PCB_Z = TOP + PIN_WORK             # dock board face (pin side)
USB = (8.94, 7.35, 3.26)           # USB-C receptacle body (w, d, h), at +x end
TOP_PART = PCB_Z + PCB_T + USB[2] + 0.8   # inside of the base plate
BASE_T = 1.6
H_END = TOP_PART + BASE_T          # outside of the base (table side)
LED_CH_W = 2.4                     # light channel under the band's charge LED
LED_CH_D = 1.0                     # its depth below the recess floor


def make_dock():
    shell_out = case.BODY
    rec = offset(shell_out, REC_CLR, kind=Kind.ARC)
    outline = offset(shell_out, REC_CLR + MARGIN, kind=Kind.ARC)
    d = case.slab(outline, TOP - REC_D, TOP_PART)
    d = fillet(d.edges().filter_by_position(Axis.Z, TOP - REC_D - 1e-3, TOP - REC_D + 1e-3), 1.0)
    d -= case.slab(rec, TOP - REC_D - 1, TOP)                     # locating recess
    # cavity for the dock board, its parts and the cables, open on the base side
    d -= case.box(PCB[0] - 0.3, PCB[1] + 0.3, PCB[2] - 0.3, PCB[3] + 0.3, TOP + SKIN, TOP_PART + 1)
    # spring-pin bores through the skin (plunger Ø1.07) and sleeve room below
    for x in case.DOCK_X:
        d -= case.cyl(x, case.DOCK_Y, 0.65, TOP - 1, TOP + SKIN + 0.01)
    # magnet pockets under a 0.2 mm skin, opened from the cavity side
    for x, y in case.MAG_XY:
        d -= case.cyl(x, y, case.MAG_POCKET_D / 2, TOP + MAG_SKIN, TOP + MAG_SKIN + case.MAG_POCKET_T + 0.4)
    # left magnet sits outside the board cavity: reach it with its own well
    lx, ly = case.MAG_XY[0]
    d -= case.cyl(lx, ly, case.MAG_POCKET_D / 2, TOP + MAG_SKIN, TOP_PART + 1)
    # USB-C slot through the +x wall, header slot through the -x wall
    ux = outline.bounding_box().max.X
    d -= case.box(PCB[1] - 1, ux + 1, (PCB[2] + PCB[3]) / 2 - 4.8, (PCB[2] + PCB[3]) / 2 + 4.8,
                  PCB_Z + PCB_T - 0.3, PCB_Z + PCB_T + USB[2] + 0.5)
    hx = outline.bounding_box().min.X
    d -= case.box(hx - 1, PCB[0] + 1, 101.0, 113.0, PCB_Z + PCB_T, TOP_PART + 1)
    d -= case.box(hx - 1, PCB[0] + 1, 101.0, 113.0, PCB_Z - 0.01, TOP_PART + 1) & case.box(hx - 1, PCB[0] + 1, 101.0, 113.0, 0, 99)
    # light channel: the band lies face down, so its charge LED faces the
    # recess floor. A groove under the LED, open through the side wall, lets
    # the glow out where it can be seen.
    lx, ly = case.LED_XY
    oy = outline.bounding_box().max.Y
    d -= case.box(lx - LED_CH_W / 2, lx + LED_CH_W / 2, ly - LED_CH_W / 2, oy + 1, TOP - REC_D - 1, TOP + LED_CH_D)
    # base plate (separate part)
    base = case.slab(offset(outline, -0.2, kind=Kind.ARC), TOP_PART, H_END)
    return d, base


def make_inside():
    """Dock board, six spring pins (mid-stroke, touching the band), USB-C, magnets."""
    pcb = case.box(*PCB, PCB_Z, PCB_Z + PCB_T)
    pins = None
    for x in case.DOCK_X:
        p = (case.cyl(x, case.DOCK_Y, 1.07 / 2, TOP, TOP + 0.71)
             + case.cyl(x, case.DOCK_Y, 1.63 / 2, TOP + 0.71, PCB_Z - 0.41)
             + case.cyl(x, case.DOCK_Y, 1.83 / 2, PCB_Z - 0.41, PCB_Z))
        pins = p if pins is None else pins + p
    usb = case.box(PCB[1] - USB[1], PCB[1] + 0.6, (PCB[2] + PCB[3]) / 2 - USB[0] / 2,
                   (PCB[2] + PCB[3]) / 2 + USB[0] / 2, PCB_Z + PCB_T, PCB_Z + PCB_T + USB[2])
    mags = None
    for x, y in case.MAG_XY:
        m = case.cyl(x, y, case.MAG_D / 2, TOP + MAG_SKIN + 0.02, TOP + MAG_SKIN + 0.02 + case.MAG_T)
        mags = m if mags is None else mags + m
    return pcb, pins, usb, mags


def out_frame(s):
    return mirror(s, about=Plane.XZ)


def print_frame(s):
    """Base plate on the bed, recess up."""
    return s.rotate(Axis.X, 180).translate((0, 0, H_END))


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    dock, base = make_dock()
    pcb, pins, usb, mags = make_inside()
    for name, s in (("dock", dock), ("base", base)):
        assert len(s.solids()) == 1 and s.is_valid, name
        bb = s.bounding_box()
        print(name, round(s.volume), [round(v, 2) for v in bb.min], [round(v, 2) for v in bb.max])
    # fit: inside parts vs dock body, and the dock vs the band's case and contacts
    shell, cover = case.make_shell(), case.make_cover()
    for n, a in (("pcb", pcb), ("pins", pins), ("usb", usb), ("magnets", mags)):
        for m, b in (("dock", dock), ("base", base), ("band shell", shell), ("band contacts", case.make_contacts())):
            r = a & b
            v = r.volume if r is not None else 0
            if v > 1e-4:
                print(f"  overlap {n} / {m}: {v:.4f} mm3")
    r = dock & shell
    print("dock vs band shell:", round(r.volume if r is not None else 0, 4))
    for name, s, col in (("dock", dock, Color(0.15, 0.15, 0.17)), ("base", base, Color(0.3, 0.3, 0.32))):
        p = out_frame(s); p.label, p.color = f"dock {name}", col
        export_step(p, str(out / f"wakeband-dock-rev-a-{name}.step"))
        export_stl(print_frame(out_frame(s)), str(out / f"wakeband-dock-rev-a-{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    for name, s, col in (("board", pcb, Color(0.1, 0.4, 0.2)), ("spring-pins", pins, Color(0.85, 0.68, 0.3)),
                         ("usb-c", usb, Color(0.75, 0.75, 0.78)), ("magnets", mags, Color(0.6, 0.6, 0.65))):
        p = out_frame(s); p.label, p.color = f"dock {name}", col
        export_step(p, str(out / f"wakeband-dock-rev-a-{name}.step"))
    print("dock height", round(H_END - (TOP - REC_D), 2), "footprint",
          [round(v, 1) for v in (dock.bounding_box().size.X, dock.bounding_box().size.Y)])
