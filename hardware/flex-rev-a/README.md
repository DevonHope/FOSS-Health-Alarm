# WakeBand flex rev A (KiCad project)

Schematic for the first custom board: a 2-layer flex PCB that folds once around
a 12 x 30 mm, 110 mAh cell (pod about 22 x 36 x 8 mm). The design plan is in
[docs/flex-pcb-schematic-plan.md](../../docs/flex-pcb-schematic-plan.md) and the
module pinout and GPIO plan are in
[docs/flex-rev-a-pinout.md](../../docs/flex-rev-a-pinout.md).

Open `flex-rev-a.kicad_pro` in KiCad 10. All sheets, the symbol library and the
footprint library are saved in KiCad 10 format. `flex-rev-a.pdf` is a plot of
the current sheets and `bom.csv` is the bill of materials.

| Sheet | Status |
| --- | --- |
| `power` | nPM1304 (QFN32) from Nordic's reference circuit "configuration 2": VBUS from dock VIN, cell pads through a cut-able current jumper, 10k NTC, BUCK1 2.0 V on VDD_2V0 (VSET1 68k), BUCK2 and load switches unused, SHPHLD on the internal 50k pull-up with a test pad (extra pull-up and button DNP), PMIC_INT on GPIO3, the bus's 4.7k I2C pull-ups. |
| `mcu` | ISP2454-LX placed, all 48 signal pins wired to global labels or marked no-connect. Pad 10 (P1.10) is no-connect (lower outer row, not routable without via-in-pad). GND pads 12, 14, 16, 18 stay unconnected on the board pending Insight SiP's OK (noted on the sheet). |
| `sensors` | LIS2DW12 on VDD_2V0 with 100 nF on each supply pin plus 10 uF bulk, I2C address 0x19 (CS and SA0 strapped high), INT1 to ACC_INT1, INT2 to a test pad. |
| `haptics` | DRV2605L on VSYS with 1 uF on VDD and REG, EN from the SoC, IN/TRIG tied to GND (effects triggered over I2C), OUT+/OUT- to two LRA lead pads. Footprint TSSOP-10_3x3mm (KiCad's land pattern for TI's DGS package). |
| `dock` | Six pogo pads (2 mm pitch, 1.2 x 3.0 mm), SMF18A TVS (18 V standoff) on VIN and TPD1E10B06 on each data pad, 100 ohm series on the four data lines, 100k pull-down on UART_RX. |
| `debug` | 0.8 mm test pads on nRESET, I2C, VDD_2V0, VSYS, VBAT, GND; DNP debug LED on LED_DBG. |

Every sheet lists its open items as **(check)** in a note. The main ones:
the nPM1304 exposed-pad size against Nordic's reference layout, TVS leakage
at 2.0 V on the data pads (TPD1E0B04 is a lower-leakage alternative), the
SMF18A's surge clamp (29.2 V) against VBUS's 22 V rating, the LIS2DW12 land
pattern, the inductor land pattern, and the GPIO used for PMIC_INT.

Reference designators are numbered per sheet (power 2xx, sensors 4xx,
haptics 5xx, dock 6xx, debug 7xx; the module is U1).

Project libraries: `wakeband.kicad_sym` (ISP2454-LX, nPM1304-QEAA and
LIS2DW12 symbols) and `wakeband.pretty` (ISP2454 footprint with its antenna
keep-out, 6-pad dock strip, 0.8 mm test pad, LRA lead pad). Sheets connect
through global labels, so the top sheet has no wires.

## BOM

`bom.csv` uses JLCPCB's column names (Comment, Designator, Footprint, LCSC)
plus MPN, Qty and DNP. Test pads, dock pads, LRA pads, the solder jumper and the
net tie are excluded (copper only). Delete the DNP rows before uploading for
assembly. LCSC numbers were checked on lcsc.com on 2026-10-30. Two parts have
none: the ISP2454-LX module and the nPM1304-QEAA (LCSC only lists the
nPM1304-EK), so they need another source or consignment.

## Review fixes (2026-10-30)

- BUCK1 raised from 1.8 V to 2.0 V (R202 47k -> 68k); the global net is now
  VDD_2V0 on every sheet. At -5 % the rail is 1.9 V, well above the
  ISP2454's 1.7 V minimum.
- DRV2605L IN/TRIG tied to GND and ISP2454 pad 10 left unconnected.
- VIN TVS changed to Littelfuse SMF18A (LCSC C409420) so a wrong 9-12 V
  supply does not destroy it.
- 10 uF bulk cap added at the LIS2DW12 VDD pin (C403).
- MCU sheet uses the GND power symbol instead of a GND global label.

## ERC status (KiCad 10.0.5, 2026-10-30)

`kicad-cli sch erc flex-rev-a.kicad_sch`: **0 errors, 0 warnings.**

- nRESET has only a test pad (the nRF54L15 has an internal pull-up). The
  passive test pad satisfies KiCad's "input not driven" check, so no
  exclusion is needed.
- The ISP2454 symbol's ground pins were renamed from VSS to GND so they no
  longer clash with the GND label (same pin numbers and connections).
- PWR_FLAGs mark the off-board sources: dock VIN (dock sheet), the cell
  (VBAT and GND, power sheet), and PVSS1, which reaches GND only through the
  net tie.
