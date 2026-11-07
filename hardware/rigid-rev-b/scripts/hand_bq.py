"""BQ25125 (U201, DSBGA-25 0.4 mm) fan-out (KiCad python): via-in-pad on the four inner balls that need
their own net (C2 GND, C3 TS, D2 /INT, D4 /PG; 0.25/0.15 mm, filled and capped), same-net links between
neighbouring balls on F.Cu, and the inner balls' escapes straight down on B.Cu."""
import os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
B = sys.argv[1]
b = pcbnew.LoadBoard(B)
F = pcbnew.FromMM
u = b.FindFootprintByReference('U201')
ball = {p.GetNumber(): (round(pcbnew.ToMM(p.GetPosition().x), 3), round(pcbnew.ToMM(p.GetPosition().y), 3)) for p in u.Pads() if p.GetNumber()}
def V(p): return pcbnew.VECTOR2I(F(p[0]), F(p[1]))
def seg(net, layer, pts, w):
    n = b.FindNet('/' + net)
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(a)); t.SetEnd(V(c)); t.SetWidth(F(w)); t.SetLayer(layer); t.SetNet(n); b.Add(t)
for k, net in (('C2', 'GND'), ('C3', 'TS'), ('D2', 'PMIC_INT'), ('D4', 'DOCK_PG'), ('A2', 'VIN')):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(ball[k])); v.SetWidth(F(0.25)); v.SetDrill(F(0.15))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/' + net)); v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True); b.Add(v)
seg('VBAT', pcbnew.F_Cu, [ball['B1'], ball['B2']], 0.2)
seg('PMID', pcbnew.F_Cu, [ball['A3'], ball['B3'], ball['B4'], ball['C4']], 0.2)
x, y = ball['C3']; seg('TS', pcbnew.B_Cu, [ball['C3'], (x, y + 1.2)], 0.15)
x, y = ball['D2']; seg('PMIC_INT', pcbnew.B_Cu, [ball['D2'], (x, y + 0.8)], 0.15)
x, y = ball['D4']; seg('DOCK_PG', pcbnew.B_Cu, [ball['D4'], (x, y + 0.8)], 0.15)
def pad(ref, num):
    q = b.FindFootprintByReference(ref).FindPadByNumber(num).GetPosition()
    return (round(pcbnew.ToMM(q.x), 3), round(pcbnew.ToMM(q.y), 3))
c206, l201, c202, r202 = pad('C206', '1'), pad('L201', '1'), pad('C202', '1'), pad('R202', '1')
x, y = ball['A3']; d = x - c206[0]
seg('PMID', pcbnew.F_Cu, [ball['A3'], (x, c206[1] + d), c206], 0.2)                       # PMID up, then 45 deg to C206 (clear of the VIN via)
x, y = ball['A4']; k = l201[0] - x
seg('SW', pcbnew.F_Cu, [ball['A4'], (x, y - 1.0), (l201[0], y - 1.0 - k), l201], 0.25)     # SW up to L201
seg('VBAT', pcbnew.F_Cu, [ball['B1'], c202], 0.3)                                             # BAT left to C202
x, y = ball['C1']; k = x - 0.3 - r202[0]
seg('ISET', pcbnew.F_Cu, [ball['C1'], (x - 0.3, y), (r202[0], y + k), r202], 0.15)          # ISET left, then 45 deg to R202 (clear of D1)
x, y = ball['B5']; seg('VDD_1V8', pcbnew.F_Cu, [ball['B5'], (x + 0.7, y)], 0.2)             # SYS stub
x, y = ball['C5']; seg('VLED', pcbnew.F_Cu, [ball['C5'], (x + 0.7, y)], 0.2)                # LS/LDO stub
for k, (dx, dy) in (('E1', (0.0, 1.2)), ('E3', (0.0, 1.2)), ('E2', (0.0, 1.75))):   # bottom-row escapes to staggered vias
    x, y = ball[k]; net = {'E1': 'CHG_MR', 'E2': 'CHG_CD', 'E3': 'LS_CTRL'}[k]
    seg(net, pcbnew.F_Cu, [ball[k], (x + dx, y + dy)], 0.15)
    v = pcbnew.PCB_VIA(b); v.SetPosition(V((x + dx, y + dy))); v.SetWidth(F(0.4)); v.SetDrill(F(0.2))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/' + net)); v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True); b.Add(v)
pcbnew.SaveBoard(B, b)
import subprocess; subprocess.run(['python3', os.path.join(HERE, 'mkpro.py')], capture_output=True)
print('BQ fan-out laid', ball['C3'])
