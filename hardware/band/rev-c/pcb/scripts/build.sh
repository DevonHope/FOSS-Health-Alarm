#!/bin/zsh
# Rebuild rigid-rev-c from scripts: symbols, footprint, schematic, board placement, Nordic copper, hand-laid cluster.
set -e
cd "$(dirname "$0")"
P3=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
F="grep -v -e wxApp -e leak -e stdpbase -e ^$"
python3 mksym.py; python3 mkfp.py
$P3 nordic_place.py 111.0 105.0 2>&1 | eval $F
python3 gen_sch.py ../rigid-rev-c.kicad_sch
$P3 gen_pcb.py ../rigid-rev-c.kicad_pcb 2>&1 | eval $F
$P3 transplant.py ../rigid-rev-c.kicad_pcb 2>&1 | eval $F
$P3 hand_cluster.py ../rigid-rev-c.kicad_pcb 2>&1 | eval $F
$P3 hand_bq.py ../rigid-rev-c.kicad_pcb 2>&1 | eval $F
$P3 zones.py ../rigid-rev-c.kicad_pcb 2>&1 | eval $F
