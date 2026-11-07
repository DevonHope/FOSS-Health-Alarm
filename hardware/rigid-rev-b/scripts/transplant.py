"""Copy Nordic's reference copper (vias, no-pour rule areas, C9 GND island; tracks are re-routed) round the nRF54L10 into the rev B board: tracks, vias, the no-pour
rule areas and the small top-layer GND island for C9, from nordic_ref_qfaa_0_8.kicad_pcb, rotated
180 degrees about U1 (same transform as nordic_place.py). Only the power, ground, crystal, reset and RF
nets inside the reference circuit are copied; Nordic's GPIO fan-out to its board edge is not.
usage (KiCad python): transplant.py BOARD"""
import os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
B = sys.argv[1]
ref = pcbnew.LoadBoard(os.path.join(HERE, 'nordic_ref_qfaa_0_8.kicad_pcb'))
b = pcbnew.LoadBoard(B)
mm, F = pcbnew.ToMM, pcbnew.FromMM
NETS = {'VDD_NRF': '/VDD_1V8', 'GND': '/GND', 'DECA': '/DECA', 'DECD': '/DECD', 'DCC': '/DCC', 'NetC13_2': '/nRESET_IC',
        'NetL2_1': '/ANT', 'NetC6_2': '/RF1', 'NetC9_2': '/RF2', 'RF': '/RF_50', 'XC1': '/XC1', 'XC2': '/XC2',
        'P1.00/XL1': '/XL1', 'P1.01/XL2': '/XL2'}
LAY = {'Top Layer': pcbnew.F_Cu, 'Bottom Layer': pcbnew.B_Cu, 'Mid-Layer 1': b.GetLayerID('In1.Cu'), 'Mid-Layer 2': b.GetLayerID('In2.Cu')}
ru = ref.FindFootprintByReference('U1').GetPosition()
bu = b.FindFootprintByReference('U1').GetPosition()
BOX = (-7.9, -6.6, 8.0, 5.0)          # reference-circuit region (Nordic frame, relative to U1)
def rel(v): return mm(v.x - ru.x), mm(v.y - ru.y)
def inside(d): return BOX[0] <= d[0] <= BOX[2] and BOX[1] <= d[1] <= BOX[3]
def T(d):                                                             # rotate 180 about U1, 0.005 mm grid
    return pcbnew.VECTOR2I(F(round((mm(bu.x) - d[0]) / 0.005) * 0.005), F(round((mm(bu.y) - d[1]) / 0.005) * 0.005))
NORDIC = {fp.GetReference() for fp in ref.GetFootprints()}
OTHER = []
for fp in b.GetFootprints():
    if fp.GetReference() in NORDIC: continue
    for p in fp.Pads():
        if p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu):
            bb = p.GetBoundingBox(); OTHER.append((mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())))
EDGE = b.GetBoardEdgesBoundingBox()
EX = (mm(EDGE.GetLeft()), mm(EDGE.GetTop()), mm(EDGE.GetRight()), mm(EDGE.GetBottom()))
def blocked(x, y, r):
    if x - r < EX[0] + 0.5 or x + r > EX[2] - 0.5 or y - r < EX[1] + 0.5 or y + r > EX[3] - 0.5: return True
    return any(x + r + 0.25 > l and x - r - 0.25 < rr and y + r + 0.25 > tt and y - r - 0.25 < bb for l, tt, rr, bb in OTHER)
skipped = []
nt = nv = 0
for t in ref.GetTracks():
    n = t.GetNetname()
    if n not in NETS: continue
    if t.Type() == pcbnew.PCB_VIA_T:
        d = rel(t.GetPosition())
        if not inside(d) or n == 'VDD_NRF': continue
        if n == 'GND' and not (-5.0 <= d[0] <= 7.5 and -6.0 <= d[1] <= 4.6): continue   # stitching near the circuit only
        q = T(d); r = mm(t.GetWidth(pcbnew.F_Cu)) / 2
        if (round(mm(q.x), 2), round(mm(q.y), 2)) in ((105.56, 103.62), (105.56, 103.63)): skipped.append('TP701 spot'); continue
        if blocked(mm(q.x), mm(q.y), r): skipped.append((round(mm(q.x), 2), round(mm(q.y), 2))); continue
        v = pcbnew.PCB_VIA(b); v.SetPosition(q); v.SetWidth(t.GetWidth(pcbnew.F_Cu)); v.SetDrill(t.GetDrill())
        v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(NETS[n])); b.Add(v); nv += 1
    else:
        continue                       # tracks: routed to the house standard instead (see route notes)
        a, e = rel(t.GetStart()), rel(t.GetEnd())
        if not (inside(a) and inside(e)): continue
        lay = LAY.get(ref.GetLayerName(t.GetLayer()))
        if lay is None: continue
        if n == 'VDD_NRF' and lay != pcbnew.F_Cu: continue     # Nordic's bottom-layer VDD feed: routed our own way
        s = pcbnew.PCB_TRACK(b); s.SetStart(T(a)); s.SetEnd(T(e)); s.SetWidth(t.GetWidth()); s.SetLayer(lay)
        s.SetNet(b.FindNet(NETS[n])); b.Add(s); nt += 1
nz = 0
for z in ref.Zones():
    o = z.Outline().Outline(0)
    pts = [rel(o.CPoint(i)) for i in range(o.PointCount())]
    if not all(inside(p) for p in pts): continue          # skips Nordic's board-edge keepouts and full pours
    layers = [ref.GetLayerName(l) for l in z.GetLayerSet().Seq()]
    nz_ = pcbnew.ZONE(b)
    ls = pcbnew.LSET()
    for ln in layers: ls.AddLayer(LAY[ln])
    nz_.SetLayerSet(ls)
    if z.GetIsRuleArea():
        nz_.SetIsRuleArea(True); nz_.SetDoNotAllowZoneFills(True); nz_.SetDoNotAllowTracks(False)
        nz_.SetDoNotAllowVias(False); nz_.SetDoNotAllowPads(False); nz_.SetDoNotAllowFootprints(False)
        nz_.SetZoneName('Nordic ref: no pour')
    else:
        nz_.SetNet(b.FindNet('/GND')); nz_.SetAssignedPriority(5); nz_.SetZoneName('Nordic ref: C9 GND island (top)')
        nz_.SetMinThickness(F(0.1)); nz_.SetLocalClearance(F(0.15)); nz_.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    ol = nz_.Outline(); ol.NewOutline()
    for p in pts:
        q = T(p); ol.Append(q.x, q.y)
    b.Add(nz_); nz += 1
pcbnew.SaveBoard(B, b)
import subprocess; subprocess.run(['python3', os.path.join(HERE, 'mkpro.py')], capture_output=True)
print('transplanted', nt, 'tracks', nv, 'vias', nz, 'zones/rule areas; skipped vias', skipped)
