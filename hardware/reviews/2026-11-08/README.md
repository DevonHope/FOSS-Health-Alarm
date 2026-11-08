# PCB review, 2026-11-08 (two advisors per board)

Every PCB in `hardware/` was reviewed by two independent advisors: one electrical (schematic, parts, power,
protection) and one layout/manufacturing/fit (copper geometry, JLCPCB rules, fab files, case fit). They did not see
each other's work. KiCad 10.0.3 DRC/ERC was also run on every board as a cross-check, and the Major findings below
were spot-checked again by hand. Nothing in the designs was changed by this review.

Reviewed at commit `25262a1` (branch `claude/project-thread-vvhma7`). The eight advisor reports are in
[`advisors/`](advisors).

| Board | Files | KiCad 10 ERC / DRC | Blockers | Major (after merging) | Advisor findings (raw) |
| --- | --- | --- | --- | --- | --- |
| Band rev B (the one to build) | `band/rev-b/pcb` | 0 / 0, parity 0 | 0 | 3 | 4 Major, 12 Minor, 10 Notes |
| Dock PCB (rev A = rev B copper) | `dock/rev-b/pcb` | 0 / 0, parity 0 | 0 | 5 | 5 Major, 11 Minor, 12 Notes |
| Contact carrier (rev A = rev B, byte-identical) | `band/rev-a/contact-carrier` | n/a / 0 | 0 | 2 | 4 Major, 10 Minor, 3 Notes |
| Band rev A (reference only) | `band/rev-a/pcb` | 0 / **1 error** | 0 | 1 | 1 Major, 11 Minor, 17 Notes |

**Bottom line:** nobody found a dead-on-arrival fault. All four dock contacts carry the right signal in the right
order on every board (dock, carrier, band rev A, band rev B), with no mirroring, and schematic-to-PCB parity is clean
everywhere. The problems are in **assembly yield** (dock vias in pads, rev B placement rotations), **RF** (one ground
cut-out missing under the rev B radio filter) and **the skin-side contacts** (solder tails as dock targets, sweat,
ESD).

## Fix before ordering

| # | Board | What | Why it matters | Effort |
| --- | --- | --- | --- | --- |
| 1 | Dock | **17 open vias sit inside pasted SMD pads** (C4, C12, C13, C15, R1, R7, R10, R12, U8 x3, U3.5, U6.4, F1.2, SW1.1, D2.2), about 15 more overlap a pad edge. No fill/cap, mask opening = pad. (D-L1, re-checked: via at 117.1, 122.7 is inside D2 pad 2.) | Solder wicks down the via: opens and tombstoned 0402s. | Dog-bone the vias off the pads in `gen_pcb.py`, or pay for filled+capped vias. |
| 2 | Band rev B | **Nordic's In1/In2 ground cut-out under the RF filter chain was not copied.** `scripts/transplant.py` only copies zones fully inside `BOX` (x up to +8.0 mm from U1); Nordic's cut-out runs to +8.5 mm, so it was skipped silently. In1 ground now sits 0.21 mm under the 0201 filter pads. (B-L1, re-checked against `nordic_ref_qfaa_0_8.kicad_pcb`.) | Adds capacitance the filter values were not designed for; the antenna match network can't undo it. Costs range. | Copy that one keep-out (Nordic rel. x +4.2..+8.5, y -1.0..+0.2, rotated 180 deg) onto In1 and In2, refill. Small. |
| 3 | Band rev B | **`pos.csv` has raw KiCad rotations, no JLC corrections** (the dock got them in `a5e8671`). X2 (32 MHz crystal, diagonal pins) or AE1 turned wrong = no radio. (B-L2) | One wrong rotation on X2, AE1, U1, U201, U202, U203, U401, U501 or D702 kills the board. | Either add the corrections like the dock's `gen_cpl.py`, or check every one of those in JLC's preview (README line 235 already says so). |
| 4 | Dock | **Top plate rests on the spring-pin barrels** (barrel top = plate underside exactly, bores = barrel diameter). (D-L2) | Any tolerance lifts the plate. | Ø2.1 x 0.5 mm counterbore per pin in the case script. |
| 5 | Band rev A only | KiCad DRC error: **C203 pad 2 has 1 GND thermal spoke** (needs 2), present in the saved fill and the Gerbers. Also U202 (KTD2026) custom footprint: EP 1.45 x 0.8 mm leaves 0.125 mm to the pins, KiCad's own footprint uses 0.7 x 1.2 mm, and paste is 100 %. Both advisors flagged U202 independently (A-E1, A-L3). | Only if rev A is ever ordered. | Fix spoke, swap U202 footprint, re-plot. |

## Band rev B

**Major**
- **B-L1** RF ground cut-out missing (fix #2 above).
- **B-L2** placement rotations (fix #3 above).
- **B-L3 / C-E5** ESD and VIN surge parts (D601-D603) sit 12-30 mm of trace from the exposed dock contacts, mostly on B.Cu and In2. The spring-pin tails touch skin, so ESD crosses the board before it is clamped. Move the TVS parts and series resistors next to J601 when there is a next spin.
- **B-E1 -> downgraded to Minor.** DRV2605L runs from raw VBAT, so the charger's 3.0 V cut-off and ship mode do not disconnect it (4-7 uA). The advisor rated it Major because it could drain the cell to 0 V. The chosen X2 Robotics 60 mAh cell is a protected cell, so its own protection stops that. Keep it in mind if the cell changes, and fix the README's "4 uA max" (it is 7 uA max).

**Minor**
- B-L4 vias inside the U201/U202 courtyards get the relaxed via-in-pad clearance rule; two normal vias end up 0.175 mm hole-to-copper (JLC asks 0.2).
- B-L5 C6 is 0.107 mm closer to L2 than Nordic's layout: 0.1 mm ANT-to-GND pad gap, 0.05 mm mask web. A bridge shorts the RF output.
- B-L6 BQ25125 ball mask dams 0.09 mm (JLC min 0.10); JLC will likely just remove them.
- B-L7 few GND vias along the 50 ohm feed (README's "12 within 1 mm" not reproduced).
- B-L8 panel mouse bites 0.05 mm from GND pour; C206 (10 uF 0603) 1 mm from a break tab. Cut the tabs, don't snap.
- B-E2 VIN TS divider: SMF12A lets VIN reach 12-20 V; TS pin (5.5 V max) is overstressed above ~11-18 V. Also BQ IN max 20 V vs 19.9 V clamp (C-E8 agrees). Only with a faulty dock or wrong charger.
- B-E3 thermistor is beside the charger, not at the cell (window still sensible).
- B-E4 blue/green LED may dim below ~3.4 V on battery.
- B-E5 a buzz on a low cell can trip the 3.0 V cut-off and reset the nRF mid-alarm: firmware should soften the buzz on low battery.
- B-E6 with no cell fitted the DRV2605L supply can sit below the 2.0 V I2C bus.
- B-E7 32 MHz crystal ESR 80 ohm; nRF54L10 limit not confirmed.
- B-E8 `parts.py`/schematic say "firmware may turn the SYS buck off"; it must never be off.

**Notes:** antenna clearance 4.2 x 5.9 mm vs Johanson's 6.5 x 6.5 (tuning in the case is essential; cell is 2.8 mm away, not 2); match network starts at 0 ohm vs Johanson's 3 parts; title block and Gerber job still say "rev A, parts-side down"; silkscreen 0.12 mm lines; case post over TP705 edge; PMID/VINLS capacitance near minimum after derating; no nRESET on the dock (SWD recovery only).

**Checked OK:** schematic/PCB/BOM/CPL parity on all 74 parts; nRF54L10 support parts match Nordic's reference within 0.03 mm (except C6/C11); 50 ohm feed calculates to 50.0 ohm; keep-out clean on 4 layers; all nets connected, no islands; BQ25125 settings (30 mA, 4.2 V, 2 mA term), I2C pull-ups on the always-on 2.0 V rail; ship-mode exit from the dock; panel rails, fiducials, tooling holes.

## Dock PCB

**Major**
- **D-L1** vias in pads (fix #1).
- **D-L2** top plate on pin barrels (fix #4).
- **D-L3** nothing stops the PCB sliding front-to-back in the tray (1.4 mm free at the back). Plugging USB-C pushes it back and the plungers take the side load. Add rear stops.
- **D-L4** crystal: SWDIO_DRV runs on top between the crystal's XIN and GND pads, with a via under the crystal body at (119.4, 100.1); XOUT runs 6.8 mm on In2 through two vias. Against Raspberry Pi's RP2040 layout guidance; SWD edges can couple into the 12 MHz clock.
- **D-E1** the exposed pins P1 (SWCLK), P2 (SWDIO) and P4 (VIN, live 5 V) have no ESD/TVS, only 22 ohm to the level shifters. Add a low-cap ESD array, a 5-6 V TVS on VIN, ~100 ohm series.

**Minor**
- D-L5 / D-E4 (both advisors) VREG_VOUT to C15 is 9.75 mm through two vias; IOVDD/USB_VDD/ADC_AVDD caps are 4-7 mm away or missing.
- D-L7 VBUS_F: 21 mm at 0.3 mm on an inner layer, ~25 C rise at 0.45 A.
- D-L9 no silkscreen at all (no pin 1, polarity, P1-P4 or revision marks).
- D-E2 band current limit R6 = 15 k gives 0.34-0.57 A; the band needs <= 0.1 A and the PTC won't trip on a short. ~33 k (0.21 A) is enough.
- D-E3 SWCLK level-shifter input floats after a debug session: add a 100 k pull-down.
- D-E5 / D-L14 (both advisors) README still says press BOOTSEL through a poke hole; rev B case has none. A blank RP2040 enumerates on its own, and `picotool reboot -u` re-enters the bootloader later.
- D-L8 RP2040 thermal-pad vias under paste; D-L13 tray pads touch TP1 / J1 shell, pin tails 0.3 mm from the tray floor.

**Notes:** CPL rotations look like the usual JLC fixes but check U1, U2, SOT-23s, J1 and LED cathodes in the preview; confirm JLC solders J1's shell legs; 0.6 mm pin holes vs Mill-Max's 0.508 mm; crystal 12 pF part with 15 pF caps; U4 LCSC part is a YONGYUTAI clone; README still says the band uses an nPM1304/nRF54L15; `gen_sch.py` would reset the rev B title block; QSPI traces long (17-27 mm); choose ENIG.

**Checked OK:** stock `debugprobe.uf2` pin map matches (no custom build needed); RP2040 minimum system, flash, USB-C CC, USBLC6, SY6280 reverse blocking; 1.8 V SWD works with both bands' 2.0 V I/O; USB-C plated slots and NPTH pegs in the drill files; BOM = CPL (49 parts); contact positions and magnets match the band.

## Contact carrier

**Major**
- **C-E1 / C-L1 / C-L2** (both advisors, same root cause). The dock plunger lands on the tip of the band pin's **solder tail** (Ø0.43 mm, 0.15 mm proud in a cone window), not on a gold target. Solder that wicks through the hole ends up on that tail, and the 1.4 mm pad under a 1.83 mm flange leaves no room for a fillet anyway. The plunger only catches the tail within about ±0.15-0.3 mm, while the dock recess allows ±0.3 mm. Options: reflow the pins with paste on a hotplate before gluing (no wicking), give the dock a real gold target, and/or tighten the recess to ±0.15 mm and use a straight bore at tail depth. Test docking with a deliberate side offset.
- **C-E2** sweat bridges neighbouring windows (0.2 mm wall on a 2.2 mm pitch). Off the dock SWDIO (2.0 V) sits next to SWDCLK (low) all night; on the dock a wet band bridges 5 V to GND. Rev A and rev B electrical advisors raised the same thing (A-E3, B-E10). Do a wet-skin leakage test; consider wider pitch or a raised rib next spin.

**Minor:** C-L3 preload 0.60 of 1.40 mm stroke, worst case 0.04-1.16 mm (barely touching at the low end; measure a real pin, the datasheet's -2 length is inconsistent); C-L4 pocket allows 0.1 mm per side vs JLC ±0.2 mm and the panel outline has sharp corners: sand the ends; C-L5 an open via sits under the SWDCLK landing point on both bands (A-L5 agrees; move it to the pad edge); C-L6 the dock pin pushes harder than the band pin, pulling on the weak joint; C-L7/C-L8 weak location on the LRA side and the LRA can is 0.02 mm from the pin envelope (3 advisors flagged this: add a rib); C-E3 GND isn't first-mate; C-E4 dock VIN is always live; C-E6 neighbouring flanges 0.37 mm apart, check for bridges after hand soldering.

**Notes:** order as "Panel by Customer", 1.6 mm, pick one finish (BUY-LIST says HASL, READMEs say ENIG; HASL is fine); band magnets are Ø3 x 1 mm (the dock's are Ø4 x 1.5).

**Checked OK:** VIN/GND/SWDCLK/SWDIO order matches at x 131.5, y 101.1/103.3/111.7/113.9 across dock, carrier, band rev A and rev B, no mirroring; carrier is symmetric so it can't be fitted backwards; a backwards band makes no contact; pins rated 5 A vs 0.45 A; zips complete; below JLC's 3 x 3 mm minimum so the 6-up panel is right.

## Band rev A (reference only, not being built)

- **KiCad DRC error** C203 starved thermal (fix #5). D701's library-mismatch warning is already excluded.
- **A-E1 (Major) / A-L3** U202 KTD2026 footprint (fix #5).
- **A-L1** C208, U202 and D702 reference text is plotted 110-230 mm off the board in the silkscreen Gerber (absolute coordinates where offsets belong).
- A-L2 four small passives solid to GND on one side (tombstone risk); A-L4 DNP parts still have paste; A-L5 via in the centre of the SWDCLK landing pad; A-L10 LRA vs pins 0.02 mm; A-E2 nPM1304 LED pins could replace U202 entirely; A-E4 no +/- marking on the cell pads; A-E5 DRV2605L EN floats while the SoC is in reset.
- Notes: ISP2454 pin map not re-checkable without the datasheet; inner GND under U1 joins through <1 mm necks; 0.15 mm to the shell roof; README via counts and TP704/705 claims are stale.

## What wasn't verified

LCSC stock and basic/extended status (LCSC blocked from the cloud), JLC's library zero orientations, the ISP2454
(confidential datasheet), the nRF54L10 crystal ESR limit, KTD2026 and TOGIALED drawings, and real spring-pin lengths
(measure one when they arrive).

## KiCad 10 cross-check

Run with `kicad-cli` 10.0.3 on every project, with and without zone refill, counting excluded items too:
ERC 0/0 on band rev A, band rev B, dock rev A and dock rev B. DRC with schematic parity 0/0 on band rev B and both
docks; 0/0 on the carrier, its panel and the rev B band panel (the panel only warns that its folder has no
`fp-lib-table`, harmless). Band rev A has the C203 thermal error above. Every project sets `missing_courtyard` to
ignore, so courtyard overlaps on parts without a courtyard are never caught; worth turning back on. The dock project
was open in the KiCad GUI during the check, so any unsaved edits there were not checked.
