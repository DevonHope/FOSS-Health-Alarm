# Flex rev A: ISP2454 pinout and GPIO plan

Step 2 of the [schematic plan](flex-pcb-schematic-plan.md#plan-for-building-the-schematic).
Source: Insight SiP ISP2454 datasheet, revision R7 (10/09/2026),
https://www.insightsip.com/fichiers_insightsip/pdf/ble/ISP2454/isp_ble_DS2454.pdf (Insight SiP), mirror: https://www.mouser.lt/datasheet/3/1572/1/isp_ble_DS2454.pdf

## Module facts that shape the schematic

- Variant **ISP2454-LX**: 32 MHz and 32.768 kHz crystals, no extra flash.
  LL has no 32.768 kHz crystal; LP adds 4 MB flash but takes P2.00 to P2.05.
- Inside the module: antenna, both crystals, DC-DC inductor, RF match and all
  decoupling (11.2 uF in total). The datasheet says only a DC supply is needed.
- VDD_nRF (pin 26): 1.7 to 3.6 V. Rev A runs it from the nPM1304 BUCK1 at 1.8 V.
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
uses P2. The choices below copy pin mappings from Zephyr's board files for the
nRF54L15 DK and the XIAO nRF54L15, so they are known to work.

| Net | Pin | Port | Peripheral | Why |
| --- | --- | --- | --- | --- |
| I2C_SDA | 33 | P0.04 | TWIM30 | Low-power domain, so the bus runs while most of the chip sleeps. Same pins as the XIAO nRF54L15's IMU bus. |
| I2C_SCL | 34 | P0.03 | TWIM30 | as above |
| ACC_INT1 | 32 | P0.02 | GPIO, wake | Accelerometer FIFO/wake interrupt, on P0 for the lowest-power wake |
| ACC_INT2 | 27 | P0.01 | GPIO | Spare accelerometer interrupt |
| PMIC_INT | 29 | P0.00 | GPIO, wake | nPM1304 interrupt: VBUS present, charger events |
| UART_TX | 40 | P1.04 | UARTE20 | Same as the nRF54L15 DK console |
| UART_RX | 38 | P1.05 | UARTE20 | Same as the nRF54L15 DK console |
| HAPT_TRIG | 10 | P1.10 | PWM20 OUT0 | DRV2605L IN/TRIG; P1.10 is the DK's PWM20 pin, so the PWM input mode also works |
| HAPT_EN | 19 | P1.08 | GPIO | DRV2605L EN |
| LED_DBG | 17 | P1.15 | GPIO | Debug LED (DNP option) |
| SWDIO | 28 | - | SWD | Dock pad 4 |
| SWDCLK | 30 | - | SWD | Dock pad 3 |
| nRESET | 13 | - | reset | Test pad only |

Left unused (no-connect for now, test pads later where there is room):
P1.02/P1.03 (NFC pins, need a register change to act as GPIO), P1.06, P1.07,
P1.09, P1.11 to P1.14, and all of P2 (trace port and high-speed pins).

Analog pins still free for later: AIN2 to AIN7 (P1.06, P1.07, P1.11 to P1.14).

## Footprint blocker

The footprint (`wakeband:InsightSiP_ISP2454_LGA-62_8x8mm`) is not drawn yet.
The pad sizes, pad positions, pin 1 corner and which pads sit on the inner row
are only in the drawing in datasheet section 4.1, which is an image. The text
says the land pattern should match the module pads, and gives this via advice:

- Standard PCB: 0.4 mm catch pads, 0.2 mm vias, plugged and capped.
- HDI: 0.25 mm catch pads, 0.1 mm copper-filled laser vias.
- If most inner pads are used, put capped vias in the pad centres.
- With a reduced pinout, use outer pads where possible; inner pads can use
  normal vias under the middle of the module, with mask openings only on the
  pads in use.

The last point matters for flex: if every pin in the table above sits on the
outer row, no via-in-pad is needed. The table will be checked against the
drawing once it is readable.
