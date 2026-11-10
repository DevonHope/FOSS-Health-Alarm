#!/bin/zsh
export RB="$(cd "$(dirname "$0")/../.." && pwd)"  # this board's pcb folder
P=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
F="grep -v -e wxApp -e leak -e Debug"
cd /tmp/wbrevb
$P export_geom.py $RB/rigid-rev-c.kicad_pcb geom.json 2>&1 | eval $F
/tmp/wb3d-venv/bin/python fan_net.py /I2C_SDA r_sda.json R203.2 | tail -1
$P apply.py r_sda.json $RB/rigid-rev-c.kicad_pcb 2>&1 | eval $F
$P export_geom.py $RB/rigid-rev-c.kicad_pcb geom.json 2>&1 | eval $F
/tmp/wb3d-venv/bin/python fan_net.py /I2C_SCL r_scl.json R204.2 | tail -1
$P apply.py r_scl.json $RB/rigid-rev-c.kicad_pcb 2>&1 | eval $F
python3 $RB/scripts/mkpro.py >/dev/null
cp $RB/rigid-rev-c.kicad_pcb pre_route.kicad_pcb
$P export_geom.py pre_route.kicad_pcb geom.json 2>&1 | eval $F
python3 mkjobs.py jobs_loop.json
python3 -c "
import json
j=json.load(open('/tmp/wbrevb/jobs_loop.json'))
for x in j:
    if x['src_pad']==['U201','A2']: x['src_via']=True
    x['layer_cost']={'F.Cu':1.0,'In2.Cu':1.5,'B.Cu':1.3}
json.dump(j,open('/tmp/wbrevb/jobs_loop.json','w'))"
python3 loop.py ${1:-14}
cp routes_best.json routes_final.json
$P apply.py routes_best.json $RB/rigid-rev-c.kicad_pcb 2>&1 | eval $F
$P dedupe.py $RB/rigid-rev-c.kicad_pcb 2>&1 | eval $F
$P cleanup.py $RB/rigid-rev-c.kicad_pcb 2>&1 | eval $F | tail -2
python3 $RB/scripts/mkpro.py >/dev/null
cd $RB && /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --refill-zones --save-board -o /tmp/revb/x.rpt rigid-rev-c.kicad_pcb >/dev/null 2>&1; python3 scripts/mkpro.py >/dev/null
cp rigid-rev-c.kicad_pcb /tmp/wbrevb/routed_v6.kicad_pcb
/tmp/wbrevb/chk.sh 2>&1 | grep -v "VDD plane"
