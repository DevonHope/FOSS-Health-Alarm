# Buy list: dock contacts and contact carrier

Quantities are for **5 bands and 1 dock**, with spares. Prices are Mouser Canada (CAD), read on
2026-11-08. Recheck stock and prices before ordering.

## Spring pins

| What | Part | Where | Per | Buy | Price (CAD) |
| --- | --- | --- | --- | --- | --- |
| Band contacts (soldered to the carrier) | Mill-Max **0906-2-15-20-75-14-11-0** | Mouser 575-906215 (109k in stock) | 4 a band | 25 (20 + 5 spares) | 1.27 each, 1.08 each at 10+, so about 27 |
| Dock contacts (soldered to the dock PCB) | Mill-Max **0906-4-15-20-75-14-11-0** | Mouser 575-906415 (82k in stock) | 4 a dock | 6 (4 + 2 spares) | 1.32 each, so about 8 |

**Dock pin change:** the dock was drawn with the low-force spring version (0906-4-15-20-**72**-14-11-0).
Mouser lists it only as a factory special order with no stock or price, so buy the stocked **-75**
version. It is the same size and fits the same holes. Its spring is a little stronger at mid-stroke:
60 g instead of 45 g a pin, so 240 g instead of 180 g for all four pins pushing the band up against the
magnets. The rev B dock gets bigger magnets to hold against that (see below).

## Contact carrier PCB

| What | File | Options | Buy |
| --- | --- | --- | --- |
| Carrier panel, 6 carriers on a 48.2 x 29.1 mm panel | `fab/contact-carrier-rev-a-panel-fab.zip` | 2 layers, **1.6 mm**, any colour, lead-free HASL or ENIG | 5 panels (JLCPCB's minimum) = 30 carriers |

- One panel is enough for 6 bands. JLCPCB's minimum order is 5 panels anyway.
- Cost: about US$2-5 for 5 panels with lead-free HASL, about US$15-25 with ENIG, plus shipping.
  HASL is fine here: the carrier pads are only soldered to, nothing presses on them. If you order it
  together with the band boards, shipping is shared.
- No assembly needed. You solder the pins by hand (case README, "Home build").

## Also needed to fit the contacts

| What | Per band | Per dock | Notes |
| --- | --- | --- | --- |
| N52 disc magnet Ø3 x 1 mm | 2 | — | dropped into the band's wrist cover during the print |
| N52 disc magnet for the dock | — | 2 | see the dock README for the size (Ø4 x 1.5 mm on the rev B dock) |
| Gel epoxy (5-minute or 30-minute) | a drop | — | seals the carrier and its joints inside the wrist cover |
| Kapton tape, 10-13 mm wide | a strip | — | over B.Cu under the cell, landing pads left clear |

Mark the magnet poles with a spare magnet before fitting: the band and dock each have one N-up and one
S-up magnet so the band only seats one way round.

The case screw (M2 x 6 countersunk) and M2 heat-set insert are listed in the case README.
