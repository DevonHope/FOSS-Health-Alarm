"""Remove duplicate vias and duplicate/zero-length tracks (same net, layer, endpoints)."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
def r(p): return (round(mm(p.x), 3), round(mm(p.y), 3))
seen = set(); n = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T: k = ('v', t.GetNetname(), r(t.GetPosition()))
    else:
        a, e = r(t.GetStart()), r(t.GetEnd())
        if a == e: b.Remove(t); n += 1; continue
        k = ('t', t.GetNetname(), t.GetLayer()) + tuple(sorted([a, e]))
    if k in seen: b.Remove(t); n += 1
    else: seen.add(k)
pcbnew.SaveBoard(sys.argv[1], b); print('dedupe removed', n)
