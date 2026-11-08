"""Write fab/bom_jlcpcb.csv from parts.py (JLCPCB BOM: one row per LCSC part).

Rows are grouped by LCSC number in parts.py order. The spring pins and test pads have
no LCSC number and are left out (hand-soldered / bare pads). The two LEDs share a part,
so their row is labelled "red LED".

usage: python3 scripts/gen_bom.py   (run from the PCB folder)
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts

COMMENT = {"C2286": "red LED"}
groups = {}
for ref, _lib, val, fp, lcsc, mpn, _nets, _nc, _desc in parts.PARTS:
    if not lcsc:
        continue
    g = groups.setdefault(lcsc, {"val": COMMENT.get(lcsc, val), "fp": fp.split(":")[1], "mpn": mpn, "refs": []})
    g["refs"].append(ref)
with open("fab/bom_jlcpcb.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["Comment", "Designator", "Footprint", "LCSC", "MPN", "Qty"])
    for lcsc, g in groups.items():
        w.writerow([g["val"], ",".join(g["refs"]), g["fp"], lcsc, g["mpn"], len(g["refs"])])
print(f"wrote {len(groups)} BOM lines, {sum(len(g['refs']) for g in groups.values())} parts")
