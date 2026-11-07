"""GND pours on all four copper layers (In1 is the solid reference plane) and the antenna keep-out
(KiCad python). The keep-out covers the chip antenna's corner on every layer: no pour, no vias;
only the antenna feed track enters it.  usage: zones.py BOARD"""
import os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
B = sys.argv[1]
b = pcbnew.LoadBoard(B)
F = pcbnew.FromMM
POCKET = (100.0, 109.1, 104.2, 115.0)
for z in list(b.Zones()):
    if z.GetZoneName() in ('GND pour', 'Antenna keep-out', 'VDD_1V8 plane'): b.Remove(z)
def outline(z, x0, y0, x1, y1):
    o = z.Outline(); o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): o.Append(F(x), F(y))
gnd = b.FindNet('/GND')
for layer in (pcbnew.F_Cu, b.GetLayerID('In1.Cu'), b.GetLayerID('In2.Cu'), pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd); z.SetZoneName('GND pour'); z.SetAssignedPriority(0)
    outline(z, 99.5, 99.5, 133.5, 115.5)
    z.SetLocalClearance(F(0.2 if layer not in (pcbnew.F_Cu, pcbnew.B_Cu) else 0.15)); z.SetMinThickness(F(0.15))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(F(0.2)); z.SetThermalReliefSpokeWidth(F(0.25))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)
# VDD_1V8 plane on In2 over the radio, sensor and charger area (priority over the In2 GND pour)
v = pcbnew.ZONE(b); v.SetLayer(b.GetLayerID('In2.Cu')); v.SetNet(b.FindNet('/VDD_1V8')); v.SetZoneName('VDD_1V8 plane'); v.SetAssignedPriority(1)
outline(v, 100.3, 100.3, 125.4, 112.0)
v.SetLocalClearance(F(0.2)); v.SetMinThickness(F(0.15)); v.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
v.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); b.Add(v)
k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetZoneName('Antenna keep-out')
ls = pcbnew.LSET()
for l in (pcbnew.F_Cu, b.GetLayerID('In1.Cu'), b.GetLayerID('In2.Cu'), pcbnew.B_Cu): ls.AddLayer(l)
k.SetLayerSet(ls)
k.SetDoNotAllowZoneFills(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowTracks(False)
k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
outline(k, POCKET[0] - 0.5, POCKET[1], POCKET[2], POCKET[3] + 0.5)
b.Add(k)
# hand-soldered lead pads: thermal relief so an iron can heat them
for ref in ('TP201', 'TP202', 'TP501', 'TP502'):
    fp = b.FindFootprintByReference(ref)
    if fp:
        for p in fp.Pads(): p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(B, b)
import subprocess; subprocess.run(['python3', os.path.join(HERE, 'mkpro.py')], capture_output=True)
print('zones added and filled')
