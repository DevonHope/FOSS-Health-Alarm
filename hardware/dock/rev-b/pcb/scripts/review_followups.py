"""Dock PCB rev B: small follow-ups from the independent verification of 2026-11-08. Run once, after
relayout.py:  python3 scripts/review_followups.py IN.kicad_pcb OUT.kicad_pcb   (KiCad 10's Python)

N1  U2's pin-1 silk dot follows U2 to its new place (next to pin 1, outside the pad).
N2  VBUS_F's In2 diagonal past J1's lower shield slot is 0.4 mm instead of 0.45 mm, so its edge sits
    0.33 mm from the slot's hole (JLC plated hole to track).
N6  D2's LED_ACT via moves 0.08 mm right: 0.28 mm hole to D2's cathode pad (was 0.20).
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_fixes import Board, V, F, IN2, MM  # noqa: E402


def main(src, dst):
    e = Board(src)
    # N1
    dots = [d for d in e.b.GetDrawings() if d.GetLayer() == pcbnew.F_SilkS and isinstance(d, pcbnew.PCB_SHAPE)
            and d.GetShape() == pcbnew.SHAPE_T_CIRCLE and e.near(d.GetCenter(), V((115.495, 119.75)), 2000)]
    assert len(dots) == 1, len(dots)
    p1 = e.pad("U2", 1)
    assert e.near(p1, V((121.805, 113.175)), 2000)
    d = dots[0]
    r = d.GetEnd().x - d.GetCenter().x
    c = pcbnew.VECTOR2I(p1.x, p1.y - MM(0.975 + 0.3))     # above the pad's outer end
    d.SetCenter(c)
    d.SetEnd(pcbnew.VECTOR2I(c.x + r, c.y))
    # N2
    t = e.find_seg(IN2, (111.25, 118.8), (114.25, 121.8))
    assert t.GetWidth() == MM(0.45)
    t.SetWidth(MM(0.4))
    # N6
    v = e.find_via((116.4, 122.7))
    e.del_seg(IN2, (116.4, 122.0), (116.4, 122.7))
    e.del_seg(IN2, (116.4, 122.0), (113.8, 119.4))
    e.del_seg(F, (117.0875, 122.7), (116.4, 122.7))
    v.SetPosition(V((116.48, 122.7)))
    p = v.GetPosition()
    e.path([V((113.8, 119.4)), V((116.48, 122.08)), p], IN2, 0.15, "LED_ACT")
    e.seg(V((117.0875, 122.7)), p, F, 0.2, "LED_ACT")
    pcbnew.SaveBoard(dst, e.b, True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
