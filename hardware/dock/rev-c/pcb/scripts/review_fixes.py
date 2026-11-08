"""Dock PCB rev B: layout side of the 2026-11-08 review fixes. Run once, after dogbone_vias.py:

    python3 scripts/review_fixes.py IN.kicad_pcb OUT.kicad_pcb     (KiCad 10's Python)

parts.py / gen_sch.py carry the schematic side (new parts R15, U9, D3; new values for R6, R11, R12).
Every edit asserts the geometry it starts from, so a second run stops instead of editing twice.
Zones are not refilled here: run kicad-cli pcb drc --refill-zones --save-board afterwards.
"""
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts  # noqa: E402

MM = pcbnew.FromMM
FPL = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/"
F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu


def V(p):
    return p if isinstance(p, pcbnew.VECTOR2I) else pcbnew.VECTOR2I(MM(p[0]), MM(p[1]))


class Board:
    def __init__(self, path):
        self.b = pcbnew.LoadBoard(path)
        self._removed = []

    def remove(self, item):
        """Remove from the board but keep a Python reference: letting pcbnew free removed items
        corrupts its SWIG wrappers in KiCad 10.0.3 (later GetTracks() calls fail)."""
        self.b.Remove(item)
        self._removed.append(item)

    def net(self, name):
        n = self.b.FindNet("/" + name)
        assert n is not None, name
        return n

    def pad(self, ref, num):
        return self.b.FindFootprintByReference(ref).FindPadByNumber(str(num)).GetPosition()

    def tracks(self):
        return [t for t in self.b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]

    def vias(self):
        return [t for t in self.b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]

    @staticmethod
    def near(p, q, tol=1000):
        return abs(p.x - q.x) <= tol and abs(p.y - q.y) <= tol

    def find_seg(self, layer, a, c):
        a, c = V(a), V(c)
        hits = [t for t in self.tracks() if t.GetLayer() == layer and (
            (self.near(t.GetStart(), a) and self.near(t.GetEnd(), c)) or
            (self.near(t.GetStart(), c) and self.near(t.GetEnd(), a)))]
        assert len(hits) == 1, f"track {self.b.GetLayerName(layer)} {a}-{c}: {len(hits)} found"
        return hits[0]

    def del_seg(self, layer, a, c):
        self.remove(self.find_seg(layer, a, c))

    def seg(self, a, c, layer, width, net):
        a, c = V(a), V(c)
        d = math.degrees(math.atan2(c.y - a.y, c.x - a.x))
        assert abs(d / 45 - round(d / 45)) < 1e-4, f"not 0/45/90: {a}-{c} {d}"
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(a)
        t.SetEnd(c)
        t.SetLayer(layer)
        t.SetWidth(MM(width))
        t.SetNet(self.net(net))
        self.b.Add(t)

    def path(self, pts, layer, width, net):
        for a, c in zip(pts, pts[1:]):
            self.seg(a, c, layer, width, net)

    def find_via(self, p):
        p = V(p)
        hits = [v for v in self.vias() if self.near(v.GetPosition(), p)]
        assert len(hits) == 1, f"via at {p}: {len(hits)} found"
        return hits[0]

    def via(self, p, net):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(V(p))
        v.SetWidth(MM(0.45))
        v.SetDrill(MM(0.3))
        v.SetLayerPair(F, B)
        v.SetNet(self.net(net))
        self.b.Add(v)
        return v

    def split(self, layer, a, c, at):
        """Split track a-c at point 'at' (on the track) so a branch can end there."""
        t = self.find_seg(layer, a, c)
        end = pcbnew.VECTOR2I(t.GetEnd().x, t.GetEnd().y)   # copy: GetEnd() is a live reference
        t.SetEnd(V(at))
        self.seg(V(at), end, layer, pcbnew.ToMM(t.GetWidth()), t.GetNetname().lstrip("/"))

    def add_part(self, ref, pos, rot):
        p = next(p for p in parts.PARTS if p[0] == ref)
        _ref, _lib, val, fpid, lcsc, mpn, pinnets, _nc, desc = p
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(FPL + lib + ".pretty", name)
        fp.SetFPIDAsString(fpid)
        fp.SetReference(ref)
        fp.SetValue(val)
        for k, v in (("LCSC", lcsc), ("MPN", mpn), ("Description", desc)):
            if v:
                fp.SetField(k, v)
        for k in ("Reference", "Value", "LCSC", "MPN", "Description", "Datasheet"):
            if fp.HasField(k):
                f = fp.GetField(k)
                f.SetLayer(pcbnew.F_Fab)
                f.SetVisible(k in ("Reference", "Value"))
        self.b.Add(fp)
        fp.SetPosition(V(pos))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            if pad.GetNumber():          # 0201 has unnumbered paste-only pads
                pad.SetNet(self.net(pinnets[pad.GetNumber()]))
        return fp

    def set_value(self, ref, old, new, lcsc, desc):
        fp = self.b.FindFootprintByReference(ref)
        assert fp.GetValue() == old, (ref, fp.GetValue())
        fp.SetValue(new)
        fp.SetField("LCSC", lcsc)
        fp.SetField("Description", desc)


def fix_values(e):
    """D-E2: band current limit 0.21 A. D-E1: 100 ohm in series with the bare SWD pins."""
    want = {p[0]: p for p in parts.PARTS}
    e.set_value("R6", "15k", "33k", "C25779", want["R6"][8])
    e.set_value("R11", "22", "100", "C25076", want["R11"][8])
    e.set_value("R12", "22", "100", "C25076", want["R12"][8])


def fix_pin_esd(e):
    """D-E1: USBLC6 (U9) on P_SWCLK/P_SWDIO next to P1/P2, SMF6.0A (D3) on VIN_BAND next to P4.
    U9 pin 5 (its clamp rail) goes to VIN_BAND, so a 5 V short between pins draws nothing."""
    u9 = e.add_part("U9", (134.8, 102.2), 0)
    d3 = e.add_part("D3", (137.3, 113.2), 270)
    p1, p2, p4 = e.pad("P1", 1), e.pad("P2", 1), e.pad("P4", 1)
    u = {n: e.pad("U9", n) for n in range(1, 7)}
    k, a = e.pad("D3", 1), e.pad("D3", 2)
    assert e.near(k, V((137.3, 111.8)), 20000) and e.near(a, V((137.3, 114.6)), 20000), (k, a)
    dy = u[1].y - p1.y                     # P1 sits 0.15 mm above U9 pin 1
    e.path([p1, pcbnew.VECTOR2I(u[1].x - dy, p1.y), u[1]], F, 0.15, "P_SWCLK")
    e.seg(u[1], u[6], F, 0.15, "P_SWCLK")                       # flow-through under the body
    dy = p2.y - u[3].y
    e.path([p2, pcbnew.VECTOR2I(u[3].x - dy, p2.y), u[3]], F, 0.15, "P_SWDIO")
    e.seg(u[3], u[4], F, 0.15, "P_SWDIO")
    gv = e.via((132.6, 102.2), "GND")
    e.seg(u[2], gv.GetPosition(), F, 0.25, "GND")
    # VIN_BAND: U9 pin 5 -> east, 45 down, down x = D3 to its cathode; P4 -> east, 45 up into the cathode
    jog = k.x - u[5].x - MM(0.66)          # 45-degree leg from pin 5's row down to the x = D3 column
    e.path([u[5], pcbnew.VECTOR2I(k.x - jog, u[5].y), pcbnew.VECTOR2I(k.x, u[5].y + jog), k], F, 0.3, "VIN_BAND")
    e.path([p4, pcbnew.VECTOR2I(k.x - (p4.y - k.y), p4.y), k], F, 0.3, "VIN_BAND")
    av = e.via((137.3, 115.6), "GND")
    e.seg(a, av.GetPosition(), F, 0.3, "GND")


def fix_swclk_pulldown(e):
    """D-E3: 100 k pull-down (R15, 0201) on SWCLK_3V3, the 74LVC1T45 input, between C2 and U7.
    Its ground goes to C2's existing GND via."""
    e.add_part("R15", (123.1, 101.6), 90)
    r1, r2 = e.pad("R15", 1), e.pad("R15", 2)
    assert r1.y > r2.y, "R15 pin 1 should be the lower pad"
    gv = e.find_via((122.95, 100.32)).GetPosition()
    e.path([r2, pcbnew.VECTOR2I(r2.x, gv.y + (r2.x - gv.x)), gv], F, 0.2, "GND")
    tap = V((pcbnew.ToMM(r1.x), 102.55))
    e.split(F, (123.45, 102.55), (119.213, 102.55), tap)
    e.seg(r1, tap, F, 0.15, "SWCLK_3V3")


def fix_u3_vbus_via(e):
    """Last dock via in a pasted pad (U3 pin 5, VBUS): USB_DP blocks the pad's east side, so the via
    moves into the gap between U3's pin columns, and pin 2's GND via moves out to the west."""
    e.del_seg(F, (105.2625, 113.0), (106.3125, 113.0))
    e.remove(e.find_via((106.3125, 113.0)))
    pin2 = e.pad("U3", 2)
    gv = e.via((104.25, 113.0), "GND")
    e.seg(pin2, gv.GetPosition(), F, 0.25, "GND")
    v = e.find_via((107.55, 113.05))
    for a, c in (((108.4, 113.05), (107.55, 113.05)), ((105.55, 115.05), (107.55, 113.05)),
                 ((108.95, 113.6), (108.4, 113.05))):
        e.del_seg(IN2, a, c)
    v.SetPosition(V((106.4, 113.0)))
    p = v.GetPosition()
    e.seg(e.pad("U3", 5), p, F, 0.3, "VBUS")
    e.path([V((105.55, 115.05)), V((106.4, 114.2)), p], IN2, 0.3, "VBUS")
    e.path([p, V((108.35, 113.0)), e.find_via((108.95, 113.6)).GetPosition()], IN2, 0.3, "VBUS")


def fix_swdio_drv(e):
    """D-L4: SWDIO_DRV no longer runs between the crystal's pads. It drops to B.Cu right at U1 pin 17
    and runs along y 102.4 to the existing via next to R10."""
    for a, c in (((117.8, 102.4), (118.55, 101.65)), ((118.55, 101.65), (118.85, 101.65)),
                 ((118.85, 101.65), (119.4, 101.1)), ((119.4, 101.1), (119.4, 100.1))):
        e.del_seg(F, a, c)
    for a, c in (((119.4, 101.6), (119.4, 100.1)), ((120.8, 103.0), (119.4, 101.6))):
        e.del_seg(B, a, c)
    e.remove(e.find_via((119.4, 100.1)))
    # XOUT's In2 run moves up from y 102.1 to 101.6 to clear the new via (still 45 degrees into R1)
    e.del_seg(IN2, (119.4, 102.1), (116.2, 102.1))
    e.del_seg(IN2, (121.95, 99.55), (119.4, 102.1))
    e.path([e.find_via((116.2, 102.1)).GetPosition(), V((116.7, 101.6)), V((119.9, 101.6)), V((121.95, 99.55))],
           IN2, 0.15, "XOUT")
    v = e.via((117.8, 102.35), "SWDIO_DRV").GetPosition()   # 0.15 mm clear of pin 17's pad
    stub = e.find_seg(F, (117.8, 103.162), (117.8, 102.4))
    stub.SetEnd(v) if e.near(stub.GetEnd(), V((117.8, 102.4))) else stub.SetStart(v)
    e.path([v, V((120.15, 102.35)), e.find_via((120.8, 103.0)).GetPosition()], B, 0.15, "SWDIO_DRV")


def fix_vbus_f_width(e, width=0.45):
    """D-L7: VBUS_F's 21 mm inner-layer run (0.5 oz copper) from 0.3 to 0.45 mm (0.5 mm would crowd J1's shield leg). Its corner by J1's
    peg hole drops 0.4 mm so the wider track keeps 0.2 mm hole clearance. The F.Cu parts stay 0.3 mm
    (1 oz outer copper, and they pass close to pads)."""
    old = [((101.6, 113.1), (102.45, 113.1)), ((102.45, 113.1), (107.75, 118.4)),
           ((107.75, 118.4), (110.85, 118.4)), ((110.85, 118.4), (114.25, 121.8))]
    for a, c in old:
        e.del_seg(IN2, a, c)
    e.path([e.find_via((101.6, 113.1)).GetPosition(), V((102.45, 113.1)), V((108.15, 118.8)), V((111.25, 118.8)),
            e.find_via((114.25, 121.8)).GetPosition()], IN2, width, "VBUS_F")
    for t in e.tracks():
        if t.GetNetname() == "/VBUS_F" and t.GetLayer() == IN2:
            t.SetWidth(MM(width))


def fix_ep_paste(e, keep_off=0.25, web=0.2, edge=0.05):
    """D-L8: U1's thermal-pad paste no longer covers its 9 open vias. The 4 paste squares become 16
    windows, one per cell of the 3 x 3 via grid: 0.2 mm stencil webs along the via lines, 0.05 mm in
    from the pad edge, and a notch round each via (drill radius 0.15 + 0.1 mm). Every window is one
    simple outline (no islands in the stencil). Coverage goes from 65 % to about 50 %."""
    u1 = e.b.FindFootprintByReference("U1")
    ep = u1.FindPadByNumber("57")
    box = ep.GetBoundingBox()
    vias = sorted((v.GetPosition() for v in e.vias() if box.Contains(v.GetPosition())), key=lambda p: (p.x, p.y))
    assert len(vias) == 9, len(vias)
    xs = sorted({v.x for v in vias})
    ys = sorted({v.y for v in vias})
    xb = [box.GetLeft()] + xs + [box.GetRight()]
    yb = [box.GetTop()] + ys + [box.GetBottom()]
    old = [q for q in u1.Pads() if q.GetNumber() == "" and q.GetShape(F) == pcbnew.PAD_SHAPE_ROUNDRECT]
    assert len(old) == 4, len(old)
    cells = []
    for i in range(4):
        for j in range(4):
            x0 = xb[i] + (MM(edge) if i == 0 else MM(web) // 2)
            x1 = xb[i + 1] - (MM(edge) if i == 3 else MM(web) // 2)
            y0 = yb[j] + (MM(edge) if j == 0 else MM(web) // 2)
            y1 = yb[j + 1] - (MM(edge) if j == 3 else MM(web) // 2)
            cells.append((x0, y0, x1, y1))
    pads = old + [pcbnew.PAD(u1) for _ in range(len(cells) - len(old))]
    for w, (x0, y0, x1, y1) in zip(pads, cells):
        c = pcbnew.VECTOR2I((x0 + x1) // 2, (y0 + y1) // 2)
        poly = pcbnew.SHAPE_POLY_SET()
        poly.NewOutline()
        for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            poly.Append(px - c.x, py - c.y)          # pad frame: orientation 0 below
        holes = pcbnew.SHAPE_POLY_SET()
        for v in vias:
            holes.NewOutline()
            for k in range(36):
                t = 2 * math.pi * k / 36
                holes.Append(int(v.x - c.x + MM(keep_off) * math.cos(t)), int(v.y - c.y + MM(keep_off) * math.sin(t)))
        poly.BooleanSubtract(holes)
        assert poly.OutlineCount() == 1 and poly.HoleCount(0) == 0, "paste window would leave a stencil island"
        if w.GetParent() is None or w not in old:
            w.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            ls = pcbnew.LSET()
            ls.AddLayer(pcbnew.F_Paste)
            w.SetLayerSet(ls)
            w.SetNumber("")
        w.SetPosition(c)
        w.SetOrientationDegrees(0)
        w.SetShape(F, pcbnew.PAD_SHAPE_CUSTOM)
        w.SetAnchorPadShape(F, pcbnew.PAD_SHAPE_CIRCLE)
        w.SetSize(F, pcbnew.VECTOR2I(MM(0.05), MM(0.05)))
        w.DeletePrimitivesList(F)
        w.AddPrimitivePoly(F, poly, 0, True)
        if w not in old:
            u1.Add(w)


def fix_silkscreen(e):
    """D-L9: the board had no legend at all. Adds pin-1 dots on the ICs, cathode bars on the LEDs and
    the VIN TVS, P1-P4 labels for the hand-soldered spring pins, and the board name and revision."""
    S = pcbnew.F_SilkS

    def dot(x, y, r=0.15):
        c = pcbnew.PCB_SHAPE(e.b)
        c.SetShape(pcbnew.SHAPE_T_CIRCLE)
        c.SetLayer(S)
        c.SetCenter(V((x, y)))
        c.SetEnd(V((x + r / 2, y)))
        c.SetWidth(MM(r))
        e.b.Add(c)

    def bar(x0, y0, x1, y1):
        c = pcbnew.PCB_SHAPE(e.b)
        c.SetShape(pcbnew.SHAPE_T_SEGMENT)
        c.SetLayer(S)
        c.SetStart(V((x0, y0)))
        c.SetEnd(V((x1, y1)))
        c.SetWidth(MM(0.15))
        e.b.Add(c)

    def text(s, x, y, angle=0, just=0):
        t = pcbnew.PCB_TEXT(e.b)
        t.SetText(s)
        t.SetLayer(S)
        t.SetPosition(V((x, y)))
        t.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        t.SetTextThickness(MM(0.15))
        t.SetTextAngleDegrees(angle)
        t.SetHorizJustify({-1: pcbnew.GR_TEXT_H_ALIGN_LEFT, 0: pcbnew.GR_TEXT_H_ALIGN_CENTER,
                           1: pcbnew.GR_TEXT_H_ALIGN_RIGHT}[just])
        e.b.Add(t)

    def pin1(ref):
        p = e.pad(ref, 1)
        return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)

    for ref in ("U3", "U6", "U7", "U8", "U9"):             # SOT-23: pin 1 top left, dot beyond its pad
        x, y = pin1(ref)
        dot(x - 0.66 - 0.3, y)
    for ref in ("U4", "U5"):                               # SOT-23-3 turned 90: pin 1 at the bottom
        x, y = pin1(ref)
        dot(x, y + 0.66 + 0.3)
    x, y = pin1("U2")                                      # SOIC-8 turned 90
    dot(x, y + 0.975 + 0.3)
    dot(119.6, 110.1)                                      # U1 (QFN, turned 180): pin 1 corner
    for ref in ("D1", "D2"):                               # LED cathode (pad 1) bar
        x, y = pin1(ref)
        bar(x - 0.44 - 0.33, y - 0.45, x - 0.44 - 0.33, y + 0.45)
    x, y = pin1("D3")                                      # TVS cathode band
    bar(x - 0.55, y - 0.55 - 0.3, x + 0.55, y - 0.55 - 0.3)
    text("P1 CLK", 131.5, 99.75)
    text("P2 DIO", 131.5, 104.75)
    text("GND P3", 130.3, 111.7, just=1)
    text("VIN P4", 130.3, 113.9, just=1)
    text("WakeBand dock rev C", 139.0, 111.0, angle=90)


def strip_new_silk(dst):
    """Footprint silk off the new parts, as gen_pcb.py does (removing items through pcbnew breaks
    its Python wrappers in KiCad 10.0.3, so it is done on the saved file)."""
    import re
    t = open(dst).read()
    out, i = [], 0
    pat = re.compile(r'\n\t\t\((fp_line|fp_poly|fp_circle|fp_arc|fp_rect)\b')
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        st, d, j = m.start() + 3, 0, m.start() + 3
        while True:
            c = t[j]
            if c == '"':
                j = t.index('"', j + 1)
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        blk = t[st:j + 1]
        out.append(t[i:m.start()])
        if '"F.SilkS"' not in blk and '"B.SilkS"' not in blk:
            out.append(t[m.start():j + 1])
        i = j + 1
    open(dst, "w").write("".join(out))


def main(src, dst):
    e = Board(src)
    fix_values(e)
    fix_pin_esd(e)
    fix_swclk_pulldown(e)
    fix_u3_vbus_via(e)
    fix_swdio_drv(e)
    fix_vbus_f_width(e)
    fix_ep_paste(e)
    fix_silkscreen(e)
    pcbnew.SaveBoard(dst, e.b, True)   # True: leave the .kicad_pro alone
    strip_new_silk(dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
