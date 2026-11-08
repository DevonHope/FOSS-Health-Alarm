"""Band rev A review fixes (review 2026-11-08, hardware/reviews/2026-11-08).

usage (KiCad 10 Python, from any folder):
  .../Python.framework/Versions/Current/bin/python3 review_fixes_2026_11_08.py ../rigid-rev-a.kicad_pcb

Asserts the starting geometry, so it runs once on the 2026-11-07 board and refuses to run twice.
It refills the zones itself with pcbnew's ZONE_FILLER (on the unchanged board this reproduces the committed fill
exactly). Don't refill with `kicad-cli pcb drc --refill-zones --save-board` here: on this board that also generates
87 teardrop zones (the pads have teardrops enabled), which the board never had.

1. C203 pad 2 (GND): solid zone connection. Its thermal relief could only get one spoke into GND_L1
   (up: PMIC_INT track, down: SWDIO and VDD_2V0 vias with R602 below, right: pad 1), KiCad DRC starved_thermal.
2. U202 (KTD2026 UTDFN-8): exposed pad 1.45 x 0.8 -> 1.2 x 0.65 mm (KiCad DFN-8 EP is 0.7 x 1.2; with these
   0.25 x 0.45 mm pins at +/-0.75 mm, 0.65 mm across the rows gives 0.2 mm to the pins, 0.7 would give 0.175),
   paste moved off the EP into two 0.45 x 0.48 mm windows (55 %). Footprint renamed ..._EP1.2x0.65mm.
   Pad 9 keeps its board-level solid zone connection and the GND track from pin 8 to its centre.
3. C208, U202, D702: reference text held absolute board coordinates as footprint offsets (plotted
   110-230 mm off the board on F.Silkscreen). Moved to F.Fab, like the other refs, at the library offsets.
4. J601.3 (SWDCLK dock landing pad, B.Cu): the via moves from the pad centre (where the spring pin lands)
   to the pad's left edge (130.65, 101.1), on its existing F.Cu track, like the VIN and GND pads' edge vias.
The library footprint wakeband.pretty/Kinetic_UTDFN-8_1.5x1.5mm_P0.4mm_EP1.2x0.65mm.kicad_mod (renamed from
..._EP1.45x0.8mm) and the Footprint fields in wakeband.kicad_sym and power.kicad_sch were changed to match, so
DRC reports no lib_footprint_mismatch and parity stays 0.
"""
import sys
import pcbnew

PCB = sys.argv[1]
b = pcbnew.LoadBoard(PCB)
MM = pcbnew.FromMM
def P(x, y): return pcbnew.VECTOR2I(MM(x), MM(y))
def near(a, c, tol=1): return abs(a.x - c.x) <= tol and abs(a.y - c.y) <= tol
def fp(ref):
    f = b.FindFootprintByReference(ref); assert f, ref; return f
def pad(f, num):
    ps = [p for p in f.Pads() if p.GetNumber() == num]; assert len(ps) == 1, (f.GetReference(), num); return ps[0]

# 1. C203 pad 2
c203 = fp('C203'); p2 = pad(c203, '2')
assert p2.GetNetname() == 'GND' and near(p2.GetPosition(), P(116.12, 111.22))
assert p2.GetLocalZoneConnection() == pcbnew.ZONE_CONNECTION_INHERITED
p2.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

# 2. U202 exposed pad
OLD = 'wakeband:Kinetic_UTDFN-8_1.5x1.5mm_P0.4mm_EP1.45x0.8mm'
NEW = 'wakeband:Kinetic_UTDFN-8_1.5x1.5mm_P0.4mm_EP1.2x0.65mm'
u = fp('U202')
assert u.GetFPIDAsString() == OLD and near(u.GetPosition(), P(126.55, 113.2)) and u.GetOrientationDegrees() == 0
ep = pad(u, '9')
assert ep.GetNetname() == 'GND' and near(ep.GetPosition(), P(126.55, 113.2))
assert ep.GetSize(pcbnew.F_Cu) == P(1.45, 0.8) and ep.IsOnLayer(pcbnew.F_Paste)
assert ep.GetLocalZoneConnection() == pcbnew.ZONE_CONNECTION_FULL
assert len(list(u.Pads())) == 9
ep.SetSize(pcbnew.F_Cu, P(1.2, 0.65))
ls = ep.GetLayerSet(); ls.RemoveLayer(pcbnew.F_Paste); ep.SetLayerSet(ls)
pcbnew.KIID.SeedGenerator(20261108)   # deterministic UUIDs for the two new paste pads
for x in (-0.3, 0.3):
    w = pcbnew.PAD(u)
    w.SetNumber('')
    w.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    w.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_RECTANGLE)
    w.SetSize(pcbnew.F_Cu, P(0.45, 0.48))
    s = pcbnew.LSET(); s.AddLayer(pcbnew.F_Paste); w.SetLayerSet(s)
    w.SetFPRelativePosition(P(x, 0))
    u.Add(w)
u.SetFPID(pcbnew.LIB_ID('wakeband', NEW.split(':')[1]))
u.SetLibDescription('Kinetic UTDFN 1.5 x 1.5 mm, 8 pins at 0.4 mm, exposed pad 1.2 x 0.65 mm (KTD2026/KTD2027, '
                    'package code WE). Pads 0.25 x 0.45 mm, rows 1.05 mm apart (inner edges), per the KTD2026 '
                    'datasheet rev 04i. EP after KiCad DFN-8-1EP_1.5x1.5mm_P0.4mm_EP0.7x1.2mm, 0.65 mm across '
                    'the rows for 0.2 mm to the pins; paste on the EP in two 0.45 x 0.48 mm windows (55 %). '
                    'Pin 1 = ST (bottom left, top view).')
u.SetKeywords('UTDFN-8 1.5x1.5 KTD2026')
# GND from pin 8 to the EP centre must still land on the EP
gnd = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == 'GND'
       and t.GetLayer() == pcbnew.F_Cu and (near(t.GetEnd(), ep.GetPosition()) or near(t.GetStart(), ep.GetPosition()))]
assert len(gnd) == 1

# 3. Reference text
for ref, abs_xy, off in (('C208', (128.1, 110.2), (0, -1.16)),
                         ('U202', (124.0, 115.7), (0, -1.6)),
                         ('D702', (130.225, 115.9), (0, -1.8))):
    t = fp(ref).Reference()
    assert t.GetLayer() == pcbnew.F_SilkS and near(t.GetFPRelativePosition(), P(*abs_xy)), ref
    t.SetLayer(pcbnew.F_Fab)
    t.SetFPRelativePosition(P(*off))

# 4. SWDCLK landing-pad via
j = fp('J601'); p3 = pad(j, '3')
assert p3.GetNetname() == '/dock/PAD_SWDCLK' and near(p3.GetPosition(), P(131.5, 101.1)) and p3.IsOnLayer(pcbnew.B_Cu)
vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and near(t.GetPosition(), P(131.5, 101.1))]
assert len(vias) == 1 and vias[0].GetNetname() == '/dock/PAD_SWDCLK'
v = vias[0]
segs = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T
        and (near(t.GetStart(), v.GetPosition()) or near(t.GetEnd(), v.GetPosition()))]
assert len(segs) == 1 and segs[0].GetLayer() == pcbnew.F_Cu
s = segs[0]
assert near(s.GetStart(), P(128.25, 101.1)) and near(s.GetEnd(), P(131.5, 101.1))
v.SetPosition(P(130.65, 101.1))
s.SetEnd(v.GetPosition())

assert pcbnew.ZONE_FILLER(b).Fill(b.Zones())
assert not any(z.IsTeardropArea() for z in b.Zones())
pcbnew.SaveBoard(PCB, b, True)   # True: don't rewrite the .kicad_pro
print('done')
