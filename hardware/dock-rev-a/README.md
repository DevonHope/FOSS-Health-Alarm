# WakeBand dock rev A (concept)

A magnetic charging and programming dock for the band in `../case-rev-a`.

You lay the band face down in the dock's recess. Two magnets pull it in and
line it up, and six spring pins press on the band's six flush gold
contacts: VIN, GND, SWDCLK, SWDIO, UART_RX, UART_TX.

The magnets are keyed. The band only seats one way round: turned end for
end it is pushed away.

![dock](wakeband-dock-rev-a-preview-iso.png)
![recess](wakeband-dock-rev-a-preview-recess.png)

| Part | File |
| --- | --- |
| Dock body (recess, pin bores, magnet pockets, USB-C and header slots) | `wakeband-dock-rev-a-dock.step` / `.stl` |
| Base plate (glued in) | `wakeband-dock-rev-a-base.step` / `.stl` |
| Dock board, spring pins, USB-C, magnets (for fit checks only) | `wakeband-dock-rev-a-{board,spring-pins,usb-c,magnets}.step` |

- **Size:** 52.4 x 26.9 x 10.2 mm.
- **Recess:** 1.5 mm deep, the band's outer outline plus 0.3 mm.
- **Frames:** the STEP files are in the band's assembly frame, docked on the
  band. The STL files are turned for printing, base side down.
- **Regenerate:** `python dock_rev_a.py OUT_DIR` (needs build123d and
  `../case-rev-a`).

## Why this layout

- **Band side:** the six flush gold contacts are already the contact
  targets, so the band's board needs no change. Its two Ø3 x 1 mm N52
  magnets sit in the case top at each end of the contact row, under a
  0.2 mm skin.
- **Ready-made 6-pin magnetic connectors were checked and not used.**
  - Adafruit 5467 (2.2 mm pitch, US$7.95 a pair) would need the band's
    pads moved to 2.2 mm pitch, and Adafruit gives no height for it.
  - CCP P2526MR01-06F200HR (2.0 mm pitch) has no distributor and no
    readable drawing.
  - Mill-Max Maxnetic connectors are about 10.9 mm tall.
- **Antenna:** the band's nearest magnet is at x 118.6, 13.6 mm from the
  ISP2454 keep-out (x 100-105). There is no steel in the band.
- **LRA:** the case magnets are 6-7 mm from the LRA's own magnet and much
  smaller, so the pull is negligible.

## Parts

| Qty | Part | Where | Price (about) |
| --- | --- | --- | --- |
| 6 | Mill-Max 0965-0-15-20-80-14-11-0 spring pin, SMT, Ø1.07 mm plunger, 2.24 mm working height | Digi-Key ED1649-ND | CA$0.81 each at 10 |
| 2 | Ø3 x 1 mm N52 disc magnet, axially magnetized (poles on the flat faces) | K&J Magnetics, JC Magnetics, Magnet Baron (100-packs) | under CA$0.20 each |
| 1 | USB-C receptacle, 5 V power only (with 5.1 k CC pull-downs) | any USB-C power-only receptacle, about 8.9 x 7.4 x 3.3 mm | about CA$1 |
| 1 | 2.54 mm 1x6 header (or Tag-Connect / 1.27 mm 2x5 SWD) | any | - |
| 1 | dock board, 27 x 9.2 x 0.8 mm | JLCPCB | - |

The same two magnets also go in the band (see `../case-rev-a/README.md`).

**Spring-pin pads.** The 0965's base is Ø1.83 mm, so at 2.0 mm pitch the
bases sit only 0.17 mm apart. Use Ø1.5 mm pads with a thin paste stencil.
Or use any 2.0 mm pitch, 6-position SMT pogo strip of a similar working
height.

## Dock board (to draw)

- **Pin row:** six pads at 2.0 mm pitch. Seen from the band's outer face,
  they run left to right as the band's contacts do: UART_TX at x 121.75,
  UART_RX, SWDIO, SWDCLK, GND, VIN at x 131.75. The dock board faces the
  band, so on the board itself the order is mirrored.
- **USB-C:** VBUS to the VIN pin, through a 500 mA PTC fuse. GND to the GND
  pin.
- **Header:** VIN, GND, SWDCLK, SWDIO, UART_RX, UART_TX, for a debug probe
  or USB-serial adapter. Signal levels are the band's 1.8 V, so use a
  level-shifting probe (see the roadmap's dock notes).
- **GND first:** if GND should mate first, use a slightly longer spring pin
  in that position.

## Magnet polarity (keying)

| Magnet | Pole facing out of its part |
| --- | --- |
| Band, left (x 118.6, antenna end of the contact row) | N |
| Band, right (x 134.9, LRA end) | S |
| Dock, left (under the band's left magnet) | S, towards the band |
| Dock, right | N, towards the band |

- **Correct way round:** both pairs attract.
- **Turned end for end:** both pairs repel.
- **Checking:** mark each magnet's pole with a reference magnet before
  fitting.

## Assembly

1. Print the dock body with its recess up and the base plate flat.
   - The dock is not worn, so finish matters less.
   - The ceiling of the board cavity bridges about 9 mm. Print it slowly,
     or add supports inside the cavity only.
2. Glue the two magnets into their pockets from inside, with the poles as
   in the table, using a drop of CA glue.
3. Solder the spring pins, the USB-C and the header to the dock board.
   Fit the board in the cavity, pins up through the bores.
4. Check the pin tips stand about 0.3 mm proud of the recess floor. Then
   glue in the base plate.
