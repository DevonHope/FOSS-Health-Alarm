"""Routing jobs for rev B: per net, group the pads already joined by copper, then Prim over groups."""
import json, math, sys
g = json.load(open('/tmp/wbrevb/geom.json'))
SKIP = {'/GND'}
PLANE_NETS = {'/VDD_1V8'}
W = {'/VIN': 0.3, '/PMID': 0.3, '/VBAT': 0.4, '/BATT_P': 0.4, '/SW': 0.3, '/VLED': 0.25, '/LRA_P': 0.3, '/LRA_N': 0.3,
     '/VDD_1V8': 0.15, '/REG': 0.2, '/DECD': 0.2, '/DECA': 0.2}
ORDER = ['/I2C_SCL', '/I2C_SDA', '/PMIC_INT', '/DOCK_PG', '/LED_EN', '/HAPT_EN', '/CHG_CD', '/LS_CTRL', '/UART_RX', '/UART_TX',
         '/ACC_INT1', '/ACC_INT2', '/SWDIO', '/SWDCLK', '/nRESET', '/LED_DBG', '/TS', '/ISET', '/CHG_MR',
         '/LED_R', '/LED_G', '/LED_B', '/PAD_RX', '/PAD_TX', '/PAD_SWDCLK', '/PAD_SWDIO', '/LED_A',
         '/SW', '/VLED', '/PMID', '/VIN', '/VBAT', '/BATT_P', '/REG', '/LRA_P', '/LRA_N', '/VDD_1V8']
def inpoly(pt, poly):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1: c = not c
    return c
nets = {}
for i, p in enumerate(g['pads']):
    n = p['net']
    if n and not n.startswith('unconnected') and n not in SKIP: nets.setdefault(n, []).append(i)
jobs = []
for n in ORDER + sorted(set(nets) - set(ORDER)):
    if n not in nets: continue
    idx = nets[n]
    par = {i: i for i in idx}
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    # copper nodes: tracks and vias; union pads touching the same copper
    nodes = []
    for t in g['tracks']:
        if t['net'] == n: nodes.append(('t', t))
    for v in g['vias']:
        if v['net'] == n: nodes.append(('v', v))
    cid = {}
    def key(pt): return (round(pt[0], 3), round(pt[1], 3))
    # union-find over points: tracks join their endpoints; vias join all layers at a point
    P = {}
    def pfind(k):
        while P[k] != k: P[k] = P[P[k]]; k = P[k]
        return k
    def punion(a, b): P.setdefault(a, a); P.setdefault(b, b); P[pfind(a)] = pfind(b)
    for kind, o in nodes:
        if kind == 't': punion(key(o['a']), key(o['b']))
        else: P.setdefault(key((o['x'], o['y'])), key((o['x'], o['y'])))
    pts = list(P)
    vias = [(o['x'], o['y'], o['d'] / 2) for k, o in nodes if k == 'v']
    # points that sit on a via join each other
    for (vx, vy, r) in vias:
        for q in pts:
            if math.dist(q, (vx, vy)) <= r + 1e-3: punion(q, key((vx, vy)))
    # free (dangling) track ends: escapes laid by hand, usable as route ends
    ends = {}
    for kind, o in nodes:
        if kind != 't': continue
        for pt in (o['a'], o['b']):
            k = key(pt); ends.setdefault((k, o['layer']), 0); ends[(k, o['layer'])] += 1
    def on_copper(k, layer):
        if any(math.dist(k, (vx, vy)) <= r + 1e-3 for vx, vy, r in vias): return True
        return any(p['net'] == n and p['layer'] == layer and any(inpoly(k, poly) for poly in p['polys']) for p in g['pads'])
    dangling = [(k, l) for (k, l), c in ends.items() if c == 1 and not on_copper(k, l)]
    groups = {}
    for i in idx:
        p = g['pads'][i]
        hit = [q for q in pts if any(inpoly(q, poly) for poly in p['polys'])] + \
              [key((vx, vy)) for vx, vy, r in vias if math.dist((vx, vy), (p['x'], p['y'])) < r + 0.15]
        root = pfind(hit[0]) if hit else ('pad', i)
        groups.setdefault(root, set()).add(i)
    # pads with identical position (e.g. multi-layer) are one node
    gpts = {}
    for k, l in dangling:
        r = pfind(k)
        if r in groups: gpts.setdefault(r, []).append((k[0], k[1], l))
    for vx, vy, r_ in vias:                     # fan-out vias: start anywhere on them
        r = pfind(key((vx, vy)))
        if r in groups: gpts.setdefault(r, []).append((vx, vy, 'via'))
    if n in PLANE_NETS:                          # groups with a via already meet on the inner plane
        roots = [r for r in groups if any(p[2] == 'via' for p in gpts.get(r, []))]
        if len(roots) > 1:
            keep = roots[0]
            for r in roots[1:]:
                groups[keep] |= groups.pop(r); gpts.setdefault(keep, []).extend(gpts.pop(r, []))
    ICS = ('U1', 'U201', 'U401', 'U202', 'U501')
    roots = sorted(groups, key=lambda r: (all(g['pads'][i]['ref'] in ICS for i in groups[r]) and not gpts.get(r), 0))
    G = [groups[r] for r in roots]; GP = [gpts.get(r, []) for r in roots]
    if len(G) < 2: continue
    def gd(a, b): return min(math.dist((g['pads'][i]['x'], g['pads'][i]['y']), (g['pads'][j]['x'], g['pads'][j]['y'])) for i in a for j in b)
    order = list(range(len(G)))
    done = [0]; rest = order[1:]
    while rest:
        bi = min(rest, key=lambda q: min(gd(G[q], G[d]) for d in done))
        rest.remove(bi)
        tgt = set().union(*[G[d] for d in done]); tpts = [p for d in done for p in GP[d]]
        tx = [(g['pads'][j]['x'], g['pads'][j]['y']) for j in tgt] + [(p[0], p[1]) for p in tpts]
        sv = False
        if GP[bi]:
            sx, sy, sl = min(GP[bi], key=lambda p: min(math.dist(p[:2], t) for t in tx)); spad = ['', '']
            if sl == 'via': sl, sv = 'F.Cu', True
        else:
            cand = [i for i in G[bi] if g['pads'][i]['ref'] not in ('U1', 'U201', 'U401', 'U202')] or list(G[bi])
            si = min(cand, key=lambda i: min(math.dist((g['pads'][i]['x'], g['pads'][i]['y']), t) for t in tx))
            sp = g['pads'][si]; sx, sy, sl = sp['x'], sp['y'], sp['layer']; spad = [sp['ref'], sp['num']]
        jobs.append({'net': n, 'w': W.get(n, 0.15), 'src': [sx, sy, sl], 'src_pad': spad,
                     'tgt_pads': [[g['pads'][j]['ref'], g['pads'][j]['num']] for j in tgt], 'tgt_points': [list(p) for p in tpts if p[2] != 'via'], 'allow_b': True, 'src_via': sv})
        done.append(bi)
json.dump(jobs, open(sys.argv[1], 'w'), indent=0)
print(len(jobs), 'jobs')
