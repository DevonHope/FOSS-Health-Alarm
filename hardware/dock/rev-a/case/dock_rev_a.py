"""WakeBand dock rev A: a printed puck the band sits on wrist side down.

Four Mill-Max 0906-4 spring pins on the dock PCB (../pcb) press on the tails
of the band's four contact pins (seen through cone windows in the wrist
cover); two Ø3 x 1 mm N52 magnets under a 0.2 mm skin pull the band's two
cover magnets in, with opposite poles so the band only seats one way round.
USB-C at the +y side; the two status LEDs and the BOOTSEL button are
reached through holes in the top margin.

Two printed parts, both printed flat on their underside with no bridges:
  - top plate: band recess, plunger guide bores, magnet pockets (open below),
    LED light holes, BOOTSEL poke hole, strap channels;
  - tray: PCB pocket with support pads and corner stops, USB-C opening,
    a 0.8 mm rim that locates the top plate.

Design frame: the band's worn frame from ../../../band/rev-a/case/case_rev_a.py (KiCad
x/y, z = 0 at the wrist face); the dock lies under the band (z < 0).
usage (needs `pip install build123d`): python dock_rev_a.py OUT_DIR
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "band" / "rev-a" / "case"))
import case_rev_a as case  # noqa: E402
from build123d import Color, Kind, Plane, export_step, export_stl, mirror, offset  # noqa: E402

# band outline at the wrist face (body + strap loops), as in make_cover()
LUGS = [case.rrect(case.X_A - case.LUG_L - 0.1, case.X_A + 1.0, case.YC - case.LUG_W / 2, case.YC + case.LUG_W / 2, 2.0),
        case.rrect(case.X_E - 1.0, case.X_E + case.LUG_L + 0.1, case.YC - case.LUG_W / 2, case.YC + case.LUG_W / 2, 2.0)]
BAND = offset(offset(case.BODY + LUGS[0] + LUGS[1], 1.5, kind=Kind.ARC), -1.5, kind=Kind.ARC)

REC_D, REC_CLR = 1.5, 0.3          # locating recess: depth, clearance round the band
TOP = REC_D                        # top of the dock (recess rim)
DOCK = (88.5, 148.8, 94.5, 125.6)  # dock outline (x0, x1, y0, y1)
DOCK_R = 4.0
RIM, RIM_H, RIM_CLR = 0.8, 0.8, 0.15
PCB = (100.0, 140.0, 97.5, 124.0)  # dock PCB (../pcb/dock-pcb-rev-a.kicad_pcb), same x/y as the band
PCB_T = 1.6
# Mill-Max 0906-4: A = 5.99 mm flange underside to free tip, stroke 1.40 (mid 0.70),
# barrel top 2.69 mm above the flange underside; plunger Ø1.07, body Ø1.50, flange Ø1.83, tail 1.75
SP_A, SP_BODY_L, SP_TAIL = 5.99, 2.69, 1.75
TAIL_TIP = case.CARRIER_Z + case.CARRIER_T - case.SP_TAIL      # band contact tails (z 0.55)
PCB_TOP = TAIL_TIP + 0.70 - SP_A                               # flange seat: mid stroke when docked
PCB_BOT = PCB_TOP - PCB_T
PLATE_Z0 = -1.3                    # underside of the top plate = ceiling of the parts cavity
FLOOR_T, GAP_UNDER = 1.6, 0.3      # tray floor, gap under the PCB (pin tails)
TRAY_Z0 = PCB_BOT - GAP_UNDER - FLOOR_T
WALL = 1.6
MAG_SKIN = 0.2
STRAP_CH = ((91.0, 97.6), (140.4, 146.4))   # x ranges under the strap loops
STRAP_W, STRAP_D = 18.0, 2.6
USB = (108.0, 13.0, 123.9)        # x centre and width of the notch in front of USB-C, notch back face (J1 face ~ y 124.0)
LEDS = ((133.0, 122.6), (116.4, 122.8))            # D1 (USB), D2 (DAP running)
BOOTSEL = (122.2, 122.2)


def outline(inset, r=DOCK_R):
    return case.rrect(DOCK[0] + inset, DOCK[1] - inset, DOCK[2] + inset, DOCK[3] - inset, max(r - inset, 0.5))


def make_top():
    t = case.slab(outline(RIM + RIM_CLR), PLATE_Z0, TOP)
    t -= case.slab(offset(BAND, REC_CLR, kind=Kind.ARC), 0, TOP + 1)            # recess
    for x0, x1 in STRAP_CH:                                                      # strap channels
        t -= case.box(x0, x1, case.YC - STRAP_W / 2, case.YC + STRAP_W / 2, -STRAP_D, TOP + 1)
    for y in case.SP_Y:                                                          # plunger guide bores
        t -= case.cyl(case.SP_X, y, 0.75, PLATE_Z0 - 1, TOP + 1)
    for x, y in case.MAG_XY:                                                     # magnets, from below
        t -= case.cyl(x, y, case.MAG_POCKET_D / 2, PLATE_Z0 - 1, -MAG_SKIN)
    for x, y in LEDS:                                                            # light holes
        t -= case.cyl(x, y, 0.75, PLATE_Z0 - 1, TOP + 1)
    t -= case.cyl(*BOOTSEL, 0.9, PLATE_Z0 - 1, TOP + 1)                         # BOOTSEL poke hole
    ux, uw, uy = USB                                                             # notch: USB-C face flush
    t -= case.box(ux - uw / 2, ux + uw / 2, uy, DOCK[3] + 1, PLATE_Z0 - 1, TOP + 1)
    return t


def make_tray():
    t = case.slab(outline(0), TRAY_Z0, PLATE_Z0 + RIM_H)
    t -= case.slab(outline(RIM), PLATE_Z0, PLATE_Z0 + RIM_H + 1)               # rim round the top plate
    t -= case.slab(outline(WALL), TRAY_Z0 + FLOOR_T, PLATE_Z0 + 1)             # cavity
    for x, y in ((PCB[0] + 2, PCB[2] + 2), (PCB[1] - 2, PCB[2] + 2), (PCB[0] + 2, PCB[3] - 2), (PCB[1] - 2, PCB[3] - 2)):
        t += case.cyl(x, y, 1.2, TRAY_Z0 + FLOOR_T - 0.01, PCB_BOT)            # PCB support pads
    for x0, x1, y0, y1 in ((PCB[0] - 1.4, PCB[0] - 0.2, PCB[2] - 1.4, PCB[2] + 3), (PCB[1] + 0.2, PCB[1] + 1.4, PCB[2] - 1.4, PCB[2] + 3),
                           (PCB[0] - 1.4, PCB[0] - 0.2, PCB[3] - 3, PCB[3] + 0.2), (PCB[1] + 0.2, PCB[1] + 1.4, PCB[3] - 3, PCB[3] + 0.2)):
        t += case.box(x0, x1, y0, y1, TRAY_Z0 + FLOOR_T - 0.01, PCB_TOP + 0.6)  # PCB corner stops
    ux, uw, uy = USB                                                             # notch: USB-C face flush
    t -= case.box(ux - uw / 2, ux + uw / 2, uy, DOCK[3] + 1, TRAY_Z0 + FLOOR_T, PLATE_Z0 + RIM_H + 1)
    for x0, x1 in STRAP_CH:
        t -= case.box(x0, x1, case.YC - STRAP_W / 2, case.YC + STRAP_W / 2, -STRAP_D, PLATE_Z0 + RIM_H + 1)
    return t


def make_inside():
    """PCB slab, the four 0906-4 spring pins (compressed on the band tails), magnets."""
    pcb = case.box(*PCB, PCB_BOT, PCB_TOP)
    pins = None
    for y in case.SP_Y:
        p = (case.cyl(case.SP_X, y, 0.43 / 2, PCB_TOP - SP_TAIL, PCB_TOP)
             + case.cyl(case.SP_X, y, 1.83 / 2, PCB_TOP, PCB_TOP + 0.41)
             + case.cyl(case.SP_X, y, 1.50 / 2, PCB_TOP + 0.40, PCB_TOP + SP_BODY_L)
             + case.cyl(case.SP_X, y, 1.07 / 2, PCB_TOP + SP_BODY_L - 0.01, TAIL_TIP))
        pins = p if pins is None else pins + p
    mags = None
    for x, y in case.MAG_XY:
        m = case.cyl(x, y, case.MAG_D / 2, -MAG_SKIN - case.MAG_T - 0.02, -MAG_SKIN - 0.02)
        mags = m if mags is None else mags + m
    return pcb, pins, mags


def out_frame(s):
    return mirror(s, about=Plane.XZ)


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    print(f"PCB top z {PCB_TOP:.2f}, bottom {PCB_BOT:.2f}; band tails z {TAIL_TIP:.2f}; "
          f"dock pin compression {PCB_TOP + SP_A - TAIL_TIP:.2f} of 1.40")
    top, tray = make_top(), make_tray()
    pcb, pins, mags = make_inside()
    for name, s in (("top", top), ("tray", tray)):
        assert len(s.solids()) == 1 and s.is_valid, name
        bb = s.bounding_box()
        print(name, round(s.volume), [round(v, 2) for v in bb.min], [round(v, 2) for v in bb.max])
    cover = case.make_cover()
    for n, a in (("pcb", pcb), ("pins", pins), ("magnets", mags)):
        for m, b in (("top", top), ("tray", tray), ("band cover", cover)):
            r = a & b
            v = r.volume if r is not None else 0
            if v > 1e-4:
                print(f"  overlap {n} / {m}: {v:.4f} mm3")
    for m, b in (("top", top), ("tray", tray)):
        r = b & cover
        print(f"dock {m} vs band cover:", round(r.volume if r is not None else 0, 4))
    r = top & tray
    print("top vs tray:", round(r.volume if r is not None else 0, 4))
    for name, s, col in (("top", top, Color(0.15, 0.15, 0.17)), ("tray", tray, Color(0.3, 0.3, 0.32))):
        p = out_frame(s); p.label, p.color = f"dock {name}", col
        export_step(p, str(out / f"wakeband-dock-rev-a-{name}.step"))
        export_stl(p, str(out / f"wakeband-dock-rev-a-{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    for name, s, col in (("spring-pins", pins, Color(0.85, 0.68, 0.3)), ("magnets", mags, Color(0.6, 0.6, 0.65)),
                         ("pcb-envelope", pcb, Color(0.1, 0.4, 0.2))):
        p = out_frame(s); p.label, p.color = f"dock {name}", col
        export_step(p, str(out / f"wakeband-dock-rev-a-{name}.step"))
    print("dock height", round(TOP - TRAY_Z0, 2), "footprint", round(DOCK[1] - DOCK[0], 1), "x", round(DOCK[3] - DOCK[2], 1))
