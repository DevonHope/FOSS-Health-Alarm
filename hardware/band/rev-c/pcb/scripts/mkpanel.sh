#!/bin/zsh
# 2 x 2 JLCPCB assembly panel (Standard PCBA needs a panel of at least 70 x 70 mm) and its fab files.
# Boards 33 x 15 mm, 4 mm between columns; a 3 mm backbone between the rows; 15 mm rails top and bottom
# -> 70.1 x 71.1 mm. Tabs (3 mm, mousebites) only where the long edges are clear of copper: one on the top
# edge, two on the bottom edge of each board (scripts/paneltabs.py); none at the dock or antenna ends. Needs KiKit 1.8
# (PYTHONPATH to a KiKit install; default /tmp/kikitlib) and KiCad 10.
# usage: scripts/mkpanel.sh   -> fab/panel/rigid-rev-c-panel.kicad_pcb, fab/jlcpcb/{gerbers.zip,bom.csv,pos.csv}
set -e
cd "$(dirname "$0")/.."
P3=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
export PYTHONPATH=${KIKIT:-/tmp/kikitlib}
mkdir -p fab/panel fab/jlcpcb
SRC=$(mktemp -d)/rigid-rev-c-tabs.kicad_pcb
$P3 scripts/paneltabs.py rigid-rev-c.kicad_pcb $SRC 2>&1 | grep -v -e wxApp -e leak -e stdpbase -e 'Debug:'
$P3 -m kikit.ui panelize \
  --layout "grid; rows: 2; cols: 2; hspace: 4mm; vspace: 2mm; hbackbone: 3mm; renameref: {orig}_{n}" \
  --tabs 'annotation' \
  --cuts 'mousebites; drill: 0.5mm; spacing: 0.75mm; offset: 0mm; prolong: 0.5mm' \
  --framing 'railstb; width: 15mm; space: 2mm' \
  --tooling '3hole; hoffset: 3mm; voffset: 3mm; size: 1.152mm; paste: false' \
  --fiducials '3fid; hoffset: 8mm; voffset: 3.5mm; coppersize: 1mm; opening: 2mm' \
  --text 'simple; text: WakeBand rigid rev C  2x2  JLCJLCJLCJLC; anchor: mt; voffset: 7mm; hjustify: center; vjustify: center; width: 1.2mm; height: 1.2mm' \
  --post 'millradius: 1mm' \
  $SRC fab/panel/rigid-rev-c-panel.kicad_pcb 2>&1 | tee fab/panel/kikit.log | grep -v -e wxApp -e leak -e stdpbase -e 'Debug:' || true
if grep -q 'errors in the panel' fab/panel/kikit.log; then echo 'KiKit reported errors (fab/panel/kikit.log)'; exit 1; fi
rm -f fab/panel/kikit.log
# same rules on the panel: nets are renamed Board_<n>-/NET and references REF_<n>, so widen the patterns
python3 - <<'PY'
import json, re
d = json.load(open('rigid-rev-c.kicad_pro'))
for p in d['net_settings']['netclass_patterns']: p['pattern'] = '*' + p['pattern']
# the VIN dock landing (J601.1) is exactly 0.30 mm from the edge; KiKit's outline approximation moves the edge
# by ~1 um, so the panel copy checks 0.29 mm (JLC's minimum is 0.2 mm; the board itself passes 0.30)
d['board']['design_settings']['rules']['min_copper_edge_clearance'] = 0.29
json.dump(d, open('fab/panel/rigid-rev-c-panel.kicad_pro', 'w'), indent=2)
r = open('rigid-rev-c.kicad_dru').read()
open('fab/panel/rigid-rev-c-panel.kicad_dru', 'w').write(re.sub(r"'((?:U|TP)\d+)'", r"'\1_*'", r))
PY
# fill the pours with the project rules (KiKit's own refill ignores the custom rules), then gate on panel DRC
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
$K pcb drc --refill-zones --save-board --severity-error --exit-code-violations --format json -o fab/panel/drc.json fab/panel/rigid-rev-c-panel.kicad_pcb >/dev/null || { echo 'panel DRC errors: see fab/panel/drc.json'; exit 1; }
rm -f fab/panel/drc.json fab/panel/*.kicad_prl fab/panel/~*.lck(N)
# KiKit's own JLC export does not run on KiCad 10's API, so the fab files come from kicad-cli + panelfab.py
$P3 scripts/panelfab.py 2>&1 | grep -v -e wxApp -e leak -e stdpbase -e 'Debug:'
ls -la fab/jlcpcb
