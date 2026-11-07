"""Small 3-layer grid router for the WakeBand rev A rework.

usage: router.py geom.json jobs.json out.json
jobs: [{net, w, src: [x, y, layer], layers: [...], b_forbid: true}] routed in order.
Output: tracks [{net, layer, w, pts}] and vias [{net, x, y}].
"""
import heapq, json, math, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

RES = 0.05
X0, Y0, X1, Y1 = 100.0, 100.0, 133.0, 115.0
NX, NY = int(round((X1 - X0) / RES)) + 1, int(round((Y1 - Y0) / RES)) + 1
LAYERS = ['F.Cu', 'In2.Cu', 'B.Cu']
CLR = 0.10
VIA_D = 0.45
EDGE = 0.30
LEAD_PADS = {'TP201', 'TP202', 'TP501', 'TP502'}
CELL = (0.0, 0.0, 0.0, 0.0)
LRA = (0.0, 0.0, 0.0)
KEEPOUT_X = 0.0

g = json.load(open(sys.argv[1]))
jobs = json.load(open(sys.argv[2]))


def px(x, y):
    return ((x - X0) / RES, (y - Y0) / RES)


def new_img():
    return Image.new('1', (NX, NY), 0)


def draw_poly(dr, pts, grow=0.0):
    if grow <= 0:
        dr.polygon([px(*p) for p in pts], fill=1)
    else:  # crude growth: draw edges as thick lines plus fill
        dr.polygon([px(*p) for p in pts], fill=1)
        for a, b in zip(pts, pts[1:] + pts[:1]):
            draw_seg(dr, a, b, 2 * grow)


def draw_seg(dr, a, b, w):
    r = w / 2 / RES
    pa, pb = px(*a), px(*b)
    dr.line([pa, pb], fill=1, width=max(1, int(round(2 * r))))
    for p in (pa, pb):
        dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=1)


def draw_circle(dr, x, y, rad):
    p = px(x, y); r = rad / RES
    dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=1)


def obstacle_dist(net):
    """Per layer: distance (mm) from each grid point to the nearest other-net copper,
    with lead pads grown by 0.4 and vias grown by 0.1 on In2 (stricter rules)."""
    out = {}
    for ln in LAYERS:
        im = new_img(); dr = ImageDraw.Draw(im)
        for p in g['pads']:
            if p['layer'] != ln or p['net'] == net:
                continue
            for poly in p['polys']:
                draw_poly(dr, poly, 0.4 if p['ref'] in LEAD_PADS else (0.12 if p['num'] == '' else 0.0))
        for t in g['tracks']:
            if t['layer'] == ln and t['net'] != net:
                draw_seg(dr, t['a'], t['b'], t['w'])
        for v in g['vias']:
            if v['net'] != net:
                draw_circle(dr, v['x'], v['y'], v['d'] / 2 + (0.12 if ln == 'In2.Cu' else 0.06))
        a = np.array(im, dtype=bool)
        d = distance_transform_edt(~a) * RES - RES * 0.5
        d[a] = 0
        out[ln] = d
    return out


yy, xx = np.mgrid[0:NY, 0:NX]
XW, YW = X0 + xx * RES, Y0 + yy * RES
edge_d = np.minimum.reduce([XW - X0, X1 - XW, YW - Y0, Y1 - YW])
# rounded corners r = 1
for cx, cy in ((101, 101), (132, 101), (101, 114), (132, 114)):
    rr = 1.0 - np.hypot(XW - cx, YW - cy)
    corner = ((XW < 101) | (XW > 132)) & ((YW < 101) | (YW > 114)) & (np.abs(XW - cx) <= 1) & (np.abs(YW - cy) <= 1)
    edge_d = np.where(corner, np.minimum(edge_d, rr), edge_d)
cell_mask = (XW >= CELL[0] - 0.05) & (XW <= CELL[1] + 0.05) & (YW >= CELL[2] - 0.05) & (YW <= CELL[3] + 0.05)
lra_mask = np.hypot(XW - LRA[0], YW - LRA[1]) <= LRA[2] + 0.05
u1 = g['u1_courtyard']
u1_mask = (XW >= u1[0]) & (XW <= u1[2]) & (YW >= u1[1]) & (YW <= u1[3])
ko_mask = np.zeros((NY, NX), bool)
for k in g['keepouts']:
    if not k['vias']: continue          # only the antenna keep-out blocks routing; Nordic's no-pour areas don't
    for poly in k['polys']:
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        ko_mask |= (XW >= min(xs) - 0.2) & (XW <= max(xs) + 0.2) & (YW >= min(ys) - 0.2) & (YW <= max(ys) + 0.2)
RF_NETS = {'/ANT', '/RF1', '/RF2', '/RF_50', '/ANT_FEED'}

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
result = {'tracks': [], 'vias': []}


DIST_CACHE = {}


def route(job, congest=None, commit=True):
    net, w = job['net'], job['w']
    if net not in DIST_CACHE:
        DIST_CACHE[net] = obstacle_dist(net)
    dist = DIST_CACHE[net]
    lay_ok = job.get('layers', LAYERS)
    free = {}
    for ln in LAYERS:
        f = (dist[ln] >= CLR + w / 2 + 0.02) & (edge_d >= EDGE + w / 2) & (XW >= KEEPOUT_X + w / 2 + 0.05)
        if ln == 'B.Cu' and job.get('b_forbid', False):
            f &= ~(cell_mask | lra_mask)
        if net not in RF_NETS:
            f &= ~ko_mask
        if ln not in lay_ok:
            f[:] = False
        free[ln] = f
    under = cell_mask | lra_mask
    via_ok = np.ones((NY, NX), bool)
    for ln in LAYERS:
        c = 0.26 if ln == 'In2.Cu' else 0.15
        via_ok &= dist[ln] >= c + VIA_D / 2 + 0.02
    via_ok &= (edge_d >= EDGE + VIA_D / 2) & (XW >= KEEPOUT_X + 0.5) & ~u1_mask & ~ko_mask
    if job.get('b_forbid', True):
        via_ok &= ~(cell_mask | lra_mask) | True  # vias under the cell are fine (they're flat)
    # targets: pad and via centres of this net
    tgt = {}
    for p in g['pads']:
        if p['net'] == net and (p['ref'], p['num']) != tuple(job.get('src_pad', ('', ''))) and (not job.get('only_ref') or p['ref'] == job['only_ref']) and p['ref'] not in job.get('exclude_refs', []) and (not job.get('tgt_pads') or [p['ref'], p['num']] in job['tgt_pads']):
            tgt[(int(round((p['x'] - X0) / RES)), int(round((p['y'] - Y0) / RES)), LAYERS.index(p['layer']))] = (p['x'], p['y'])
    for v in g['vias']:
        if v['net'] == net and not job.get('only_ref'):
            for li in range(3):
                tgt[(int(round((v['x'] - X0) / RES)), int(round((v['y'] - Y0) / RES)), li)] = (v['x'], v['y'])
    for x, y, ln in job.get('tgt_points', []):
        tgt[(int(round((x - X0) / RES)), int(round((y - Y0) / RES)), LAYERS.index(ln))] = (x, y)
    for k in list(tgt):  # target cells are always enterable
        free[LAYERS[k[2]]][k[1], k[0]] = True
    sx, sy, sl = job['src']
    s = (int(round((sx - X0) / RES)), int(round((sy - Y0) / RES)), LAYERS.index(sl))
    free[sl][s[1], s[0]] = True
    # clear a small disc round the source and targets inside their own pads
    tlist = list(tgt)
    if not tlist:
        print(net, 'no targets'); return False
    tx = np.array([t[0] for t in tlist]); ty = np.array([t[1] for t in tlist])

    def h(i, j):
        dx = np.abs(tx - i); dy = np.abs(ty - j)
        return float(np.min(np.maximum(dx, dy) + (math.sqrt(2) - 1) * np.minimum(dx, dy))) * RES

    VIA_COST = job.get('via_cost', 1.5)
    LAYER_COST = job.get('layer_cost', {'F.Cu': 1.0, 'In2.Cu': 1.0, 'B.Cu': 1.3})
    starts = [(s[0], s[1], l, -1) for l in (range(3) if job.get('src_via') else [s[2]])]
    for st in starts:
        free[LAYERS[st[2]]][s[1], s[0]] = True
    openq = [(h(s[0], s[1]), 0.0, st) for st in starts]
    best = {st: 0.0 for st in starts}; came = {}
    start = starts[0]
    goal = None; n = 0
    while openq:
        f, gc, cur = heapq.heappop(openq)
        if gc > best.get(cur, 1e9) + 1e-9:
            continue
        i, j, l, d = cur
        if (i, j, l) in tgt and (i, j) != s[:2]:
            goal = cur; break
        n += 1
        if n > 4_000_000:
            break
        ln = LAYERS[l]
        for di, (dx, dy) in enumerate(DIRS):
            ni, nj = i + dx, j + dy
            if not (0 <= ni < NX and 0 <= nj < NY) or not free[ln][nj, ni]:
                continue
            step = RES * (math.sqrt(2) if dx and dy else 1.0) * LAYER_COST[ln]
            if ln == 'B.Cu' and under[nj, ni]:
                step *= job.get('b_under_cost', 8.0)
            if congest is not None:
                step *= congest[l][nj, ni]
            turn = 0.0 if d in (-1, di) else job.get('turn_cost', 0.15)
            nxt = (ni, nj, l, di); ng = gc + step + turn
            if ng < best.get(nxt, 1e9):
                best[nxt] = ng; came[nxt] = cur
                heapq.heappush(openq, (ng + h(ni, nj), ng, nxt))
        if via_ok[j, i] or (i, j, l) == s[:3] or (i, j, l) in tgt:
            for nl in range(3):
                if nl == l or not free[LAYERS[nl]][j, i]:
                    continue
                if not (via_ok[j, i]):
                    continue
                vc = VIA_COST
                if congest is not None:
                    vc *= max(congest[0][j, i], congest[1][j, i], congest[2][j, i])
                nxt = (i, j, nl, -1); ng = gc + vc
                if ng < best.get(nxt, 1e9):
                    best[nxt] = ng; came[nxt] = cur
                    heapq.heappush(openq, (ng + h(i, j), ng, nxt))
    if goal is None:
        print(f"{net}: no route ({n} expansions) src {job['src']} {job.get('src_pad')}")
        return None
    path = [goal]
    while path[-1] in came:
        path.append(came[path[-1]])
    path = path[::-1]
    if not commit:
        return path, free, tgt[goal[:3]]
    return finish(job, path, free, tgt[goal[:3]])


def finish(job, path, free, exact_end):
    net, w = job['net'], job['w']
    runs = [[path[0]]]
    for a, b in zip(path, path[1:]):
        if b[2] != a[2]:
            result['vias'].append({'net': net, 'x': X0 + a[0] * RES, 'y': Y0 + a[1] * RES})
            g['vias'].append({'net': net, 'x': X0 + a[0] * RES, 'y': Y0 + a[1] * RES, 'd': VIA_D})
            runs.append([b])
        else:
            runs[-1].append(b)
    for ri, r in enumerate(runs):
        if len(r) < 2:
            continue
        pts = [(X0 + q[0] * RES, Y0 + q[1] * RES) for q in r]
        pts = simplify(pts, free[LAYERS[r[0][2]]])
        if ri == len(runs) - 1:
            pts = snap_end(pts, exact_end, free[LAYERS[r[0][2]]])
        result['tracks'].append({'net': net, 'layer': LAYERS[r[0][2]], 'w': w, 'pts': pts})
        for a, b in zip(pts, pts[1:]):
            g['tracks'].append({'net': net, 'layer': LAYERS[r[0][2]], 'w': w, 'a': a, 'b': b})
    print(f"{net}: routed, {len(runs)} layer runs, {sum(len(r) for r in runs)} cells, "
          f"{sum(1 for v in result['vias'] if v['net'] == net)} vias")
    return True


def snap_end(pts, e, free=None):
    """Move the last point onto the exact target centre, keeping 0/45/90 angles.
    Tries doglegs from the last few vertices and keeps the first that stays clear."""
    e = (round(e[0], 4), round(e[1], 4))
    if abs(pts[-1][0] - e[0]) < 1e-6 and abs(pts[-1][1] - e[1]) < 1e-6:
        return pts
    cands = []
    for back in (2, 3, 4):
        if len(pts) < back:
            continue
        a = pts[-back]; head = pts[:-back + 1]
        dx, dy = e[0] - a[0], e[1] - a[1]
        if abs(dx) < 1e-9 or abs(dy) < 1e-9 or abs(abs(dx) - abs(dy)) < 1e-9:
            cands.append(head + [e])
        for mid in dogleg(a, e):
            cands.append(head + [(round(mid[0], 4), round(mid[1], 4)), e])
    def ok(c):
        segs = list(zip(c[len(c) - 4 if len(c) > 4 else 0:], c[len(c) - 3 if len(c) > 3 else 1:]))
        if any(math.dist(a, b) < 0.08 for a, b in segs if a != b):
            return False
        return free is None or all(clear_line(a, b, free, tol=True) for a, b in segs if a != b)
    for c in cands:
        c = [q for k, q in enumerate(c) if k == 0 or math.dist(q, c[k - 1]) > 1e-6]
        if ok(c):
            return c
    print('  warning: end snap unchecked', pts[-1], e)
    return pts[:-1] + [e]


def clear_line(a, b, free, tol=False):
    """True if the straight 0/45/90 segment a-b runs over free cells only."""
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    if not (abs(dx) < 1e-9 or abs(dy) < 1e-9 or abs(abs(dx) - abs(dy)) < 1e-9):
        return False
    if tol:  # end snap: last 0.06 mm sits on the pad/via itself
        n = int(round(max(abs(dx), abs(dy)) / RES))
        for k in range(n + 1):
            x = x1 + dx * k / max(n, 1); y = y1 + dy * k / max(n, 1)
            if math.dist((x, y), b) < 0.06:
                continue
            i, j = int(round((x - X0) / RES)), int(round((y - Y0) / RES))
            if not free[j, i]:
                return False
        return True
    n = int(round(max(abs(dx), abs(dy)) / RES))
    for k in range(n + 1):
        x = x1 + dx * k / max(n, 1); y = y1 + dy * k / max(n, 1)
        i, j = int(round((x - X0) / RES)), int(round((y - Y0) / RES))
        if not free[j, i]:
            return False
    return True


def dogleg(a, b):
    """Two 45-degree-legal options from a to b: diagonal first, or straight first."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    m = min(abs(dx), abs(dy))
    sx, sy = math.copysign(1, dx) if dx else 0, math.copysign(1, dy) if dy else 0
    p1 = (a[0] + sx * m, a[1] + sy * m)
    p2 = (b[0] - sx * m, b[1] - sy * m)
    return [p1, p2]


def simplify(pts, free):
    """Greedy: from each point jump to the farthest point reachable with one
    straight segment or one dogleg (two segments)."""
    out = [pts[0]]; i = 0
    while i < len(pts) - 1:
        best = None
        for j in range(len(pts) - 1, i, -1):
            a, b = pts[i], pts[j]
            if clear_line(a, b, free):
                best = (j, [b]); break
            for mid in dogleg(a, b):
                if clear_line(a, mid, free) and clear_line(mid, b, free):
                    best = (j, [mid, b]); break
            if best:
                break
        j, add = best
        for q in add:
            q = (round(q[0], 4), round(q[1], 4))
            if q != out[-1]:
                out.append(q)
        i = j
    # merge collinear
    m = [out[0]]
    for k in range(1, len(out) - 1):
        a, b, c = m[-1], out[k], out[k + 1]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-9:
            continue
        m.append(b)
    m.append(out[-1])
    return m


def claim(path, w, via_r=VIA_D / 2):
    """Cells another net's centreline must not use near this path (per layer)."""
    ims = [new_img() for _ in LAYERS]; drs = [ImageDraw.Draw(im) for im in ims]
    r = w / 2 + CLR + 0.15 + 0.02
    for a, b in zip(path, path[1:]):
        pa = (X0 + a[0] * RES, Y0 + a[1] * RES); pb = (X0 + b[0] * RES, Y0 + b[1] * RES)
        if a[2] == b[2]:
            draw_seg(drs[a[2]], pa, pb, 2 * r)
        else:
            for d in drs:
                draw_circle(d, pa[0], pa[1], via_r + 0.2 + 0.15)
    return [np.array(im, dtype=bool) for im in ims]


if len(sys.argv) > 4 and sys.argv[4] == 'pf':
    hist = [np.zeros((NY, NX)) for _ in LAYERS]
    claims = {}; paths = {}
    pres = 0.5
    for it in range(14):
        for job in jobs:
            net = job['net']
            claims.pop(net, None)
            occ = [np.zeros((NY, NX)) for _ in LAYERS]
            for c in claims.values():
                for l in range(3):
                    occ[l] += c[l]
            congest = [(1 + hist[l]) * (1 + pres * occ[l]) for l in range(3)]
            res = route(job, congest, commit=False)
            if res is None:
                print('  hard fail', net); continue
            paths[net] = res
            claims[net] = claim(res[0], job['w'])
        # overuse
        over = 0
        tot = [sum(c[l].astype(int) for c in claims.values()) for l in range(3)]
        for l in range(3):
            # a cell is overused when another net's centreline sits in a claimed area
            pass
        conflicts = []
        for job in jobs:
            net = job['net']
            if net not in paths: continue
            others = [sum(claims[n][l] for n in claims if n != net) for l in range(3)]
            for q in paths[net][0]:
                if others[q[2]][q[1], q[0]] > 0:
                    conflicts.append((net, q)); hist[q[2]][q[1], q[0]] += 0.6
        nets_bad = sorted(set(c[0] for c in conflicts))
        print(f'iteration {it}: {len(conflicts)} conflicting cells, nets {nets_bad}', flush=True)
        if not conflicts and len(paths) == len(jobs):
            break
        pres *= 1.8
    guide = [1 + hist[l] for l in range(3)]
    for job in jobs:
        DIST_CACHE.clear()
        ok = route(job, guide, commit=True)
        if not ok:
            print('  commit failed for', job['net'])
else:
    for job in jobs:
        DIST_CACHE.clear()
        ok = route(job)
        if not ok and job.get('allow_b'):
            job['b_forbid'] = False; job['b_under_cost'] = 1.0
            print('  retry with B under the cell/LRA')
            DIST_CACHE.clear()
            route(job)
json.dump(result, open(sys.argv[3], 'w'), indent=1)
