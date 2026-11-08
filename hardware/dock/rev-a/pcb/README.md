# WakeBand dock PCB rev A

The board inside the charging dock: USB-C in, an RP2040 running Raspberry Pi's `debugprobe` firmware
(a USB CMSIS-DAP probe, so the computer can flash the band and read its log over SEGGER RTT), and a
current-limited 5 V feed to the band's VIN pin. Four Mill-Max spring pins on top touch the band's four
contacts (VIN, GND, SWDCLK, SWDIO).

For the rev A dock housing ([`../case`](../case)). The rev B dock has its own copy of this circuit in
[`../../rev-b/pcb`](../../rev-b/pcb); order that one for new builds.

| File | What |
| --- | --- |
| `dock-pcb-rev-a.kicad_pro` / `.kicad_sch` / `.kicad_pcb` | KiCad 10 project |
| `dock-pcb-rev-a-schematic.pdf`, `dock-pcb-rev-a-layout.pdf` | PDFs |
| `fab/dock-pcb-rev-a-fab.zip` | JLCPCB order files (Gerbers, drill, BOM, CPL) |
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
| SWD level shift | 74LVC1T45 (C168856) for SWCLK, TXS0101 (C132604) for SWDIO, 22 R series | band side at 1.8 V, so 3.3 V never reaches the band |
| Band power | SY6280AAC (C55136), Rset 15 k (C25756) | current-limited switch, about 0.45 A (the part's minimum is 0.4 A), behind the PTC |
| Pins | 4 x Mill-Max 0906-4-15-20-75-14-11-0 (stocked; was -72, special order) | hand-soldered; the GND pin (P3) has a thermal relief so it solders by hand |

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
at 0, 45 or 90 degrees, every bend 45 degrees, no stair-steps (no segment
under 0.3 mm between bends), no overlapping same-net tracks, every track end
on its pad or via centre, no dangling ends. The router's leftovers were
re-laid by hand (QSPI fan-out, the RP2040 inner +1V1/+3V3 links, SWD and
power stubs; C3, C6, C10, C19, R4, R10, R11 and R13 nudged so their pad
centres line up with 45-degree runs). DRC with parity 0 / 0 / 0, with
`track_not_centered_on_via` as an error; ERC 0. Segments 352, vias 88.

**Cost (rough, JLCPCB, 5 boards):** board about US$10 for a small 4-layer
order; parts about US$4 a board (RP2040 0.90, flash 1.00, crystal 0.09, the
rest cents each) plus about US$3 setup per extended part type (about 12);
spring pins a few US$ each from distributors (4 a dock).

**Fab:** `fab/dock-pcb-rev-a-fab.zip` (Gerbers, drill, `bom_jlcpcb.csv`,
`cpl_jlcpcb.csv`). The CPL leaves out the spring pins and test pads. Check
the RP2040, SOT-23 parts and USB-C rotations in the JLCPCB preview.

## Power notes

- USB 5 V goes through the PTC to the SY6280 switch and out to the band's
  VIN pin; the band's nPM1304 does the charging (firmware sets the charge
  current, see the board README).
- If the band's pins short, the switch limits at about 0.45 A and the PTC
  backs it up.
- The probe side draws about 30-40 mA from USB.
- The band's SWD lines see 1.8 V from the dock. The band's I/O runs at
  2.0 V, which reads 1.8 V as high, and the TXS0101 accepts the band's 2.0 V.

## Flashing the dock (once)

1. Download `debugprobe.uf2` from the latest release of
   https://github.com/raspberrypi/debugprobe (the build for the Raspberry Pi
   Debug Probe; this board copies its pin map, so no rebuild is needed).
2. Hold **BOOTSEL** (a pin through the poke hole) and plug in USB-C. The
   dock appears as a drive called `RPI-RP2`.
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
