"""WakeBand dock rev B: the rev A dock (../dock-rev-a) restyled for everyday use. Same dock PCB, spring
pin and magnet positions, USB-C opening, keyed magnets.

What changed from rev A:
  - outside: one smooth shape. Larger plan radius (7 mm), 1.2 mm round on the top edge, 2.2 mm
    shorter; the top plate now covers the whole outline and meets the tray on a hidden lip, so the only
    joint is a small shadow line on the side, 2.5 mm below the top; nothing on the top face.
  - strap: wider (18.6 mm) channels with rounded floors, rounded top lips, and a 3.5 mm rounded saddle at
    each end so the strap drapes down and out over the end instead of over a sharp edge. The channel
    floors are solid (end blocks in the tray), not open into the cavity as on rev A.
  - LEDs: shine through a 0.4 mm skin (no holes). BOOTSEL: no hole. The button faces up on the PCB,
    so it can't be reached from underneath, and a press-through skin would need ~1 mm of travel; flash
    the dock before fitting the top plate, and lift the plate (held by the lip, not glued) to re-flash.
  - magnets: Ø4 x 1.5 mm N52 (pockets Ø4.1 x 1.55, same 0.2 mm skin, same positions and polarity), to
    hold the band against the stocked 0906-4-...-75 spring pins (60 g each at mid-stroke).
  - underneath: four Ø8.2 x 0.6 mm recesses for Ø8 mm self-adhesive rubber feet; 0.5 mm chamfer on the
    bottom edge against elephant's foot.
  - recess: 0.3 mm shallower (1.2 mm) with a 0.4 mm lead-in chamfer.
Both parts print flat on their underside with no supports (top plate: underside down; tray: floor down).
Design frame as rev A (band worn frame, z = 0 at the wrist face, the dock below).
usage (needs build123d): python dock_rev_b.py OUT_DIR [DOCK_PCB_STEP]"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "case-rev-a"))
sys.path.insert(0, str(HERE.parent / "dock-rev-a"))
import case_rev_a as case  # noqa: E402
import dock_rev_a as A  # noqa: E402
from build123d import (Axis, Box, Color, Cylinder, Kind, Plane, Pos, Rot, chamfer, export_step, export_stl,  # noqa: E402
                       fillet, import_step, loft, mirror, offset)

REC_D = 1.2
TOP = REC_D
DOCK = (89.35, 147.95, 94.5, 125.6)         # 58.6 x 31.1 (rev A 60.3 x 31.1)
DOCK_R = 7.0
TOP_ROUND = 1.2
SEAM_CH = 0.35                               # shadow-line chamfer each side of the joint
LIP = (0.85, 1.65, 0.8)                      # tray locating lip: inset from, inset to, height
GROOVE = (0.7, 1.8, 0.9)                     # matching groove in the top plate
TRAY_Z0, PCB, PCB_TOP, PCB_BOT = A.TRAY_Z0, A.PCB, A.PCB_TOP, A.PCB_BOT
PLATE_Z0 = -2.05                             # flat underside, low enough to hold the Ø4 x 1.5 magnets (rev A -1.3)
FLOOR_T, WALL = A.FLOOR_T, A.WALL
STRAP_W, STRAP_D = 18.6, 2.6
CH_IN = (97.6, 140.4)                        # inner ends of the channels (under the strap loops), as rev A
SADDLE_R, CH_R, LIP_R = 3.5, 2.0, 1.0
END_BLOCK = (98.4, 141.6)                    # tray cavity filled outside these x (under the channels)
MAG_D, MAG_T, MAG_POCKET_D, MAG_POCKET_T, MAG_SKIN = 4.0, 1.5, 4.1, 1.55, 0.2
LED_SKIN, LED_POCKET_R = 0.4, 1.3
FEET = [(x, y) for x in (DOCK[0] + 7.0, DOCK[1] - 7.0) for y in (DOCK[2] + 6.0, DOCK[3] - 6.0)]
FOOT_D, FOOT_DEPTH = 8.2, 0.6
YC = case.YC


def outline(inset, r=DOCK_R):
    return case.rrect(DOCK[0] + inset, DOCK[1] - inset, DOCK[2] + inset, DOCK[3] - inset, max(r - inset, 0.5))


def ring(i0, i1, z0, z1):
    return case.slab(outline(i0), z0, z1) - case.slab(outline(i1), z0 - 1, z1 + 1)


def ycyl(x, z, r, y0, y1):
    """cylinder along y"""
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, y1 - y0)


def xcyl(y, z, r, x0, x1):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def strap_cutters():
    """channel (rounded floor corners), rounded top lips, rounded end saddle; both ends"""
    cuts = []
    y0, y1 = YC - STRAP_W / 2, YC + STRAP_W / 2
    for side in (0, 1):
        xe = DOCK[0] if side == 0 else DOCK[1]
        xa, xb = (xe - 1, CH_IN[0]) if side == 0 else (CH_IN[1], xe + 1)
        zf = -STRAP_D
        ch = case.box(xa, xb, y0 + CH_R, y1 - CH_R, zf, TOP + 1) + case.box(xa, xb, y0, y1, zf + CH_R, TOP + 1)
        for yy in (y0 + CH_R, y1 - CH_R):
            ch += xcyl(yy, zf + CH_R, CH_R, xa, xb)
        # rounded top lips along the channel sides (convex round of radius LIP_R)
        for yy, sgn in ((y0, -1), (y1, 1)):
            cut = case.box(xa, xb, yy + (0 if sgn > 0 else -LIP_R), yy + (LIP_R if sgn > 0 else 0), TOP - LIP_R, TOP + 1)
            cut -= xcyl(yy + sgn * LIP_R, TOP - LIP_R, LIP_R, xa - 1, xb + 1)
            ch += cut
        # end saddle: convex round where the channel floor meets the end face
        sx = 1 if side == 0 else -1
        c0 = xe + sx * SADDLE_R
        cut = case.box(min(xe - sx * 1, c0), max(xe - sx * 1, c0), y0, y1, zf - SADDLE_R, zf + 0.01)
        cut -= ycyl(c0, zf - SADDLE_R, SADDLE_R, y0 - 1, y1 + 1)
        ch += cut
        cuts.append(ch)
    return cuts[0] + cuts[1]


def make_top():
    t = case.slab(outline(0), PLATE_Z0, TOP)
    t = fillet(t.edges().group_by(Axis.Z)[-1], TOP_ROUND)
    t = chamfer(t.edges().group_by(Axis.Z)[0], SEAM_CH)
    t -= ring(GROOVE[0], GROOVE[1], PLATE_Z0 - 1, PLATE_Z0 + GROOVE[2])                  # hidden joint
    rec = offset(A.BAND, A.REC_CLR, kind=Kind.ARC)
    t -= case.slab(rec, 0, TOP + 1)                                                      # recess
    t -= loft([Pos(0, 0, TOP - 0.4) * rec, Pos(0, 0, TOP + 0.01) * offset(rec, 0.41, kind=Kind.ARC)])  # lead-in
    t -= strap_cutters()
    for y in case.SP_Y:                                                                  # plunger guide bores
        t -= case.cyl(case.SP_X, y, 0.75, PLATE_Z0 - 1, TOP + 1)
    for x, y in case.MAG_XY:                                                             # magnets, from below
        t -= case.cyl(x, y, MAG_POCKET_D / 2, -MAG_SKIN - MAG_POCKET_T - 1, -MAG_SKIN)
    for x, y in A.LEDS:                                                                  # LEDs: thin skin
        t -= case.cyl(x, y, LED_POCKET_R, PLATE_Z0 - 1, TOP - LED_SKIN)
    ux, uw, uy = A.USB                                                                   # USB-C notch
    t -= case.box(ux - uw / 2, ux + uw / 2, uy, DOCK[3] + 1, PLATE_Z0 - 1, TOP + 1)
    return t


def make_tray():
    t = case.slab(outline(0), TRAY_Z0, PLATE_Z0)
    t = chamfer(t.edges().group_by(Axis.Z)[0], 0.5)
    t = chamfer(t.edges().group_by(Axis.Z)[-1], SEAM_CH)
    t -= case.slab(outline(WALL), TRAY_Z0 + FLOOR_T, PLATE_Z0 + 1)                       # cavity
    t += ring(LIP[0], LIP[1], PLATE_Z0 - 0.01, PLATE_Z0 + LIP[2])                        # locating lip
    cav = case.slab(outline(WALL + 0.01), TRAY_Z0 + FLOOR_T - 0.01, PLATE_Z0)
    t += cav & (case.box(DOCK[0] - 1, END_BLOCK[0], DOCK[2] - 1, DOCK[3] + 1, TRAY_Z0, PLATE_Z0)
                + case.box(END_BLOCK[1], DOCK[1] + 1, DOCK[2] - 1, DOCK[3] + 1, TRAY_Z0, PLATE_Z0))  # solid ends
    for x, y in ((PCB[0] + 2, PCB[2] + 2), (PCB[1] - 2, PCB[2] + 2), (PCB[0] + 2, PCB[3] - 2), (PCB[1] - 2, PCB[3] - 2)):
        t += case.cyl(x, y, 1.2, TRAY_Z0 + FLOOR_T - 0.01, PCB_BOT)                       # PCB support pads
    for x0, x1, y0, y1 in ((PCB[0] - 1.4, PCB[0] - 0.2, PCB[2] - 1.4, PCB[2] + 3), (PCB[1] + 0.2, PCB[1] + 1.4, PCB[2] - 1.4, PCB[2] + 3),
                           (PCB[0] - 1.4, PCB[0] - 0.2, PCB[3] - 3, PCB[3] + 0.2), (PCB[1] + 0.2, PCB[1] + 1.4, PCB[3] - 3, PCB[3] + 0.2)):
        t += case.box(x0, x1, y0, y1, TRAY_Z0 + FLOOR_T - 0.01, PCB_TOP + 0.6)          # PCB corner stops
    ux, uw, uy = A.USB
    t -= case.box(ux - uw / 2, ux + uw / 2, uy, DOCK[3] + 1, TRAY_Z0 + FLOOR_T, PLATE_Z0 + LIP[2] + 1)
    t -= strap_cutters()
    for x, y in FEET:                                                                    # rubber-foot recesses
        t -= case.cyl(x, y, FOOT_D / 2, TRAY_Z0 - 1, TRAY_Z0 + FOOT_DEPTH)
    return t


def make_inside():
    pcb, pins, _ = A.make_inside()
    mags = None
    for x, y in case.MAG_XY:
        m = case.cyl(x, y, MAG_D / 2, -MAG_SKIN - MAG_T - 0.02, -MAG_SKIN - 0.02)
        mags = m if mags is None else mags + m
    return pcb, pins, mags


def strap_standin():
    """16 x 1.5 mm strap round the loop bars, lying in the channels and draping over the saddles"""
    y0, y1 = YC - 8, YC + 8
    s = None
    for side in (0, 1):
        xe = DOCK[0] if side == 0 else DOCK[1]
        sx = -1 if side == 0 else 1
        xi = CH_IN[0] + 1.0 if side == 0 else CH_IN[1] - 1.0
        flat = case.box(min(xi, xe), max(xi, xe), y0, y1, -STRAP_D + 0.05, -STRAP_D + 1.55)
        c0 = xe - sx * SADDLE_R
        drape = (Pos(c0, YC, -STRAP_D - SADDLE_R) * Rot(90, 0, 0) * Cylinder(SADDLE_R + 1.55, 16)) - \
                (Pos(c0, YC, -STRAP_D - SADDLE_R) * Rot(90, 0, 0) * Cylinder(SADDLE_R + 0.05, 17))
        drape &= case.box(min(c0, xe + sx * 5), max(c0, xe + sx * 5), y0, y1, -STRAP_D - SADDLE_R, -STRAP_D + 2)
        down = case.box(min(xe + sx * (0.05), xe + sx * 1.6), max(xe + sx * 0.05, xe + sx * 1.6), y0, y1, TRAY_Z0 - 4, -STRAP_D - SADDLE_R + 0.01)
        part = flat + drape + down
        s = part if s is None else s + part
    return s


def out_frame(s):
    return mirror(s, about=Plane.XZ)


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    top, tray = make_top(), make_tray()
    pcb, pins, mags = make_inside()
    ok = True
    for name, s in (("top", top), ("tray", tray)):
        good = len(s.solids()) == 1 and s.is_valid
        ok &= good
        bb = s.bounding_box()
        print(f"{name}: solids {len(s.solids())} valid {s.is_valid} volume {s.volume:.0f} mm3 "
              f"bbox {[round(v, 2) for v in bb.min]} {[round(v, 2) for v in bb.max]}")
    cover = case.make_cover()
    parts = [("pcb envelope", pcb), ("spring pins", pins), ("magnets", mags)]
    if len(sys.argv) > 2:                                   # dock PCB KiCad STEP: every part model
        board = import_step(sys.argv[2])
        board = mirror(board, about=Plane.XZ)               # KiCad STEP has y up
        board = Pos(0, 0, PCB_BOT) * board
        for i, s in enumerate(board.solids()):
            parts.append((f"pcb solid {i}", s))
    hits = []
    for n, a in parts:
        for m, b in (("top", top), ("tray", tray), ("band cover", cover)):
            if n == "pcb envelope" and m == "band cover":
                continue
            r = a & b
            v = r.volume if r is not None else 0
            if v > 1e-4:
                hits.append((n, m, round(v, 4)))
    for m, b in (("top", top), ("tray", tray)):
        r = b & cover
        v = r.volume if r is not None else 0
        if v > 1e-4:
            hits.append(("band cover", m, round(v, 4)))
    r = top & tray
    print("top vs tray overlap:", round(r.volume if r is not None else 0, 4))
    print(f"clash check: {len(parts)} parts against top, tray and band cover: {len(hits)} overlaps", hits[:8])
    print(f"pin compression {PCB_TOP + A.SP_A - A.TAIL_TIP:.2f} of 1.40 (mid-stroke 0.70); "
          f"magnet pocket z {-MAG_SKIN - MAG_POCKET_T:.2f} to {-MAG_SKIN}; plate underside {PLATE_Z0}")
    print("dock size", round(DOCK[1] - DOCK[0], 2), "x", round(DOCK[3] - DOCK[2], 2), "x", round(TOP - TRAY_Z0, 2))
    strap = strap_standin()
    for name, s, col in (("top", top, Color(0.92, 0.92, 0.9)), ("tray", tray, Color(0.35, 0.36, 0.38))):
        p = out_frame(s); p.label, p.color = f"dock rev B {name}", col
        export_step(p, str(out / f"wakeband-dock-rev-b-{name}.step"))
        export_stl(p, str(out / f"wakeband-dock-rev-b-{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    for name, s, col in (("magnets", mags, Color(0.6, 0.6, 0.65)), ("spring-pins", pins, Color(0.85, 0.68, 0.3)),
                         ("strap-standin", strap, Color(0.2, 0.25, 0.35))):
        p = out_frame(s); p.label, p.color = f"dock rev B {name}", col
        export_step(p, str(out / f"wakeband-dock-rev-b-{name}.step"))
    sys.exit(0 if ok and not hits else 1)
