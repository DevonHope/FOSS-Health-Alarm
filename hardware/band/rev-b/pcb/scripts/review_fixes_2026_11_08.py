"""Review fixes of 2026-11-08 (hardware/reviews/2026-11-08) on the rev B board, applied once:

  B-L1  In1-only void under the RF filter (Nordic's QFAA reference void, clipped at x >= 103.5 so the
        50 ohm feed keeps its In1 reference); In2 stays solid as the filter's reference, so the In2 copy of
        the small C9-island void is removed (the island's vias now tie it to In2 as well as B.Cu, as
        Nordic ties it to their reference plane). I2C_SDA (B.Cu) now passes above the filter area
        (y <= 103.6), round the ACC_INT1 via, which moves 0.57 mm up its own B.Cu diagonal to make room; I2C_SCL (B.Cu) drops its via left of the feed and crosses under the feed at y 108.7, so no
        signal runs on In2/B.Cu inside x 102.5-106.9, y 103.8-106.6.
  B-L4  VLED via in the U201 courtyard moved 0.15 mm up and left so it clears In2 I2C_SDA by 0.2 mm once the
        courtyard via-in-pad rules no longer relax it (.kicad_dru: those rules now need A.Hole < 0.16mm).
  B-L5  C6 back at Nordic's position (y 105.707): 0.2 mm L2-C6 pad gap.
  B-L6  U201 (DSBGA) ball mask margin 0.04 -> 0.03 mm: openings 0.29 mm, 0.11 mm mask dams.
  B-L7  GND vias along the 0.36 mm feed (0.57-0.78 mm from its centre line).
  B-E8  L201 Description field: the SYS buck must stay on (matches parts.py and the schematic).

Asserts the starting geometry, so a second run fails. Save keeps the project settings (SaveBoard(..., True)).
Refill afterwards: kicad-cli pcb drc --refill-zones --save-board rigid-rev-b.kicad_pcb
usage (KiCad python): review_fixes_2026_11_08.py [BOARD]"""
import os, sys, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
B = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'rigid-rev-b.kicad_pcb')
b = pcbnew.LoadBoard(B); F, mm = pcbnew.FromMM, pcbnew.ToMM
P = lambda x, y: pcbnew.VECTOR2I(F(x), F(y))
L = {n: b.GetLayerID(n) for n in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')}
def near(a, x, y, tol=0.0006): return abs(mm(a.x) - x) < tol and abs(mm(a.y) - y) < tol
def seg(layer, net, x0, y0, x1, y1):
    m = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == L[layer] and t.GetNetname() == net
         and ((near(t.GetStart(), x0, y0) and near(t.GetEnd(), x1, y1)) or (near(t.GetStart(), x1, y1) and near(t.GetEnd(), x0, y0)))]
    assert len(m) == 1, f'expected one {layer} {net} track ({x0},{y0})-({x1},{y1}), found {len(m)}'
    return m[0]
def via(net, x, y):
    m = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net and near(t.GetPosition(), x, y)]
    assert len(m) == 1, f'expected one {net} via at ({x},{y}), found {len(m)}'
    return m[0]
def pad(ref, num):
    return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def add_track(layer, net, pts, w):
    """pts: VECTOR2I or (x, y) mm; consecutive points become segments."""
    pts = [p if isinstance(p, pcbnew.VECTOR2I) else P(*p) for p in pts]
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(F(w)); t.SetLayer(L[layer])
        t.SetNet(b.FindNet(net)); b.Add(t)
def add_via(net, x, y, d, drill):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(F(d)); v.SetDrill(F(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v); return v

# ---------------------------------------------------------------- starting geometry (fails on a second run)
old_sda = [seg('B.Cu', '/I2C_SDA', *c) for c in ((115.1, 100.4, 111.05, 100.4), (111.05, 100.4, 106.25, 105.2),
           (106.25, 105.2, 104.0, 105.2), (104.0, 105.2, 102.0, 103.2), (102.0, 103.2, 101.8375, 103.2))]
sda_via = via('/I2C_SDA', 101.8375, 103.2)
old_scl_f = seg('F.Cu', '/I2C_SCL', 101.3, 104.6, 102.15, 105.45)
old_scl_via = via('/I2C_SCL', 102.15, 105.45)
old_scl_b = [seg('B.Cu', '/I2C_SCL', *c) for c in ((102.15, 105.45, 104.55, 107.85), (104.55, 107.85, 104.55, 108.85),
             (104.55, 108.85, 106.6, 110.9))]
seg('B.Cu', '/I2C_SCL', 106.6, 110.9, 109.7, 110.9)
c6 = b.FindFootprintByReference('C6')
assert near(c6.GetPosition(), 106.83, 105.6), 'C6 is not at (106.83, 105.6)'
c6_gnd = seg('F.Cu', '/GND', 107.115, 105.6, 107.975, 105.6)
c6_rf1 = seg('F.Cu', '/RF1', 106.545, 105.6, 106.545, 105.2)
vled_via = via('/VLED', 122.7, 106.2)
vled_f = [seg('F.Cu', '/VLED', *c) for c in ((122.3, 105.4, 122.7, 105.8), (122.7, 105.8, 122.7, 106.2))]
vled_b = seg('B.Cu', '/VLED', 123.95, 107.45, 122.7, 106.2)
acc_via = via('/ACC_INT1', 106.35, 103.6)
acc_f = seg('F.Cu', '/ACC_INT1', 107.975, 103.6, 106.35, 103.6)
acc_b = seg('B.Cu', '/ACC_INT1', 106.35, 103.6, 104.4, 101.65)
u201 = b.FindFootprintByReference('U201')
balls = [p for p in u201.Pads() if p.IsOnLayer(pcbnew.F_Mask)]
assert len(balls) == 25 and all(p.GetLocalSolderMaskMargin() == F(0.04) for p in balls), 'U201 ball mask margin is not 0.04'
NAME = 'Nordic ref (In1 only): RF filter void'
assert not [z for z in b.Zones() if z.GetZoneName() == NAME], 'In1 RF filter void already present'
c9_in2 = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'Nordic ref: no pour' and z.IsOnLayer(L['In2.Cu'])]
assert len(c9_in2) == 1 and list(c9_in2[0].GetLayerSet().CuStack()) == [L['In2.Cu']]
bb = c9_in2[0].GetBoundingBox()
assert near(P(mm(bb.GetLeft()), mm(bb.GetTop())), 104.0, 103.795) and near(P(mm(bb.GetRight()), mm(bb.GetBottom())), 105.83, 104.795)
FEED_VIAS = [(103.5, 105.75), (103.45, 106.75), (103.45, 107.25), (103.45, 107.75), (103.45, 108.25),
             (102.15, 105.2), (102.15, 105.7), (102.15, 106.2)]
L201_OLD = 'buck inductor (buck output unused; firmware may turn it off)'
L201_NEW = ('buck inductor (SYS buck must stay enabled: the BQ25125\'s /CD and LSCTRL thresholds are referenced to VSYS; '
            'output unloaded)')
l201 = b.FindFootprintByReference('L201')
assert l201.GetFieldText('Description') == L201_OLD, 'L201 description already changed'
for x, y in FEED_VIAS + [(101.3, 104.6)]:
    assert not [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and near(t.GetPosition(), x, y)], f'via at ({x},{y}) exists'

# ---------------------------------------------------------------- B-L1: I2C_SDA above the filter (B.Cu)
# ACC_INT1 via up its B.Cu diagonal to (105.95, 103.2); F.Cu gets a 45-degree step to it
acc_via.SetPosition(P(105.95, 103.2))
for t in (acc_f, acc_b): b.Remove(t)
add_track('F.Cu', '/ACC_INT1', [pad('U1', '27').GetPosition(), (106.35, 103.6), acc_via.GetPosition()], 0.15)
add_track('B.Cu', '/ACC_INT1', [acc_via.GetPosition(), (104.4, 101.65)], 0.15)
for t in old_sda: b.Remove(t)
add_track('B.Cu', '/I2C_SDA', [sda_via.GetPosition(), (102.4375, 102.6), (104.8, 102.6), (105.8, 103.6), (107.1, 103.6),
                                (110.3, 100.4), (115.1, 100.4)], 0.15)
# I2C_SCL: via at the end of the F.Cu run (101.3, 104.6), B.Cu down the left of the feed, under it at y 108.7
end = old_scl_f.GetStart() if near(old_scl_f.GetStart(), 101.3, 104.6) else old_scl_f.GetEnd()
for t in [old_scl_f, old_scl_via] + old_scl_b: b.Remove(t)
v = add_via('/I2C_SCL', mm(end.x), mm(end.y), 0.45, 0.3)
add_track('B.Cu', '/I2C_SCL', [v.GetPosition(), (101.3, 108.2), (101.8, 108.7), (104.4, 108.7), (106.6, 110.9)], 0.15)
# In1-only rule area (no pour, no tracks; vias allowed so the shunt-cap GND vias stay)
z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(NAME); z.SetLayer(L['In1.Cu'])
z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(False)
z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
ol = z.Outline(); ol.NewOutline()
for x, y in ((106.832, 105.961), (106.832, 104.793), (104.495, 104.793), (104.114, 104.412), (103.5, 104.412),
             (103.5, 105.986), (103.809, 105.986), (104.19, 105.605), (106.197, 105.605), (106.197, 105.961)):
    ol.Append(F(x), F(y))
b.Add(z)
b.Remove(c9_in2[0])

# ---------------------------------------------------------------- B-L5: C6 at Nordic's y
c6.SetPosition(P(106.83, 105.707))
g, r = pad('C6', '1').GetPosition(), pad('C6', '2').GetPosition()
b.Remove(c6_gnd); b.Remove(c6_rf1)
u32 = pad('U1', '32').GetPosition(); d = u32.y - g.y                       # -0.107 mm: one 45-degree step up
add_track('F.Cu', '/GND', [g, pcbnew.VECTOR2I(g.x - d, u32.y), u32], 0.2)
add_track('F.Cu', '/RF1', [r, P(106.545, 105.2)], 0.25)

# ---------------------------------------------------------------- B-L4: VLED via to (122.55, 106.05)
vled_via.SetPosition(P(122.55, 106.05))
w = [t.GetWidth() for t in vled_f]
for t in vled_f: b.Remove(t)
add_track('F.Cu', '/VLED', [(122.3, 105.4), (122.55, 105.65)], mm(w[0]))
add_track('F.Cu', '/VLED', [(122.55, 105.65), vled_via.GetPosition()], mm(w[1]))
b.Remove(vled_b)
add_track('B.Cu', '/VLED', [vled_via.GetPosition(), (123.95, 107.45)], 0.25)

# ---------------------------------------------------------------- B-L6: U201 mask dams 0.11 mm
for p in balls: p.SetLocalSolderMaskMargin(F(0.03))

# ---------------------------------------------------------------- B-L7: GND vias along the feed
for x, y in FEED_VIAS: add_via('/GND', x, y, 0.4, 0.2)

# ---------------------------------------------------------------- B-E8: L201 description
l201.GetField('Description').SetText(L201_NEW)

pcbnew.SaveBoard(B, b, True)
print('review fixes applied to', B)
