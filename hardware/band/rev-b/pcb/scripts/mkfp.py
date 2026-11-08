"""Write the DSBGA-25 footprint for the BQ25120A (TI YFP, 5x5 balls, 0.4 mm pitch) to ../wakeband.pretty.
Land pattern per the datasheet: 0.23 mm round NSMD copper, mask opening 0.31 mm; paste 0.25 mm square (R0.05)."""
import os, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'wakeband.pretty', 'TI_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm.kicad_mod')
P, BODY = 0.4, 2.53
U = lambda: str(uuid.uuid4())
def line(x0, y0, x1, y1, layer, w):
    return (f'\t(fp_line\n\t\t(start {x0:g} {y0:g})\n\t\t(end {x1:g} {y1:g})\n\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)\n')
def rect(h, layer, w):
    return line(-h, -h, h, -h, layer, w) + line(h, -h, h, h, layer, w) + line(h, h, -h, h, layer, w) + line(-h, h, -h, -h, layer, w)
s = ('(footprint "TI_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm"\n\t(version 20260206)\n\t(generator "pcbnew")\n\t(generator_version "10.0")\n'
     '\t(layer "F.Cu")\n\t(descr "TI YFP DSBGA-25, 2.5x2.5 mm, 0.4 mm pitch, 0.23 mm NSMD pads (BQ25120A datasheet p.69-70)")\n'
     '\t(tags "DSBGA WCSP BGA 0.4mm")\n')
for k, v, y, lay in (('Reference', 'REF**', -2.0, 'F.SilkS'), ('Value', 'TI_DSBGA-25', 2.0, 'F.Fab')):
    s += (f'\t(property "{k}" "{v}"\n\t\t(at 0 {y} 0)\n\t\t(layer "{lay}")\n\t\t(uuid "{U()}")\n\t\t(effects\n\t\t\t(font\n'
          f'\t\t\t\t(size 0.6 0.6)\n\t\t\t\t(thickness 0.1)\n\t\t\t)\n\t\t)\n\t)\n')
s += '\t(attr smd)\n'
s += rect(BODY / 2, 'F.Fab', 0.1) + rect(1.55, 'F.CrtYd', 0.05)
s += line(-1.4, -1.0, -1.4, -1.4, 'F.SilkS', 0.12) + line(-1.4, -1.4, -1.0, -1.4, 'F.SilkS', 0.12)
for r, row in enumerate('ABCDE'):
    for c in range(5):
        x, y = round((c - 2) * P, 3), round((r - 2) * P, 3)
        s += (f'\t(pad "{row}{c + 1}" smd circle\n\t\t(at {x:g} {y:g})\n\t\t(size 0.23 0.23)\n\t\t(layers "F.Cu" "F.Mask")\n'
              f'\t\t(solder_mask_margin 0.04)\n\t\t(uuid "{U()}")\n\t)\n')
        s += (f'\t(pad "" smd roundrect\n\t\t(at {x:g} {y:g})\n\t\t(size 0.25 0.25)\n\t\t(layers "F.Paste")\n'
              f'\t\t(roundrect_rratio 0.2)\n\t\t(uuid "{U()}")\n\t)\n')
s += '\t(embedded_fonts no)\n)\n'
open(OUT, 'w').write(s)
print('wrote', OUT)
