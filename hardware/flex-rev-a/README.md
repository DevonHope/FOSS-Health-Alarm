# WakeBand flex rev A (KiCad project)

Schematic for the first custom board: a 2-layer flex PCB that folds once around
a 12 x 30 mm, 110 mAh cell (pod about 22 x 36 x 8 mm). The design plan is in
[docs/flex-pcb-schematic-plan.md](../../docs/flex-pcb-schematic-plan.md) and the
module pinout and GPIO plan are in
[docs/flex-rev-a-pinout.md](../../docs/flex-rev-a-pinout.md).

Open `flex-rev-a.kicad_pro` in KiCad 10. All sheets and the symbol library are
saved in KiCad 10 format. `flex-rev-a.pdf` is a plot of the current sheets.

| Sheet | Status |
| --- | --- |
| `power` | nPM1304 (QFN32) drafted from Nordic's reference circuit "configuration 2": VBUS from dock VIN with TVS, cell pads through a cut-able current jumper, 10k NTC, BUCK1 1.8 V (VSET1 47k), BUCK2 and load switches unused, SHPHLD test pad + optional pull-up and button, PMIC_INT on GPIO3, I2C pull-ups. Open items are marked (check) on the sheet. |
| `mcu` | ISP2454-LX placed, all 48 signal pins wired to global labels or marked no-connect |
| `sensors`, `haptics`, `dock`, `debug` | Notes only (steps 5 and 6) |

Reference designators are numbered per sheet (power sheet = 2xx).

Project libraries: `wakeband.kicad_sym` (ISP2454-LX and nPM1304-QEAA symbols)
and `wakeband.pretty` (ISP2454 footprint with its antenna keep-out). Sheets
connect through global labels, so the top sheet has no wires.

## ERC status (KiCad 10.0.5, 2026-10-30)

`kicad-cli sch erc flex-rev-a.kicad_sch`: 2 errors, 10 warnings, none on the
power sheet. All are expected until the dock, sensors, haptics and debug sheets
are drawn:

- 9 warnings: global labels on the MCU sheet whose other ends are not drawn
  yet (nRESET, SWDIO, SWDCLK, UART_TX, UART_RX, ACC_INT1, HAPT_TRIG, LED_DBG,
  HAPT_EN).
- 2 errors: ISP2454 inputs nRESET and SWDCLK are not driven yet (dock sheet).
- 1 warning: the ISP2454 symbol's hidden VSS pins share the net with the GND
  label; GND is used in the netlist, so this is harmless.

PWR_FLAGs on the power sheet mark the off-board sources: dock VIN, the cell
(VBAT and GND), and PVSS1, which reaches GND only through the net tie.
