"""Review B-L3 (hardware/reviews/2026-11-08): ESD clamps next to the dock contacts. Run once, after
review_fixes_2026_11_08.py.

J601 is four B.Cu landing circles (D 1.6) at x 131.5: SWDCLK y 101.1, SWDIO 103.3, GND 111.7, VIN 113.9.
The clamps used to sit 13-23 mm of trace away (D601 at 121.0,113.8; D602/D603 at 118.75/116.25,111.0).
Now each contact goes through one via (touching its landing circle) and a short F.Cu run straight into
its clamp pad, and the rest of the net leaves from that clamp pad, so ESD is clamped before it reaches
anything else. Case keep-outs respected: dock land (F side, x >= 127.6, y < 103.2) and the post behind
the bottom pin pair (x >= 131.75, y 110.8-114.6) carry copper under mask only, no parts.

  SWD   D602 (SWDCLK) and D603 (SWDIO) move into the strip right of U501, just below the land:
        D602 vertical at (130.9, 104.0), D603 horizontal at (132.1, 103.85), each with its own GND via.
        SWDCLK: via (131.2,101.7) in the landing -> F.Cu -> D602.1 -> F.Cu y 103.65 -> the old In2 route.
        SWDIO:  via (131.35,102.65) in the landing -> F.Cu -> D603.1 -> via (131.5,104.6) -> B.Cu
        -> the old B.Cu route at (129.85,108.7). The old far-end routes to R601/R602 stay.
        C502 (U501 REG cap) moves 0.3 mm down and turns to horizontal (131.5, 105.38); it shares D603's GND via.
        PMID used to run down F.Cu at x 132.6 past the clamps: it now hops to B.Cu between the two SWD
        landings (via 132.45,102.2) and back to F.Cu at (132.45,106.6), beside TP203.
  VIN   D601 becomes a DFN1006 TVS (ESD5681N07, 7 V standoff, 11 V clamp at 8 kV ESD, 16 V at 27 A
        8/20 us; the SMF12A clamped 19.9 V) at (131.25, 110.8), where TP705 was, over the GND landing:
        via (132.0,113.3) in the VIN landing -> F.Cu (under the post) -> D601.1 -> via (131.25,109.8)
        -> the old In2 route to the charger. D601.2 has a GND via (131.25,111.75) into the GND landing.
        The 13 mm In2 run to the old D601 position and its branch are removed.
        TP705 (PMID test pad) moves to (127.1, 101.6) on the PMID run along the top edge; the PMID In2
        link to U202 now starts at the PMID via (130.55,109.1).

Asserts the starting geometry, so a second run fails. Save keeps the project settings (SaveBoard(..., True)).
Refill afterwards: kicad-cli pcb drc --refill-zones --save-board rigid-rev-c.kicad_pcb
usage (KiCad python): relayout_esd_2026_11_08.py [BOARD]"""
import os, sys, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
B = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'rigid-rev-c.kicad_pcb')
b = pcbnew.LoadBoard(B); F, mm = pcbnew.FromMM, pcbnew.ToMM
P = lambda x, y: pcbnew.VECTOR2I(F(x), F(y))
L = {n: b.GetLayerID(n) for n in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')}
def near(a, x, y, tol=0.002): return abs(mm(a.x) - x) < tol and abs(mm(a.y) - y) < tol
def seg(layer, net, x0, y0, x1, y1):
    m = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == L[layer] and t.GetNetname() == net
         and ((near(t.GetStart(), x0, y0) and near(t.GetEnd(), x1, y1)) or (near(t.GetStart(), x1, y1) and near(t.GetEnd(), x0, y0)))]
    assert len(m) == 1, f'expected one {layer} {net} track ({x0},{y0})-({x1},{y1}), found {len(m)}'
    return m[0]
def via(net, x, y):
    m = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net and near(t.GetPosition(), x, y)]
    assert len(m) == 1, f'expected one {net} via at ({x},{y}), found {len(m)}'
    return m[0]
def fp(ref): return b.FindFootprintByReference(ref)
def pad(ref, num): return [p for p in fp(ref).Pads() if p.GetNumber() == num][0]
def add_track(layer, net, pts, w):
    """pts: VECTOR2I or (x, y) mm; consecutive points become segments."""
    pts = [p if isinstance(p, pcbnew.VECTOR2I) else P(*p) for p in pts]
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(F(w)); t.SetLayer(L[layer])
        t.SetNet(b.FindNet(net)); b.Add(t)
def add_via(net, x, y, d, drill):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(F(d)); v.SetDrill(F(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v); return v
def place(ref, x, y, deg, want):
    """move a footprint and check where its pads land: want = {pad: (x, y)}"""
    f = fp(ref); f.SetOrientationDegrees(deg); f.SetPosition(P(x, y))
    for n, (px, py) in want.items():
        assert near(pad(ref, n).GetPosition(), px, py, 1e-4), f'{ref}.{n} at {mm(pad(ref, n).GetPosition().x)},{mm(pad(ref, n).GetPosition().y)}'

# ---------------------------------------------------------------- starting geometry (fails on a second run)
for ref, x, y in (('D601', 121.0, 113.8), ('D602', 118.75, 111.0), ('D603', 116.25, 111.0), ('C502', 131.2, 104.65),
                  ('TP705', 131.6, 110.5)):
    assert near(fp(ref).GetPosition(), x, y), f'{ref} is not at ({x}, {y})'
assert fp('D601').GetFPIDAsString() == 'Diode_SMD:D_SOD-123F'
gone = [
    # VIN: contact via, In2 run to the old D601 and the branch back up to the charger route, old D601 stubs
    seg('B.Cu', '/VIN', 131.5, 113.9, 132.25, 113.9), seg('B.Cu', '/VIN', 132.25, 113.9, 132.35, 114.0),
    via('/VIN', 132.35, 114.0), seg('In2.Cu', '/VIN', 131.85, 114.5, 132.35, 114.0),
    seg('In2.Cu', '/VIN', 121.1, 114.5, 131.85, 114.5), seg('In2.Cu', '/VIN', 121.05, 114.45, 121.1, 114.5),
    seg('In2.Cu', '/VIN', 121.05, 114.45, 127.75, 114.45), seg('In2.Cu', '/VIN', 127.75, 114.45, 131.5, 110.7),
    seg('In2.Cu', '/VIN', 131.5, 110.7, 131.5, 108.85), seg('In2.Cu', '/VIN', 131.5, 108.85, 129.6, 106.95),
    via('/VIN', 121.05, 114.45), seg('F.Cu', '/VIN', 119.6, 113.8, 120.25, 114.45), seg('F.Cu', '/VIN', 120.25, 114.45, 121.05, 114.45),
    # GND stubs from the old clamp pads (their vias stay as stitching)
    seg('F.Cu', '/GND', 122.4, 113.8, 122.95, 113.8), seg('F.Cu', '/GND', 119.1, 111.0, 119.65, 111.0),
    seg('F.Cu', '/GND', 116.6, 111.0, 117.15, 111.0),
    # SWDCLK: contact via and its F.Cu run to the In2 via; old D602 via-in-pad and its B.Cu corner
    seg('B.Cu', '/PAD_SWDCLK', 131.5, 101.1, 131.8, 101.1), seg('B.Cu', '/PAD_SWDCLK', 131.8, 101.1, 132.1, 101.4),
    via('/PAD_SWDCLK', 132.1, 101.4), seg('F.Cu', '/PAD_SWDCLK', 132.1, 101.4, 129.85, 103.65),
    seg('F.Cu', '/PAD_SWDCLK', 129.85, 103.65, 129.05, 103.65),
    seg('B.Cu', '/PAD_SWDCLK', 122.85, 111.5, 118.9, 111.5), seg('B.Cu', '/PAD_SWDCLK', 118.9, 111.5, 118.4, 111.0),
    seg('B.Cu', '/PAD_SWDCLK', 118.4, 111.0, 117.3, 112.1), via('/PAD_SWDCLK', 118.4, 111.0),
    # SWDIO: B.Cu run from the contact down the board edge
    seg('B.Cu', '/PAD_SWDIO', 131.5, 103.3, 132.1, 103.9), seg('B.Cu', '/PAD_SWDIO', 132.1, 103.9, 132.1, 106.45),
    seg('B.Cu', '/PAD_SWDIO', 132.1, 106.45, 129.85, 108.7),
    # C502 (REG cap) copper
    seg('F.Cu', '/REG', 129.6, 104.85, 129.88, 105.13), seg('F.Cu', '/REG', 129.88, 105.13, 131.2, 105.13),
    seg('F.Cu', '/GND', 131.2, 104.17, 130.65, 104.17), via('/GND', 130.65, 104.17),
    # PMID: F.Cu down the board edge past the clamps; TP705 stub and via; its In2 link to U202
    seg('F.Cu', '/PMID', 132.6, 101.15, 132.6, 106.45), seg('F.Cu', '/PMID', 132.6, 106.45, 131.8, 107.25),
    seg('F.Cu', '/PMID', 131.6, 110.5, 130.95, 110.5), via('/PMID', 130.95, 110.5),
    seg('In2.Cu', '/PMID', 130.95, 110.5, 128.0, 113.45),
    seg('F.Cu', '/PMID', 132.3, 100.85, 122.2, 100.85),
]
for t in gone: b.Remove(t)

# ---------------------------------------------------------------- D601: SMF12A (SOD-123F) -> ESD5681N07 (DFN1006)
old = fp('D601')
new = pcbnew.FootprintLoad('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Diode_SMD.pretty', 'D_SOD-882')
new.SetFPID(pcbnew.LIB_ID('Diode_SMD', 'D_SOD-882'))
new.SetReference('D601'); new.SetValue('ESD5681N07')
for name, val in (('Datasheet', ''), ('Description', 'VIN TVS'), ('LCSC', 'C240204'), ('MPN', 'Will Semi ESD5681N07-2/TR')):
    new.SetField(name, val)
for fld in new.GetFields():
    if fld.GetName() not in ('Reference', 'Value'):
        fld.SetVisible(False); fld.SetLayer(pcbnew.F_Fab)
new.SetPath(old.GetPath()); new.SetSheetname(old.GetSheetname()); new.SetSheetfile(old.GetSheetfile())
new.SetAttributes(old.GetAttributes())
for txt in (new.Reference(), new.Value()):   # the board keeps reference and value on F.Fab
    txt.SetLayer(pcbnew.F_Fab)
b.Remove(old); b.Add(new)
for p in new.Pads():
    if p.GetNumber() == '1': p.SetNet(b.FindNet('/VIN'))
    elif p.GetNumber() == '2': p.SetNet(b.FindNet('/GND'))
place('D601', 131.25, 110.8, 270, {'1': (131.25, 110.45), '2': (131.25, 111.15)})   # cathode (pin 1, VIN) up

# ---------------------------------------------------------------- moves
place('D602', 130.9, 104.0, 270, {'1': (130.9, 103.65), '2': (130.9, 104.35)})
place('D603', 132.1, 103.85, 0, {'1': (131.75, 103.85), '2': (132.45, 103.85)})
place('C502', 131.5, 105.38, 0, {'1': (131.02, 105.38), '2': (131.98, 105.38)})
place('TP705', 127.1, 101.6, 0, {'1': (127.1, 101.6)})
for ref in ('D601', 'D602', 'D603', 'C502', 'TP705'):   # F.Fab reference next to the part
    f = fp(ref); f.Reference().SetPosition(f.GetPosition() + P(0, -0.9 if ref != 'D601' else 0)); f.Reference().SetTextAngleDegrees(0)
fp('D601').Reference().SetPosition(P(130.2, 110.8))

# ---------------------------------------------------------------- SWDCLK
add_via('/PAD_SWDCLK', 131.2, 101.7, 0.45, 0.3)                                   # touches the J601.3 landing
add_track('F.Cu', '/PAD_SWDCLK', [(131.2, 101.7), (130.9, 102.0), pad('D602', '1').GetPosition()], 0.15)
add_track('F.Cu', '/PAD_SWDCLK', [pad('D602', '1').GetPosition(), (129.05, 103.65)], 0.15)   # on to the In2 via
add_track('B.Cu', '/PAD_SWDCLK', [(122.85, 111.5), (117.9, 111.5), (117.3, 112.1)], 0.15)   # old D602 via removed
add_via('/GND', 130.3, 104.35, 0.4, 0.2)
add_track('F.Cu', '/GND', [pad('D602', '2').GetPosition(), (130.3, 104.35)], 0.2)

# ---------------------------------------------------------------- SWDIO
add_via('/PAD_SWDIO', 131.35, 102.65, 0.45, 0.3)                                  # touches the J601.4 landing
add_track('F.Cu', '/PAD_SWDIO', [(131.35, 102.65), (131.75, 103.05), pad('D603', '1').GetPosition()], 0.15)
add_via('/PAD_SWDIO', 131.5, 104.6, 0.45, 0.3)
add_track('F.Cu', '/PAD_SWDIO', [pad('D603', '1').GetPosition(), (131.75, 104.35), (131.5, 104.6)], 0.15)
add_track('B.Cu', '/PAD_SWDIO', [(131.5, 104.6), (131.5, 107.05), (129.85, 108.7)], 0.15)
add_via('/GND', 132.2, 104.5, 0.4, 0.2)
add_track('F.Cu', '/GND', [pad('D603', '2').GetPosition(), (132.45, 104.25), (132.2, 104.5)], 0.2)

# ---------------------------------------------------------------- C502
add_track('F.Cu', '/REG', [pad('U501', '1').GetPosition(), (130.13, 105.38), pad('C502', '1').GetPosition()], 0.2)
add_track('F.Cu', '/GND', [pad('C502', '2').GetPosition(), (131.98, 104.72), (132.2, 104.5)], 0.2)

# ---------------------------------------------------------------- PMID
add_track('F.Cu', '/PMID', [(132.3, 100.85), (127.1, 100.85)], 0.15)
add_track('F.Cu', '/PMID', [(127.1, 100.85), (122.2, 100.85)], 0.15)
add_track('F.Cu', '/PMID', [(127.1, 100.85), pad('TP705', '1').GetPosition()], 0.15)
add_track('F.Cu', '/PMID', [(132.6, 101.15), (132.6, 102.05), (132.45, 102.2)], 0.15)
add_via('/PMID', 132.45, 102.2, 0.45, 0.3)                                        # between the two SWD landings
add_track('B.Cu', '/PMID', [(132.45, 102.2), (132.6, 102.35), (132.6, 106.45), (132.45, 106.6)], 0.15)
add_via('/PMID', 132.45, 106.6, 0.45, 0.3)
add_track('F.Cu', '/PMID', [(132.45, 106.6), (131.8, 107.25)], 0.15)
add_track('In2.Cu', '/PMID', [(130.55, 109.1), (130.55, 110.9), (128.0, 113.45)], 0.3)

# ---------------------------------------------------------------- VIN
add_via('/VIN', 132.0, 113.3, 0.45, 0.3)                                          # touches the J601.1 landing
add_track('F.Cu', '/VIN', [(132.0, 113.3), (132.0, 110.8), (131.65, 110.45), pad('D601', '1').GetPosition()], 0.3)
add_via('/VIN', 131.25, 109.8, 0.45, 0.3)
add_track('F.Cu', '/VIN', [pad('D601', '1').GetPosition(), (131.25, 109.8)], 0.3)
add_track('In2.Cu', '/VIN', [(131.25, 109.8), (131.25, 108.6), (129.6, 106.95)], 0.15)
add_via('/GND', 131.25, 111.75, 0.4, 0.2)                                         # into the J601.2 landing
add_track('F.Cu', '/GND', [pad('D601', '2').GetPosition(), (131.25, 111.75)], 0.25)

pcbnew.SaveBoard(B, b, True)
print('saved', B)
