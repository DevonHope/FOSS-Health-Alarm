"""Dog-bone the vias that sat in SMD pads on the dock PCB (review 2026-11-08, fix D-L1).

Run once with KiCad 10's Python:
    python3 dogbone_vias.py IN.kicad_pcb OUT.kicad_pcb
Each via in MOVES is moved from its old centre to a new point next to its pad.
Tracks that ended on the old centre are rerouted to the new centre: the track is
re-aimed at the new point when that keeps it at 0/45/90 degrees, otherwise a short
stub joins the old point to the new one. Pads that had no F.Cu track to their via
get one. Zones are not refilled here (do that with kicad-cli --refill-zones).
"""
import math
import sys

import pcbnew

MM = pcbnew.FromMM

# (owning pad, old via centre, new via centre)
MOVES = [
    ("C12.1", (111.30, 113.20), (111.70, 112.80)),   # table: (111.76,112.74); this is the existing corner
    ("C13.1", (110.35, 109.75), (109.50, 109.75)),
    ("C4.1", (102.05, 108.30), (101.35, 108.30)),
    ("R7.1", (111.95, 100.35), (111.55, 100.35)),
    ("R10.2", (121.74, 103.09), (122.59, 103.09)),
    ("R1.1", (121.95, 99.55), (122.85, 99.55)),
    ("C15.1", (110.30, 111.70), (109.50, 111.70)),
    ("D2.2", (117.10, 122.70), (116.40, 122.70)),
    ("U8.3", (124.70, 105.10), (125.45, 105.10)),
    ("R12.1", (128.70, 103.30), (128.70, 103.95)),
    ("U8.5", (126.20, 104.40), (127.75, 104.40)),
    ("U8.1", (124.45, 103.40), (123.45, 103.40)),
    ("U6.4", (128.20, 120.25), (127.75, 120.25)),
    ("F1.2", (101.60, 112.25), (101.60, 113.10)),
    ("SW1.1", (119.75, 122.20), (119.10, 122.20)),
    ("U5.3", (104.90, 102.55), (105.25, 102.55)),
    ("C20.1", (123.35, 105.50), (123.35, 106.10)),
    ("D1.2", (133.30, 122.10), (133.00, 122.10)),
    ("U3.2", (106.0125, 113.00), (106.3125, 113.00)),
    ("Y1.4", (119.05, 99.05), (119.35, 99.05)),
    ("C13.2", (111.08, 108.75), (111.73, 108.75)),   # review table: "C11.2 edge"
    ("U6.2", (127.2125, 119.30), (127.5125, 119.30)),
    ("U7.2", (125.2125, 100.60), (125.5125, 100.60)),
    ("C19.1", (126.7375, 98.05), (126.7375, 99.05)),  # table: (126.7375,97.75) is 0.025 mm from the board edge
    ("U6.5", (128.45, 118.65), (128.804, 119.004)),
    ("R9.2", (114.35, 116.80), (114.65, 116.79)),    # on the pad centreline
    # Review table "C14.2 edge": this is C15.2's GND via. There is no clean spot off the
    # pads (In2 USB_DM and B.Cu +1V1 run close), so it slides down its own track until
    # the drill clears both pad openings (C14.2 and C15.2 are both GND; only the land touches).
    ("C15.2", (111.08, 110.95), (111.08, 111.15)),
    # U3.5 (VBUS) stays in its pad: USB_DP on F.Cu at x 108.45 blocks the only free side.
]


def V(p):
    return pcbnew.VECTOR2I(MM(p[0]), MM(p[1]))


def is45(a, b):
    d = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
    return abs(d / 45 - round(d / 45)) < 1e-6


def on_segment(p, a, b):
    cross = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x)
    if cross != 0:
        return False
    dot = (p.x - a.x) * (b.x - a.x) + (p.y - a.y) * (b.y - a.y)
    return 0 < dot < (b.x - a.x) ** 2 + (b.y - a.y) ** 2


def add_track(board, a, b, layer, width, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(a)
    t.SetEnd(b)
    t.SetLayer(layer)
    t.SetWidth(width)
    t.SetNet(net)
    board.Add(t)
    return t


def pad_by_name(board, name):
    ref, num = name.split(".")
    return board.FindFootprintByReference(ref).FindPadByNumber(num)


def unit(a, b):
    d = math.hypot(b.x - a.x, b.y - a.y)
    return ((b.x - a.x) / d, (b.y - a.y) / d)


def two_leg(q, u, p1):
    """Keep direction u from q, then turn 45 degrees onto p1. Returns the corner or None."""
    dx, dy = p1.x - q.x, p1.y - q.y
    for sign in (1, -1):
        c, s_ = math.cos(math.radians(45)), sign * math.sin(math.radians(45))
        w = (u[0] * c - u[1] * s_, u[0] * s_ + u[1] * c)
        det = u[0] * w[1] - u[1] * w[0]
        t = (dx * w[1] - dy * w[0]) / det
        s = (u[0] * dy - u[1] * dx) / det
        if t > MM(0.05) and s > MM(0.05):
            return pcbnew.VECTOR2I(int(round(q.x + t * u[0])), int(round(q.y + t * u[1])))
    return None


def segments(board):
    return [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]


def tidy(board, points):
    """Split tracks at touching ends or via centres, drop covered duplicates,
    and merge straight-through joints at the edited points."""
    changed = True
    while changed:
        changed = False
        segs = segments(board)
        vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
        for t in segs:
            stops = [e for s in segs if s is not t and s.GetLayer() == t.GetLayer()
                     and s.GetNetCode() == t.GetNetCode() for e in (s.GetStart(), s.GetEnd())]
            stops += [v.GetPosition() for v in vias if v.GetNetCode() == t.GetNetCode()]
            for x in stops:
                if on_segment(x, t.GetStart(), t.GetEnd()):
                    add_track(board, x, t.GetEnd(), t.GetLayer(), t.GetWidth(), t.GetNet())
                    t.SetEnd(x)
                    changed = True
                    break
            if changed:
                break
        if changed:
            continue
        seen = {}
        for t in segs:
            k = (t.GetLayer(), t.GetNetCode(), frozenset([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]))
            if t.GetStart() == t.GetEnd() or k in seen:
                board.Remove(t)
                changed = True
                break
            seen[k] = t
        if changed:
            continue
        # dead-end stubs left near the edited points
        for t in segs:
            sp = special_points(board, t.GetLayer())
            for e in (t.GetStart(), t.GetEnd()):
                if (e.x, e.y) in sp or not any((e - p).EuclideanNorm() <= 1000 for p in points):
                    continue
                if not any(o is not t and o.GetLayer() == t.GetLayer() and e in (o.GetStart(), o.GetEnd()) for o in segs):
                    board.Remove(t)
                    changed = True
                    break
            if changed:
                break
        if changed:
            continue
        vpos = {(v.GetPosition().x, v.GetPosition().y) for v in vias}
        pads = {}
        for fp in board.GetFootprints():
            for p in fp.Pads():
                pads[(p.GetPosition().x, p.GetPosition().y)] = p
        for pt in list(points):
            key = (pt.x, pt.y)
            if key in vpos or key in pads:
                continue
            for layer in {t.GetLayer() for t in segs}:
                at = [t for t in segs if t.GetLayer() == layer and pt in (t.GetStart(), t.GetEnd())]
                if len(at) != 2 or at[0].GetWidth() != at[1].GetWidth():
                    continue
                a = at[0].GetEnd() if at[0].GetStart() == pt else at[0].GetStart()
                b = at[1].GetEnd() if at[1].GetStart() == pt else at[1].GetStart()
                if on_segment(pt, a, b):
                    at[0].SetStart(a)
                    at[0].SetEnd(b)
                    board.Remove(at[1])
                    changed = True
                    break
            if changed:
                break


# Hand-laid In2 link between the U6.4 and U6.5 vias (both VBUS_F), replacing
# the dog-leg between them (as left after U6.4 has moved).
IN2_OVERRIDES = {
    "U6.5": {
        "remove": [((128.45, 118.65), (128.20, 118.90)), ((128.20, 118.90), (128.20, 119.80)),
                   ((128.20, 119.80), (127.75, 120.25))],
        "add": [((127.75, 120.25), (128.804, 119.196)), ((128.804, 119.196), (128.804, 119.004))],
    },
}
# Pad-centre to via on F.Cu: "diag" puts the 45-degree leg at the pad, "straight" at the via.
FIRST_LEG = {"U6.5": "straight"}


def far(s, p):
    return s.GetEnd() if s.GetStart() == p else s.GetStart()


def special_points(board, layer):
    """Via centres, and centres of pads on this layer."""
    pts = {(t.GetPosition().x, t.GetPosition().y) for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(layer):
                pts.add((p.GetPosition().x, p.GetPosition().y))
    return pts


def pad_route(board, pad, p1, net, width, first):
    c = pad.GetPosition()
    if is45(c, p1):
        add_track(board, c, p1, pcbnew.F_Cu, width, net)
        return
    dx, dy = p1.x - c.x, p1.y - c.y
    k = min(abs(dx), abs(dy))
    if first == "diag":
        m = pcbnew.VECTOR2I(c.x + int(math.copysign(k, dx)), c.y + int(math.copysign(k, dy)))
    else:
        m = pcbnew.VECTOR2I(p1.x - int(math.copysign(k, dx)), p1.y - int(math.copysign(k, dy)))
    add_track(board, c, m, pcbnew.F_Cu, width, net)
    add_track(board, m, p1, pcbnew.F_Cu, width, net)


def find_seg(board, layer, a, b):
    """The track between two points, matched to within 1 um."""
    a, b = V(a), V(b)
    near = lambda p, q: abs(p.x - q.x) <= 1000 and abs(p.y - q.y) <= 1000
    hits = [t for t in segments(board) if t.GetLayer() == layer and (
        (near(t.GetStart(), a) and near(t.GetEnd(), b)) or (near(t.GetStart(), b) and near(t.GetEnd(), a)))]
    assert len(hits) == 1, f"track {a}-{b} not found"
    return hits[0]


def main(src, dst):
    board = pcbnew.LoadBoard(src)
    touched = []
    for pad_name, old, new in MOVES:
        p0 = V(old)
        vias = [t for t in board.GetTracks()
                if t.Type() == pcbnew.PCB_VIA_T and t.GetPosition() == p0]
        assert len(vias) == 1, f"{pad_name}: no via at {old} (already moved?)"
        via = vias[0]
        via.SetPosition(V(new))
        p1 = via.GetPosition()
        pad = pad_by_name(board, pad_name)
        width = MM(0.3) if via.GetNetname().split("/")[-1] in (
            "VBUS", "VBUS_F", "+3V3", "+1V8") else MM(0.2)
        touched.append(p0)
        ov = IN2_OVERRIDES.get(pad_name)
        if ov:
            for a, b in ov["remove"]:
                board.Remove(find_seg(board, pcbnew.In2_Cu, a, b))
            for a, b in ov["add"]:
                add_track(board, V(a), V(b), pcbnew.In2_Cu, MM(0.3), via.GetNet())
        # 1. F.Cu: drop the old pad-to-via link (a chain of short tracks from the old
        #    via centre to the pad centre); it is redrawn from the pad centre in step 3
        had_link = False
        target = pad.GetPosition()
        stack = [(p0, [])]
        seen = set()
        while stack:
            pt, path = stack.pop()
            if pt == target:
                for t in path:
                    board.Remove(t)
                had_link = True
                break
            seen.add((pt.x, pt.y))
            for t in segments(board):
                if (t.GetLayer() == pcbnew.F_Cu and t.GetNetCode() == via.GetNetCode()
                        and pt in (t.GetStart(), t.GetEnd()) and t.GetLength() < MM(0.5)):
                    o = far(t, pt)
                    if (o.x, o.y) not in seen:
                        stack.append((o, path + [t]))
        # 2. other tracks that ended on the old centre: re-aim at the new via
        for s in segments(board):
            if p0 not in (s.GetStart(), s.GetEnd()):
                continue
            layer = s.GetLayer()
            q = far(s, p0)
            if q == p1:
                # the via moved onto this track's far end: the track is no longer needed
                board.Remove(s)
                continue
            # back up through a short corner so the reroute does not leave a stair-step
            others = [t for t in segments(board) if t.m_Uuid.AsString() != s.m_Uuid.AsString() and t.GetLayer() == layer and q in (t.GetStart(), t.GetEnd())]
            if (s.GetLength() < MM(0.5) and len(others) == 1 and (q.x, q.y) not in special_points(board, layer)
                    and not (on_segment(p1, q, p0) or is45(q, p1))):
                board.Remove(s)
                s, p0_here = others[0], q
                q = far(s, q)
            else:
                p0_here = p0
            at_start = s.GetStart() == p0_here
            u = unit(q, p0_here)
            m = None
            if not (on_segment(p1, q, p0_here) or (is45(q, p1) and unit(q, p1) == u)):
                m = two_leg(q, u, p1)
            if m is None and not (on_segment(p1, q, p0_here) or is45(q, p1)):
                add_track(board, p0_here, p1, layer, s.GetWidth(), s.GetNet())
                continue
            if m is not None:
                add_track(board, m, p1, layer, s.GetWidth(), s.GetNet())
                touched.append(m)
            if at_start:
                s.SetStart(m if m is not None else p1)
            else:
                s.SetEnd(m if m is not None else p1)
        # 3. pad to via on F.Cu
        if not any(t.GetLayer() == pcbnew.F_Cu and p1 in (t.GetStart(), t.GetEnd()) for t in segments(board)) or had_link:
            w = MM(0.25) if via.GetNetname().endswith("GND") else width
            pad_route(board, pad, p1, via.GetNet(), w, FIRST_LEG.get(pad_name, "diag"))
        print(f"{pad_name}: via {old} -> {new}")
    tidy(board, touched)
    pcbnew.SaveBoard(dst, board, True)  # True: leave the .kicad_pro alone


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
