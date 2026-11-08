"""Move router track ends that stop inside a same-net pad/via onto its centre,
keeping every segment at 0/45/90 degrees (direct move, else a short dogleg)."""
import sys, math
sys.path.insert(0, '/tmp/wbrevb')
from common import *
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
def P(v): return (round(pcbnew.ToMM(v.x), 4), round(pcbnew.ToMM(v.y), 4))
def V(p): return pcbnew.VECTOR2I(pcbnew.FromMM(p[0]), pcbnew.FromMM(p[1]))
def okang(a, c):
    dx, dy = abs(c[0]-a[0]), abs(c[1]-a[1])
    return dx < 1e-3 or dy < 1e-3 or abs(dx-dy) < 1e-3
segs = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
def owner(pt, net, layer):
    for v in vias:
        if v.GetNetname() == net and math.dist(pt, P(v.GetPosition())) <= pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2: return P(v.GetPosition())
    for p in pads:
        if p.GetNetname() == net and p.IsOnLayer(layer) and p.HitTest(V(pt)): return P(p.GetPosition())
    return None
ends = {}
for s in segs:
    for k, pt in (('s', P(s.GetStart())), ('e', P(s.GetEnd()))):
        ends.setdefault((pt, s.GetLayer(), s.GetNetname()), []).append((s, k))
moved = dog = 0
dead = []
for (pt, layer, net), lst in ends.items():
    c = owner(pt, net, layer)
    if c is None or math.dist(c, pt) < 0.002: continue
    others = [(s.GetEnd() if k == 's' else s.GetStart()) for s, k in lst]
    if all(okang(P(o), c) for o in others):
        for s, k in lst:
            (s.SetStart if k == 's' else s.SetEnd)(V(c))
            if P(s.GetStart()) == P(s.GetEnd()) and s not in dead: dead.append(s)
        moved += 1; continue
    if len(lst) == 1:
        s, k = lst[0]; o = P(s.GetEnd() if k == 's' else s.GetStart())
        d = (pt[0]-o[0], pt[1]-o[1]); L = math.hypot(*d)
        if L < 1e-6: continue
        u = (d[0]/L, d[1]/L); best = None
        for cond in range(4):
            # K = o + t*u ; want (c-K) axis or diagonal
            A = [(u[0], c[0]-o[0]), (u[1], c[1]-o[1]), (u[0]-u[1], (c[0]-o[0])-(c[1]-o[1])), (u[0]+u[1], (c[0]-o[0])+(c[1]-o[1]))][cond]
            if abs(A[0]) < 1e-9: continue
            t = A[1] / A[0]
            if 0.05 < t < L + 0.6:
                K = (round(o[0]+t*u[0], 4), round(o[1]+t*u[1], 4))
                if math.dist(K, c) < 0.8 and okang(o, K) and okang(K, c):
                    if best is None or abs(t-L) < abs(best[0]-L): best = (t, K)
        if best:
            K = best[1]
            (s.SetStart if k == 's' else s.SetEnd)(V(K))
            n = pcbnew.PCB_TRACK(b); n.SetStart(V(K)); n.SetEnd(V(c)); n.SetWidth(s.GetWidth()); n.SetLayer(layer); n.SetNet(s.GetNet()); b.Add(n)
            dog += 1
for s in dead: b.Remove(s)
pcbnew.SaveBoard(B, b); b = pcbnew.LoadBoard(B)     # fresh object list (SWIG lists go stale after Remove)
# remove exact duplicate segments
seen = set()
for t in list(b.GetTracks()):
    if t.Type() != pcbnew.PCB_TRACE_T: continue
    a, e = P(t.GetStart()), P(t.GetEnd())
    key = (t.GetNetname(), t.GetLayer(), min(a, e), max(a, e))
    if key in seen or a == e: b.Remove(t)
    else: seen.add(key)
pcbnew.SaveBoard(B, b); b = pcbnew.LoadBoard(B)
# merge collinear overlapping same-net segments
changed = True
ts = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
while changed:
    changed = False
    for i, t1 in enumerate(ts):
        a1, e1 = P(t1.GetStart()), P(t1.GetEnd())
        for t2 in ts[i+1:]:
            if t2.GetNetname() != t1.GetNetname() or t2.GetLayer() != t1.GetLayer(): continue
            a2, e2 = P(t2.GetStart()), P(t2.GetEnd())
            d = (e1[0]-a1[0], e1[1]-a1[1]); L = math.hypot(*d)
            if L < 1e-6: continue
            u = (d[0]/L, d[1]/L)
            def off(p): return abs((p[0]-a1[0])*u[1] - (p[1]-a1[1])*u[0])
            if off(a2) > 1e-3 or off(e2) > 1e-3: continue
            def tpar(p): return (p[0]-a1[0])*u[0] + (p[1]-a1[1])*u[1]
            s2 = sorted([tpar(a2), tpar(e2)])
            if s2[1] < -1e-3 or s2[0] > L + 1e-3: continue   # disjoint
            if min(s2[1], L) - max(s2[0], 0) < 1e-3: continue   # only touching
            lo, hi = min(0, s2[0]), max(L, s2[1])
            pa = (round(a1[0]+u[0]*lo, 4), round(a1[1]+u[1]*lo, 4)); pb = (round(a1[0]+u[0]*hi, 4), round(a1[1]+u[1]*hi, 4))
            t1.SetStart(V(pa)); t1.SetEnd(V(pb)); t1.SetWidth(max(t1.GetWidth(), t2.GetWidth())); ts.remove(t2); b.Remove(t2)
            changed = True; break
        if changed: break
pcbnew.SaveBoard(B, b); b = pcbnew.LoadBoard(B)
# 2-segment fix for any remaining off-angle segment
fix2 = 0
for t in list(b.GetTracks()):
    if t.Type() != pcbnew.PCB_TRACE_T: continue
    a, e = P(t.GetStart()), P(t.GetEnd())
    if okang(a, e): continue
    dx, dy = e[0]-a[0], e[1]-a[1]
    m = min(abs(dx), abs(dy)); sx = 1 if dx > 0 else -1; sy = 1 if dy > 0 else -1
    K1 = (round(a[0]+sx*m, 4), round(a[1]+sy*m, 4))        # diagonal first
    K = K1
    t.SetEnd(V(K))
    n = pcbnew.PCB_TRACK(b); n.SetStart(V(K)); n.SetEnd(V(e)); n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer()); n.SetNet(t.GetNet()); b.Add(n)
    fix2 += 1
print('moved', moved, 'doglegs', dog, 'two-seg fixes', fix2)
refill(b); pcbnew.SaveBoard(B, b)
