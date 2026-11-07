"""Failed-first reordering around router.py: rerun with the jobs that failed moved to the front; keep the best."""
import json, subprocess, sys, re, shutil
jobs = json.load(open('/tmp/wbrevb/jobs_loop.json'))
best = None
for it in range(int(sys.argv[1]) if len(sys.argv) > 1 else 6):
    json.dump(jobs, open('/tmp/wbrevb/jobs_it.json', 'w'))
    out = subprocess.run(['/tmp/wb3d-venv/bin/python', '/tmp/wbrevb/router.py', '/tmp/wbrevb/geom.json', '/tmp/wbrevb/jobs_it.json', '/tmp/wbrevb/routes_it.json'],
                         capture_output=True, text=True).stdout
    failed = []
    for line in out.splitlines():
        m = re.match(r"(\S+): no route .* src \[([-\d.]+), ([-\d.]+), '([^']+)'\]", line)
        if m: failed.append((m.group(1), round(float(m.group(2)), 3), round(float(m.group(3)), 3)))
    failed = list(dict.fromkeys(failed))
    print('iter', it, 'failed', len(failed), [f[0] for f in failed], flush=True)
    if best is None or len(failed) < best:
        best = len(failed); shutil.copy('/tmp/wbrevb/routes_it.json', '/tmp/wbrevb/routes_best.json'); shutil.copy('/tmp/wbrevb/jobs_it.json', '/tmp/wbrevb/jobs_best.json')
    if not failed: break
    fk = {(f[0], f[1], f[2]) for f in failed}
    def isf(j): return (j['net'], round(j['src'][0], 3), round(j['src'][1], 3)) in fk
    jobs = [j for j in jobs if isf(j)] + [j for j in jobs if not isf(j)]
print('best', best)
