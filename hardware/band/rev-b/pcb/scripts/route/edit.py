"""Point edits on a board.  usage: edit.py BOARD OPS.json
ops: ["mv", net, [x,y], [x2,y2], layer|null]   move every via centre / track end of net at x,y (optionally one layer's tracks only)
     ["del", net, layer, [x,y], [x2,y2]]       delete the track with these ends (either order)
     ["add", net, layer, width, [[x,y], ...]]  add a polyline
     ["delvia", net, [x,y]]"""
import sys, json, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); ops = json.load(open(sys.argv[2])); mm, F = pcbnew.ToMM, pcbnew.FromMM
def P(v): return (round(mm(v.x), 4), round(mm(v.y), 4))
def V(p): return pcbnew.VECTOR2I(F(p[0]), F(p[1]))
def near(a, c): return math.dist(a, c) < 0.002
TRALL = list(b.GetTracks()); DEAD = []
for op in ops:
    TR = [t for t in TRALL if not any(t is d for d in DEAD)]; k = op[0]; n = 0
    if k == 'mv':
        _, net, a, c = op[:4]; lay = op[4] if len(op) > 4 else None
        for t in TR:
            if t.GetNetname() != net: continue
            if t.Type() == pcbnew.PCB_VIA_T:
                if lay is None and near(P(t.GetPosition()), a): t.SetPosition(V(c)); n += 1
            elif lay is None or b.GetLayerName(t.GetLayer()) == lay:
                if near(P(t.GetStart()), a): t.SetStart(V(c)); n += 1
                if near(P(t.GetEnd()), a): t.SetEnd(V(c)); n += 1
    elif k == 'del':
        _, net, lay, a, c = op
        for t in TR:
            if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == net and b.GetLayerName(t.GetLayer()) == lay and \
               ((near(P(t.GetStart()), a) and near(P(t.GetEnd()), c)) or (near(P(t.GetStart()), c) and near(P(t.GetEnd()), a))):
                DEAD.append(t); n += 1; break
    elif k == 'delvia':
        _, net, a = op
        for t in TR:
            if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net and near(P(t.GetPosition()), a): DEAD.append(t); n += 1; break
    elif k == 'add':
        _, net, lay, w, pts = op
        for p, q in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(p)); t.SetEnd(V(q)); t.SetWidth(F(w)); t.SetLayer(b.GetLayerID(lay))
            t.SetNet(b.FindNet(net)); b.Add(t); TRALL.append(t); n += 1
    if n == 0: print('NO MATCH', op)
    TR = None
for t in DEAD: b.Remove(t)
pcbnew.SaveBoard(sys.argv[1], b); print('ops', len(ops))
