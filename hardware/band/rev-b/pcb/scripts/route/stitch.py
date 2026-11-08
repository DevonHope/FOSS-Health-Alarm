"""Ground stitching: for every GND fill island on F.Cu/B.Cu (bbox area > 5 mm2) with fewer than 2 GND vias,
add 0.45/0.3 mm GND vias where the point lies inside GND fill on all four layers with MARGIN to the fill
edge (so the via is clear of every other net), at least 1.5 mm from other vias and outside rule areas.
Prints the candidates; run DRC afterwards and drop any via it flags (stitch.py BOARD --drop x,y ...).
usage (KiCad python): stitch.py BOARD"""
import sys, math, pcbnew
B = sys.argv[1]; b = pcbnew.LoadBoard(B); mm, F = pcbnew.ToMM, pcbnew.FromMM
if '--drop' in sys.argv:
    pts = [tuple(map(float, a.split(','))) for a in sys.argv[sys.argv.index('--drop') + 1:]]
    rm = [t for t in list(b.GetTracks()) if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == '/GND'
          and any(math.dist((mm(t.GetPosition().x), mm(t.GetPosition().y)), p) < 0.01 for p in pts)]
    for t in rm: b.Remove(t)
    pcbnew.SaveBoard(B, b); print('dropped', len(rm)); sys.exit()
MARGIN = 0.3
# fills as saved by kicad-cli drc --refill-zones (refilling from Python here leaves them empty)
gnd = b.FindNet('/GND')
LAY = [pcbnew.F_Cu, b.GetLayerID('In1.Cu'), b.GetLayerID('In2.Cu'), pcbnew.B_Cu]
fills = {L: [] for L in LAY}
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() != '/GND': continue
    for L in LAY:
        if z.IsOnLayer(L): fills[L].append(z.GetFilledPolysList(L))
rules = [z for z in b.Zones() if z.GetIsRuleArea()]
vias = [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
def inside_all(x, y):
    p = pcbnew.VECTOR2I(F(x), F(y))
    for L in LAY:
        ok = False
        for ps in fills[L]:
            for k in range(ps.OutlineCount()):
                poly = pcbnew.SHAPE_POLY_SET(); poly.AddOutline(ps.Outline(k))
                for h in range(ps.HoleCount(k)): poly.AddHole(ps.Hole(k, h))
                if poly.Contains(p):
                    # distance to the island's boundary (outline and holes)
                    d = min([math.sqrt(ps.Outline(k).SquaredDistance(p, True))] + [math.sqrt(ps.Hole(k, h).SquaredDistance(p, True)) for h in range(ps.HoleCount(k))])  # outline only: 0 inside otherwise
                    if mm(int(d)) >= MARGIN: ok = True
        if not ok: return False
    return not any(z.Outline().Contains(p) for z in rules)
added = []
for L in (pcbnew.F_Cu, pcbnew.B_Cu):
    for ps in fills[L]:
        for k in range(ps.OutlineCount()):
            o = ps.Outline(k); bb = o.BBox()
            if mm(bb.GetWidth()) * mm(bb.GetHeight()) < 5: continue
            poly = pcbnew.SHAPE_POLY_SET(); poly.AddOutline(o)
            have = sum(1 for v in vias + added if poly.Contains(pcbnew.VECTOR2I(F(v[0]), F(v[1]))))
            x0, y0, x1, y1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
            y = round(y0, 1)
            while have < 2 and y <= y1:
                x = round(x0, 1)
                while have < 2 and x <= x1:
                    if poly.Contains(pcbnew.VECTOR2I(F(x), F(y))) and all(math.dist((x, y), v) >= 1.5 for v in vias + added) and inside_all(x, y):
                        added.append((x, y)); have += 1
                    x = round(x + 0.1, 1)
                y = round(y + 0.1, 1)
for x, y in added:
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(F(x), F(y))); v.SetWidth(F(0.45)); v.SetDrill(F(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); b.Add(v)
pcbnew.SaveBoard(B, b); print('stitching vias added', len(added), added)
