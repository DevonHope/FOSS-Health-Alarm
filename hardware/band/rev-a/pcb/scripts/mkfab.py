"""Re-plot the rigid rev A fab package and layout PDF with kicad-cli 10 (same commands as the 2026-11-07 package;
checked on the unchanged board: every file identical apart from dates, and F.Cu apart from the run-to-run jitter
of the --check-zones refill).  usage: python3 mkfab.py

bom_jlcpcb.csv is curated by hand (comments differ from the schematic BOM), so it is only read here, to pick the
assembled parts for the CPL and to zip it.  rigid-rev-a.pdf (schematic) and fab/u1-pin1-drawing.pdf are not made here.
"""
import csv, os, subprocess, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.normpath(os.path.join(HERE, '..'))
FAB = os.path.join(B, 'fab'); GER = os.path.join(FAB, 'gerbers')
PCB = os.path.join(B, 'rigid-rev-a.kicad_pcb')
K = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
LAYERS = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
PDF_LAYERS = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Fab,User.Drawings'
def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
prl = os.path.join(B, 'rigid-rev-a.kicad_prl'); had_prl = os.path.exists(prl)
for f in os.listdir(GER): os.remove(os.path.join(GER, f))
run(K, 'pcb', 'export', 'gerbers', '--layers', LAYERS, '--subtract-soldermask', '--check-zones', '-o', GER + '/', PCB)
run(K, 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format',
    'gerberx2', '--excellon-units', 'mm', '-o', GER + '/', PCB)
run(K, 'pcb', 'export', 'pdf', '--mode-multipage', '-l', PDF_LAYERS, '--cl', 'Edge.Cuts',
    '-o', os.path.join(B, 'rigid-rev-a-layout.pdf'), PCB)
# CPL: top-side placements of the parts in bom_jlcpcb.csv
bom = list(csv.DictReader(open(os.path.join(FAB, 'bom_jlcpcb.csv'))))
assembled = {r for row in bom for r in row['Designator'].split(',')}
pos = os.path.join(FAB, '_pos.csv')
run(K, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'front', '--exclude-dnp', '-o', pos, PCB)
rows = [r for r in csv.DictReader(open(pos)) if r['Ref'] in assembled]
os.remove(pos)
if {r['Ref'] for r in rows} != assembled: raise SystemExit('CPL and BOM disagree')
with open(os.path.join(FAB, 'cpl_jlcpcb_top.csv'), 'w') as f:
    f.write('Designator,Mid X,Mid Y,Layer,Rotation\n')
    for r in rows:
        f.write(f"{r['Ref']},{float(r['PosX']):.4f}mm,{float(r['PosY']):.4f}mm,Top,{float(r['Rot']) % 360:.1f}\n")
z = os.path.join(FAB, 'rigid-rev-a-fab.zip')
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fn in sorted(os.listdir(GER)): zf.write(os.path.join(GER, fn), fn)
    for fn in ('bom_jlcpcb.csv', 'cpl_jlcpcb_top.csv'): zf.write(os.path.join(FAB, fn), fn)
if not had_prl and os.path.exists(prl): os.remove(prl)
print('fab:', len(os.listdir(GER)), 'gerber/drill files,', len(rows), 'placed parts ->', z)
