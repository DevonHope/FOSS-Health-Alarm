"""JLCPCB files for the 2 x 2 panel (fab/panel/rigid-rev-b-panel.kicad_pcb, from mkpanel.sh):
Gerbers + Excellon drill zipped (kicad-cli), BOM grouped by LCSC number and top-side CPL, both from the
panel's footprints (references are <ref>_<board>, so BOM and CPL rows match one to one).
Not assembled: test/landing pads (TP*, J6*), the solder jumper (JP*) and DNP parts.
usage (KiCad python): panelfab.py"""
import csv, os, re, subprocess, sys, zipfile, tempfile
from collections import OrderedDict
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts
B = os.path.normpath(os.path.join(HERE, '..'))
PAN = os.path.join(B, 'fab', 'panel', 'rigid-rev-b-panel.kicad_pcb')
OUT = os.path.join(B, 'fab', 'jlcpcb')
K = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
LAYERS = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
os.makedirs(OUT, exist_ok=True)
with tempfile.TemporaryDirectory() as g:
    run(K, 'pcb', 'export', 'gerbers', '--layers', LAYERS, '--subtract-soldermask', '-o', g + '/', PAN)
    run(K, 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map',
        '--map-format', 'gerberx2', '--excellon-units', 'mm', '-o', g + '/', PAN)
    files = sorted(os.listdir(g))
    with zipfile.ZipFile(os.path.join(OUT, 'gerbers.zip'), 'w', zipfile.ZIP_DEFLATED) as zf:
        for fn in files: zf.write(os.path.join(g, fn), fn)
SKIP = tuple(('TP', 'J6', 'JP'))
def base(r): return r.rsplit('_', 1)[0]
b = pcbnew.LoadBoard(PAN); mm = pcbnew.ToMM
info = {p[0]: p for p in parts.PARTS}
groups = OrderedDict(); cpl = []
for f in b.GetFootprints():
    r = f.GetReference(); br = base(r)
    if br not in info or br.startswith(SKIP) or br in parts.DNP: continue
    lcsc = f.GetFieldText('LCSC') if f.HasField('LCSC') else ''
    if lcsc != info[br][4]: raise SystemExit(f'{r}: LCSC {lcsc!r} != parts.py {info[br][4]!r}')
    if f.GetLayer() != pcbnew.F_Cu: raise SystemExit(f'{r} is not on the top side')
    groups.setdefault((info[br][2], info[br][3].split(':')[1], lcsc), []).append(r)
    p = f.GetPosition()
    cpl.append((r, mm(p.x), -mm(p.y), f.GetOrientationDegrees()))
def key(r):
    m = re.match(r'([A-Z]+)(\d+)_(\d+)', r); return (m.group(1), int(m.group(2)), int(m.group(3)))
with open(os.path.join(OUT, 'bom.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC'])
    for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: key(sorted(kv[1], key=key)[0])):
        w.writerow([val, ','.join(sorted(refs, key=key)), fp, lcsc])
with open(os.path.join(OUT, 'pos.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r, x, y, rot in sorted(cpl, key=lambda c: key(c[0])):
        w.writerow([r, f'{x:.4f}mm', f'{y:.4f}mm', 'Top', f'{rot % 360:.1f}'])
per = len(cpl) // 4
print(f'gerbers.zip ({len(files)} files), bom.csv {len(groups)} lines / {len(cpl)} placements ({per} per board), pos.csv')
