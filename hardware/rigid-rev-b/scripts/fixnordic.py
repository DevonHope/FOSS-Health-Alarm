"""Post-process the footprints imported from Nordic's QFAA reference layout (Altium -> KiCad):
add F.CrtYd rectangles (pads + 0.03 mm: Nordic's own placement is tighter than IPC courtyards), split the QFN48 exposed-pad paste into
four 1.8 mm windows (the 16 EP vias are filled and capped), set descriptions. Idempotent."""
import os, re, uuid
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wakeband.pretty')
U = lambda: str(uuid.uuid4())
def line(a, b, layer, w=0.05):
    return (f'\t(fp_line\n\t\t(start {a[0]:g} {a[1]:g})\n\t\t(end {b[0]:g} {b[1]:g})\n\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n'
            f'\t\t)\n\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)\n')
for fn in sorted(os.listdir(LIB)):
    if not fn.startswith('Nordic_'): continue
    p = os.path.join(LIB, fn); t = open(p).read()
    if 'F.CrtYd' in t: continue
    xs, ys = [], []
    for m in re.finditer(r'\(pad "[^"]*" smd \w+\s*\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)\s*\(size ([-\d.]+) ([-\d.]+)\)', t):
        x, y, r, w, h = m.groups(); x, y, w, h = map(float, (x, y, w, h))
        if r and abs(float(r)) % 180 == 90: w, h = h, w
        xs += [x - w / 2, x + w / 2]; ys += [y - h / 2, y + h / 2]
    m = 0.03
    x0, x1, y0, y1 = round(min(xs) - m, 2), round(max(xs) + m, 2), round(min(ys) - m, 2), round(max(ys) + m, 2)
    crt = line((x0, y0), (x1, y0), 'F.CrtYd') + line((x1, y0), (x1, y1), 'F.CrtYd') + line((x1, y1), (x0, y1), 'F.CrtYd') + line((x0, y1), (x0, y0), 'F.CrtYd')
    if 'QFN40P600X600X90-48N' in fn:
        pass
    if 'QFN40P600X600X90-48N' in fn and '(layers "F.Cu" "F.Mask" "F.Paste")\n\t\t(uuid' in t.split('(pad "49"')[1][:200]:
        t = t.replace('(pad "49" smd rect\n\t\t(at 0 0)\n\t\t(size 4.7 4.7)\n\t\t(layers "F.Cu" "F.Mask" "F.Paste")',
                      '(pad "49" smd rect\n\t\t(at 0 0)\n\t\t(size 4.7 4.7)\n\t\t(layers "F.Cu" "F.Mask")')
        for sx in (-1.15, 1.15):
            for sy in (-1.15, 1.15):
                crt += f'\t(pad "" smd rect\n\t\t(at {sx} {sy})\n\t\t(size 1.8 1.8)\n\t\t(layers "F.Paste")\n\t\t(uuid "{U()}")\n\t)\n'
    i = t.index('\t(embedded_fonts')
    t = t[:i] + crt + t[i:]
    t = re.sub(r'\(descr "[^"]*"\)', '', t)
    t = t.replace('\t(layer "F.Cu")\n', f'\t(layer "F.Cu")\n\t(descr "From Nordic nRF54L15-QFAA reference layout v0.8 (Altium import); courtyard added")\n', 1)
    open(p, 'w').write(t); print('fixed', fn, (x0, y0, x1, y1))
