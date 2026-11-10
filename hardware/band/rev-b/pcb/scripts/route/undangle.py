"""Remove vias/tracks KiCad DRC reports as dangling (from /tmp/revb/drc.json), plus stubs that end on a removed via."""
import sys, json, math, pcbnew
B = sys.argv[1]; b = pcbnew.LoadBoard(B); mm = pcbnew.ToMM
d = json.load(open('/tmp/revb/drc.json'))
dv, dt = [], []
for x in d['violations']:
    for i in x['items']:
        p = (round(i['pos']['x'], 3), round(i['pos']['y'], 3))
        if x['type'] == 'via_dangling': dv.append(p)
        if x['type'] == 'track_dangling': dt.append(p)
def r(q): return (round(mm(q.x), 3), round(mm(q.y), 3))
TR = list(b.GetTracks()); rm = []
for t in TR:
    if t.Type() == pcbnew.PCB_VIA_T:
        if r(t.GetPosition()) in dv and not any(p.GetNetname() == t.GetNetname() and p.HitTest(t.GetPosition()) for f in b.GetFootprints() for p in f.Pads()):
            rm.append(t)                                  # keep vias in pads (they tie the pad to the inner layers)
PADS = [p for f in b.GetFootprints() for p in f.Pads()]
def touches(t, q):                                    # anything else of the same net at point q on t's layer?
    for o in TR:
        if o is t or o in rm or o.GetNetname() != t.GetNetname(): continue
        if o.Type() == pcbnew.PCB_VIA_T:
            if math.dist(r(o.GetPosition()), r(q)) < 0.01: return True
        elif o.GetLayer() == t.GetLayer() and min(math.dist(r(o.GetStart()), r(q)), math.dist(r(o.GetEnd()), r(q))) < 0.01: return True
    return any(p.GetNetname() == t.GetNetname() and p.IsOnLayer(t.GetLayer()) and p.HitTest(q) for p in PADS)
for t in TR:
    if t.Type() == pcbnew.PCB_VIA_T: continue
    a, e = r(t.GetStart()), r(t.GetEnd())
    if any(min(math.dist(a, p), math.dist(e, p)) < 0.01 for p in dt) and not (touches(t, t.GetStart()) and touches(t, t.GetEnd())):
        rm.append(t)                                  # a true dead end: one end touches nothing
for t in rm: b.Remove(t)
pcbnew.SaveBoard(B, b); print('removed', len(rm))
