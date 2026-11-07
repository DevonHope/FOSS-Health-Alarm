"""Hand-laid copper for the nRF54L10 reference circuit (KiCad python), after transplant.py.
Clean 0/45/90 versions of Nordic's reference routes (same topology), every end on a pad or via centre.
RF: ladder on one line, 50-ohm (0.36 mm) feed from C11 through the tuning network to the antenna."""
import os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
B = sys.argv[1]
b = pcbnew.LoadBoard(B)
F, mm = pcbnew.FromMM, pcbnew.ToMM
def V(x, y): return pcbnew.VECTOR2I(F(x), F(y))
def seg(net, layer, pts, w):
    n = b.FindNet('/' + net); L = b.GetLayerID(layer)
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetWidth(F(w)); t.SetLayer(L); t.SetNet(n); b.Add(t)
VIAS = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]   # cached: GetTracks() goes stale after Remove()
def via_at(x, y):
    for v in VIAS:
        if abs(mm(v.GetPosition().x) - x) < 0.01 and abs(mm(v.GetPosition().y) - y) < 0.01:
            return v
    raise SystemExit(f'no via at {x},{y}')
def move_via(a, c): via_at(*a).SetPosition(V(*c))
move_via((106.525, 106.775), (106.56, 106.775))     # DECA via: 45 deg from C5
move_via((110.31, 109.595), (110.31, 109.56))       # DECA via: 45 deg from C12
move_via((112.19, 109.49), (112.17, 109.6))         # DECD via: on the C1-L1 line, clear of DCC
move_via((106.135, 104.61), (106.135, 104.615))     # C13 GND via in line with the pad
_v = via_at(113.69, 108.475); VIAS.remove(_v); b.Remove(_v)
move_via((110.92, 109.9), (110.97, 109.9))          # C12 GND via under the pad (no pour here: Nordic rule area)                   # clashes with the pin 47/48 VDD link; C10 GND goes to the pour
# RF ladder (F.Cu) and 50-ohm feed
seg('ANT', 'F.Cu', [(107.975, 105.2), (107.115, 105.2)], 0.25)
seg('RF1', 'F.Cu', [(106.545, 105.2), (106.015, 105.2)], 0.25)
seg('RF1', 'F.Cu', [(106.545, 105.6), (106.545, 105.2)], 0.25)
seg('RF2', 'F.Cu', [(105.445, 105.2), (104.9, 105.2)], 0.25)
seg('RF2', 'F.Cu', [(104.9, 105.2), (104.36, 105.2)], 0.25)
seg('RF_50', 'F.Cu', [(103.79, 105.2), (103.25, 105.2)], 0.25)
seg('RF_50', 'F.Cu', [(103.25, 105.2), (102.75, 105.7), (102.75, 106.89)], 0.36)
seg('RF_50', 'F.Cu', [(102.75, 106.89), (101.73, 106.89)], 0.36)
seg('ANT_FEED', 'F.Cu', [(102.75, 107.91), (101.73, 107.91)], 0.36)
seg('ANT_FEED', 'F.Cu', [(102.75, 107.91), (102.75, 110.5), (102.15, 111.1)], 0.36)
# grounds Nordic routes on purpose
seg('GND', 'F.Cu', [(107.115, 105.6), (107.975, 105.6), (109.2, 105.6)], 0.2)   # C6 -> VSS_PA -> EP via only
seg('GND', 'F.Cu', [(104.9, 104.63), (104.9, 104.21)], 0.25)                                       # C9 -> via (bottom-layer ground)
seg('GND', 'F.Cu', [(106.54, 104.615), (106.135, 104.615)], 0.25)                                  # C13
seg('GND', 'F.Cu', [(106.545, 106.22), (106.135, 106.22)], 0.25)                                   # C5
seg('GND', 'F.Cu', [(106.19, 107.98), (105.04, 109.13), (105.04, 109.43)], 0.15)                    # X2 case pads (no pour under X2)
seg('GND', 'F.Cu', [(105.04, 109.43), (105.04, 110.455)], 0.15)
seg('GND', 'F.Cu', [(115.085, 103.03), (115.085, 102.585)], 0.25)                                  # C7
seg('GND', 'F.Cu', [(110.97, 109.47), (110.97, 109.9)], 0.2)                                        # C12
# crystals
seg('XC1', 'F.Cu', [(107.975, 106.4), (107.575, 106.4), (106.725, 107.25), (105.77, 107.25), (105.04, 107.98)], 0.15)
seg('XC2', 'F.Cu', [(107.975, 106.8), (107.6, 106.8), (106.88, 107.52), (106.88, 108.74), (106.19, 109.43)], 0.15)
seg('XL1', 'F.Cu', [(114.025, 107.2), (115.12, 107.2), (115.825, 107.905)], 0.15)
seg('XL2', 'F.Cu', [(114.025, 106.8), (115.48, 106.8), (115.825, 106.455)], 0.15)
# DECA / DECD / DCC (Nordic topology: DECA via bottom to the FB1 side, DECD via bottom to FB1)
seg('DECA', 'F.Cu', [(107.975, 106.0), (107.55, 106.0), (107.33, 106.22), (107.115, 106.22)], 0.2)
seg('DECA', 'F.Cu', [(107.115, 106.22), (106.56, 106.775)], 0.2)
seg('DECA', 'B.Cu', [(106.56, 106.775), (106.56, 107.93), (108.19, 109.56), (110.31, 109.56)], 0.3)
seg('DECA', 'F.Cu', [(111.2, 108.025), (111.2, 108.67), (110.97, 108.9)], 0.2)
seg('DECA', 'F.Cu', [(110.97, 108.9), (110.31, 109.56)], 0.2)
seg('DECA', 'F.Cu', [(110.31, 109.56), (110.31, 110.5)], 0.2)
seg('DECA', 'F.Cu', [(110.31, 110.5), (110.97, 110.5)], 0.2)
seg('DECD', 'F.Cu', [(112.0, 108.025), (112.0, 108.74), (112.17, 108.91)], 0.2)
seg('DECD', 'F.Cu', [(112.17, 108.91), (112.17, 109.6)], 0.2)
seg('DECD', 'F.Cu', [(112.17, 109.6), (112.17, 110.23)], 0.2)
seg('DECD', 'B.Cu', [(112.17, 109.6), (112.17, 110.625), (111.22, 111.575)], 0.2)
seg('DECD', 'F.Cu', [(111.22, 111.575), (110.97, 111.325), (110.97, 111.07)], 0.2)
seg('DCC', 'F.Cu', [(112.4, 108.025), (112.4, 108.4), (112.62, 108.62), (112.62, 109.33), (113.52, 110.23)], 0.2)
# VDD next to the IC
seg('VDD_2V0', 'F.Cu', [(112.8, 108.025), (113.2, 108.025)], 0.2)
seg('VDD_2V0', 'F.Cu', [(112.8, 108.025), (112.8, 108.35), (113.025, 108.575), (113.025, 108.905)], 0.2)
seg('VDD_2V0', 'F.Cu', [(107.975, 107.2), (107.69, 107.2), (107.44, 107.45), (107.44, 107.71)], 0.2)
seg('VDD_2V0', 'F.Cu', [(109.6, 101.975), (109.6, 101.04)], 0.2)
seg('VDD_2V0', 'F.Cu', [(114.025, 103.6), (115.085, 103.6)], 0.2)
# nRESET filter
seg('nRESET_IC', 'F.Cu', [(107.975, 104.8), (107.295, 104.8), (107.11, 104.615)], 0.15)
seg('nRESET_IC', 'F.Cu', [(107.11, 104.615), (107.11, 104.525), (106.635, 104.05)], 0.15)
# ---- GPIO fan-out to vias (0.4/0.2 mm) outside the QFN; the router continues from each via ----
def via(net, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(F(0.4)); v.SetDrill(F(0.2))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('/' + net)); v.SetRemoveUnconnected(True); v.SetKeepStartEnd(True); b.Add(v)
X = 114.025                                            # east pins 5-9: straight stubs, vias staggered in two columns
for pin_y, net, vx in ((105.6, 'I2C_SCL', 115.75), (105.2, 'PMIC_INT', 116.5), (104.8, 'DOCK_PG', 115.75),
                       (104.4, 'HAPT_EN', 116.5), (104.0, 'I2C_SDA', 115.75)):
    seg(net, 'F.Cu', [(X, pin_y), (vx, pin_y)], 0.15); via(net, vx, pin_y)
seg('SWDCLK', 'F.Cu', [(107.975, 103.2), (106.95, 103.2)], 0.15); via('SWDCLK', 106.95, 103.2)                 # west
seg('SWDIO', 'F.Cu', [(107.975, 102.8), (107.3, 102.8), (106.95, 102.45)], 0.15); via('SWDIO', 106.95, 102.45)
seg('ACC_INT1', 'F.Cu', [(107.975, 103.6), (106.35, 103.6)], 0.15); via('ACC_INT1', 106.35, 103.6)
seg('ACC_INT2', 'F.Cu', [(108.8, 101.975), (108.8, 101.75), (108.4, 101.35)], 0.15); via('ACC_INT2', 108.4, 101.35)   # top
seg('UART_TX', 'F.Cu', [(110.8, 101.975), (110.8, 100.95)], 0.15); via('UART_TX', 110.8, 100.95)
seg('UART_RX', 'F.Cu', [(111.2, 101.975), (111.2, 101.4), (111.6, 101.0)], 0.15); via('UART_RX', 111.6, 101.0)
seg('LS_CTRL', 'F.Cu', [(113.2, 101.975), (113.2, 100.95)], 0.15); via('LS_CTRL', 113.2, 100.95)
seg('LED_EN', 'F.Cu', [(109.2, 108.025), (109.2, 108.9)], 0.15); via('LED_EN', 109.2, 108.9)                   # bottom
seg('CHG_CD', 'F.Cu', [(109.6, 108.025), (109.6, 108.65), (109.85, 108.9)], 0.15); via('CHG_CD', 109.85, 108.9)
pcbnew.SaveBoard(B, b)
import subprocess; subprocess.run(['python3', os.path.join(HERE, 'mkpro.py')], capture_output=True)
print('hand-laid cluster copper')
