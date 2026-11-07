# WakeBand contact carrier rev A

A small bare PCB that holds the band's four dock contacts. It is glued into
a pocket in the wrist cover (`../case-rev-a`) and doubles as the soldering
jig: the pins drop into its plated holes, which hold them square while you
solder the flanges with the cover lying wrist side down on the bench.

| Item | Value |
| --- | --- |
| Board | 2.2 x 15.1 mm, 1.6 mm FR4, 2 layers, ENIG, corner radius 0.5 mm |
| Holes | 4 x 0.6 mm plated, Ø1.4 mm pads both sides, at x 131.5, y 101.1 / 103.3 / 111.7 / 113.9 (band board coordinates) |
| Pins | 4 x Mill-Max 0906-2-15-20-75-14-11-0 (tail Ø0.43 mm in the 0.6 mm hole, flange Ø1.83 mm on the top pad) |
| Copper | pads only; each pin is its own contact (no traces) |
| Files | `contact-carrier-rev-a.kicad_pcb` (one board), `contact-carrier-rev-a-panel.kicad_pcb` (6-up panel, 48.2 x 29.1 mm), `fab/contact-carrier-rev-a-fab.zip`, `fab/contact-carrier-rev-a-panel-fab.zip` |
| DRC | 0 violations, 0 unconnected (board and panel) |

The coordinates match the main board's B-side landing pads (J601) directly,
so the KiCad file can be overlaid on the band board.

## Why 0906-2 and 1.6 mm

The pin has to reach from the wrist face to B.Cu (6.7 mm) with its tail as
the outer contact and its plunger at about mid-stroke on the board:

| | z (mm) |
| --- | --- |
| B.Cu landing pad | 6.70 |
| 0906-2 free tip: flange underside + A (5.00) | 7.30 |
| flange underside = carrier top | 2.30 |
| carrier underside, on a 0.7 mm floor step | 0.70 |
| tail end (2.30 - 1.75) | 0.55 |
| wrist face | 0 |

Compression when closed: 7.30 - 6.70 = **0.60 mm** of a 1.40 mm stroke
(mid-stroke 0.70). No cutting: every length is the catalogue length. A
thinner carrier would push the tails further out of their windows; a
longer 0906 (-3, -4) would run the spring close to full stroke.

## Ordering

- JLCPCB (or any fab): upload **`fab/contact-carrier-rev-a-panel-fab.zip`**,
  1.6 mm, ENIG, 2 layers. The single board is only 2.2 mm wide, below most
  fabs' minimum, so the panel holds six carriers, each joined to the frame
  by a 1.2 mm tab at both ends (routed slots round the rest). Snap or cut
  the tabs and file the stubs flush.
- Pins: Mill-Max 0906-2-15-20-75-14-11-0 (bulk) from Mill-Max, Digi-Key or
  Mouser; buy a few spares.

Assembly is in the case README ("Home build").
