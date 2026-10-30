# Flex PCB schematic plan (rev A)

This is the plan for the first custom board: one flexible PCB that carries every
part of the band, has a flat stiffened area where the coin LRA is taped down,
and includes a proper battery-management (BMS) block. It replaces the rigid
"Stage 1" board in the [hardware roadmap](hardware-roadmap.md); the rigid board
is now a fallback only.

Researched 2026-10-29/30 from vendor datasheets, fab capability pages and
published papers (sources at the end). Items marked **(check)** were not fully
confirmed and are on the open-items list.

## When do the battery and BMS get tested?

The Stage 0 Digi-Key cart had no battery (Digi-Key ships lithium by ground only
and did not list the cell for Canada) and no BMS, because the XIAO board has its
own charger. The battery and BMS are now tested in a new **Stage 0b**, before
the flex board is ordered:

| Step | What | When |
| --- | --- | --- |
| 0a | Buy a protected LiPo locally for the XIAO (PiShop.ca, Abra, Solarbotics; see sourcing below). Stage 0 power and wake-logic tests run on it. | Now, with the Stage 0 parts |
| 0b | **nPM1304-EK** (Nordic's evaluation kit for the chosen PMIC) wired to the XIAO nRF54L15 over I2C, with a small 80 to 110 mAh protected cell and a 10 kohm NTC. Test charge current, JEITA temperature cut-off, ship mode and whether docking alone wakes it, the battery model for the fuel gauge, and the motor's current peaks on the small cell. | After Stage 0 firmware reads the accelerometer and drives the LRA, and **before the flex schematic is frozen** |
| 1 | Same circuit on the flex board, measured again with the PPK2. | Flex rev A bring-up |

The 0b results feed straight into the schematic: charge current, NTC values,
buck voltage and the battery size. Zephyr has an `npm1304_ek` shield, so the
firmware written for 0b runs unchanged on the flex board.

How to wire the EK to the XIAO without fighting the XIAO's own charger (power
the XIAO from the EK's regulated output and leave its BAT pads empty) needs a
check against the XIAO schematic before the first power-up **(check)**.

## Block diagram

```
 Dock pads (6)                 nPM1304 PMIC                     Loads
 ------------                  ------------                     -----
 VIN  --TVS--+---------------> VBUS   VSYS -------------------> DRV2605L VDD (2.0-5.2 V)
 GND  -------+                        BUCK1 2.0 V ------------> ISP2454 VDD, LIS2DW12, I2C pull-ups
 SWDCLK --R--TVS-------------------------------------------------> ISP2454 SWDCLK
 SWDIO  --R--TVS-------------------------------------------------> ISP2454 SWDIO
 RX     --R--TVS-------------------------------------------------> ISP2454 UART RX
 TX     --R--TVS-------------------------------------------------> ISP2454 UART TX
                               VBAT <--- cell PCM <--- LiPo 80-110 mAh
                               NTC  <--- 10 k NTC on the cell
                               I2C + INT <-----------------------> ISP2454

 ISP2454 (nRF54L15) --I2C 1.8 V--> LIS2DW12 (INT1 -> wake GPIO)
                    --I2C 1.8 V--> DRV2605L (EN <- GPIO) --> LRA pads --> VG0832012
```

## Part choices for rev A

Rev A favours parts that are easy to place and rework on flex, and saves the
smallest packages for rev B.

| Block | Rev A part | Package | Why | Rev B upgrade |
| --- | --- | --- | --- | --- |
| SoC | Insight SiP **ISP2454-LX** (nRF54L15, with both crystals) | 8 x 8 x 1 mm LGA-62, 0.65 mm pitch | Antenna, 32 MHz and 32.768 kHz crystals, DC-DC inductor and all decoupling are inside. The only external part is a board trace joining pin 20 (OUT_ANT) to pin 22 (OUT_MOD). 1.7 to 3.6 V. Single units via the -TB/-EB parts at Digi-Key **(check stock)**. | Smaller nRF54L15 SiPs exist (u-blox ANNA-B5 6.5 x 6.5 mm, MinewSemi ME54BS61 6 x 6 mm) |
| PMIC / charger | Nordic **nPM1304** | QFN32 5 x 5 mm | 4 to 100 mA charging (the only charger here sized for 50 to 110 mAh cells), two bucks, load switches, JEITA NTC input, ship mode, battery discharge limit, VBUS works at 4.0 to 5.5 V and survives 22 V transients, fuel gauge that runs on the SoC. First-party Zephyr driver. | WLCSP 3.1 x 2.4 mm |
| Battery protection | Factory PCM on the cell | on the cell | Nordic's own FAQ says the PMIC does not replace a protection circuit. A cell with a PCM gives overcharge, over-discharge and short-circuit cut-off; the PMIC adds charge control, NTC and a current limit. | Board-level ABLIC S-82N1B or TI BQ2970 + dual FET, only if we move to bare cells |
| Fuel gauge | nPM1304 built-in (host side) | none | No extra parts. A separate gauge IC (MAX17048, BQ27427) would add 7 to 55 % to the average drain, and the BQ27427 does not support cells under 100 mAh. | same |
| Accelerometer | ST **LIS2DW12** | LGA-12 2 x 2 mm | 1.5 uA at 25 Hz low-power, 32-sample FIFO, wake interrupts, Zephyr driver, plenty of LCSC stock (C189624). | ADXL367 (0.9 uA, 512-sample FIFO) once LCSC stock improves |
| Haptic driver | TI **DRV2605L** | VSSOP-10 3 x 3 mm | Hand-solderable, same chip as the Stage 0 breakout, runs from VSYS with 1.8 V I2C. LRA auto-resonance and soft-ramp library. | DRV2625 DSBGA-9 (105 nA shutdown, but needs at least 2.7 V) |
| Motor | Vybronics **VG0832012** coin LRA | 8 x 3.25 mm | Same as Stage 0, 235 Hz, 58 mA typ. Taped to the stiffened motor pad. | VG0825003D (2.55 mm thick) **(check specs)** |
| Battery | Protected LiPo, **110 mAh, 12 x 30 mm**, 3 to 4 mm thick | e.g. 401230 class | The LRA's 60 to 80 mA peak is about 1.5C on a 50 mAh cell, so 80 mAh or more is safer. Solder tabs or a short lead to flex pads; no connector. | true 3 mm cell once a supplier is found |
| Dock ESD | 6 x 0402 TVS with leakage under 50 nA (VIN TVS working voltage at least 5.5 V) + 4 x 0402 100 ohm series resistors | 0402 / 0201 | Pads touch skin and sweat all night; a leaky TVS would cost more than the whole sleep budget. | same |

## Power tree and rails

| Rail | Source | Voltage | Feeds |
| --- | --- | --- | --- |
| VBUS | Dock pad 1 | 5 V | nPM1304 VBUS only |
| VBAT | Cell (through its PCM) | 3.0 to 4.2 V | nPM1304 VBAT |
| VSYS | nPM1304 | VBUS or VBAT | DRV2605L VDD, BUCK1 input |
| VDD_2V0 | nPM1304 BUCK1 | 2.0 V (VSET1 = 68 kohm; raised from 1.8 V after review, see below) | ISP2454 VDD, LIS2DW12 VDD/VDDIO, I2C pull-ups |
| BUCK2 | nPM1304 | off | Unused: no inductor, VOUT2 tied to VSYS (Nordic says this stops leakage), VSET2 to GND, SW2 left open and PVSS2 to GND (as in Nordic's reference configuration 2) |

Notes:

- **nPM1304 strapping.** VSET1 resistor so BUCK1 starts at 1.8 V on its own
  (the datasheet's VSET1 table confirms 47 kohm = 1.8 V, resistor 5 % or
  better), VDDIO tied to VOUT1, CC1/CC2 to GND (no USB-C; the datasheet allows
  floating or GND, and VBUS then stays at its 100 mA default limit). BUCK1 with a 5 % tolerance can sit at 1.71 V, just
  above the nRF54L15's 1.7 V minimum, so check the brown-out margin.
- **Ship mode for storage.** The nPM1304 enters ship mode over I2C. The
  datasheet's ship-mode chapter lists two ways out: SHPHLD held low (a button
  to GND), or VBUS rising above VBUSPOR (3.9 V typ), so docking alone should
  wake it; confirm on the EK in Stage 0b. SHPHLD has an internal 50 kohm
  pull-up; the board adds a test pad, an optional (DNP) extra pull-up to VBAT
  and a footprint for a tiny button. Nordic warns not to
  tie SHPHLD to a SoC GPIO because of leakage.
- **Battery current limit.** The nPM1304 caps battery current at about
  210 mA and VSYS from the battery is good for about 100 mA including the
  bucks. The LRA's overdrive and braking peaks are measured in Stage 0b, and
  the DRV2605L's OD_CLAMP is set so they stay under that.
- **No buzzing on the dock.** While docked VSYS follows VBUS up to 5.5 V,
  which is above the DRV2605L's 5.2 V recommended maximum. Firmware blocks the
  motor while VBUS is present, and the dock supplies 5.0 V.
- **Charge current** starts at 0.5C (40 to 55 mA for 80 to 110 mAh) and is set
  in firmware from the Stage 0b results.
- **Hot cut-off** near 45 C through JEITA, since the band charges on a dock but
  may be warm from the wrist. IEC 62368-1 limits long skin contact to about 43 C.
- **DRV2605L standby** is 4 uA typ (7 uA max) with EN low, about 0.1 mAh per
  day or 10 % of the budget. Its VDD cannot simply be switched off: the
  datasheet limits SDA, SCL, EN and IN to VDD + 0.3 V, so an unpowered driver
  would clamp the shared I2C bus. Rev A keeps it powered with EN low. If the
  0.1 mAh matters, rev B moves it to its own I2C bus (driven low before its
  VDD goes off) behind a load switch, or switches to the DRV2625 (105 nA).
- **Current-measure jumper.** A cut-able solder bridge between the cell and
  VBAT, so the PPK2 can go in series with no rework.

## I2C and signals

| Device | Address | Notes |
| --- | --- | --- |
| LIS2DW12 | 0x19 (SA0 strapped high) | CS tied to 1.8 V for I2C mode; SA0 hard-strapped (it has an internal pull-up); INT1 to a wake-capable GPIO, INT2 to a test pad |
| DRV2605L | 0x5A | EN to GPIO, IN/TRIG to GPIO (PWM option) |
| nPM1304 | 0x6B (datasheet: 7-bit address 110 1011) | GPIO/INT to SoC for VBUS-present and charger events |

One shared 1.8 V I2C bus with 4.7 kohm pull-ups to VDD_2V0. 10 kohm would
give about 425 ns rise time, too slow for 400 kHz. Every signal, plus nRESET
(module pin 13), gets a test pad on the electronics island.

GPIO assignment waits for the ISP2454 pinout check: the nRF54L15 ties some
peripherals to specific pins and power domains, and the 0.65 mm double-row LGA
may need via-in-pad for inner-row pads. **Step 2 of the build plan settles
this before anything else is drawn.**

## Dock pads (from the roadmap)

Six pads at 2 mm pitch, about 1.2 x 3 mm each: VIN, GND, SWDCLK, SWDIO, UART RX,
UART TX. TVS on every pad and 100 ohm in series on the four data pads. The
UART is only enabled while the PMIC reports VBUS present, and the RX pad gets
a pull-down so it does not float. SWDIO has an internal pull-up in the
nRF54L15 that cannot be turned off, so pad 4 sits at 1.8 V on the skin all
night; watch it for corrosion and consider a pad coating. Finish: JLCPCB flex
only offers ENIG; PCBWay offers hard gold, which wears better under pogo pins.
Rev A uses ENIG and we watch wear; rev B moves to hard gold if needed.

## Flex construction

| Item | Rev A choice | Source |
| --- | --- | --- |
| Stackup | 2-layer flex, 25 um adhesiveless polyimide, 18 um copper, about 0.12 mm finished | JLCPCB flex capabilities |
| Cover | Coverlay (not solder mask), 0.15 mm opening clearance | JLCPCB |
| Finish | ENIG | JLCPCB (PCBWay for hard gold) |
| Stiffeners | FR4 0.3 to 0.4 mm under every part area and under the motor pad; PI 0.2 mm behind the dock pads | JLCPCB offers PI, FR4 and steel |
| No steel stiffeners | Steel is slightly magnetic: it would pull on the LRA magnet and the dock magnets, and it detunes the antenna | PMD, Insight SiP, JLCPCB |
| Trace/space | 4/4 mil or wider (fab minimum is 3.5/3.5 mil at 18 um) | JLCPCB |
| Vias | 0.3 mm drill / 0.55 mm pad standard, only on stiffened areas, at least 0.5 mm from a stiffener edge | JLCPCB, Sierra, Epec |
| Bend zones | No vias, no parts, hatched ground, curved traces at right angles to the bend, teardrops, coverlay overlapping pad entries | IPC-2223 guidance via Altium/Sierra/Epec, Critcher 2021 |
| Bend radius | At least 10 x thickness, so 1.2 mm or more; a fold around a 3 to 4 mm cell gives about 1.5 to 2 mm | Altium, Sierra |
| Assembly | JLCPCB turnkey flex SMT; all parts on the top side, stiffeners on the bottom (applied before SMT) | JLCPCB |
| Rigid-flex | Not used (JLCPCB does not offer it) | JLCPCB |

### Outline concept: one fold around the battery

**Decided 2026-10-30:** a bigger pod with a common 12 x 30 mm, 110 mAh cell,
instead of the 35 x 18 mm Fitbit Air size with a shorter cell.

With about 1 mm case walls, the motor beside the cell across the width needs
12 + 0.5 + 8 = about 20.5 mm inside, so the pod is about **22 x 36 mm**
outside (36 mm = 30 mm cell + about 2 mm fold loop + walls). Putting the motor
at the end of the cell instead would need about 20 x 41 mm, and stacking it on
the electronics side would push the height to about 10 mm.

```
     Island A (top, faces away from the wrist), about 32 x 18 mm
  +--------------------------------------------+
  | ISP2454 (antenna corner, far end) nPM1304   |  FR4 0.4 mm stiffener,
  | LIS2DW12  DRV2605L  passives  test pads     |  no metal under antenna
  +--------------------------------------------+
   )  fold, about 5 mm wide neck, 1.5 to 2 mm radius, no vias
  +--------------------------------------------+
  | battery bay, 12 x 30 mm cell, 110 mAh        |  Island B (skin side)
  | NTC under the cell                           |  bonded to the case floor
  +---------------------------------+----------+
  | six dock pads on the outer face | LRA pad  |
  |                                 | 9 mm     |
  +---------------------------------+----------+
     Island B, about 32 x 20 mm (cell strip 12 mm + motor strip 8 mm)
```

- **Cell.** 12 x 30 mm, 3 to 4 mm thick, 110 mAh with a protection circuit,
  for example the Solarbotics 110 mAh (12 x 32 x 4, check the exact length)
  or a 401230. The motor's 60 to 80 mA peak is under 1C on this cell.
- **Motor zone.** The LRA needs a rigid, heavy mount: Precision Microdrives
  rates its 8 mm LRA on a 100 g sled and warns soft mounts absorb the
  vibration and shift resonance. So the LRA pad gets its own FR4 stiffener on
  island B, pressed against the skin-side wall of the case. Tape: the
  motor's own 3M VHB-class backing, or 3M 467MP. No superglue. The DRV2605L's
  auto-resonance tracks whatever shift is left.
- **Antenna.** ISP2454 in the corner of island A at the far end from the fold,
  1 mm from the board edge. The keep-out covers the whole folded stack, not
  just island A: the battery pouch, the LRA and island B's ground must not sit
  under the antenna corner. That corner sits over the end of island B past
  the cell, with island B's copper cut back there.
- **Height.** Case walls 1.6 + two flex islands with stiffeners about 1.0 +
  tallest part 1.0 + cell 3 to 4 + clearance 0.5 gives about 7 to 8 mm. A
  4 mm cell puts it right at the 8 mm target.

Rev A can also be powered up flat on the bench before it is folded, which makes
bring-up and probing much easier than on a folded board.

## KiCad setup

KiCad 10 has no native flex or stiffener layers. The plan:

- Stackup manager: 2 copper layers, polyimide dielectric; the mask layers act
  as coverlay openings.
- User.1 = top stiffener, User.2 = bottom stiffener, User.3 = bend zones,
  User.4 = antenna keep-out; plus a fab-notes drawing. Confirm with JLCPCB which
  layers they read before ordering.
- DRC rule areas: no vias in bend zones, keep-out zone for the antenna.
- Hierarchical sheets, one per block (below), so each block can be reviewed
  and reused in rev B.

## Plan for building the schematic

| Step | Work | Output | Advisor check |
| --- | --- | --- | --- |
| 1 | Create the KiCad 10 project in `hardware/flex-rev-a/`, project libraries for symbols and footprints, and sheet structure: `power`, `mcu`, `sensors`, `haptics`, `dock`, `debug`. | Empty project with sheets | none |
| 2 | **ISP2454 pinout study:** symbol and footprint from the datasheet (pads 1 to 48 signal, 49 to 62 mechanical, a trace joining pins 20 and 22). Check the nRF54L15 port and power-domain rules for each serial block, the dedicated clock pins, and the register setting NFC pins need before they work as GPIO. Decide which pads are reachable without via-in-pad on flex. Assign GPIOs against nRF54L15 pin and power-domain rules. | Symbol, footprint, GPIO table | Second check of footprint dimensions and pin map |
| 3 | **Power sheet:** nPM1304 per Nordic's reference schematic and the nPM1304-EK design, VBUS TVS, battery pads, NTC, current jumper, SHPHLD pull-up, BUCK1 1.8 V. | Power sheet | Review against the nPM1304 datasheet and the Stage 0b results |
| 4 | **MCU sheet:** ISP2454, SWD, UART, I2C, interrupts, NFC pins as plain GPIO only after the register change. | MCU sheet | Review against ISP2454 datasheet |
| 5 | **Sensors and haptics sheets:** LIS2DW12 (1.8 V, INT1 wake), DRV2605L (VSYS, 1 uF VDD and REG caps, EN and IN/TRIG), LRA pads, load-switch option. | Two sheets | Review against TI and ST datasheets |
| 6 | **Dock and debug sheets:** six pads, TVS, series resistors, test pads, one 0402 debug LED (DNP option). | Two sheets | Pad protection review |
| 7 | ERC, BOM with LCSC part numbers (JLCPCB assembly), power budget check against Stage 0/0b measurements. | Clean ERC, BOM CSV | Full schematic review by an independent advisor |
| 8 | Hand-off to layout: board outline, stiffener map, bend zone, antenna keep-out, fold check with a paper or PI-film mock-up around a dummy cell. | Layout-ready schematic | Mechanical review |

Steps 1, 2 and 4 to 6 can start now. Step 3 is drafted now and frozen after
Stage 0b.

**Progress (2026-10-30):** step 1 is done (`hardware/flex-rev-a/`). Step 2 is done,
including the module footprint; every signal uses an outer-row pad, so the
flex needs no via-in-pad (see [flex-rev-a-pinout.md](flex-rev-a-pinout.md)).
Step 3 is drafted: the power sheet follows the nPM1304 datasheet's reference
circuit "configuration 2" (QFN), and the project is now saved in KiCad 10
format. Its remaining **(check)** items (QFN exposed-pad size against Nordic's
reference layout, TVS and inductor part numbers, the GPIO used for PMIC_INT)
are listed on the sheet. It is frozen after Stage 0b.
Steps 5 and 6 are drafted too (sensors, haptics, dock and debug sheets), with
the BOM (`hardware/flex-rev-a/bom.csv`, LCSC numbers) from step 7. ERC is
clean. Step 7's power-budget check and independent review are still to do.
SHPHLD decision: rely on the nPM1304's internal 50 kohm pull-up; the extra
pull-up and the button stay DNP.

## Battery sourcing in Canada

Digi-Key only ships lithium cells by ground, which is likely why the cell
showed as not found from Canada. Buy locally:

| Seller | Cell | Size (mm) | Notes |
| --- | --- | --- | --- |
| Solarbotics (Calgary) | 110 mAh, PCM, JST | 12 x 32 x 4 | About USD 5.39, in stock when checked |
| Abra Electronics | 100 mAh and 150 mAh (Adafruit 1317), PCM, JST-PH | 150 mAh: 19.75 x 26 x 3.8 | Prices not visible **(check)** |
| PiShop.ca (took over Elmwood) | Adafruit 1317 150 mAh, Adafruit 3898 400 mAh | | Elmwood listed about CAD 9.99 / 11.99; PiShop stock not verified |
| X2 Robotics | 110 mAh 501430, PCM | 31 x 14 x 4 | CAD 5.99, out of stock when checked |

For Stage 0a (XIAO, charges at about 200 mA) use the 400 mAh cell. For Stage 0b
and the flex board use a 100 to 150 mAh cell. All of these are about 4 mm
thick; a true 3 mm cell still needs a supplier.

## Open items and risks

1. **RF exposure note.** The ISP2454 datasheet's RF-exposure statement assumes
   10 mm from the body. Ask Insight SiP whether a low-power wrist device is
   covered, or whether the band needs its own assessment **(check)**.
2. **ISP2454 inner-row pads.** Solved in step 2: every signal uses an
   outer-row pad. Some outer-row positions in the footprint were derived from
   the drawing, not printed; check them against Insight SiP's CAD files.
3. **ISP2454 stock.** One distributor shows an 8-week lead time and an odd
   "discontinued" flag. Confirm before step 4.
4. **Motor coupling** on a flex island is untested. Stage 0b can test it: tape
   the LRA to a scrap of 0.4 mm FR4 on foam and compare to a hard mount.
5. **Dock pad wear** with ENIG under pogo pins, and slow corrosion from the
   always-on SWDIO pull-up if the band is worn in the shower.
6. **Motion-only wake accuracy.** Walch et al. 2019 found motion alone barely
   separates sleep stages (kappa 0.08); motion plus heart rate does better.
   The band triggers on restlessness inside the window, which is what motion
   can measure. Rev A leaves no room for a heart-rate sensor; Stage 0 decides
   if that matters.

7. **Fuel gauge model.** The nPM1304 gauge needs a battery model for the exact
   cell; the nPM1304-EK can profile it in Stage 0b.

## Questions for you

1. Is a 4 mm thick cell (pod about 8 mm) acceptable, or should we hunt for a 3 mm cell?
2. Will the band be worn in the shower or during sweaty sleep? That decides hard gold pads and a pad coating.
3. The ISP2454's RF-exposure note assumes 10 mm from the body. For a personal device, are you fine proceeding while we ask Insight SiP?

## Accelerometer settings for sleep (from the papers)

- Range +-4 g, 25 Hz low-power mode (Walch used about 50 Hz, van Hees about
  85 Hz at +-8 g, then averaged to 5 s).
- Every 5 s: arm angle (z-angle) and ENMO. "No change over 5 degrees for 5 min"
  is the van Hees sleep rule.
- Every 30 or 60 s epoch: an activity count for Cole-Kripke / Sadeh-style
  scoring.
- Run the LIS2DW12 at 12.5 Hz and lean on its activity/inactivity interrupt. Its
  32-sample FIFO fills every 1.28 s at 25 Hz (2.6 s at 12.5 Hz), so it cannot
  hold a whole minute; draining it is the biggest digital cost in the budget.

## Sources

Fab and flex design:
- JLCPCB flex capabilities: https://jlcpcb.com/capabilities/flex-pcb-capabilities
- JLCPCB stiffener and SMT order: https://api.jlcpcb.com/blog/fpc-stiffener-smt-sequence-guide
- PCBWay flex: https://www.pcbway.com/fpc-rigid-flex-pcb/flex-pcb.html
- Altium, bend reliability: https://resources.altium.com/p/bend-reliability-trace-geometry-materials-flex-lifespan
- Sierra Circuits, IPC-2223: https://www.protoexpress.com/blog/ipc-2223-standards-and-design-violations-rigid-flex-boards/
- Epec flex design: https://www.epectec.com/flex/design
- KiCad stackup regions request: https://gitlab.com/kicad/code/kicad/-/issues/3823

Papers:
- Critcher and Freeborn, "Flexible PCB Failures From Dynamic Activity", IEEE OJCAS, 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8656411
- Soman et al., "Reliability Challenges in Fabrication of Flexible Hybrid Electronics for Human Performance Monitors", IEEE TCPMT, 2019. https://www.smtnet.com/library/files/upload/soman2019reliability.pdf
- Khan et al., "Flexible Hybrid Electronics: Direct Interfacing of Soft and Hard Electronics for Wearable Health Monitoring", Adv. Funct. Mater., 2016. https://smtnet.com/library/files/upload/Khan_et_al-2016-Advanced_Functional_Materials.pdf
- van Hees et al., "A Novel, Open Access Method to Assess Sleep Duration Using a Wrist-Worn Accelerometer", PLOS ONE, 2015. https://doi.org/10.1371/journal.pone.0142533
- Walch et al., "Sleep stage prediction with raw acceleration and photoplethysmography heart rate data derived from a consumer wearable device", Sleep, 2019. https://doi.org/10.1093/sleep/zsz180
- Cole et al., "Automatic sleep/wake identification from wrist activity", Sleep, 1992.
- Sadeh et al., "Activity-based sleep-wake identification: an empirical test of methodological issues", Sleep, 1994. https://pubmed.ncbi.nlm.nih.gov/7939118/
- Tassi and Muzet, "Sleep inertia", Sleep Medicine Reviews, 2000. https://pubmed.ncbi.nlm.nih.gov/12531174/

Parts:
- ISP2454 datasheet: https://www.mouser.lt/datasheet/3/1572/1/isp_ble_DS2454.pdf
- nPM1304: https://www.nordicsemi.com/products/npm1304 and FAQ https://devzone.nordicsemi.com/nordic/nordic-blog/b/blog/posts/frequently-asked-questions-for-the-npm1300-and-npm1304
- nPM1304-EK: https://www.digikey.ca/en/products/detail/nordic-semiconductor-asa/NPM1304-EK/27258986
- DRV2605L: https://www.ti.com/lit/ds/symlink/drv2605l.pdf, DRV2625: https://www.ti.com/lit/ds/symlink/drv2625.pdf
- LIS2DW12 at LCSC: https://www.lcsc.com/product-detail/C189624.html
- Precision Microdrives on LRA mounting: https://www.precisionmicrodrives.com/making-a-haptic-device and https://www.precisionmicrodrives.com/why-does-the-resonant-frequency-of-an-lra-shift
- Digi-Key lithium shipping: https://forum.digikey.com/t/lithium-battery-shipping/8153
- Solarbotics 110 mAh: https://solarbotics.com/?p=171978
- Abra 150 mAh: https://abra-electronics.com/batteries-holders/batteries-polymer-lithium-ion/1317-ada-lithium-ion-polymer-battery-37v-150mah-1317-ada.html

Open designs to borrow from: ZSWatch (nPM1300, KiCad) https://github.com/Kampi/ZSWatch-HW,
PineTime https://wiki.pine64.org/wiki/Category:PineTime, SensWear (nRF54L15
wearable, 2026) https://www.cnx-software.com/2026/07/29/senswear-an-open-source-modular-nordic-nrf54l15-development-platform-for-wearables/

## Schematic review (2026-10-30)

An independent review of the finished rev A schematic, checked against the
vendor datasheets. Every IC pin map, decoupling value and strap was correct,
the nets match across sheets, and there is one set of I2C pull-ups. Fixes:

| # | Finding | Fix |
| --- | --- | --- |
| 1 | ISP2454 pad 10 (HAPT_TRIG) sits in the lower outer row on the module mid-line. Below it is antenna keep-out, and the gaps between inner pads (0.25 mm) are too narrow for a trace, so it cannot escape without via-in-pad. | DRV2605L IN/TRIG tied to GND (TI's "if unused" option). Effects are started over I2C (GO bit). Pad 10 left unconnected. |
| 2 | BUCK1 at 1.8 V +-5 % can drop to 1.71 V, against the module's 1.7 V minimum. | VSET1 changed to 68 kohm for 2.0 V; the rail is renamed VDD_2V0. The LIS2DW12, DRV2605L inputs and nPM1304 VDDIO all work at 2.0 V. |
| 3 | DRV2605L footprint was TSSOP-10; TI's DGS package is VSSOP-10. | Kept KiCad's TSSOP-10_3x3mm_P0.5mm footprint: it follows TI drawing MPDS035, which is the DGS (VSSOP) land pattern, and KiCad 10 has no footprint under the VSSOP name. |
| 4 | ST asks for 10 uF bulk next to the LIS2DW12. | 10 uF added on the sensors sheet. |
| 5 | The VIN TVS (6 V minimum breakdown) would burn on a wrong 9 to 12 V supply, giving up the nPM1304's 22 V input tolerance. | VIN TVS changed to a higher standoff part; the nPM1304 cuts VSYS off above 5.5 V by itself. |

Other risks noted, not schematic changes:

- **Trapped ground pads.** GND pads 12, 14, 16 and 18 are in the same trapped
  row. They are tied together inside the module; ask Insight SiP whether they
  may stay unconnected on the board. Pads 8 and 24 reach the large pads 7 and 25
  with a short trace.
- **Dock logic level.** There is no VTref pad, so the dock must drive SWD and UART
  at the band's 2.0 V and only after the band is alive (for example when it
  sees UART_TX high). A 3.3 V probe would back-power the band through the
  100 ohm resistors.
- **Dock supply.** VSYS follows VBUS up to 5.5 V, the DRV2605L's absolute maximum,
  so the dock supply must be 5.0 V +-3 %.
- **Sweat.** The SWDIO pad sits at 2.0 V (internal pull-up) next to GND all night.
- **Sourcing.** The ISP2454 and nPM1304 have no LCSC stock, so they must be
  consigned to JLCPCB.

### Power budget (estimate)

Battery 3.8 V, buck about 85 % efficient.

| Load | Typical (uA at the battery) | Worst (uA) |
| --- | --- | --- |
| nPM1304, one buck, auto mode | 0.8 | 1.1 |
| nRF54L15 System ON idle with RTC (GRTC + 32 kHz crystal) | 0.8 | 1.8 |
| LIS2DW12 low-power at 25 Hz | 0.8 | 1.1 |
| FIFO drains every 1.28 s | 4.5 | 8.9 |
| DRV2605L standby, EN low | 4.0 | 7.0 |
| Cell protection circuit | 3.0 | 6.0 |
| BLE, light use | 4.5 | 8.9 |
| TVS leakage, NTC (biased only when measuring), pull-ups idle | about 0 | 0.1 |
| **Sleep total** | **18 uA (0.44 mAh/day)** | **35 uA (0.84 mAh/day)** |
| Morning buzz, 30 s at 60 to 80 mA | 0.5 to 0.67 mAh/day | |

That is about 0.95 mAh per day typical and 1.5 mAh worst case: **roughly 3 to 4
months on the 110 mAh cell** (2 months worst case), well past the 2-week target.
The buzz is over half of it. Stage 0b measures the real numbers.
