"""Write fab/cpl_jlcpcb.csv from the board, with JLCPCB's rotation conventions.

KiCad and JLCPCB (EasyEDA) draw some packages turned relative to each other, so the
placement preview shows those parts rotated even though the board is right. The offsets
below are the usual KiCad-to-JLCPCB corrections (same as the kicad-jlcpcb-tools plugin's
defaults). Positions are the footprint origins, which are the body centres for every
part on this board (checked against the courtyards and fab outlines).

usage: python scripts/gen_cpl.py   (run from the PCB folder)
"""
import csv
import re
from pathlib import Path

ROT_FIX = [  # (footprint name regex, degrees added)
    (r"^SOT-23", 180),
    (r"^SOIC-", 270),
    (r"^QFN-", 270),
]
SKIP = re.compile(r"^(P\d+|TP\d+)$")  # hand-soldered spring pins, test pads

pcb = next(Path(".").glob("*.kicad_pcb"))
s = pcb.read_text()
starts = [m.start() for m in re.finditer(r"\n\t\(footprint \"", s)] + [len(s)]
rows = []
for a, b in zip(starts, starts[1:]):
    f = s[a:b]
    name = re.search(r'\(footprint "([^"]+)"', f).group(1).split(":")[-1]
    ref = re.search(r'\(property "Reference" "([^"]+)"', f).group(1)
    if SKIP.match(ref):
        continue
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", f)
    x, y, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    layer = re.search(r'\n\t\t\(layer "([^"]+)"\)', f).group(1)
    for rx, d in ROT_FIX:
        if re.match(rx, name):
            rot += d
    rot = rot % 360
    rows.append((ref, f"{x:.4f}mm", f"{-y:.4f}mm", "Top" if layer == "F.Cu" else "Bottom", f"{rot:.1f}"))

key = lambda r: (re.sub(r"\d", "", r[0]), int(re.sub(r"\D", "", r[0]) or 0))
with open("fab/cpl_jlcpcb.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    w.writerows(sorted(rows, key=key))
print(f"wrote {len(rows)} parts")
