import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); mm=pcbnew.ToMM
net=sys.argv[2]; x0,y0,x1,y1=map(float,sys.argv[3:7])
for t in b.GetTracks():
    if t.GetNetname()!=net: continue
    if t.Type()==pcbnew.PCB_VIA_T:
        p=t.GetPosition()
        if x0<=mm(p.x)<=x1 and y0<=mm(p.y)<=y1: print('  via',round(mm(p.x),4),round(mm(p.y),4),mm(t.GetWidth(pcbnew.F_Cu)))
    else:
        a,c=t.GetStart(),t.GetEnd()
        if any(x0<=mm(q.x)<=x1 and y0<=mm(q.y)<=y1 for q in (a,c)): print(' ',b.GetLayerName(t.GetLayer()),[round(mm(a.x),4),round(mm(a.y),4)],[round(mm(c.x),4),round(mm(c.y),4)],mm(t.GetWidth()))
for f in b.GetFootprints():
    for p in f.Pads():
        q=p.GetPosition()
        if p.GetNetname()==net and x0-0.5<=mm(q.x)<=x1+0.5 and y0-0.5<=mm(q.y)<=y1+0.5: print('  pad',f.GetReference(),p.GetNumber(),round(mm(q.x),4),round(mm(q.y),4),[b.GetLayerName(l) for l in p.GetLayerSet().CuStack()][:2], [round(mm(p.GetSize(pcbnew.F_Cu).x),3),round(mm(p.GetSize(pcbnew.F_Cu).y),3)])
