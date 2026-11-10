"""Self-check of a JLCPCB CPL file: lay each part's JLC (EasyEDA) footprint pads, from jlc_cpl_fix.json, at
its CPL point and rotation, and compare with the board's own pads (the Gerber frame: x, -y). Prints per
LCSC part the worst pad-centre error and whether JLC's pad 1 lands on KiCad's pad 1.
usage (KiCad python): jlc_cpl_check.py BOARD CPL.csv jlc_cpl_fix.json"""
import csv, json, math, sys
import pcbnew
board, cplf, fixf = sys.argv[1:4]
FIX = json.load(open(fixf)); mm = pcbnew.ToMM
fps = {f.GetReference(): f for f in pcbnew.LoadBoard(board).GetFootprints()}
worst = {}; nf = []
for row in csv.DictReader(open(cplf)):
    ref = row['Designator']; f = fps[ref]; lcsc = f.GetFieldText('LCSC'); fx = FIX.get(lcsc, {})
    if 'jlc_pads' not in fx or not isinstance(fx['jlc_pads'], list):
        nf.append(f'{ref} ({lcsc}): {fx.get("status", "no JLC footprint")}'); continue
    X, Y, R = float(row['Mid X'][:-2]), float(row['Mid Y'][:-2]), math.radians(float(row['Rotation']))
    kp = {p.GetNumber(): (mm(p.GetPosition().x), -mm(p.GetPosition().y)) for p in f.Pads() if p.GetNumber()}
    errs = []; pin1 = None
    for n, x, y in fx['jlc_pads']:
        gx, gy = X + x * math.cos(R) - y * math.sin(R), Y + x * math.sin(R) + y * math.cos(R)
        if n in kp: errs.append(math.hypot(gx - kp[n][0], gy - kp[n][1]))
        if n == '1' and '1' in kp: pin1 = math.hypot(gx - kp['1'][0], gy - kp['1'][1]) < 0.35
    e = max(errs) if errs else float('nan')
    if lcsc not in worst or e > worst[lcsc][0]: worst[lcsc] = (e, pin1, ref, fx['drot'], fx['dx'], fx['dy'])
for l, (e, p1, ref, drot, dx, dy) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
    print(f"{ref:8} {l:10} drot {drot:3} dx {dx:+.3f} dy {dy:+.3f}  worst pad error {e:.3f} mm  pin1 {'ok' if p1 else ('n/a' if p1 is None else 'WRONG')}")
for s in nf: print('not checked:', s)
