# Flex rev A: ISP2454 pinout and GPIO plan

Step 2 of the [schematic plan](flex-pcb-schematic-plan.md#plan-for-building-the-schematic).
Source: Insight SiP ISP2454 datasheet, revision R7 (10/09/2026),
https://www.insightsip.com/fichiers_insightsip/pdf/ble/ISP2454/isp_ble_DS2454.pdf (Insight SiP), mirror: https://www.mouser.lt/datasheet/3/1572/1/isp_ble_DS2454.pdf

## Module facts that shape the schematic

- Variant **ISP2454-LX**: 32 MHz and 32.768 kHz crystals, no extra flash.
  LL has no 32.768 kHz crystal; LP adds 4 MB flash but takes P2.00 to P2.05.
- Inside the module: antenna, both crystals, DC-DC inductor, RF match and all
  decoupling (11.2 uF in total). The datasheet says only a DC supply is needed.
- VDD_nRF (pin 26): 1.7 to 3.6 V. Rev A runs it from the nPM1304 BUCK1 at 2.0 V (raised from 1.8 V for margin over the 1.7 V minimum).
- Pin 20 OUT_ANT must be joined to pin 22 OUT_MOD on the board (net `ANT_LINK`).
- Pins 49 to 62 are mechanical pads: isolated copper, no net.
- 12 ground pads: 1, 7, 8, 12, 14, 16, 18, 21, 23, 24, 25, 31.
- Firmware: set the 32.768 kHz crystal load to 19 pF in the devicetree
  (`load-capacitors = "internal"; load-capacitance-femtofarad = <19000>;`).
- Antenna: module 1 mm from the board edge, nothing on any layer in the
  keep-out except the mechanical pads; a corner placement allows a smaller
  keep-out (figure in section 4.3).
- Reflow peak 260 C. The datasheet lists both MSL 2 and MSL 3; treat it as MSL 3
  (bake if the bag has been open).
- Datasheet RF exposure note: 10 mm minimum from the body. Still an open
  question for Insight SiP.

## GPIO plan

nRF54L15 peripherals are tied to port groups: instances 30 (TWIM30, UARTE30)
use port P0 in the low-power domain, instances 20 to 22 use P1, and instance 00
uses P2. The UART and PWM pins copy Zephyr's board files for the nRF54L15 DK;
the I2C clock pin copies the XIAO nRF54L15.

**Every signal sits on an outer-row pad**, so the flex board needs no
via-in-pad under the module (see the footprint section). That costs one choice:
P0.00, P0.01 and P0.04 are inner-row pads, so the accelerometer and PMIC
interrupts move from P0 to P1.

| Net | Pin | Port | Row | Peripheral | Why |
| --- | --- | --- | --- | --- | --- |
| I2C_SDA | 32 | P0.02 | outer | TWIM30 | Low-power domain, so the bus runs while most of the chip sleeps **(check that TWIM30 SDA may use P0.02)** |
| I2C_SCL | 34 | P0.03 | outer | TWIM30 | Same SCL pin as the XIAO nRF54L15's IMU bus |
| ACC_INT1 | 36 | P1.07 | outer | GPIO, wake | Accelerometer FIFO/wake interrupt **(check GPIOTE20 port-event sleep current)** |
| PMIC_INT | 48 | P1.11 | outer | GPIO, wake | nPM1304 interrupt: VBUS present, charger events |
| UART_TX | 40 | P1.04 | outer | UARTE20 | Same as the nRF54L15 DK console |
| UART_RX | 38 | P1.05 | outer | UARTE20 | Same as the nRF54L15 DK console |
| HAPT_EN | 42 | P2.05 | outer | GPIO | DRV2605L EN (static output) |
| LED_DBG | 44 | P2.04 | outer | GPIO | Debug LED (DNP option) |
| SWDIO | 28 | - | outer | SWD | Dock pad 4 |
| SWDCLK | 30 | - | outer | SWD | Dock pad 3 |
| VDD_2V0 | 26 | - | outer | supply | BUCK1 2.0 V |
| ANT_LINK | 20, 22 | - | outer | RF | Short trace joining OUT_ANT and OUT_MOD |
| nRESET | 13 | - | inner | reset | Optional test pad through a tented via under the module; SWD can reset the chip without it |
| GND | 1, 7, 8, 12, 14, 16, 18, 24, 25, 31 outer; 21, 23 inner | - | | | Inner GND pads may use tented vias under the module, or be left as isolated pads |

The accelerometer's second interrupt (INT2) goes to a test pad only.

**Lower outer row (pads 8 to 24).** These sit on the module mid-line with the
antenna keep-out directly below, and the 0.25 mm gaps between inner pads are
too narrow for a trace. So they cannot be routed without via-in-pad. Pad 10
(P1.10) is therefore unused: the DRV2605L's IN/TRIG is tied to GND and effects
are started over I2C. Only ANT_LINK (20 to 22, a short trace along the row) and
GND pads 8 and 24 (short traces to the large pads 7 and 25) use this row.
GND pads 12 to 18 stay unconnected on the board, pending Insight SiP's OK.

Left unused: P1.10 (pad 10, trapped, see above), P1.02/P1.03 (NFC pins, outer, need a register change to act as
GPIO), P2.01 and P2.02 (outer, spare), and every inner-row GPIO (P0.00, P0.01,
P0.04, P1.06, P1.08, P1.09, P1.12 to P1.15, P2.00, P2.03, P2.06 to P2.10).

## Footprint

`hardware/flex-rev-a/wakeband.pretty/InsightSiP_ISP2454_LGA-62_8x8mm.kicad_mod`,
built from the datasheet's section 4.1 drawing (read from the user's local
copy of rev R7; the PDF is marked confidential, so it is not in this repo).
Origin is the module centre; pin 1 is top-left; the antenna half (pins 49 to
62) is the bottom 4 mm.

| Pad type | Size (mm) | Pins |
| --- | --- | --- |
| A, corner | 0.75 x 0.75 | 1, 31, 52, 59 |
| B, side | 0.75 x 0.80 | 7, 25 |
| c, outer row | 0.40 x 0.35 | top row 32 to 48 (even), lower row 8 to 24 (even), 53 to 58 |
| d, inner row | 0.40 x 0.40 | 3, 5, 9 to 23 (odd), 27, 29, 33 to 47 (odd) |
| e, side columns | 0.35 x 0.40 | 2, 4, 6, 26, 28, 30, 49 to 51, 60 to 62 |

Pad centres (from the module's top-left corner, mm):

| Pins | X | Y |
| --- | --- | --- |
| 48, 46 ... 32 (top outer, left to right) | 1.40 + 0.65 k | 0.30 |
| 47, 45 ... 33 (top inner) | 1.725 + 0.65 k | 0.95 |
| 2, 4, 6 / 30, 28, 26 (outer side columns) | 0.30 / 7.70 | 1.40, 2.05, 2.70 |
| 3, 5 / 29, 27 (inner side columns) | 0.95 / 7.05 | 1.725, 2.375 |
| 7 / 25 | 0.525 / 7.475 | 3.60 |
| 9, 11 ... 23 (lower inner) | 1.725 + 0.65 k | 3.15 |
| 8, 10 ... 24 (lower outer) | 1.40 + 0.65 k | 3.80 |
| 49, 50, 51 / 62, 61, 60 | 0.30 / 7.70 | 4.55, 5.55, 6.55 |
| 1, 31, 52, 59 (corners) | 0.525 / 7.475 | 0.525 / 7.475 |
| 53 ... 58 (bottom, pitch 1.0) | 1.475 ... 6.475 | 7.68 |

Printed on the drawing: the 0.65 pitch, the pad sizes, X 6.6 / 6.475 / 6.275 /
7.05, and Y 0.525 / 2.375 / 2.7 / 3.6 / 3.8 / 6.55 / 7.475. **Derived, not
printed:** the outer rows and columns at 0.30 mm from the edge (from the 0.65
pitch and symmetry) and the bottom row at Y 7.68 (measured). The bottom row may
be centred at 1.5 to 6.5 instead of 1.475 to 6.475 (0.025 mm at most). Check
these against Insight SiP's own CAD files before ordering boards. The closest
pad-to-pad gap is 0.25 mm, inside JLCPCB's flex limits.

Land pattern rules from section 4.2: pads and mask openings the same size as
the module pads (the footprint uses 0 mask margin); outer pads only where
possible; a few inner pads may use normal vias under the middle of the module,
tented, with mask openings only on the pads in use.

The footprint includes a keep-out rule area on both copper layers for the
antenna: from the module's mid-line down to the board edge 1 mm below the
module, and 5 mm past each side (the large-board default). On the band's
18 mm-wide island the module is centred, so 5 + 8 + 5 = 18 mm fills the width.
Section 4.3 also allows 1 mm side clearance for a corner placement.
