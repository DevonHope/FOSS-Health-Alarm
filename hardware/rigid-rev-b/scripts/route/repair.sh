#!/bin/zsh
# one repair round: rip router copper of nets with DRC errors or gaps, reroute them, apply, check
RB=/Users/devonhope/Library/CloudStorage/SynologyDrive-WakeBand/foss-health-alarm-git/hardware/rigid-rev-b
P=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
cd /tmp/wbrevb
NETS=$(python3 - <<'PY'
import json,re
d=json.load(open('/tmp/revb/drc.json'))
nets=set()
for x in d['violations']:
    if x['type'] in ('clearance','hole_clearance','shorting_items','tracks_crossing','track_not_centered_on_via','track_dangling','copper_edge_clearance'):
        for i in x['items']:
            m=re.search(r'\[(/[^\]]+)\]',i['description'])
            if m and ('Track' in i['description'] or 'Via' in i['description']): nets.add(m.group(1))
for u in d['unconnected_items']:
    for i in u['items']:
        m=re.search(r'\[(/[^\]]+)\]',i['description'])
        if m: nets.add(m.group(1))
nets.discard('/GND')
print(','.join(sorted(nets)))
PY
)
echo "rip: $NETS"
[ -z "$NETS" ] && exit 0
$P rip.py $RB/rigid-rev-b.kicad_pcb pre_route.kicad_pcb $NETS 2>&1 | grep ripped
python3 $RB/scripts/mkpro.py >/dev/null
$P export_geom.py $RB/rigid-rev-b.kicad_pcb geom.json 2>&1 | grep pads
python3 mkjobs.py jobs_loop.json
python3 -c "
import json
j=json.load(open('/tmp/wbrevb/jobs_loop.json'))
for x in j:
    if x['src_pad']==['U201','A2']: x['src_via']=True
    x['layer_cost']={'F.Cu':1.0,'In2.Cu':1.5,'B.Cu':1.3}
json.dump(j,open('/tmp/wbrevb/jobs_loop.json','w'))"
python3 loop.py 6 | tail -2
$P apply.py routes_best.json $RB/rigid-rev-b.kicad_pcb 2>&1 | grep -v -E "wxApp|leak|Debug"
$P dedupe.py $RB/rigid-rev-b.kicad_pcb 2>&1 | grep dedupe
python3 $RB/scripts/mkpro.py >/dev/null
cd $RB && /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --refill-zones --save-board -o /tmp/revb/x.rpt rigid-rev-b.kicad_pcb >/dev/null 2>&1; python3 scripts/mkpro.py >/dev/null
/tmp/wbrevb/chk.sh 2>&1 | grep -v "VDD plane"
