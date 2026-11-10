import os, sys, json; sys.path.insert(0,'/tmp/wbrevb')
from common import *
B=sys.argv[2] if len(sys.argv)>2 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','rigid-rev-c.kicad_pcb'); b=pcbnew.LoadBoard(B)
r=json.load(open(sys.argv[1]))
for t in r['tracks']: seg(b,t['net'],t['layer'],[tuple(p) for p in t['pts']],t['w'])
for v in r['vias']: via(b,v['net'],round(v['x'],4),round(v['y'],4),v.get('d',0.45),v.get('drill',0.3))
refill(b); pcbnew.SaveBoard(B,b)
