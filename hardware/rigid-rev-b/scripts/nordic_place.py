"""Place the nRF54L10 support parts exactly as in Nordic's QFAA reference layout v0.8
(nordic_ref_qfaa_0_8.kicad_pcb, imported from Nordic's Altium files), rotated 180 degrees about U1 (positions rounded to 0.005 mm)
so the RF output faces the antenna at the board's left end. Updates placement.json.
Run with KiCad's python."""
import json, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
UX, UY, ROT = float(sys.argv[1]), float(sys.argv[2]), 180
b = pcbnew.LoadBoard(os.path.join(HERE, 'nordic_ref_qfaa_0_8.kicad_pcb'))
mm = pcbnew.ToMM
u = b.FindFootprintByReference('U1'); c = u.GetPosition()
P = json.load(open(os.path.join(HERE, 'placement.json')))
for fp in b.GetFootprints():
    p = fp.GetPosition(); dx, dy = mm(p.x - c.x), mm(p.y - c.y)
    P[fp.GetReference()] = [round(round((UX - dx) / 0.005) * 0.005, 3), round(round((UY - dy) / 0.005) * 0.005, 3), (fp.GetOrientationDegrees() + ROT) % 360, 'F']
P['C11'] = [P['C11'][0], round(P['L4'][1] - 0.285, 3), 270.0, 'F']   # C11 RF pad on the ladder line, GND pad up (clear of the feed)
# sub-0.05 mm nudges so the re-routed links are straight 0/45/90 segments between pad centres
for r, dx, dy in (('L1', -0.03, 0.0), ('C8', -0.005, 0.0), ('C7', 0.0, -0.005), ('C6', 0.0, -0.105)):
    P[r][0] = round(P[r][0] + dx, 3); P[r][1] = round(P[r][1] + dy, 3)
json.dump(P, open(os.path.join(HERE, 'placement.json'), 'w'), indent=0)
print('placed', len(list(b.GetFootprints())), 'Nordic parts about U1 at', UX, UY)
