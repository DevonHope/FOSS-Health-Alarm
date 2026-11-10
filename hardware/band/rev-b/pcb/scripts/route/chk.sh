#!/bin/zsh
export RB="$(cd "$(dirname "$0")/../.." && pwd)"  # this board's pcb folder
cd $RB && /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --severity-all --schematic-parity --format json -o /tmp/revb/drc.json rigid-rev-b.kicad_pcb >/dev/null 2>&1
python3 - <<'PY'
import json
from collections import Counter
d=json.load(open('/tmp/revb/drc.json'))
v=d['violations']; print(Counter(x['type'] for x in v))
others=[u for u in d['unconnected_items'] if not all('/GND' in i['description'] for i in u['items'])]
print(len(d['unconnected_items']),'unconnected; non-GND', [[i['description'][:50] for i in u['items']] for u in others])
for x in v:
  if x['type'] in ('clearance','copper_edge_clearance','shorting_items','hole_clearance','tracks_crossing','hole_to_hole','track_not_centered_on_via'): print(' ',x['type'],[(i['description'][:45],round(i['pos']['x'],2),round(i['pos']['y'],2)) for i in x['items']])
PY
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 - <<'PY' 2>&1 | grep -v -E "wxApp|leak|Debug"
import pcbnew
b=pcbnew.LoadBoard(__import__('os').environ['RB']+'/rigid-rev-b.kicad_pcb'); mm=pcbnew.ToMM
for z in b.Zones():
    if z.GetZoneName()=='VDD_1V8 plane':
        fp=z.GetFilledPolysList(b.GetLayerID('In2.Cu'))
        print('VDD plane pieces',[(round(mm(fp.Outline(i).BBox().GetLeft()),1),round(mm(fp.Outline(i).BBox().GetTop()),1),round(fp.Outline(i).Area()/1e12,1)) for i in range(fp.OutlineCount())])
PY
