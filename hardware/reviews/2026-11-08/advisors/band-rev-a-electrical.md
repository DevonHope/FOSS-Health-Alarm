# WakeBand band rigid rev A: electrical review (Advisor 1)

Scope: `hardware/band/rev-a/pcb/` at commit 25262a1 (branch claude/project-thread-k0vt9w). Read-only; nothing in the repo was changed.

Method: KiCad is not installed, so I wrote my own S-expression parsers (sexpdata):
- Schematic netlist: built from all 7 sheets (wires, junctions, local/global/hierarchical labels, sheet pins, power symbols, embedded lib symbols with pin transforms).
- PCB netlist: pad nets from `rigid-rev-a.kicad_pcb`. Separately, a copper connectivity check for every non-GND net, using tracks, vias and pads.
- Pinouts checked against public references: nPM1300-QEXX QFN32 symbols (Nordic engineer's lib hlord2000/nordic-lib-kicad and MLAB), assuming the nPM1304 QFN32 is pin-compatible with the nPM1300, which Nordic states; KiCad's official KTD2026 symbol and DFN-8 footprint; KiCad's LGA-12 footprint; Zephyr's nRF54L15 DK pinctrl; the nRF54L15 clock-pin list (P0.03/04, P1.03/04/08/11/12, P2.01/06, as quoted from the PS in public repos).
- LCSC numbers checked against public part libraries and BOMs on GitHub.
- Not available to me: nordicsemi docs (proxy-blocked), the Insight SiP ISP2454 datasheet, the Kinetic KTD2026 PDF and the TOGIALED PDF. Every finding that depends on them says so.

## Findings

### A-E1: KTD2026 (U202) land pattern disagrees with KiCad's library footprint for the same datasheet; EP-to-pin gap is only 0.125 mm
- **Severity:** Major
- **Confidence:** medium. The two drawings disagree; I could not open the Kinetic PDF to see which is right.
- **What:** The custom footprint `wakeband.pretty/Kinetic_UTDFN-8_1.5x1.5mm_P0.4mm_EP1.45x0.8mm` has:
  - an exposed pad (EP) of 1.45 x 0.8 mm;
  - signal pads of 0.25 x 0.45 mm centred at ±0.75 mm, so the EP-to-signal-pad copper gap is **0.125 mm**.
- KiCad's official `Package_DFN_QFN:DFN-8-1EP_1.5x1.5mm_P0.4mm_EP0.7x1.2mm` cites the same Kinetic datasheet (rev 04h) and has:
  - EP 0.7 x 1.2 mm (rotated the same way, that is 1.2 along the pin row and 0.7 across);
  - 0.2 mm wide pads with a 0.2 mm EP-to-pad gap.
- The custom EP is about 40 % larger in area and reaches 0.05 mm closer to each pin row.
- **Why it matters:** the EP is GND. A solder bridge from the EP:
  - to pin 5 (VIN = VSYS) shorts VSYS;
  - to D1-D3 (pins 2-4) puts the RGB LED straight across VSYS with no current limit. The LED burns and VSYS is loaded.
- **Evidence:** footprint file above; board pads U202.1-9 at (125.95-127.15, 112.45/113.95), EP at (126.55, 113.2); KiCad library footprint pad table.
- **Fix:** compare against the package outline and land pattern in KTD2026 datasheet rev 04i.
  - If the package EP really is 0.7 x 1.2 mm, use the KiCad footprint (rotated 90°), or at least shrink the EP copper and paste to about 0.7 x 1.2 mm.
  - In either case, put the EP paste at 50-60 % in windows.
  - See A-E2 for removing the part altogether.

### A-E2: The charge LED could run from the nPM1304's own LED pins, removing U202 (no LCSC stock, consigned) and the firmware dependency
- **Severity:** Minor (design simplification)
- **Confidence:** medium. This assumes the nPM1304 keeps the nPM1300's three 5 mA LED sinks with charger-status modes.
- **What:** LED0/LED1/LED2 (U201 pins 25-27) are left open, while a separate I2C RGB driver (U202, KTD2026) is added.
  - On the nPM13xx family these pins are open-drain current sinks (about 5 mA). They can be set to show charging or charge error with no SoC involvement.
  - Driving D702's three cathodes from LED0-2, with the anode on VSYS, would remove U202 and C208.
  - It would remove a consigned part with no LCSC listing, a 0.4 mm-pitch UTDFN with the risk in A-E1, and one more I2C device.
  - Charge indication would work even with blank or crashed firmware.
- **Trade-off:** fixed current (no dimming or mixing), and you need to check the nPM1304 PS for the LEDx pin voltage limit against VSYS up to 5.5 V.
- **Evidence:** power.kicad_sch: `unconnected-(U201-LED0..2)`, U202/D702/C208 on VSYS.
- **Fix:** consider it for rev A if U202 sourcing or assembly is a concern; otherwise for rev B.

### A-E3: The biased SWD contacts sit at the wrist face, 2.2 mm apart, so sweat can leak current and corrode them
- **Severity:** Minor (battery life and reliability)
- **Confidence:** medium. The mechanism is certain; the size needs measuring.
- **What:**
  - The carrier README states that the spring-pin tails are the outer contacts at the wrist face, recessed about 0.55 mm.
  - SWDIO (J601.4, y 103.3) sits at 2.0 V through the nRF54L's always-on pull-up. SWDCLK (J601.3, y 101.1, internal pull-down) is 2.2 mm away.
  - Sweat between the two tails forms a DC-biased electrolytic path. Through the about 10-15 k internal pull-up, a 100 k-1 M sweat film draws about 2-20 µA, against an 18 µA typical sleep budget. The budget line "TVS leakage ... about 0" leaves this out.
  - DC bias in sweat also drives electrochemical corrosion and migration between those two tails.
  - VIN/GND, the other adjacent pair, carries no bias when undocked, so it is not affected.
- **Evidence:** pcb pads J601.3/.4; contact-carrier P1/P2 at the same coordinates; dock.kicad_sch note "pad 4 sits at 2.0 V on the skin all night".
- **Fix:**
  - Do a wet-skin or saline leakage test on the first boards before trusting the battery-life estimate.
  - Inspect the tails after a week of wear.
  - Options for rev B: seal around the tails (gasket or conformal coat at the window), or order the pads so that SWDIO sits next to VIN, which is unbiased when undocked.
  - The 100 Ω series resistors do not limit this current.

### A-E4: No polarity marking on the hand-soldered cell pads, and no reverse-battery protection
- **Severity:** Minor
- **Confidence:** high
- **What:** TP201 (BAT+, bottom-right) and TP202 (BAT-, top edge) are labelled only on B.Fab. Only the pad outlines are on silk.
  - The cell is hand-soldered with wire leads, and nothing protects VBAT against reversal: there is no FET, and the cell's protection circuit (PCM) does not cover a swapped lead.
  - A swapped lead puts -3.7 V on nPM1304 VBAT/VSYS, which likely destroys the PMIC.
- **Evidence:** PCB footprints TP201/TP202: Reference and Value on B.Fab, no text on B.SilkS.
- **Fix:** add "+" and "-" (or "BAT+"/"BAT-") on B.SilkS next to TP201 and TP202, and add a polarity step to the assembly notes.

### A-E5: DRV2605L EN has no defined level while the SoC is in reset, blank or being flashed
- **Severity:** Minor
- **Confidence:** low-medium. I am not sure whether the DRV2605L has an internal pull-down on EN.
- **What:** HAPT_EN (U1.42, P2.05) to U501.5 has no external pull-down. nRF GPIOs come out of reset as disconnected inputs, so EN floats on a blank board, during SWD sessions and in any reset.
  - If EN drifts high, the driver leaves shutdown. With IN/TRIG tied to GND and the default registers it should not drive the motor, but it draws more than the shutdown current.
- **Fix:** add a 100 k-1 M pull-down from EN to GND (a 0402 footprint, even if DNP), or confirm the datasheet's EN input structure.

### A-E6: ISP2454 pinout, decoupling and mechanical pads could not be verified
- **Severity:** Note, but a blocker if the pin map is wrong
- **Confidence:** n/a
- **What I could check:**
  - The symbol, footprint and PCB agree with each other: VDD_nRF on pad 26; GND on 1, 7, 8, 12, 14, 16, 18, 21, 23, 24, 25, 31; SWDIO 28, SWDCLK 30, nRESET 13; OUT_ANT 20 joined to OUT_MOD 22.
  - The GPIO choices obey nRF54L15 rules, assuming pad-to-port names are right: TWIM30 SDA P0.02 / SCL P0.03, where P0.03 is a clock pin and both are on the same port; UARTE20 on P1.04/P1.05; interrupts on P1.07/P1.11; the P2 pins used only as plain GPIO.
- **What I could not check:**
  - the pad-to-signal map against the confidential datasheet;
  - that the "-LX" suffix is the nRF54L15 variant;
  - the mechcanical pads 49-62. They are netless on the PCB. Many SiP LGAs want these on GND.
- **Decoupling:** the mcu sheet note ("datasheet R7: all decoupling inside") is the only justification for having no capacitor at pad 26. The nearest VDD_2V0 capacitor is C207, about 7.8 mm away, and C403 is about 10 mm away.
- **Fix:** have a second person check the pin map and the pin-1 orientation against datasheet R7. If there is room, add a 0402 1 µF (DNP) beside pad 26.

### A-E7: VSYS follows VBUS on the dock: DRV2605L and KTD2026 run close to their limits
- **Severity:** Note
- **Confidence:** medium. This depends on how the nPM1304 handles VSYS from VBUS.
- **What:** U501 (DRV2605L: 5.2 V recommended maximum, 5.5 V absolute maximum) and U202 (KTD2026: VIN maximum 5.5 V) are on VSYS. The schematic notes say VSYS follows VBUS up to the nPM1304's OVP (5.5 V typical).
  - The dock passes USB 5 V through a PTC and the SY6280 switch, so VSYS normally sits around 4.9-5.1 V, which is fine.
  - An out-of-spec USB supply near 5.5 V would take the DRV2605L out of its recommended range before OVP trips. The design already blocks the motor while docked.
- **Fix:** none needed for rev A. Keep the firmware block. Check the nPM1304 PS: if VSYS is regulated below VBUS, this note goes away.

### A-E8: Stale schematic text that contradicts the current board
- **Severity:** Note
- **Confidence:** high
- **What:**
  - dock.kicad_sch: "six round 1.6 mm pogo pads on B.Cu (the pod outer face), 2.5 mm pitch". The board has four 1.6 mm pads on B at x 131.5 and two 1.4 mm UART pads on F.
  - dock.kicad_sch: "Firmware enables the UART only while the PMIC reports VBUS present". The dock no longer carries UART.
  - haptics.kicad_sch: "Leads hand-soldered to TP501/TP502 on F.Cu". They are on B.Cu.
  - Root sheet: "parts side down". The README says parts side out since 2026-11-06.
  - README via table total 136 vs 140 in the header (layout's area, listed for completeness).
- **Fix:** update the notes so the schematic PDF that goes with the order is not misleading.

### A-E9: UART bench pads are 2.0 V logic, and RX has a pull-down
- **Severity:** Note
- **Confidence:** high
- **What:** J601.5/.6 run through 100 Ω to the 2.0 V I/O.
  - A common 3.3 V USB-UART adapter would push about 8 mA through R603/R604 into the nRF's ESD diodes and back-power VDD_2V0. Use a 1.8 V adapter, or say so in the README.
  - R605 (100 k to GND) holds RX low, which a UART reads as a break, when nothing is attached. If firmware enables the UARTE with the pin's pull-up, RX reads high and the divider draws about 17 µA. Keep the UART off except on the bench.

### A-E10: The debug LED barely lights at 2.0 V through 1 kΩ
- **Severity:** Note (DNP part)
- **Confidence:** medium
- **What:** P2.04 at 2.0 V drives R701 (1 k) into D701 (red, Vf about 1.7-2.0 V), which gives roughly 0-0.3 mA. That is hard to see.
- **Fix:** if it is fitted for bring-up, use 47-100 Ω.

### A-E11: D702 BOM data vs the README/3D model, and the LED pin map is unverified
- **Severity:** Note
- **Confidence:** medium
- **What:** A public LCSC-derived library describes C273610 as a red/emerald/blue common-anode LED in an "LED-4 1.5x1.6x**0.8**" package. The README and the generated 3D model use 0.6 mm.
  - The pad map (1 = anode, 2 = B, 3 = G, 4 = R, anode at the top-right pad) could not be checked against the TOGIALED datasheet.
  - A wrong anode pad means the LED never lights. Swapped cathodes only swap colours.
- **Fix:** check against the datasheet before ordering, and update the height stack if 0.8 mm is right.

### A-E12: Bring-up with a flat or protection-tripped cell depends on firmware
- **Severity:** Note
- **Confidence:** medium
- **What:** On the dock, VBUS powers VSYS and BUCK1 (VSET1 strap), so the SoC boots and can be flashed with no cell or a flat one. That part is OK.
  - Charging stays off until firmware enables it (per the README's power-on defaults).
  - If the cell's protection circuit has tripped from over-discharge, VBAT reads near 0 V. Firmware must still enable the charger so the PCM can recover, and must not gate charging on "battery detected".
- **Fix:** add this to the firmware charger requirements in the README.

### A-E13: D601 LCSC number not verified
- **Severity:** Note
- **What:** I could not confirm that C207255 is a Littelfuse SMF12A. All the other LCSC numbers match their descriptions (see below).

### A-E14: ESD path from the dock pads (cross-reference to layout)
- **Severity:** Note
- **What:** The topology is right: pad, then TVS, then 100 Ω, then SoC, and VIN has the SMF12A.
  - But the tails are exposed at the wrist face, so every ESD hit comes in here, and it travels 8-20 mm of inner-layer trace before it is clamped (README compromise 11).
  - This is the layout reviewer's call; electrically it is the weakest part of the protection.

## Checked and found OK

- **Schematic vs PCB parity:**
  - 53 parts on both sides, with the same values, footprints and DNP flags.
  - Every multi-pin net is identical. The only extra item on the PCB is U1 mechanical pads 49-62, which are netless.
  - Every non-GND net is fully connected by tracks and vias. VIN reaches J601.1 through a via overlapping the pad edge, as the README says. GND is through zones, which I did not check.
- **nPM1304 (U201)**, every pin checked against the nPM1300 QFN32 pinout:
  - 1 VOUT1 = VDD_2V0; 2 PVSS1 to NT201 to GND with C204 and C207 returns; 3 SW1 to L201 2.2 µH; 4 PVDD = VSYS (C204 10 µF);
  - 5 SW2 open, 6 PVSS2 GND, 32 VOUT2 = VSYS, 16 VSET2 GND: BUCK2 unused as in Nordic config 2;
  - 17 VSET1 68 k 1 %, giving 2.0 V (consistent with the nPM13xx VSET table as I remember it);
  - 12 VDDIO = VDD_2V0; 13/14 on the I2C bus; 10 GPIO3 to PMIC_INT (P1.11); 15 SHPHLD to TP203 (internal pull-up, R201 DNP);
  - 18 NTC to 10 k B3380 (NCP15XH103F03RC, a supported type); 19 VBAT (C202, JP201, TP706); 20 VSYS (C205 10 µF); 21 VBUS = VIN (C201 1 µF 50 V); 22 VBUSOUT (C206 1 µF);
  - 23/24 CC to GND (no USB-C, 100 mA limit, enough for a 30 mA charge); 28-31 load switches to GND; 7/8/9/11 GPIO and 25-27 LED open; 33 EP GND.
- **Charger:** 30 mA (0.5 C) and 4.2 V termination in firmware are appropriate for the 60 mAh cell.
- **Interface pinouts across the three boards:** VIN 113.9, GND 111.7, SWDCLK 101.1, SWDIO 103.3 at x 131.5 are identical on the band board, the contact carrier and the dock PCB.
- **Dock SWD levels:** the dock's 1.8 V SWD drive reads as high on a 2.0 V nRF54L (VIH about 1.4 V). The band's 2.0 V SWDIO into the dock's TXS0101 1.8 V port is within its absolute maximum.
- **VIN protection:** SMF12A (12 V standoff, 19.9 V clamp) with its cathode on VIN (D_Zener pin 1 K to footprint pad 1), below the nPM VBUS 22 V absolute maximum. MLCCs on VIN are rated 50 V.
  - Hot-plug ringing on 1 µF stays well under the TVS breakdown.
  - Reverse VIN is not mechanically possible with the fixed carrier.
- **Data-pad ESD:** TPD1E10B06 bidirectional, 5.5 V working voltage, more than the 2.0 V signals. Series 100 Ω sits on the SoC side of the TVS.
- **LIS2DW12 (U401):**
  - The footprint's 4-2-4-2 pad order matches the pin table.
  - CS strapped high for I2C; SA0 high gives address 0x19; pins 5 and 7 to GND as ST allows; VDD and VDD_IO at 2.0 V.
  - 100 nF + 100 nF + 10 µF decoupling as ST recommends.
  - INT1 to P1.07, INT2 to a test pad.
- **DRV2605L (U501, DGS pinout):** REG with 1 µF; VDD and VDD/NC on VSYS with 1 µF; IN/TRIG to GND as TI allows; EN to GPIO; OUT+ and OUT- to the LRA pads; VIH 1.3 V is compatible with the 2.0 V bus. Footprint TSSOP-10 3x3 P0.5 is right for DGS.
- **KTD2026:** the pin map (1 ST, 2 D3, 3 D2, 4 D1, 5 VIN, 6 SCL, 7 SDA, 8 GND, 9 EP) matches KiCad's official symbol. Colour wiring is D1 blue, D2 green, D3 red, consistent with D702 pins.
- **I2C bus:** addresses 0x6B / 0x5A / 0x19 / 0x30 do not clash. 4.7 k pull-ups to 2.0 V suit 400 kHz with this load. Every device on the bus is powered whenever VDD_2V0 is up, so nothing back-powers through the bus.
- **BOM:** every LCSC number checked matches its description: C15849, C23630, C96446 (CL10A106MA8NRNC 10 µF 25 V), C1525, C52923, C36871, C25741, C25076, C25900, C11702, C337891 (DFE201610E-2R2M), C48260 (TPD1E10B06DPYR), C189624 (LIS2DW12), C527464 (DRV2605LDGSR), C77131 (NCP15XH103F03RC) and C273610 (RGB common-anode LED).
  - MLCC voltage ratings and DC-bias derating are adequate: 10 µF 25 V 0603 at 2.0-5 V, 1 µF 25-50 V at up to 5.5 V.
  - The JLCPCB BOM and CPL cover exactly the fitted parts.
- **Leakage budget:** SMF12A and the TVS diodes, apart from A-E3; KTD2026 shutdown; LIS2DW12 straps (no current); R201 DNP. Nothing else found beyond the documented DRV2605L standby current of about 4 µA.

## Not checked or out of scope

- RF (antenna keep-out) and the copper geometry and DRC: left to the layout reviewer.
- The Gerbers against the .kicad_pcb.
- The nPM1304 reference-design capacitor values for VBAT (2.2 µF here) and VBUS/VBUSOUT: Nordic's docs were blocked, so these are taken as plausible, not verified.
