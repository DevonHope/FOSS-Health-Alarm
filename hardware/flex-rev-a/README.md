# WakeBand flex rev A (KiCad project)

Schematic for the first custom board: a 2-layer flex PCB that folds once around
a 12 x 30 mm, 110 mAh cell (pod about 22 x 36 x 8 mm). The design plan is in
[docs/flex-pcb-schematic-plan.md](../../docs/flex-pcb-schematic-plan.md) and the
module pinout and GPIO plan are in
[docs/flex-rev-a-pinout.md](../../docs/flex-rev-a-pinout.md).

Open `flex-rev-a.kicad_pro` in KiCad. The files were written in KiCad 7 format
(the newest the build machine had); KiCad 10 opens them and offers to upgrade
the format on save. `flex-rev-a.pdf` is a plot of the current sheets.

| Sheet | Status |
| --- | --- |
| `mcu` | ISP2454-LX placed, all 48 signal pins wired to global labels or marked no-connect |
| `power` | Notes only; three temporary PWR_FLAGs stand in for the nPM1304 until step 3 |
| `sensors`, `haptics`, `dock`, `debug` | Notes only (steps 5 and 6) |

Project libraries: `wakeband.kicad_sym` (ISP2454-LX symbol) and
`wakeband.pretty` (ISP2454 footprint with its antenna keep-out). Sheets connect through global
labels, so the top sheet has no wires.

Not run yet: a full ERC (the build machine's KiCad 7 CLI has no ERC command).
Run Inspect > Electrical Rules Checker in KiCad 10 after opening. Expected
warnings for now: global labels that only appear on the MCU sheet, because
their other ends are not drawn yet.
