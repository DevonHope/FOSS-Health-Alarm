"""Plane fan-out: a via (0.4/0.2) with a short 0/45/90 stub next to the given pads, onto an inner plane.
usage: fan_net.py NET OUT.json REF.PAD [REF.PAD ...]   (a pad given as x,y uses that point: stub end)"""
import sys, json, math
NET, OUT, PADS = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.argv = ['router.py', '/tmp/wbrevb/geom.json', '/tmp/wbrevb/empty.json', '/tmp/wbrevb/_x.json']
json.dump([], open('/tmp/wbrevb/empty.json', 'w'))
sys.path.insert(0, '/tmp/wbrevb')
import router as R
VD = 0.4
dist = R.obstacle_dist(NET)
def ok_pt(x, y):
    i, j = int(round((x - R.X0) / R.RES)), int(round((y - R.Y0) / R.RES))
    return all(dist[l][j, i] >= R.CLR + VD / 2 + 0.03 + (0.1 if l == 'In2.Cu' else 0) for l in R.LAYERS) and R.edge_d[j, i] >= R.EDGE + VD / 2 + 0.06 and not R.ko_mask[j, i]
def ok_seg(a, b, w):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.025))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n; y = a[1] + (b[1] - a[1]) * k / n
        i, j = int(round((x - R.X0) / R.RES)), int(round((y - R.Y0) / R.RES))
        if dist['F.Cu'][j, i] < R.CLR + w / 2 + 0.01: return False
    return True
u1 = R.g['u1_courtyard']
placed = [(v['x'], v['y']) for v in R.g['vias']]
out = {'tracks': [], 'vias': []}
for spec in PADS:
    if ',' in spec:
        px, py = map(float, spec.split(','))
    else:
        ref, num = spec.split('.')
        p = [q for q in R.g['pads'] if q['ref'] == ref and q['num'] == num and q['layer'] == 'F.Cu'][0]; px, py = p['x'], p['y']
    best = None
    for rr in (0.55, 0.65, 0.75, 0.9, 1.05, 1.2, 1.4, 1.6):
        for k in range(8):
            a = 2 * math.pi * k / 8
            x = round(px + rr * math.cos(a), 3); y = round(py + rr * math.sin(a), 3)
            if u1[0] - 0.2 <= x <= u1[2] + 0.2 and u1[1] - 0.2 <= y <= u1[3] + 0.2: continue
            if any(math.hypot(x - q[0], y - q[1]) < 0.65 for q in placed): continue
            if ok_pt(x, y) and ok_seg((px, py), (x, y), 0.2): best = (x, y); break
        if best: break
    if best:
        placed.append(best)
        out['vias'].append({'net': NET, 'x': best[0], 'y': best[1], 'd': 0.4, 'drill': 0.2})
        out['tracks'].append({'net': NET, 'layer': 'F.Cu', 'w': 0.2, 'pts': [[px, py], list(best)]})
    else:
        print('no via spot for', spec)
json.dump(out, open(OUT, 'w')); print(NET, 'vias', len(out['vias']))
