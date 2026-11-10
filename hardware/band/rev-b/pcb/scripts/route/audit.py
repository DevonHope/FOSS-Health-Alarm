"""Trace audit for the rigid rev A board (KiCad python): the checks of the
board README "Trace audit" section. Prints totals and lists issues."""
import math, sys
from collections import defaultdict
import pcbnew
mm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
TOL = 0.002
segs = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
issues = defaultdict(list)


def P(v):
    return (round(mm(v.x), 4), round(mm(v.y), 4))


def inside_pad_or_via(pt, net, layer):
    for v in vias:
        if v.GetNetname() == net and math.dist(pt, P(v.GetPosition())) <= mm(v.GetWidth(pcbnew.F_Cu)) / 2 + TOL:
            return v
    for p in pads:
        if p.GetNetname() == net and p.IsOnLayer(layer) and p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(pt[0]), pcbnew.FromMM(pt[1]))):
            return p
    return None


def centre(o):
    return P(o.GetPosition())


ends = defaultdict(list)
for s in segs:
    a, c = P(s.GetStart()), P(s.GetEnd())
    L = math.dist(a, c)
    ang = math.degrees(math.atan2(c[1] - a[1], c[0] - a[0])) % 45
    in_a = inside_pad_or_via(a, s.GetNetname(), s.GetLayer())
    in_c = inside_pad_or_via(c, s.GetNetname(), s.GetLayer())
    wholly_inside = in_a is not None and in_a is in_c
    if min(ang, 45 - ang) > 0.05 and not wholly_inside:
        issues['segment not at 0/45/90'].append((s.GetNetname(), a, c))
    if L < 0.1 and not (in_a or in_c):
        issues['segment < 0.1 mm outside pads'].append((s.GetNetname(), a, c))
    for pt in (a, c):
        ends[(s.GetNetname(), s.GetLayer(), pt)].append(s)
# track ends
for (net, layer, pt), lst in ends.items():
    o = inside_pad_or_via(pt, net, layer)
    if o is not None:
        if math.dist(pt, centre(o)) > TOL and len(lst) >= 1:
            # allowed if another segment of this run continues to the centre
            if not any(math.dist(centre(o), q) < TOL for s in lst for q in (P(s.GetStart()), P(s.GetEnd()))):
                issues['track end off pad/via centre'].append((net, layer, pt))
        continue
    if len(lst) == 1:
        # does it end on the middle of another same-net track?
        mid = False
        for s in segs:
            if s is lst[0] or s.GetNetname() != net or s.GetLayer() != layer:
                continue
            a, c = P(s.GetStart()), P(s.GetEnd())
            d = abs((c[0] - a[0]) * (a[1] - pt[1]) - (a[0] - pt[0]) * (c[1] - a[1])) / max(math.dist(a, c), 1e-9)
            if d < TOL and min(a[0], c[0]) - TOL <= pt[0] <= max(a[0], c[0]) + TOL and min(a[1], c[1]) - TOL <= pt[1] <= max(a[1], c[1]) + TOL:
                mid = True
        issues['ends on the middle of a track' if mid else 'dangling end'].append((net, b.GetLayerName(layer), pt))
    elif len(lst) == 2:
        s1, s2 = lst
        def vec(s):
            a, c = P(s.GetStart()), P(s.GetEnd())
            return (c[0] - a[0], c[1] - a[1]) if math.dist(a, pt) < TOL else (a[0] - c[0], a[1] - c[1])
        v1, v2 = vec(s1), vec(s2)
        cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / max(math.hypot(*v1) * math.hypot(*v2), 1e-12)
        bend = 180 - math.degrees(math.acos(max(-1, min(1, cosang))))
        if bend > 45.5:
            issues[f'bend sharper than 45 deg'].append((net, b.GetLayerName(layer), pt, round(bend)))
# staircase: three consecutive segments alternating direction with a short middle
for (net, layer, pt), lst in ends.items():
    if len(lst) != 2 or inside_pad_or_via(pt, net, layer):
        continue
    for s in lst:
        if mm(s.GetLength()) < 0.3:
            other_end = P(s.GetEnd()) if math.dist(P(s.GetStart()), pt) < TOL else P(s.GetStart())
            if len(ends.get((net, layer, other_end), [])) == 2 and not inside_pad_or_via(other_end, net, layer):
                issues['short zig-zag step (< 0.3 mm between bends)'].append((net, b.GetLayerName(layer), pt, round(mm(s.GetLength()), 3)))
# same-net overlap: collinear overlapping segments
by = defaultdict(list)
for s in segs:
    by[(s.GetNetname(), s.GetLayer())].append(s)
for k, lst in by.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            a1, c1 = P(lst[i].GetStart()), P(lst[i].GetEnd()); a2, c2 = P(lst[j].GetStart()), P(lst[j].GetEnd())
            cr = lambda o, p, q: (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
            if abs(cr(a1, c1, a2)) < 1e-6 and abs(cr(a1, c1, c2)) < 1e-6:
                d = (c1[0] - a1[0], c1[1] - a1[1]); L2 = d[0] ** 2 + d[1] ** 2
                if L2 == 0: continue
                t = sorted(((a2[0] - a1[0]) * d[0] + (a2[1] - a1[1]) * d[1]) / L2 for _ in [0])
                t1 = ((a2[0] - a1[0]) * d[0] + (a2[1] - a1[1]) * d[1]) / L2; t2 = ((c2[0] - a1[0]) * d[0] + (c2[1] - a1[1]) * d[1]) / L2
                lo, hi = min(t1, t2), max(t1, t2)
                if hi > 1e-6 and lo < 1 - 1e-6 and min(hi, 1) - max(lo, 0) > 1e-3:
                    issues['overlapping same-net tracks'].append((k[0], a1, c1, a2, c2))
print('segments', len(segs), 'vias', len(vias))
for k, v in issues.items():
    print(f'{k}: {len(v)}')
    for x in v[:40]:
        print('   ', x)
