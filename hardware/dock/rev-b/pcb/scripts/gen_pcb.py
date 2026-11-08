"""Build dock-pcb-rev-b.kicad_pcb: 4-layer 1.6 mm, footprints from the libraries with the nets in parts.py."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew, parts
D = os.path.normpath(os.path.join(HERE, '..'))
FPL = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/'
OUT = sys.argv[1]
POS = {  # ref: (x, y, rot, side)
 'U1': (118.0, 106.5, 180, 'F'), 'Y1': (116.4, 101.0, 0, 'F'), 'C1': (113.9, 100.6, 0, 'F'), 'C2': (119.0, 100.6, 0, 'F'), 'R1': (119.0, 102.0, 0, 'F'),
 'U2': (126.0, 109.6, 90, 'F'), 'J1': (121.0, 116.6, 0, 'F'), 'R2': (115.6, 116.4, 90, 'F'), 'R3': (126.4, 116.4, 90, 'F'),
 'U3': (113.8, 113.6, 90, 'F'), 'R4': (117.2, 111.6, 90, 'F'), 'R5': (116.2, 111.6, 90, 'F'),
 'F1': (127.6, 114.2, 90, 'F'), 'C3': (110.6, 116.8, 90, 'F'), 'U4': (108.0, 113.4, 90, 'F'), 'C4': (106.2, 113.4, 90, 'F'),
 'U5': (108.0, 109.2, 90, 'F'), 'C5': (106.2, 109.2, 90, 'F'), 'U6': (129.2, 118.6, 0, 'F'), 'R6': (127.2, 119.4, 0, 'F'),
 'C6': (126.9, 117.9, 0, 'F'), 'C7': (131.6, 118.4, 90, 'F'),
 'C8': (114.0, 104.4, 90, 'F'), 'C9': (114.0, 108.6, 90, 'F'), 'C10': (122.0, 104.4, 90, 'F'), 'C11': (122.0, 108.6, 90, 'F'),
 'C12': (115.4, 110.9, 0, 'F'), 'C13': (120.6, 110.9, 0, 'F'), 'C14': (118.6, 111.6, 90, 'F'), 'C15': (119.6, 111.6, 90, 'F'),
 'C16': (121.6, 111.6, 90, 'F'), 'C17': (128.9, 109.6, 90, 'F'), 'R7': (112.6, 103.0, 90, 'F'), 'R8': (123.2, 112.4, 0, 'F'),
 'R9': (110.6, 119.6, 0, 'F'), 'SW1': (107.6, 118.4, 0, 'F'), 'U7': (125.4, 101.6, 90, 'F'), 'U8': (125.4, 105.0, 90, 'F'),
 'C18': (123.4, 101.0, 90, 'F'), 'C19': (127.6, 101.0, 90, 'F'), 'C20': (123.4, 104.4, 90, 'F'), 'C21': (127.6, 104.4, 90, 'F'),
 'R10': (122.4, 106.6, 90, 'F'), 'R11': (129.4, 101.6, 0, 'F'), 'R12': (129.4, 103.3, 0, 'F'),
 'D1': (113.2, 119.6, 0, 'F'), 'R13': (113.2, 118.4, 0, 'F'), 'D2': (106.4, 105.6, 90, 'F'), 'R14': (106.4, 103.8, 90, 'F'),
 'P1': (131.5, 101.1, 0, 'F'), 'P2': (131.5, 103.3, 0, 'F'), 'P3': (131.5, 111.7, 0, 'F'), 'P4': (131.5, 113.9, 0, 'F'),
 'TP1': (106.0, 100.6, 0, 'B'), 'TP2': (108.0, 100.6, 0, 'B'), 'TP3': (110.0, 100.6, 0, 'B'), 'TP4': (104.9, 102.4, 0, 'B'),
}
if len(sys.argv) > 2:
    import json; POS.update({k: tuple(v) for k, v in json.load(open(sys.argv[2])).items()})
b = pcbnew.BOARD()
b.SetCopperLayerCount(4)
ds = b.GetDesignSettings()
ds.SetBoardThickness(pcbnew.FromMM(1.6))
nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, '/' + n); b.Add(ni); nets[n] = ni
    return nets[n]
import symlib
NCNET = {}
for p in parts.PARTS:
    for n in p[6].values(): net(n)
    if p[7]:
        lib, name = p[1].split(':')
        pn = {q['num']: q['name'] for q in symlib.pins(symlib.get(lib, name, D + '/dock.kicad_sym' if lib == 'dock' else None))}
        for k in p[7]:
            nn = f"unconnected-({p[0]}-{pn[k]}-Pad{k})".replace("/", "{slash}")
            ni = pcbnew.NETINFO_ITEM(b, nn); b.Add(ni); NCNET[(p[0], k)] = ni
for ref, libid, val, fpid, lcsc, mpn, pinnets, ncs, desc in parts.PARTS:
    lib, name = fpid.split(':')
    path = (D + '/dock.pretty') if lib == 'dock' else FPL + lib + '.pretty'
    fp = pcbnew.FootprintLoad(path, name)
    fp.SetFPIDAsString(fpid)
    fp.SetReference(ref); fp.SetValue(val)
    for k, v in (('LCSC', lcsc), ('MPN', mpn), ('Description', desc)):
        if v: fp.SetField(k, v) if hasattr(fp, 'SetField') else None
    b.Add(fp)
    fp.Reference().SetLayer(pcbnew.F_Fab)
    x, y, rot, side = POS[ref]
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientationDegrees(rot)
    if side == 'B':
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.Reference().SetLayer(pcbnew.B_Fab)
    for pad in fp.Pads():
        n = pad.GetNumber()
        if n in pinnets: pad.SetNet(nets[pinnets[n]])
        elif (ref, n) in NCNET: pad.SetNet(NCNET[(ref, n)])
        elif n == '' : pass
# outline
X0, X1, Y0, Y1, R = 100.0, 140.0, 97.5, 124.0, 1.0
def line(a, b_):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1]))); s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b_[0]), pcbnew.FromMM(b_[1])))
    s.SetWidth(pcbnew.FromMM(0.05)); b.Add(s)
def arc(c, st, ang):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetCenter(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]), pcbnew.FromMM(c[1]))); s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(st[0]), pcbnew.FromMM(st[1])))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T)); s.SetWidth(pcbnew.FromMM(0.05)); b.Add(s)
line((X0+R, Y0), (X1-R, Y0)); line((X1, Y0+R), (X1, Y1-R)); line((X1-R, Y1), (X0+R, Y1)); line((X0, Y1-R), (X0, Y0+R))
arc((X1-R, Y0+R), (X1-R, Y0), 90); arc((X1-R, Y1-R), (X1, Y1-R), 90); arc((X0+R, Y1-R), (X0+R, Y1), 90); arc((X0+R, Y0+R), (X0, Y0+R), 90)
# GND zones: In1 solid, F/B/In2 fill
for layer, prio in ((pcbnew.In1_Cu, 0), (pcbnew.F_Cu, 1), (pcbnew.B_Cu, 1), (pcbnew.In2_Cu, 0)):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(nets['GND']); z.SetAssignedPriority(prio)
    o = z.Outline(); o.NewOutline()
    for px, py in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)): o.Append(pcbnew.FromMM(px), pcbnew.FromMM(py))
    z.SetLocalClearance(pcbnew.FromMM(0.2)); z.SetMinThickness(pcbnew.FromMM(0.15))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetThermalReliefGap(pcbnew.FromMM(0.2)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.25))
    b.Add(z)
pcbnew.SaveBoard(OUT, b)
import re
t = open(OUT).read()
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
t = strip_silk(t)
t = re.sub(r'(\(property "(?!Reference|Value)[^"]*" "[^"]*"\s*\(at [^)]*\)\s*)\(layer "F\.SilkS"\)', lambda m: m.group(1) + '(layer "F.Fab")\n\t\t\t(hide yes)', t)
t = re.sub(r'(\(property "(?!Reference|Value)[^"]*" "[^"]*"\s*\(at [^)]*\)\s*)\(layer "B\.SilkS"\)', lambda m: m.group(1) + '(layer "B.Fab")\n\t\t\t(hide yes)', t)
open(OUT, 'w').write(t)
print('saved', len(parts.PARTS), 'footprints')
