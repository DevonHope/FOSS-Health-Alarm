"""Write ../rigid-rev-b.kicad_pro from rev A's (same rules, stackup classes) with rev B net-class patterns.
Run after gen_pcb.py: pcbnew.SaveBoard() resets the project rules to KiCad defaults."""
import json, os, copy
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, '..', '..', 'rigid-rev-a', 'rigid-rev-a.kicad_pro')))
d['meta']['filename'] = 'rigid-rev-b.kicad_pro'
d['sheets'] = []
d['board']['design_settings']['drc_exclusions'] = []
ns = d['net_settings']
rf = copy.deepcopy(next(c for c in ns['classes'] if c['name'] == 'Default'))
rf.update(name='RF', track_width=0.3, clearance=0.15, priority=-1)
ns['classes'] = [c for c in ns['classes'] if c['name'] != 'RF'] + [rf]
P = {'Power': ['/VIN', '/PMID', '/SW', '/VLED'], 'Motor': ['/LRA_P', '/LRA_N'], 'Rail': ['/VDD_1V8', '/DECD', '/DECA', '/DCC'],
     'Gnd': ['/GND'], 'Batt': ['/BATT_P', '/VBAT'], 'RF': ['/ANT', '/RF1', '/RF2', '/RF_50', '/ANT_FEED']}
ns['netclass_patterns'] = [{'netclass': k, 'pattern': p} for k, v in P.items() for p in v]
s = json.dumps(d, indent=2).replace('rigid-rev-a', 'rigid-rev-b')
open(os.path.join(HERE, '..', 'rigid-rev-b.kicad_pro'), 'w').write(s + '\n')
print('wrote rigid-rev-b.kicad_pro')
