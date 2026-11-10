"""Dock PCB rev B: second review pass (re-layout). Run once, after review_fixes.py:

    python3 scripts/relayout.py IN.kicad_pcb OUT.kicad_pcb     (KiCad 10's Python)

1. RP2040 decoupling (D-L5 / D-E4 / D-L6): the flash (U2) turns 180 degrees and moves right, which frees
   the space under the RP2040's bottom-edge supply pins. C15 (VREG_VOUT 1 uF) now sits at pin 45, and new
   100 nF caps sit at pin 43 (ADC_AVDD, C22), pins 48/49 (USB_VDD/IOVDD, C23) and pin 50 (DVDD, C24).
   The QSPI bus is re-routed (all six lines now 5-13 mm instead of up to 27 mm), the USB series
   resistors R4/R5 move under the new caps, C12 takes C15's old place, and R8/R9/C17 follow the flash.
2. Crystal (D-L4): see fix_crystal().
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from review_fixes import Board, V, F, B, IN2, MM, strip_new_silk  # noqa: E402

QSPI = ("QSPI_SS", "QSPI_SD0", "QSPI_SD1", "QSPI_SD2", "QSPI_SD3", "QSPI_SCLK")


def P(x, y):
    return V((x, y))


def move(e, ref, pos, rot):
    fp = e.b.FindFootprintByReference(ref)
    fp.SetPosition(V(pos))
    fp.SetOrientationDegrees(rot)
    return fp


def rip_net(e, net):
    for t in list(e.b.GetTracks()):
        if t.GetNetname() == "/" + net:
            e.remove(t)


def relayout_bottom(e):
    # ---- rip up --------------------------------------------------------------------------
    for n in QSPI + ("USB_DM_MCU", "USB_DP_MCU"):
        rip_net(e, n)
    e.del_seg(F, (113.09, 111.2), (112.2, 111.2))                       # USB_DM old R5 side
    e.remove(e.find_via((112.2, 111.2)))
    e.del_seg(IN2, (112.2, 111.2), (108.25, 115.15))
    e.del_seg(F, (113.09, 112.25), (108.85, 112.25))                    # USB_DP old R4 side
    for a, c in (((116.0, 110.85), (116.2, 110.65)), ((116.2, 110.65), (116.2, 110.037)),
                 ((110.12, 111.7), (109.5, 111.7))):                      # +1V1 detour to old C15
        e.del_seg(F, a, c)
    for a, c in (((115.15, 111.7), (116.0, 110.85)), ((109.5, 111.7), (115.15, 111.7))):
        e.del_seg(B, a, c)
    e.remove(e.find_via((116.0, 110.85)))
    e.remove(e.find_via((109.5, 111.7)))
    for a, c in (((111.7, 112.82), (111.7, 112.8)), ((113.12, 114.62), (113.12, 113.4)),
                 ((111.12, 113.4), (111.7, 112.82)), ((115.495, 113.555), (115.1, 113.95)),
                 ((115.4, 110.037), (115.4, 113.43)), ((115.4, 113.43), (115.495, 113.525)),
                 ((115.1, 113.95), (113.67, 113.95)), ((114.0, 115.5), (113.12, 114.62)),
                 ((113.1, 113.4), (113.12, 113.4)), ((115.495, 113.555), (115.495, 113.525)),
                 ((112.5, 112.8), (111.7, 112.8)), ((113.1, 113.4), (112.5, 112.8)),
                 ((113.67, 113.95), (113.12, 113.4)), ((114.0, 115.5), (114.0, 115.51))):
        e.del_seg(F, a, c)                                                # +3V3 to old C12/C17/R8/U2
    for a, c in (((112.75, 111.75), (112.75, 110.85)), ((111.7, 112.8), (112.75, 111.75)),
                 ((112.75, 110.85), (111.8, 109.9))):
        e.del_seg(IN2, a, c)
    e.remove(e.find_via((111.7, 112.8)))
    for a, c, v in (((114.08, 113.4), (114.61, 112.87), (114.61, 112.87)),
                    ((112.08, 113.4), (112.08, 114.15), (112.08, 114.15)),
                    ((119.305, 118.475), (120.055, 118.475), (120.055, 118.475))):
        e.del_seg(F, a, c)                                                # GND of old C17/C12/U2.4
        e.remove(e.find_via(v))
    e.del_seg(F, (114.0, 116.79), (114.65, 116.79))                     # BOOT
    e.remove(e.find_via((114.65, 116.79)))
    for a, c in (((114.65, 117.1), (114.65, 116.79)), ((119.1, 121.55), (114.65, 117.1)),
                 ((119.1, 121.55), (119.1, 122.2))):
        e.del_seg(IN2, a, c)
    e.del_seg(IN2, (133.0, 121.8), (120.3, 109.1))                      # LED_USB diagonal
    e.del_seg(IN2, (120.3, 109.1), (120.3, 107.75))

    # ---- place ---------------------------------------------------------------------------
    move(e, "C15", (113.98, 111.77), 270)
    e.b.FindFootprintByReference("C15").SetField("Description", "VREG_VOUT, at pin 45")
    move(e, "C12", (110.6, 111.7), 0)
    e.add_part("C22", (112.94, 111.77), 270)
    e.add_part("C23", (115.41, 111.55), 270)
    e.add_part("C24", (116.2, 111.55), 270)
    move(e, "R5", (112.6, 113.4), 0)
    move(e, "R4", (112.6, 114.45), 0)
    move(e, "U2", (119.9, 115.65), 270)
    move(e, "R9", (123.2, 112.2), 90)
    move(e, "R8", (123.2, 114.3), 90)
    move(e, "C17", (123.2, 117.73), 270)
    p = {(r, n): e.pad(r, n) for r, n in (
        ("C15", 1), ("C15", 2), ("C22", 1), ("C22", 2), ("C23", 1), ("C23", 2), ("C24", 1), ("C24", 2),
        ("C12", 1), ("R5", 1), ("R5", 2), ("R4", 1), ("R4", 2), ("R8", 1), ("R8", 2), ("R9", 1), ("R9", 2),
        ("C17", 1), ("C17", 2), ("U1", 43), ("U1", 45), ("U1", 46), ("U1", 47), ("U1", 49), ("U1", 50),
        ("U2", 1), ("U2", 2), ("U2", 3), ("U2", 4), ("U2", 5), ("U2", 6), ("U2", 7), ("U2", 8))}
    for (r, n), exp in {("C15", 1): (113.98, 111.29), ("C22", 1): (112.94, 111.29), ("C23", 1): (115.41, 111.23),
                        ("C24", 1): (116.2, 111.23), ("R5", 2): (113.11, 113.4), ("R4", 2): (113.11, 114.45),
                        ("R9", 1): (123.2, 112.71), ("R8", 2): (123.2, 113.79), ("C17", 1): (123.2, 117.25),
                        ("U2", 1): (121.805, 113.175), ("U2", 5): (117.995, 118.125)}.items():
        assert e.near(p[(r, n)], V(exp), 2000), (r, n, p[(r, n)], exp)
    q = lambda r, n: p[(r, n)]

    # ---- route: caps ---------------------------------------------------------------------
    e.path([q("U1", 43), P(113.4, 110.83), q("C22", 1)], F, 0.2, "+3V3")
    e.path([q("U1", 45), P(114.2, 111.07), q("C15", 1)], F, 0.2, "+1V1")
    # pins 48/49 (+3V3) had their supply through the old U2 route: a via between them now drops to
    # the B.Cu +3V3 run under the chip
    v48 = e.via((115.6, 110.72), "+3V3").GetPosition()
    e.path([e.pad("U1", 48), P(115.4, 110.52), v48], F, 0.2, "+3V3")
    e.path([v48, P(115.6, 111.04), q("C23", 1)], F, 0.2, "+3V3")
    e.split(B, (111.8, 109.9), (120.18, 109.9), (115.6, 109.9))
    e.seg(v48, P(115.6, 109.9), B, 0.2, "+3V3")
    e.seg(q("U1", 50), q("C24", 1), F, 0.2, "+1V1")
    g1 = e.via((112.35, 112.25), "GND").GetPosition()
    e.seg(q("C15", 2), q("C22", 2), F, 0.25, "GND")
    e.seg(q("C22", 2), g1, F, 0.25, "GND")
    g2 = e.via((115.805, 112.6), "GND").GetPosition()
    e.seg(q("C23", 2), P(115.805, 112.265), F, 0.2, "GND")
    e.path([q("C24", 2), P(115.805, 112.265), g2], F, 0.2, "GND")
    e.seg(V((110.12, 110.6)), q("C12", 1), F, 0.2, "+3V3")             # C12 from C14's +3V3 pad

    # ---- route: USB ----------------------------------------------------------------------
    e.path([q("U1", 46), P(114.6, 112.9), P(114.1, 113.4), q("R5", 2)], F, 0.2, "USB_DM_MCU")
    e.path([q("U1", 47), P(115.0, 113.85), P(114.4, 114.45), q("R4", 2)], F, 0.2, "USB_DP_MCU")
    vdm = e.via((111.3, 113.4), "USB_DM").GetPosition()
    e.seg(q("R5", 1), vdm, F, 0.2, "USB_DM")
    e.path([vdm, P(110.05, 114.65), P(108.75, 114.65), e.find_via((108.25, 115.15)).GetPosition()],
           IN2, 0.2, "USB_DM")
    e.path([q("R4", 1), P(111.4, 114.45), P(110.6, 113.65), P(110.6, 112.65), P(110.2, 112.25),
            P(108.85, 112.25)], F, 0.2, "USB_DP")

    # ---- route: QSPI (U2 turned: top row GND SD2 SD1 SS, bottom row SD0 SCLK SD3 VCC) ----
    def qp(n):
        return e.pad("U1", n)
    e.path([qp(56), P(118.6, 110.7), P(118.9, 111.0), P(121.505, 111.0), P(121.805, 111.3), q("U2", 1)],
           F, 0.15, "QSPI_SS")
    e.path([qp(55), P(118.2, 111.1), P(118.5, 111.4), P(120.235, 111.4), P(120.535, 111.7), q("U2", 2)],
           F, 0.15, "QSPI_SD1")
    e.path([qp(54), P(117.8, 111.5), P(118.1, 111.8), P(118.965, 111.8), P(119.265, 112.1), q("U2", 3)],
           F, 0.15, "QSPI_SD2")
    e.path([qp(53), P(117.4, 117.53), q("U2", 5)], F, 0.15, "QSPI_SD0")
    e.path([qp(52), P(117.0, 119.5), P(117.3, 119.8), P(118.965, 119.8), P(119.265, 119.5), q("U2", 6)],
           F, 0.15, "QSPI_SCLK")
    e.path([qp(51), P(116.6, 119.9), P(116.9, 120.2), P(120.235, 120.2), P(120.535, 119.9), q("U2", 7)],
           F, 0.15, "QSPI_SD3")
    gv = e.via((117.995, 115.0), "GND").GetPosition()
    e.seg(q("U2", 4), gv, F, 0.25, "GND")

    # ---- route: SS pull-up / BOOT resistor, flash supply ---------------------------------
    e.path([q("U2", 1), P(122.585, 113.175), q("R8", 2)], F, 0.15, "QSPI_SS")
    e.seg(q("R8", 2), q("R9", 1), F, 0.15, "QSPI_SS")
    v33 = e.via((123.95, 116.5), "+3V3").GetPosition()
    e.path([q("R8", 1), P(123.2, 115.75), v33], F, 0.2, "+3V3")
    e.seg(v33, q("C17", 1), F, 0.2, "+3V3")
    e.path([q("U2", 8), P(122.325, 118.125), q("C17", 1)], F, 0.2, "+3V3")
    e.path([e.find_via((120.18, 109.9)).GetPosition(), P(123.95, 113.67), v33], B, 0.2, "+3V3")
    gc = e.via((123.2, 118.95), "GND").GetPosition()
    e.seg(q("C17", 2), gc, F, 0.25, "GND")
    vb = e.via((123.2, 111.0), "BOOT").GetPosition()
    e.seg(q("R9", 2), vb, F, 0.15, "BOOT")
    e.path([vb, P(123.2, 118.1), e.find_via((119.1, 122.2)).GetPosition()], IN2, 0.15, "BOOT")

    # ---- LED_USB on In2 goes round the flash's new spot ----------------------------------
    # (straight east from its via, then 45 degrees, 0.9 mm clear of the P4 spring-pin pad)
    e.path([e.find_via((120.3, 107.75)).GetPosition(), P(124.05, 107.75), P(133.0, 116.7), V((133.0, 121.8))],
           IN2, 0.2, "LED_USB")


def main(src, dst):
    e = Board(src)
    relayout_bottom(e)
    pcbnew.SaveBoard(dst, e.b, True)
    strip_new_silk(dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
