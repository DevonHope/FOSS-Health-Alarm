"""Band rev B: follow-ups from the independent verification of 2026-11-08. Run once, after
relayout_esd_2026_11_08.py.  usage (KiCad python): followups_2026_11_08.py [BOARD]

1. D601's GND via moves from (131.25, 111.75), 0.26 mm from the J601.2 (GND) landing centre, i.e. under
   the dock's spring-pin plunger, to (130.85, 111.7): 0.65 mm from the centre, at the landing's edge like
   the SWDCLK, SWDIO and VIN landing vias.
2. B-L10: the board title block still read "WakeBand rigid rev A", rev A, "mounts parts-side down"
   (inherited from rev A's board file); the Gerber job file and every Gerber header carry that revision.
   Now rev B, with the right mounting (parts on F.Cu towards the shell roof, dock contacts on B.Cu).
Saves with SaveBoard(..., True) so the .kicad_pro is untouched; refill afterwards with kicad-cli."""
import sys
import pcbnew

MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
path = sys.argv[1] if len(sys.argv) > 1 else "rigid-rev-b.kicad_pcb"
b = pcbnew.LoadBoard(path)
keep = []
near = lambda p, q: abs(p.x - q.x) <= 1000 and abs(p.y - q.y) <= 1000

old, new = V(131.25, 111.75), V(130.85, 111.7)
vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and near(t.GetPosition(), old)]
assert len(vias) == 1, "D601 GND via not where expected (already moved?)"
segs = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.F_Cu
        and {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)} == {(MM(131.25), MM(111.15)), (old.x, old.y)}]
assert len(segs) == 1
gnd = vias[0].GetNet()
b.Remove(segs[0]); keep.append(segs[0])
vias[0].SetPosition(new)
pad = b.FindFootprintByReference("D601").FindPadByNumber("2").GetPosition()
assert near(pad, V(131.25, 111.15))
for a, c in ((pad, V(131.25, 111.3)), (V(131.25, 111.3), new)):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(a); t.SetEnd(c); t.SetLayer(pcbnew.F_Cu); t.SetWidth(MM(0.25)); t.SetNet(gnd)
    b.Add(t)

tb = b.GetTitleBlock()
assert tb.GetRevision() == "A", tb.GetRevision()
tb.SetTitle("WakeBand rigid rev B")
tb.SetRevision("B")
tb.SetDate("2026-11-08")
tb.SetComment(0, "4-layer 0.8 mm FR4 (JLC04081H-7628), ENIG, 15 x 33 mm; parts on F.Cu towards the shell roof, "
                 "dock contacts on B.Cu at the wrist")
pcbnew.SaveBoard(path, b, True)
print("D601 GND via moved, title block rev B")
