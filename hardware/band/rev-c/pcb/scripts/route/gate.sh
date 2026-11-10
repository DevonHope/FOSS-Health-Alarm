#!/bin/zsh
# gate.sh BOARD : DRC (refilled, all severities, minus /tmp lib warnings) + audit counts
P3=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
export R="$(cd "$(dirname "$0")/../.." && pwd)"  # this board's pcb folder
d=$(dirname $1); n=$(basename $1 .kicad_pcb)
cp $R/rigid-rev-c.kicad_pro $d/$n.kicad_pro; cp $R/rigid-rev-c.kicad_dru $d/$n.kicad_dru
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --refill-zones --format json --severity-all -o $d/$n.json $1 >/dev/null 2>&1
python3 - $d/$n.json <<'EOF'
import json,sys,collections
d=json.load(open(sys.argv[1]))
v=[x for x in d['violations'] if x['type'] not in ('lib_footprint_issues','lib_footprint_mismatch')]
print('DRC',dict(collections.Counter(x['type'] for x in v)),'unconnected',len(d['unconnected_items']))
for x in v: print('  ',x['type'],[(i['description'][:60],i['pos']['x'],i['pos']['y']) for i in x['items']])
EOF
$P3 $R/scripts/route/audit.py $1 2>&1 | grep -v -e wxApp -e leak -e stdpbase | grep -v "^    (" | tr '\n' ';'; echo
