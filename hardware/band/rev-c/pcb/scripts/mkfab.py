"""JLCPCB fab package for rigid rev B: Gerbers + drill (kicad-cli), BOM with LCSC numbers (from parts.py),
top-side CPL (from the board), zipped into ../fab/rigid-rev-c-fab.zip.  usage: python3 mkfab.py"""
import csv, os, subprocess, sys, zipfile
from collections import OrderedDict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts
B = os.path.normpath(os.path.join(HERE, '..'))
FAB = os.path.join(B, 'fab'); GER = os.path.join(FAB, 'gerbers')
PCB = os.path.join(B, 'rigid-rev-c.kicad_pcb')
K = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
os.makedirs(GER, exist_ok=True)
for f in os.listdir(GER): os.remove(os.path.join(GER, f))
LAYERS = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
run(K, 'pcb', 'export', 'gerbers', '--layers', LAYERS, '--subtract-soldermask', '--check-zones', '-o', GER + '/', PCB)
run(K, 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2',
    '--excellon-units', 'mm', '-o', GER + '/', PCB)
# BOM: only assembled parts (LCSC number, not DNP, not pads/jumpers)
groups = OrderedDict()
for ref, lib, val, fp, lcsc, mpn, nets, nc, desc in parts.PARTS:
    if not lcsc or ref in parts.DNP or ref.startswith(('TP', 'J6', 'JP')): continue
    k = (val, fp.split(':')[1], lcsc, mpn)
    groups.setdefault(k, []).append(ref)
def refkey(r):
    import re
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))
with open(os.path.join(FAB, 'bom_jlcpcb.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC', 'MPN'])
    for (val, fp, lcsc, mpn), refs in sorted(groups.items(), key=lambda kv: refkey(sorted(kv[1], key=refkey)[0])):
        w.writerow([val, ','.join(sorted(refs, key=refkey)), fp, lcsc, mpn])
# CPL from the board (top side, assembled parts only)
pos = os.path.join(FAB, '_pos.csv')
run(K, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'front', '--exclude-dnp', '-o', pos, PCB)
assembled = {r for refs in groups.values() for r in refs}
rows = list(csv.DictReader(open(pos)))
with open(os.path.join(FAB, 'cpl_jlcpcb_top.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in rows:
        if r['Ref'] not in assembled: continue
        w.writerow([r['Ref'], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", 'Top', r['Rot']])
os.remove(pos)
missing = assembled - {r['Ref'] for r in rows}
if missing: raise SystemExit(f'CPL missing {sorted(missing)}')
z = os.path.join(FAB, 'rigid-rev-c-fab.zip')
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fn in sorted(os.listdir(GER)): zf.write(os.path.join(GER, fn), fn)
    for fn in ('bom_jlcpcb.csv', 'cpl_jlcpcb_top.csv'): zf.write(os.path.join(FAB, fn), fn)
print('fab:', len(os.listdir(GER)), 'gerber/drill files,', len(groups), 'BOM lines,', len(assembled), 'placed parts ->', z)
