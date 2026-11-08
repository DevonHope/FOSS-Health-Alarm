import pcbnew
MM=pcbnew.FromMM; mm=pcbnew.ToMM
P=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
def seg(b,net,layer,pts,w):
    n=b.FindNet(net)
    for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
        t=pcbnew.PCB_TRACK(b); t.SetStart(P(x1,y1)); t.SetEnd(P(x2,y2)); t.SetWidth(MM(w))
        t.SetLayer(b.GetLayerID(layer)); t.SetNet(n); b.Add(t)
def via(b,net,x,y,d=0.45,drill=0.3):
    v=pcbnew.PCB_VIA(b); v.SetPosition(P(x,y)); v.SetWidth(MM(d)); v.SetDrill(MM(drill))
    v.SetNet(b.FindNet(net)); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); b.Add(v)
def refill(b):
    f=pcbnew.ZONE_FILLER(b); f.Fill(b.Zones())
