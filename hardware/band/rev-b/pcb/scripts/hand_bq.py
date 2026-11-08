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
x, y = ball['B5']; seg('VSYS', pcbnew.F_Cu, [ball['B5'], (x + 0.7, y)], 0.2)                # SYS stub (buck output, unloaded)
x, y = ball['C5']; seg('VLED', pcbnew.F_Cu, [ball['C5'], (x + 0.7, y)], 0.2)                # LS/LDO stub
for k, (dx, dy) in (('E1', (0.0, 1.2)), ('E3', (0.0, 1.2)), ('E2', (0.0, 1.75))):   # bottom-row escapes to staggered vias
    x, y = ball[k]; net = {'E1': 'CHG_MR', 'E2': 'CHG_CD', 'E3': 'LS_CTRL'}[k]
    seg(net, pcbnew.F_Cu, [ball[k], (x + dx, y + dy)], 0.15)
    v = pcbnew.PCB_VIA(b); v.SetPosition(V((x + dx, y + dy))); v.SetWidth(F(0.4)); v.SetDrill(F(0.2))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/' + net)); v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True); b.Add(v)
# ground balls: C2 (above), A5 and D5 via-in-pad; D1 to the C2 via (0.1 mm diagonal); A1 to C202's GND pad and a via
def gvia(p, d=0.25, drill=0.15):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(p)); v.SetWidth(F(d)); v.SetDrill(F(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/GND')); v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True); b.Add(v)
gvia(ball['A5']); gvia(ball['D5'])
seg('GND', pcbnew.F_Cu, [ball['D1'], ball['C2']], 0.1)
c202g = pad('C202', '2'); x, y = ball['A1']; k = y - c202g[1]
seg('GND', pcbnew.F_Cu, [ball['A1'], (x - k, c202g[1]), c202g], 0.2)
gvia((round(c202g[0] + 0.85, 3), c202g[1]), 0.4, 0.2)
# 2.0 V LDO (U203): EN tied to IN above the package (clear of the exposed pad), caps in line with IN and OUT
l_in, l_en, l_out = pad('U203', '4'), pad('U203', '3'), pad('U203', '1')
top = round(l_in[1] - 0.17, 3)
seg('PMID', pcbnew.F_Cu, [l_in, (l_in[0], top), (l_en[0], top), l_en], 0.2)
seg('PMID', pcbnew.F_Cu, [pad('C210', '1'), l_in], 0.2)
seg('VDD_2V0', pcbnew.F_Cu, [pad('C211', '1'), l_out], 0.2)
# dock landings (B.Cu, J601 1/3/4): vias at the pads' outer edges (as rev A) so the corner nets can leave;
# the pogo tips land on the flat ENIG at the pad centres (all vias are filled and capped)
# (J601.4 / PAD_SWDIO had one too; the routed board leaves that pad on B.Cu, so it was dropped)
for num, net, p in (('1', 'VIN', (132.35, 114.0)), ('3', 'PAD_SWDCLK', (132.1, 101.4))):
    c = pad('J601', num)
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(p)); v.SetWidth(F(0.45)); v.SetDrill(F(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/' + net)); b.Add(v)
    dx, dy = p[0] - c[0], p[1] - c[1]
    if abs(abs(dx) - abs(dy)) < 1e-6 or abs(dx) < 1e-6 or abs(dy) < 1e-6:
        seg(net, pcbnew.B_Cu, [c, p], 0.3)
    else:
        k = min(abs(dx), abs(dy)); mid = (round(c[0] + (dx - (k if dx > 0 else -k)), 3), c[1])
        seg(net, pcbnew.B_Cu, [c, mid, p], 0.3)
# LED driver VCC and SDB (U202 pins 2, 1): vias in the pads' outer ends, 0.25/0.15 (filled and capped)
fp = b.FindFootprintByReference('U202')
for num, net in (('2', 'PMID'),):                       # VCC sits between the LED outputs and the board edge (SDB/LED_EN leaves on F.Cu, no via)
    pp = pad('U202', num)
    outer = (round(pp[0] + (0.25 if pp[0] > pcbnew.ToMM(fp.GetPosition().x) else -0.25), 3), pp[1])
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(outer)); v.SetWidth(F(0.25)); v.SetDrill(F(0.15))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/' + net)); v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True); b.Add(v)
    seg(net, pcbnew.F_Cu, [pp, outer], 0.15)
# LRA lead pad TP502 (B.Cu, hand-soldered): via in the pad so the leads reach the driver on any layer (rev A had one in TP501)
for ref, net in (('TP502', 'LRA_N'),):                   # TP501/LRA_P is routed on B.Cu from the pad, no via needed
    c = pad(ref, '1')
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(c)); v.SetWidth(F(0.45)); v.SetDrill(F(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/' + net)); b.Add(v)
pcbnew.SaveBoard(B, b)
import subprocess; subprocess.run(['python3', os.path.join(HERE, 'mkpro.py')], capture_output=True)
print('BQ fan-out laid', ball['C3'])
