"""Export copper geometry of the board for the grid router (run with KiCad's python)."""
import json, sys
import pcbnew
mm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
LAY = {'F.Cu': pcbnew.F_Cu, 'In2.Cu': b.GetLayerID('In2.Cu'), 'B.Cu': pcbnew.B_Cu}
out = {'pads': [], 'tracks': [], 'vias': [], 'zones': [], 'keepouts': []}


def poly_list(sps):
    res = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        res.append([(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())])
    return res


for fp in b.GetFootprints():
    for p in fp.Pads():
        for ln, lid in LAY.items():
            if not p.IsOnLayer(lid):
                continue
            sps = p.GetEffectivePolygon(lid, pcbnew.ERROR_OUTSIDE)
            out['pads'].append({'ref': fp.GetReference(), 'num': p.GetNumber(), 'net': p.GetNetname(),
                                'layer': ln, 'x': mm(p.GetPosition().x), 'y': mm(p.GetPosition().y),
                                'polys': poly_list(sps)})
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        out['vias'].append({'net': t.GetNetname(), 'x': mm(t.GetPosition().x), 'y': mm(t.GetPosition().y),
                            'd': mm(t.GetWidth(pcbnew.F_Cu))})
    else:
        ln = b.GetLayerName(t.GetLayer())
        if ln in LAY:
            out['tracks'].append({'net': t.GetNetname(), 'layer': ln, 'w': mm(t.GetWidth()),
                                  'a': (mm(t.GetStart().x), mm(t.GetStart().y)),
                                  'b': (mm(t.GetEnd().x), mm(t.GetEnd().y))})
for z in b.Zones():
    if z.GetIsRuleArea():
        out['keepouts'].append({'layers': [b.GetLayerName(l) for l in z.GetLayerSet().Seq()],
                                'tracks': z.GetDoNotAllowTracks(), 'vias': z.GetDoNotAllowVias(),
                                'polys': poly_list(z.Outline())})
        continue
    for ln, lid in LAY.items():
        if z.IsOnLayer(lid) and z.GetNetname() not in ('GND', '/GND'):
            out['zones'].append({'net': z.GetNetname(), 'layer': ln, 'polys': poly_list(z.GetFilledPolysList(lid))})
u1 = b.FindFootprintByReference('U1').GetCourtyard(pcbnew.F_CrtYd).BBox()
out['u1_courtyard'] = [mm(u1.GetLeft()), mm(u1.GetTop()), mm(u1.GetRight()), mm(u1.GetBottom())]
json.dump(out, open(sys.argv[2], 'w'))
print('pads', len(out['pads']), 'tracks', len(out['tracks']), 'vias', len(out['vias']),
      'zones(non-GND)', len(out['zones']), 'keepouts', len(out['keepouts']))
