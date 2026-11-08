# WakeBand dock PCB rev B

The board inside the charging dock: USB-C in, an RP2040 running Raspberry Pi's `debugprobe` firmware
(a USB CMSIS-DAP probe, so the computer can flash the band and read its log over SEGGER RTT), and a
current-limited 5 V feed to the band's VIN pin. Four Mill-Max spring pins on top touch the band's four
contacts (VIN, GND, SWDCLK, SWDIO).

For the rev B dock housing ([`../case`](../case)). It started as dock PCB rev A
([`../../rev-a/pcb`](../../rev-a/pcb), now superseded) with the stocked spring pins
(Mill-Max **0906-4-15-20-75-14-11-0**); the 2026-11-08 review then changed both circuit and layout:
ESD/TVS on the four pins, a SWCLK pull-down, the band current limit down to 0.21 A, the RP2040
decoupling at its supply pins, the flash turned, no open vias under paste, and a silkscreen legend (see
"Review fixes" below). Order this one with the rev B dock.

| File | What |
| --- | --- |
| `dock-pcb-rev-b.kicad_pro` / `.kicad_sch` / `.kicad_pcb` | KiCad 10 project |
| `dock-pcb-rev-b-schematic.pdf`, `dock-pcb-rev-b-layout.pdf` | PDFs |
| `fab/dock-pcb-rev-b-fab.zip` | JLCPCB order files (Gerbers, drill, BOM, CPL) |
| `dock.pretty`, `dock.kicad_sym`, `dock.3dshapes` | project footprints, symbols and 3D models |
| `scripts/` | `parts.py` (netlist and BOM source), `gen_sch.py`, `gen_pcb.py`, `placement.json`, `gen_cpl.py` (JLC placement file) |

**USB-C 3D model (2026-11-08):** J1 (HRO TYPE-C-31-M-12, LCSC C165948) uses the LCSC/EasyEDA STEP
(`dock.3dshapes/HRO_TYPE-C-31-M-12_C165948.step`) on a project copy of KiCad's footprint
(`dock.pretty`), offset 1.6 mm so the shell's front face sits on the board edge (y 124.0) and the leads
over the pad row; KiCad's own library has no model for this part.


**Placement file (`fab/cpl_jlcpcb.csv`):** written by `scripts/gen_cpl.py` (run from this folder) with
JLCPCB's rotation conventions (SOT-23 +180, SOIC +270, QFN +270) and a per-part offset for J1: JLC's
EasyEDA footprint for the HRO USB-C has its origin 1.42 mm behind KiCad's, so J1's point is moved
1.42 mm back (to y 118.88) or its legs miss their holes in JLC's preview. In the preview, also check the
cathode mark of D1/D2. The spring pins (P1-P4) and test pads are left out: they are hand-soldered.

## Board

4-layer 1.6 mm, 40 x 26.5 mm, all parts on the top side for JLCPCB
assembly; the four spring pins are hand-soldered.

| Block | Parts (LCSC) | Notes |
| --- | --- | --- |
| USB-C | HRO TYPE-C-31-M-12 (C165948), 2 x 5.1 k CC pull-downs (C25905), USBLC6-2SC6 (C7519), 2 x 27 R (C25100) | USB 2.0 device, 5 V sink |
| Input | 500 mA PTC FSMD050-0805 (C181350), 10 uF (C19702) | |
| Probe | RP2040 (C2040), W25Q16JVSNIQ 2 MB flash (C2456211), 12 MHz crystal (C2981639) + 2 x 15 pF, BOOTSEL TS-1088 (C720477) | Raspberry Pi Debug Probe pin map: SWCLK GPIO12, SWDI GPIO13, SWDIO GPIO14, LEDs GPIO2 (USB) and GPIO16 (DAP running) |
| Rails | XC6206P332MR 3.3 V (C2897477), XC6206P182MR 1.8 V (C21659) | |
| SWD level shift | 74LVC1T45 (C168856) for SWCLK, TXS0101 (C132604) for SWDIO, 22 R on the SWDIO drive (C25092), 100 k pull-down on the 74LVC1T45 input (R15, 0201, C106224) | band side at 1.8 V, so 3.3 V never reaches the band; R15 holds SWCLK low when debugprobe releases GPIO12 after a session |
| Band power | SY6280AAC (C55136), Rset 33 k (C25779) | current-limited switch: 6800 / 33 k = 0.21 A (0.16-0.26 A at the part's +-25 %); the band draws at most 0.1 A |
| Pins | 4 x Mill-Max 0906-4-15-20-75-14-11-0 (stocked; was -72, special order) | hand-soldered; the GND pin (P3) has a thermal relief so it solders by hand |
| Pin protection | USBLC6-2SC6 (U9, C7519) on SWCLK/SWDIO, SMF6.0A TVS (D3, C123790) on VIN, 100 R in series with both SWD pins (R11, R12, C25076) | the pins are bare contacts people touch; U9's clamp rail is VIN, so a coin across VIN and an SWD pin draws nothing through it, and 100 R limits what reaches the translators |

**Why these translators.** The stock firmware has no direction pin for
SWDIO (GPIO14 drives, GPIO13 reads the same line), so SWDIO needs an
auto-direction part: the TXS0101. SWCLK only goes out, and the nRF54L15
pulls it down internally, which would fight a TXS's weak pull-up, so it gets
a fixed-direction 74LVC1T45.

**Checks:** ERC 0; DRC with schematic parity 0 violations, 0 unconnected,
0 parity. The schematic and board are generated from `scripts/`
(`parts.py` is the netlist and BOM source; `gen_sch.py`, `gen_pcb.py`,
`placement.json`), then routed with a grid router plus a hand-laid QSPI
fan-out, and ground-stitched to the solid In1 plane.

**Trace audit (2026-11-07, same checks as the band board):** every segment
at 0, 45 or 90 degrees, every bend 45 degrees, no stair-steps (no short segment
between two bends; short pad-entry stubs from a bend into a pad centre are allowed), no overlapping same-net tracks, every track end
on its pad or via centre, no dangling ends. The router's leftovers were
re-laid by hand (QSPI fan-out, the RP2040 inner +1V1/+3V3 links, SWD and
power stubs; C3, C6, C10, C19, R4, R10, R11 and R13 nudged so their pad
centres line up with 45-degree runs). DRC with parity 0 / 0 / 0, with
`track_not_centered_on_via` as an error; ERC 0. Segments 390, vias 90.

**Review fixes (2026-11-08).** `scripts/dogbone_vias.py` moved 27 vias out of SMD pads;
`scripts/review_fixes.py` (run after it) does the rest of the layout side, and `parts.py` /
`gen_sch.py` the schematic side:

- No open via sits under paste any more. U3 pin 5's VBUS via moved between U3's pin columns (its
  GND via moved west), and the RP2040 thermal pad's four paste squares became 16 windows that keep
  0.1 mm off each via drill (0.2 mm stencil webs, no islands, 57 % paste coverage). So no filled or
  capped vias are needed.
- ESD/TVS on the pins (U9, D3, R11/R12 at 100 R), SWCLK pull-down (R15), band current limit 0.21 A (R6
  33 k): see the table above.
- SWDIO_DRV no longer runs between the crystal's pads: it drops to B.Cu at RP2040 pin 17. XOUT still
  runs on In2 (9.2 mm, two vias) under the solid In1 ground. A top-layer XOUT does not fit: the 3225
  crystal's XIN/XOUT pads are diagonal, so with the RP2040's pin order every rotation either crosses
  XIN and XOUT or sends XIN about 10 mm round the crystal; the one clean option (crystal turned 180
  degrees, XIN up the channel between its pads) puts R1 on top of pin 23's +1V1 stub and C16, and R1
  does not fit under the board-edge clearance. It would take a 2520 crystal and re-routing pins 23-26.
- VBUS_F's 21 mm inner-layer run is 0.45 mm wide (was 0.3).
- Silkscreen: pin-1 dots, LED and TVS cathode bars, P1-P4 labels and "WakeBand dock rev B" (the board
  had no legend).
- RP2040 decoupling (`scripts/relayout.py`, run after `review_fixes.py`): the flash (U2) is turned 180
  degrees and moved right, which frees the space under the RP2040's bottom-edge supply pins. C15
  (VREG_VOUT 1 uF) now sits at pin 45 (1.3 mm of track), with new 100 nF caps at pin 43 (ADC_AVDD, C22,
  0402), pins 48/49 (USB_VDD/IOVDD, C23, 0201) and pin 50 (DVDD, C24, 0201). R4/R5 (USB 27 R) sit under
  them, C12 takes C15's old place, and R8/R9/C17 follow the flash. QSPI is now 4-16 mm per line (was up
  to 27 mm; 56 mm in total, was 74), with no line between the two rows of flash pins. BOOT runs on In2
  to SW1, and LED_USB's In2 run goes round the flash.

`fab/bom_jlcpcb.csv` is written by `scripts/gen_bom.py` from `parts.py`.

**Cost (rough, JLCPCB, 5 boards):** board about US$10 for a small 4-layer
order; parts about US$4 a board (RP2040 0.90, flash 1.00, crystal 0.09, the
rest cents each) plus about US$3 setup per extended part type (about 15);
spring pins a few US$ each from distributors (4 a dock).

**Fab:** `fab/dock-pcb-rev-b-fab.zip` (Gerbers, drill, `bom_jlcpcb.csv`,
`cpl_jlcpcb.csv`). The CPL leaves out the spring pins and test pads. Check
the RP2040, SOT-23 parts and USB-C rotations in the JLCPCB preview.

## Power notes

- USB 5 V goes through the PTC to the SY6280 switch and out to the band's
  VIN pin; the band's nPM1304 does the charging (firmware sets the charge
  current, see the board README).
- If the band's pins short, the switch limits at about 0.21 A. The PTC (1 A trip) will not trip at
  that current; the switch's own thermal shutdown is the backstop.
- The probe side draws about 30-40 mA from USB.
- The band's SWD lines see 1.8 V from the dock. The band's I/O runs at
  2.0 V, which reads 1.8 V as high, and the TXS0101 accepts the band's 2.0 V.

## Flashing the dock (once)

1. Download `debugprobe.uf2` from the latest release of
   https://github.com/raspberrypi/debugprobe (the build for the Raspberry Pi
   Debug Probe; this board copies its pin map, so no rebuild is needed).
2. Plug in USB-C. A blank RP2040 (no firmware in the flash yet) comes up as a drive called `RPI-RP2`
   on its own. To get back to the bootloader later, run `picotool reboot -u -f`, or take the top plate
   off and hold **BOOTSEL** (SW1) while plugging in: the rev B case has no poke hole.
3. Copy `debugprobe.uf2` onto it. The dock restarts as "Debug Probe
   (CMSIS-DAP)", and the USB LED (D1) lights.
4. **Recovery:** if the RP2040 won't show the drive, the pads on the
   underside of the dock PCB (TP1 SWCLK, TP2 SWDIO, TP3 RUN, TP4 GND) give
   direct SWD access to the RP2040.

## Programming the band

Put the band in the dock, then use any CMSIS-DAP tool. Check these on the
nRF54L15 DK first; nRF54L15 support is recent in each tool:

- **probe-rs:** `probe-rs download --chip nRF54L15 --binary-format hex app.hex`
  (or give it the `.elf`), then `probe-rs reset --chip nRF54L15`.
- **Logs over RTT:** `probe-rs attach --chip nRF54L15 app.elf` prints the
  RTT channels; with Zephyr, enable `CONFIG_USE_SEGGER_RTT` and the RTT log
  backend.
- **Zephyr:** `west flash --runner pyocd` (or the probe-rs runner if your
  Zephyr version has it).
- **pyOCD:** `pyocd flash -t nrf54l15 app.hex` once the nRF54L target
  support is installed.
- **Locked part:** if the nRF54L15's access port protection is on, erase it
  with the tool's recover / erase-all command before flashing.

There is no reset pin on the dock; the tools reset the chip over SWD.
