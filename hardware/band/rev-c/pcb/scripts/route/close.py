"""Close DRC 'unconnected' pairs (non-GND) with direct router jobs: A -> B. Writes jobs_close.json."""
import json, re
d = json.load(open('/tmp/revb/drc.json'))
L = {'F.Cu': 1.0, 'In2.Cu': 1.5, 'B.Cu': 1.3}
def item(i):
    s = i['description']; x, y = round(i['pos']['x'], 4), round(i['pos']['y'], 4)
    net = re.search(r'\[(/[^\]]+)\]', s).group(1)
    lay = re.search(r'on (\S+\.Cu)', s); lay = lay.group(1) if lay else 'F.Cu'
    m = re.match(r'Pad (\S+) \[[^\]]+\] of (\S+) on', s)
    if m: return net, ('pad', m.group(2), m.group(1), x, y, lay)
    if s.startswith('Via'): return net, ('via', x, y)
    return net, ('pt', x, y, lay)
jobs = []
for u in d['unconnected_items']:
    if all('/GND' in i['description'] for i in u['items']): continue
    (net, a), (_, bb) = item(u['items'][0]), item(u['items'][1])
    # source: prefer the non-pad end
    if a[0] == 'pad' and bb[0] != 'pad': a, bb = bb, a
    j = {'net': net, 'w': 0.15, 'layer_cost': L, 'src_pad': ['', '']}
    if a[0] == 'pad': j['src'] = [a[3], a[4], a[5]]; j['src_pad'] = [a[1], a[2]]
    elif a[0] == 'via': j['src'] = [a[1], a[2], 'F.Cu']; j['src_via'] = True
    else: j['src'] = [a[1], a[2], a[3]]
    if bb[0] == 'pad': j['only_ref'] = bb[1]; j['tgt_pads'] = [[bb[1], bb[2]]]
    else:
        j['only_ref'] = '__none__'; j['tgt_pads'] = []
        j['tgt_points'] = [[bb[1], bb[2], l] for l in ('F.Cu', 'In2.Cu', 'B.Cu')] if bb[0] == 'via' else [[bb[1], bb[2], bb[3]]]
    jobs.append(j)
json.dump(jobs, open('/tmp/wbrevb/jobs_close.json', 'w'))
for j in jobs: print(j['net'], j['src'], j.get('tgt_pads'), j.get('tgt_points', [])[:1])
