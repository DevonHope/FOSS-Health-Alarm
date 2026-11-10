"""Per-part JLCPCB placement corrections, derived from JLC's own (EasyEDA) footprints.

JLCPCB places the origin of its EasyEDA footprint for each LCSC part at the CPL "Mid X/Y" and turns it by
"Rotation" (counter-clockwise, board seen from the top, y up). Where that footprint's origin or zero
orientation differs from KiCad's, the raw KiCad positions put parts off their pads in JLC's preview.

For each LCSC number this script fetches the EasyEDA footprint (easyeda2kicad's API client), takes its pads
relative to the footprint origin (EasyEDA units are 10 mil, y down -> mm, y up), and finds the rotation
step (0/90/180/270) and offset that lay them on the KiCad footprint's pads (from jlc_kicad_pads.py), pad
numbers matched. The result, per LCSC number: drot (added to the KiCad rotation) and dx, dy (mm, in the
KiCad footprint's own frame, before its rotation; the CPL point is the footprint origin plus that offset
turned by the part's rotation). Parts whose pad numbers cannot be matched are fitted on geometry alone and
flagged for a pin-1 check in JLC's preview.

usage (Python with easyeda2kicad): jlc_cpl_fix.py KICAD_PADS.json OUT.json
"""
import json
import math
import sys
import time

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi

U = 0.254  # EasyEDA unit (10 mil) in mm


def rot(p, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def easyeda_pads(data):
    ds = data["packageDetail"]["dataStr"]
    hx, hy = float(ds["head"]["x"]), float(ds["head"]["y"])
    pads = []
    for sh in ds["shape"]:
        f = sh.split("~")
        if f[0] != "PAD" or f[6] not in ("1", "11"):          # top copper or multi-layer (THT)
            continue
        pads.append([f[8], round((float(f[2]) - hx) * U, 4), round(-(float(f[3]) - hy) * U, 4)])
    return data["packageDetail"].get("title", ""), pads


def fit(kp, jp, by_number=True):
    """Best rotation step + translation laying JLC pads (jp) onto KiCad pads (kp)."""
    best = None
    for drot in (0, 90, 180, 270):
        jr = [(n, rot((x, y), drot)) for n, x, y in jp]
        if by_number:
            kd = {n: (x, y) for n, x, y in kp}
            pairs = [(kd[n], q) for n, q in jr if n in kd]
            if len(pairs) != len(kp) or len(jr) != len(kp):
                return None
        else:
            if len(jr) != len(kp):
                return None
            # translate by centroid, then nearest-pad pairing
            kc = (sum(x for _, x, _ in kp) / len(kp), sum(y for _, _, y in kp) / len(kp))
            jc = (sum(q[0] for _, q in jr) / len(jr), sum(q[1] for _, q in jr) / len(jr))
            pairs = []
            for _, x, y in kp:
                q = min((q for _, q in jr), key=lambda q: (q[0] - jc[0] + kc[0] - x) ** 2 + (q[1] - jc[1] + kc[1] - y) ** 2)
                pairs.append(((x, y), q))
        tx = sum(k[0] - q[0] for k, q in pairs) / len(pairs)
        ty = sum(k[1] - q[1] for k, q in pairs) / len(pairs)
        res = max(math.hypot(k[0] - q[0] - tx, k[1] - q[1] - ty) for k, q in pairs)
        if best is None or res < best[3] - 1e-6:
            best = (drot, tx, ty, res)
    return best


def main(src, dst):
    kicad = json.load(open(src))
    api = EasyedaApi()
    try:
        cache = json.load(open(dst))      # reuse footprints already fetched (EasyEDA rate-limits)
    except (OSError, ValueError):
        cache = {}
    out = {}
    for lcsc, k in sorted(kicad.items()):
        if "jlc_pads" in cache.get(lcsc, {}):
            title, jp = cache[lcsc]["jlc_fp"], cache[lcsc]["jlc_pads"]
        else:
          try:
              for attempt in range(6):                       # EasyEDA rate-limits (HTTP 403): back off
                  try:
                      data = api.get_cad_data_of_component(lcsc_id=lcsc)
                      title, jp = easyeda_pads(data)
                      break
                  except Exception:  # noqa: BLE001
                      if attempt == 5:
                          raise
                      time.sleep(15 * (attempt + 1))
          except Exception as ex:  # noqa: BLE001
              out[lcsc] = {"ref": k["ref"], "kicad_fp": k["fp"], "status": f"not fetched: {ex}"}
              print(f"{lcsc:10} {k['ref']:6} NOT FETCHED {ex}")
              continue
        r = fit(k["pads"], jp, True)
        mode = "pad numbers"
        if r is None or r[3] > 0.35:      # JLC land patterns differ by up to ~0.3 mm; beyond that, numbering differs
            r2 = fit(k["pads"], jp, False)
            if r2 and (r is None or r2[3] < r[3]):
                r, mode = r2, "geometry only: check pin 1 in JLC's preview"
        if r is None:
            out[lcsc] = {"ref": k["ref"], "kicad_fp": k["fp"], "jlc_fp": title, "status": "pad count differs",
                         "kicad_pads": len(k["pads"]), "jlc_pad_count": len(jp)}
            print(f"{lcsc:10} {k['ref']:6} pad count differs ({len(k['pads'])} vs {len(jp)}) {title}")
            continue
        drot, tx, ty, res = r
        tx, ty = (0.0 if abs(tx) < 0.01 else tx), (0.0 if abs(ty) < 0.01 else ty)   # fit noise
        # JLC origin in the KiCad footprint frame is (tx, ty): that is the CPL offset
        out[lcsc] = {"ref": k["ref"], "kicad_fp": k["fp"], "jlc_fp": title, "drot": drot,
                     "dx": round(tx, 4), "dy": round(ty, 4), "residual": round(res, 4), "match": mode,
                     "jlc_pads": jp}
        print(f"{lcsc:10} {k['ref']:6} drot {drot:3} dx {tx:+.3f} dy {ty:+.3f} res {res:.3f}  {mode[:12]}  {title}")
        time.sleep(0 if "jlc_pads" in cache.get(lcsc, {}) else 3)
    json.dump(out, open(dst, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
