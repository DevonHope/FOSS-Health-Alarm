"""Build rigid-rev-b.kicad_pcb from rev A's board file (keeps its 4-layer 0.8 mm stackup, rules and outline):
drop rev A's parts, tracks and zones, add the rev B footprints with the nets from parts.py at placement.json.
usage: gen_pcb.py OUT.kicad_pcb [placement.json]"""
import sys, os, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew, parts, symlib
B = os.path.join(HERE, '..')
REVA = os.path.join(B, '..', '..', 'rev-a', 'pcb', 'rigid-rev-a.kicad_pcb')
FPL = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/'
OUT = sys.argv[1]
POS = {k: tuple(v) for k, v in json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'placement.json'))).items()}
F = pcbnew.FromMM
def top_blocks(t):
    """split a .kicad_pcb into its top-level s-expression blocks (text)."""
    i = t.index('\n\t('); head = t[:i]; out = []
    while True:
        j = t.find('\n\t(', i)
        if j < 0: break
        k = j + 2; d = 0
        while True:
            c = t[k]
            if c == '"':
                k += 1
                while t[k] != '"':
                    if t[k] == '\\': k += 1
                    k += 1
            elif c == '(': d += 1
            elif c == ')':
                d -= 1
                if d == 0: break
            k += 1
        out.append(t[j + 2:k + 1]); i = k + 1
    return head, out
head, blks = top_blocks(open(REVA).read())
keep = [x for x in blks if not re.match(r'\((footprint|segment|via|arc|zone|net|group|dimension|generated|image|target)\b', x)
        and not (x.startswith('(gr_') and '(layer "Edge.Cuts")' not in x)]
TMP = OUT + '.base.kicad_pcb'
open(TMP, 'w').write(head + ''.join('\n\t' + x for x in keep) + '\n)\n')
b = pcbnew.LoadBoard(TMP); os.remove(TMP)
nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, '/' + n); b.Add(ni); nets[n] = ni
    return nets[n]
NCNET = {}
for p in parts.PARTS:
    for n in p[6].values(): net(n)
    if p[7]:
        lib, name = p[1].split(':')
        pn = {q['num']: q['name'] for q in symlib.pins(symlib.get(lib, name, os.path.join(B, 'wakeband.kicad_sym') if lib == 'wakeband' else None))}
        for k in p[7]:
            nn = f"unconnected-({p[0]}-{pn[k]}-Pad{k})".replace("/", "{slash}")
            ni = pcbnew.NETINFO_ITEM(b, nn); b.Add(ni); NCNET[(p[0], k)] = ni
missing = []
for ref, libid, val, fpid, lcsc, mpn, pinnets, ncs, desc in parts.PARTS:
    lib, name = fpid.split(':')
    path = os.path.join(B, 'wakeband.pretty') if lib == 'wakeband' else FPL + lib + '.pretty'
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    fp.SetFPIDAsString(fpid)
    fp.SetReference(ref); fp.SetValue(val)
    b.Add(fp)
    fp.Reference().SetLayer(pcbnew.F_Fab)
    if ref not in POS:
        missing.append(ref); POS[ref] = (140.0, 100.0 + len(missing) * 2.5, 0, 'F')
    x, y, rot, side = POS[ref]
    fp.SetPosition(pcbnew.VECTOR2I(F(x), F(y)))
    fp.SetOrientationDegrees(rot)
    if side == 'B':
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.Reference().SetLayer(pcbnew.B_Fab)
    if ref in parts.DNP: fp.SetDNP(True)
    if ref.startswith(('TP', 'J6', 'JP')): fp.SetExcludedFromBOM(True)
    if ref.startswith(('TP', 'J6', 'JP')) or ref in parts.DNP: fp.SetExcludedFromPosFiles(True)
    for pad in fp.Pads():
        n = pad.GetNumber()
        if n in pinnets: pad.SetNet(nets[pinnets[n]])
        elif (ref, n) in NCNET: pad.SetNet(NCNET[(ref, n)])
        elif n: raise SystemExit(f'pad {ref}.{n} has no net')
pcbnew.SaveBoard(OUT, b)
# LCSC / MPN fields on the footprints (text edit: FOOTPRINT field API differs between builds)
t = open(OUT).read()
info = {p[0]: (p[4], p[5], p[8]) for p in parts.PARTS}
def addf(m):
    ref = m.group(2)
    lcsc, mpn, desc = info.get(ref, ('', '', ''))
    add = ''
    for k, v in (('LCSC', lcsc), ('MPN', mpn), ('Description', desc)):
        if v: add += (f'\n\t\t(property "{k}" "{v}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n'
                      f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
    return m.group(0) + add
t = re.sub(r'\n\t\t\(property "Description" "[^"]*"[\s\S]*?\n\t\t\)', '', t)
t = re.sub(r'(\(property "Reference" "([^"]+)"[\s\S]*?\n\t\t\))', addf, t)
def strip_silk(t):
    out, i = [], 0
    pat = re.compile(r'\n\t\t\((fp_line|fp_poly|fp_circle|fp_arc|fp_rect|fp_text)\b')
    while True:
        m = pat.search(t, i)
        if not m: out.append(t[i:]); break
        st = m.start() + 3; d = 0; j = st
        while True:
            c = t[j]
            if c == '"':
                j += 1
                while t[j] != '"': j += 1
            elif c == '(': d += 1
            elif c == ')':
                d -= 1
                if d == 0: break
            j += 1
        blk = t[st:j + 1]
        out.append(t[i:m.start()])
        if '"F.SilkS"' not in blk and '"B.SilkS"' not in blk: out.append(t[m.start():j + 1])
        i = j + 1
    return ''.join(out)
t = re.sub(r'(\(property "(?!Reference|Value)[^"]*" "[^"]*"\s*\(at [^)]*\)\s*)\(layer "F\.SilkS"\)', lambda m: m.group(1) + '(layer "F.Fab")\n\t\t\t(hide yes)', t)
t = re.sub(r'(\(property "(?!Reference|Value)[^"]*" "[^"]*"\s*\(at [^)]*\)\s*)\(layer "B\.SilkS"\)', lambda m: m.group(1) + '(layer "B.Fab")\n\t\t\t(hide yes)', t)
open(OUT, 'w').write(t)
import subprocess; subprocess.run([sys.executable if False else 'python3', os.path.join(HERE, 'mkpro.py')])
print('saved', len(parts.PARTS), 'footprints; unplaced:', missing)
