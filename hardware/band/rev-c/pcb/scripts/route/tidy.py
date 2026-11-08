"""Route tidy for router output (chains per net/layer):
 - fold short jogs (<0.3 mm between bends) into the neighbouring segments,
 - re-aim chain ends that stop inside a pad/via onto its centre (0/45/90 only),
 - merge collinear runs, drop zero-length bits.
usage: tidy.py BOARD [--only NET,...]"""
import sys, math
from collections import defaultdict
sys.path.insert(0, '/tmp/wbrevb')
from common import *
B = sys.argv[1]
b = pcbnew.LoadBoard(B)
R4 = lambda v: round(v, 4)
def P(v): return (R4(pcbnew.ToMM(v.x)), R4(pcbnew.ToMM(v.y)))
def V(p): return pcbnew.VECTOR2I(pcbnew.FromMM(p[0]), pcbnew.FromMM(p[1]))
def okdir(d):
    dx, dy = d
    return (abs(dx) < 1e-4) or (abs(dy) < 1e-4) or abs(abs(dx) - abs(dy)) < 1e-4
def unit(a, c):
    d = (c[0]-a[0], c[1]-a[1]); L = math.hypot(*d)
    return (d[0]/L, d[1]/L) if L > 1e-9 else (0, 0)
def same(u, v): return abs(u[0]-v[0]) < 1e-3 and abs(u[1]-v[1]) < 1e-3
def isect(p, u, q, v):
    den = u[0]*v[1] - u[1]*v[0]
    if abs(den) < 1e-9: return None
    t = ((q[0]-p[0])*v[1] - (q[1]-p[1])*v[0]) / den
    return (R4(p[0]+u[0]*t), R4(p[1]+u[1]*t)), t
DIRS = [(1,0),(0,1),(-1,0),(0,-1)] + [(s1/math.sqrt(2), s2/math.sqrt(2)) for s1 in (1,-1) for s2 in (1,-1)]
segs = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
def anchor(pt, net, layer):
    for v in vias:
        if v.GetNetname() == net and math.dist(pt, P(v.GetPosition())) <= pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2 + 1e-3:
            return P(v.GetPosition())
    for p in pads:
        if p.GetNetname() == net and p.IsOnLayer(layer) and p.HitTest(V(pt)):
            return P(p.GetPosition())
    return None
groups = defaultdict(list)
for s in segs:
    groups[(s.GetNetname(), s.GetLayer())].append(s)
only = set(sys.argv[sys.argv.index('--only')+1].split(',')) if '--only' in sys.argv else None
changes = 0
for (net, layer), ss in groups.items():
    if only and net not in only: continue
    adj = defaultdict(list)
    for s in ss:
        a, e = P(s.GetStart()), P(s.GetEnd())
        if a == e: b.Remove(s); continue
        adj[a].append((s, e)); adj[e].append((s, a))
    viapts = {P(v.GetPosition()) for v in vias if v.GetNetname() == net}
    # chain endpoints: degree != 2, or a via/pad centre
    def is_node(pt):
        return len(adj[pt]) != 2 or pt in viapts or any(p.GetNetname() == net and P(p.GetPosition()) == pt for p in pads)
    used = set()
    chains = []
    for start in list(adj):
        if not is_node(start): continue
        for s, nxt in adj[start]:
            if id(s) in used: continue
            chain = [start]; cur = start; seg = s; nn = nxt; width = s.GetWidth(); members = []
            while True:
                used.add(id(seg)); members.append(seg); chain.append(nn)
                if is_node(nn): break
                nxt_list = [(s2, o) for s2, o in adj[nn] if id(s2) not in used]
                if not nxt_list: break
                seg, nn2 = nxt_list[0]; nn = nn2
            chains.append((chain, members, width))
    for chain, members, width in chains:
        pts = list(chain)
        orig = list(pts)
        # end re-aim onto pad/via centres
        for end in (0, -1):
            e = pts[end]; c = anchor(e, net, layer)
            if c is None or c == e or len(pts) < 2: continue
            if len(pts) >= 3:
                p0 = pts[-3] if end == -1 else pts[2]; p1 = pts[-2] if end == -1 else pts[1]
                u = unit(p0, p1); best = None
                for v in DIRS:
                    r = isect(p0, u, c, v)
                    if not r: continue
                    X, t = r
                    w = unit(X, c)
                    if t > 0.25 and okdir((c[0]-X[0], c[1]-X[1])) and math.dist(X, c) < 1.2 and (u[0]*w[0]+u[1]*w[1]) > 0.7:
                        if best is None or abs(math.dist(X, c) - math.dist(e, c)) < best[0]: best = (abs(math.dist(X, c) - math.dist(e, c)), X)
                if best:
                    X = best[1]
                    if end == -1: pts[-2:] = [X, c] if X != c else [c]
                    else: pts[:2] = [c, X] if X != c else [c]
                    continue
            if okdir((c[0]-pts[end+1 if end == 0 else -2][0], c[1]-pts[end+1 if end == 0 else -2][1])):
                pts[end] = c
        # jog folding
        changed = True
        while changed and len(pts) >= 4:
            changed = False
            for i in range(len(pts)-3):
                a, p1, p2, p3 = pts[i], pts[i+1], pts[i+2], pts[i+3]
                if math.dist(p1, p2) >= 0.3: continue
                u, v = unit(a, p1), unit(p2, p3)
                r = isect(a, u, p3, v)
                if not r: continue
                X, t = r
                if t > 0.05 and same(unit(X, p3), v) and okdir(u) and okdir(v) and math.dist(X, p3) > 0.05 and (u[0]*v[0]+u[1]*v[1]) > 0.7:
                    pts[i+1:i+3] = [X]; changed = True; break
        # merge collinear points and drop zero length
        q = [pts[0]]
        for p in pts[1:]:
            if p == q[-1]: continue
            if len(q) >= 2 and same(unit(q[-2], q[-1]), unit(q[-1], p)): q[-1] = p
            else: q.append(p)
        if q != orig and all(okdir((q[k+1][0]-q[k][0], q[k+1][1]-q[k][1])) for k in range(len(q)-1)):
            for m in members: b.Remove(m)
            netobj = b.FindNet(net)
            for k in range(len(q)-1):
                t = pcbnew.PCB_TRACK(b); t.SetStart(V(q[k])); t.SetEnd(V(q[k+1])); t.SetWidth(width); t.SetLayer(layer); t.SetNet(netobj); b.Add(t)
            changes += 1
print('chains changed', changes)
refill(b); pcbnew.SaveBoard(B, b)
