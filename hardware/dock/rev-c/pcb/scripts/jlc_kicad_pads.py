"""Dump, per LCSC part, the KiCad footprint's pads in the footprint's own frame (mm, y up, before the
footprint's rotation): input for jlc_cpl_fix.py.  usage (KiCad python): jlc_kicad_pads.py BOARD OUT.json"""
import json, math, sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
out = {}
for f in b.GetFootprints():
    if not f.HasField('LCSC'): continue
    lcsc = f.GetFieldText('LCSC')
    if not lcsc or lcsc in out: continue
    th = math.radians(f.GetOrientationDegrees()); o = f.GetPosition(); pads = []
    for p in f.Pads():
        if not p.GetNumber() or not (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)): continue
        vx, vy = mm(p.GetPosition().x - o.x), -mm(p.GetPosition().y - o.y)
        lx = vx * math.cos(-th) - vy * math.sin(-th); ly = vx * math.sin(-th) + vy * math.cos(-th)
        pads.append([p.GetNumber(), round(lx, 4), round(ly, 4)])
    out[lcsc] = {'ref': f.GetReference(), 'fp': f.GetFPIDAsString().split(':')[1], 'rot': f.GetOrientationDegrees(), 'pads': pads}
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(len(out), 'LCSC parts')
