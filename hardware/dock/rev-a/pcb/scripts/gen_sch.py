"""Generate dock-pcb-rev-a.kicad_sch from parts.py: every symbol placed on a grid,
each connected pin gets a net label at its end, unused pins a no-connect flag."""
import sys, uuid, re
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import symlib, parts
OUT = sys.argv[1]
PROJ = "dock-pcb-rev-a"
ROOT = str(uuid.uuid4())
U = lambda: str(uuid.uuid4())
LOCAL = os.path.join(HERE, '..', 'dock.kicad_sym')

def load(libid):
    lib, name = libid.split(':')
    blk = symlib.get(lib, name, LOCAL if lib == 'dock' else None)
    return blk

def embed(libid, blk):
    name = libid.split(':')[1]
    b = blk.replace(f'(symbol "{name}"', f'(symbol "{libid}"', 1)
    return '\t\t' + b.replace('\n', '\n\t') + '\n'

def prop(k, v, x, y, hide=False):
    v = v.replace('"', '\\"')
    h = '\n\t\t\t(hide yes)' if hide else ''
    return (f'\t\t(property "{k}" "{v}"\n\t\t\t(at {x:.2f} {y:.2f} 0){h}\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
            f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')

def symbol(libid, ref, val, fp, x, y, pins, lcsc='', mpn='', desc='', unit_pins=None):
    s = (f'\t(symbol\n\t\t(lib_id "{libid}")\n\t\t(at {x:.2f} {y:.2f} 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n'
         f'\t\t(in_bom {"no" if ref.startswith(("#", "TP")) else "yes"})\n\t\t(on_board {"no" if ref.startswith("#") else "yes"})\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "{U()}")\n')
    s += prop("Reference", ref, x + 2.54, y - 6, ref.startswith('#'))
    s += prop("Value", val, x + 2.54, y + 6)
    s += prop("Footprint", fp, x, y, True) + prop("Datasheet", "", x, y, True) + prop("Description", desc, x, y, True)
    if lcsc: s += prop("LCSC", lcsc, x, y, True)
    if mpn: s += prop("MPN", mpn, x, y, True)
    for p in pins:
        s += f'\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
    s += (f'\t\t(instances\n\t\t\t(project "{PROJ}"\n\t\t\t\t(path "/{ROOT}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n'
          f'\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    return s

def label(net, x, y, ang):
    j = 'left bottom' if ang in (0, 90) else 'right bottom'
    return (f'\t(label "{net}"\n\t\t(at {x:.2f} {y:.2f} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {j})\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')

def nc(x, y): return f'\t(no_connect\n\t\t(at {x:.2f} {y:.2f})\n\t\t(uuid "{U()}")\n\t)\n'

lib_blocks, body = {}, ''
GRID = 2.54
def snap(v): return round(v / GRID) * GRID
# placement: big parts first in a row, small parts in a grid below
x, y, rowh = 40.64, 50.8, 0
for i, (ref, libid, val, fp, lcsc, mpn, nets, ncs, desc) in enumerate(parts.PARTS):
    blk = lib_blocks.setdefault(libid, load(libid))
    pl = symlib.pins(blk)
    xs = [p['x'] for p in pl]; ys = [p['y'] for p in pl]
    w = (max(xs) - min(xs)) if xs else 5; h = (max(ys) - min(ys)) if ys else 5
    w = max(w, 5) + 30; h = max(h, 5) + 15
    if x + w > 390: x, y, rowh = 40.64, y + rowh, 0
    cx, cy = snap(x - min(xs) + 12.7 if xs else x), snap(y - min(-yy for yy in ys) + 5 if ys else y)
    allpins = sorted({p['num'] for p in pl}, key=lambda s: (len(s), s))
    body += symbol(libid, ref, val, fp, cx, cy, allpins, lcsc, mpn, desc)
    seen = set()
    for p in pl:
        if (p['num']) in seen: continue
        seen.add(p['num'])
        px, py = cx + p['x'], cy - p['y']
        ang = {0: 180, 180: 0, 90: 270, 270: 90}[int(p['a']) % 360]
        if p['num'] in nets:
            body += label(nets[p['num']], px, py, ang)
        else:
            assert p['num'] in ncs, (ref, p['num'], p['name'])
            body += nc(px, py)
    x += w; rowh = max(rowh, h)
# power flags
fl = load('power:PWR_FLAG'); lib_blocks['power:PWR_FLAG'] = fl
fx = 40.64; fy = y + rowh + 20
for k, net in enumerate(parts.FLAGS):
    X = snap(fx + k * 25.4); Y = snap(fy)
    body += symbol('power:PWR_FLAG', f'#FLG{k+1:02d}', 'PWR_FLAG', '', X, Y, ['1'])
    body += label(net, X, Y, 0)
head = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "{ROOT}")\n\t(paper "A3")\n'
        '\t(title_block\n\t\t(title "WakeBand dock rev A - USB-C charger and SWD probe")\n\t\t(date "2026-11-07")\n\t\t(rev "A")\n'
        '\t\t(company "FOSS Health Alarm")\n\t\t(comment 1 "RP2040 running Raspberry Pi debugprobe (Debug Probe pin map: SWCLK GPIO12, SWDI GPIO13, SWDIO GPIO14, LEDs GPIO2/16)")\n'
        '\t\t(comment 2 "Band side of SWD at 1.8 V (no VTref on the 4 dock pins); VIN 5 V through a 0.45 A switch")\n\t)\n\t(lib_symbols\n')
txt = head + ''.join(embed(k, v) for k, v in lib_blocks.items()) + '\t)\n' + body
txt += f'\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n'
open(OUT, 'w').write(txt)
print('symbols', len(parts.PARTS), 'libs', len(lib_blocks))
