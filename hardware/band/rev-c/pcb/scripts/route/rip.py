"""Remove router-made copper (not in the pre-route board) on the given nets. usage: rip.py BOARD PRE NET,NET"""
import sys, pcbnew
B, PRE, NETS = sys.argv[1], sys.argv[2], set(sys.argv[3].split(','))
def key(t):
    if t.Type() == pcbnew.PCB_VIA_T: return ('v', t.GetNetname(), round(pcbnew.ToMM(t.GetPosition().x), 3), round(pcbnew.ToMM(t.GetPosition().y), 3))
    a, e = sorted([(round(pcbnew.ToMM(t.GetStart().x), 3), round(pcbnew.ToMM(t.GetStart().y), 3)), (round(pcbnew.ToMM(t.GetEnd().x), 3), round(pcbnew.ToMM(t.GetEnd().y), 3))])
    return ('t', t.GetNetname(), t.GetLayer(), a, e)
pre = {key(t) for t in pcbnew.LoadBoard(PRE).GetTracks()}
b = pcbnew.LoadBoard(B); n = 0
for t in list(b.GetTracks()):
    if t.GetNetname() in NETS and key(t) not in pre: b.Remove(t); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(B, b); print('ripped', n)
