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

# Per-LCSC corrections derived from JLC's own (EasyEDA) footprints by scripts/jlc_cpl_fix.py (pads matched
# by number; see that script): "drot" is added to the KiCad rotation and (dx, dy) (mm, footprint frame, y up)
# moves the CPL point onto JLC's footprint origin. Re-run jlc_kicad_pads.py + jlc_cpl_fix.py if an LCSC
# number changes. This replaced the generic kicad-jlcpcb-tools table (SOT-23 +180, SOIC +270, QFN +270),
# which was wrong for the RP2040 QFN (JLC's footprint needs 0), the SOT-23-5/6 parts (270) and the LEDs (180).
import json
FIX = json.load(open(Path(__file__).with_name("jlc_cpl_fix.json")))
SKIP = re.compile(r"^(P\d+|TP\d+)$")  # hand-soldered spring pins, test pads
# JLCPCB places its own (EasyEDA) footprint with its origin at the CPL point. Where that origin is not
# KiCad's, shift the point by (dx, dy) in the footprint's own frame (mm, KiCad axes, before rotation).
# J1, HRO TYPE-C-31-M-12 (C165948): the EasyEDA footprint's origin is 1.42 mm from KiCad's toward the
# back (-y), measured on the shield legs and locating holes (EasyEDA SH y -1.71/+2.47, NPTH -1.21;
# KiCad -3.13/+1.05, -2.60), same orientation, so its legs only line up with the holes after the shift.
# J1's EasyEDA footprint has 20 pads to KiCad's 16 (it adds the shell legs), so jlc_cpl_fix.py cannot fit it;
# this hand-measured offset stays. Y1: EasyEDA has no footprint data for C2981639; left at 0 (a 3225 4-pad
# crystal is the same at 0 and 180 deg) -- check it is not turned 90 in JLC's preview.
OFFSET = {"J1": (0.0, -1.42)}

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
    if ref in OFFSET:
        import math
        dx, dy = OFFSET[ref]
        a = math.radians(rot)            # KiCad: positive rotation is counter-clockwise on screen (y down)
        x += dx * math.cos(a) + dy * math.sin(a)
        y += -dx * math.sin(a) + dy * math.cos(a)
    lcsc = re.search(r'\(property "LCSC" "([^"]*)"', f)
    fx = FIX.get(lcsc.group(1) if lcsc else "", {})
    if "drot" in fx:
        import math
        a = math.radians(rot)                    # (dx, dy) is y-up; this file works in KiCad axes (y down)
        x += fx["dx"] * math.cos(a) - fx["dy"] * math.sin(a)
        y -= fx["dx"] * math.sin(a) + fx["dy"] * math.cos(a)
        rot += fx["drot"]
    elif ref not in OFFSET and ref != "Y1":
        raise SystemExit(f"{ref}: no JLC correction for {lcsc.group(1) if lcsc else '?'} in jlc_cpl_fix.json")
    rot = rot % 360
    rows.append((ref, f"{x:.4f}mm", f"{-y:.4f}mm", "Top" if layer == "F.Cu" else "Bottom", f"{rot:.1f}"))

key = lambda r: (re.sub(r"\d", "", r[0]), int(re.sub(r"\D", "", r[0]) or 0))
with open("fab/cpl_jlcpcb.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    w.writerows(sorted(rows, key=key))
print(f"wrote {len(rows)} parts")
