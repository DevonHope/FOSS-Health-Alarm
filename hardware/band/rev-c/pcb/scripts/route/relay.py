"""Local re-lay: delete NET's segments on LAYER that lie inside a box, then reconnect the loose ends
with octilinear (0/45/90) paths, ends on pad/via centres. Tries both bend orders per link; MODE picks
which ('a' diagonal first, 'b' straight first, or a string per link like 'ab').
usage: relay.py BOARD NET LAYER x0 y0 x1 y1 [MODE] [WIDTH]"""
import sys, math, pcbnew
B, NET, LAY = sys.argv[1], sys.argv[2], sys.argv[3]
x0, y0, x1, y1 = map(float, sys.argv[4:8])
MODE = sys.argv[8] if len(sys.argv) > 8 else 'a'
WID = float(sys.argv[9]) if len(sys.argv) > 9 else None
b = pcbnew.LoadBoard(B); mm, F = pcbnew.ToMM, pcbnew.FromMM
L = b.GetLayerID(LAY); net = b.FindNet(NET)
def P(v): return (round(mm(v.x), 4), round(mm(v.y), 4))
def V(p): return pcbnew.VECTOR2I(F(p[0]), F(p[1]))
def inb(p): return x0 - 1e-6 <= p[0] <= x1 + 1e-6 and y0 - 1e-6 <= p[1] <= y1 + 1e-6
TR = list(b.GetTracks())
segs = [t for t in TR if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == NET and t.GetLayer() == L]
vias = [t for t in TR if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == NET]
pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == NET and p.IsOnLayer(L)]
rm = [s for s in segs if inb(P(s.GetStart())) and inb(P(s.GetEnd()))]
keep = [s for s in segs if s not in rm]
w = WID or max(mm(s.GetWidth()) for s in rm)
def anchor(p):
    """centre of the via/pad that p lies in, or p itself if it meets a kept segment end/middle; else None"""
    for v in vias:
        if math.dist(p, P(v.GetPosition())) <= mm(v.GetWidth(pcbnew.F_Cu)) / 2 + 0.002: return P(v.GetPosition())
    for pd in pads:
        if pd.HitTest(V(p)): return P(pd.GetPosition())
    for s in keep:
        if min(math.dist(p, P(s.GetStart())), math.dist(p, P(s.GetEnd()))) < 0.002: return p
    return None
terms = []
for s in rm:
    for q in (P(s.GetStart()), P(s.GetEnd())):
        a = anchor(q)
        if a is not None and all(math.dist(a, t) > 0.002 for t in terms): terms.append(a)
if len(terms) < 2:
    print('terminals', terms, '- nothing to connect'); sys.exit(1)
for s in rm: b.Remove(s)
# Prim tree over the terminals
done, links = [terms[0]], []
left = terms[1:]
while left:
    best = min(((math.dist(a, c), a, c) for a in done for c in left))
    links.append((best[1], best[2])); done.append(best[2]); left.remove(best[2])
def path(a, c, m):
    dx, dy = c[0] - a[0], c[1] - a[1]
    k = min(abs(dx), abs(dy)); sx = math.copysign(1, dx); sy = math.copysign(1, dy)
    if k < 1e-4 or abs(abs(dx) - abs(dy)) < 1e-4: return [a, c]
    if m == 'a': mid = (round(a[0] + sx * k, 4), round(a[1] + sy * k, 4))
    else: mid = (round(c[0] - sx * k, 4), round(c[1] - sy * k, 4))
    return [a, mid, c]
n = 0
for i, (a, c) in enumerate(links):
    m = MODE[i] if i < len(MODE) else MODE[-1]
    pts = path(a, c, m)
    for p, q in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(p)); t.SetEnd(V(q)); t.SetWidth(F(w)); t.SetLayer(L); t.SetNet(net); b.Add(t); n += 1
pcbnew.SaveBoard(B, b)
print('removed', len(rm), 'added', n, 'terminals', terms, 'links', links)
