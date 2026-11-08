"""WakeBand case for the rigid rev B board: rev A's case (../case-rev-a/case_rev_a.py) with two shell changes.

1. Antenna pocket: the Johanson chip antenna (AE1, 3.2 x 1.6 x 1.3 mm) stands 0.2 mm taller than the
   1.1 mm the rev A shell leaves over F.Cu, so the roof gets a 0.35 mm deep pocket over it (0.85 mm of
   roof left).
2. Dock land: rev A pressed a solid land onto F.Cu from x 119.8 to the board end over the top pin pair;
   rev B has the charger's inductor and capacitors under the start of it, so the land starts at x 127.6
   (still over the whole top spring-pin pair at x 131.5, on pads and solder mask only).
The cover, contact carrier, spring pins, magnets, dock and strap are unchanged from rev A.
usage (needs build123d): python case_rev_b.py OUT_DIR [board.step cell.step lra.step]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "case-rev-a"))
import case_rev_a as A  # noqa: E402
from build123d import Color, export_step, export_stl  # noqa: E402

A.LAND = (127.6, A.CAV[1], A.CAV[2], 103.2)
ANT = (102.15, 112.55)                # AE1 centre (board coordinates), long axis along y
ANT_POCKET = (1.6 + 0.6, 3.2 + 0.6)   # body + 0.3 mm a side
ANT_H = 1.3 + 0.1                      # height + tolerance
POCKET_TOP = A.BOARD_F + ANT_H + 0.15  # 0.15 mm air over the antenna


def make_shell():
    s = A.make_shell()
    x, y = ANT
    s -= A.slab(A.rrect(x - ANT_POCKET[0] / 2, x + ANT_POCKET[0] / 2, y - ANT_POCKET[1] / 2, y + ANT_POCKET[1] / 2, 0.3),
                A.ROOF_IN - 0.1, POCKET_TOP)
    return s


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    shell, cover = make_shell(), A.make_cover()
    assert len(shell.solids()) == 1 and shell.is_valid
    bb = shell.bounding_box()
    print(f"shell: valid {shell.is_valid}, volume {shell.volume:.0f} mm3, roof inside {A.ROOF_IN:.2f}, "
          f"antenna pocket to z {POCKET_TOP:.2f} (roof left {A.TOP - POCKET_TOP:.2f} mm), top {A.TOP:.2f}")
    ov = shell & cover
    print("shell vs cover overlap:", round(ov.volume if ov is not None else 0, 4))
    p = A.to_step_frame(shell); p.label, p.color = "case shell", Color(0.20, 0.22, 0.25)
    export_step(p, str(out / "wakeband-case-rev-b-shell.step"))
    export_stl(p, str(out / "wakeband-case-rev-b-shell.stl"), tolerance=0.01, angular_tolerance=0.1)
    if len(sys.argv) > 4:
        asm = A.assembly_in_design_frame(sys.argv[2:5])
        hits = A.clash((("shell", shell), ("cover", cover)), asm)
        print(f"clash check: {len(asm)} assembly solids, {len(hits)} overlaps")
        for h in hits:
            print("  ", h)
