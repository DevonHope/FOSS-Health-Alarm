"""Copy the board to SRC_OUT and add KiKit tab annotations where the long edges are clear of copper and
courtyards (found by scanning for 4 mm windows with nothing within 0.65 mm of the edge):
top edge only near x 122.6; bottom edge 105.4-116.7 (tabs at 108.5 and 115.0, clear of the antenna corner).
usage (KiCad python, KiKit on PYTHONPATH): paneltabs.py BOARD SRC_OUT"""
import os, sys, pcbnew
import kikit
lib = os.path.join(os.path.dirname(kikit.__file__), 'resources', 'kikit.pretty')
b = pcbnew.LoadBoard(sys.argv[1]); F = pcbnew.FromMM
TABS = [((122.6, 99.9), 270), ((108.5, 115.1), 90), ((115.0, 115.1), 90)]   # just outside the edge, arrow pointing into the board
for i, ((x, y), ang) in enumerate(TABS):
    fp = pcbnew.FootprintLoad(lib, 'Tab'); fp.SetFPID(pcbnew.LIB_ID('kikit', 'Tab')); fp.SetReference(f'KIKIT_TAB{i + 1}')
    fp.SetPosition(pcbnew.VECTOR2I(F(x), F(y))); fp.SetOrientationDegrees(ang); b.Add(fp)
pcbnew.SaveBoard(sys.argv[2], b); print('tab annotations:', len(TABS))
