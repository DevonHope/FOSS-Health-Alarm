# Dock PCB rev B: electrical review (Advisor 1)

Scope: `hardware/dock/rev-b/pcb` (schematic, PCB, `scripts/parts.py`, BOM/CPL, README), compared against
rev A and against the band's SWD/VIN interface (band rev A and rev B READMEs). Read-only review.

Method: I parsed the `.kicad_sch` (label at each pin end) and `.kicad_pcb` (pad nets) with sexpdata and
compared them pin by pin against `scripts/parts.py`. I checked the RP2040 QFN-56 pin numbers by hand.
Firmware facts come from the raspberrypi/debugprobe master sources and pico-sdk `boards/debug_probe.h`.
Part facts come from the JLCPCB part pages, TI product pages and the SY6280AAC datasheet (Olimex
mirror). LCSC, ti.com PDFs and datasheets.raspberrypi.com were blocked by the proxy, so the RP2040 HDG
points below are from memory of the HDG and are marked as such.

## Findings

### D-E1: Major: The exposed spring pins have no ESD or over-voltage protection, and the weaker ESD port of each translator faces the contacts
- **What:** With no band in the dock, P1 (SWCLK), P2 (SWDIO) and P4 (VIN, always live at 5 V) are bare
  contacts on top of the dock that people will touch.
  - P1 and P2 reach the translators through only 22 Ω (R11, R12).
  - The TXS0101 has to have VCCA ≤ VCCB, so its A port (2.5 kV HBM, against 8 kV on B) is the side
    that faces the band.
  - The 74LVC1T45 is 2 kV HBM. HBM ratings are not system-level IEC 61000-4-2 protection.
  - A coin or key across P4 and P1/P2 (pin centres y 101.1 / 103.3 / 111.7 / 113.9, total span about
    12.8 mm) forces 5 V into U7.B and U8.A, which run from the 1.8 V rail. Through 22 Ω that is about
    (5 − 1.8) / 22 ≈ 145 mA, well past the parts' output and clamp-current ratings. The SY6280 limit
    (0.45 A) does not protect this path.
- **Evidence:** `parts.py` U7 (pin 4 SWCLK_1V8 → R11 → P_SWCLK), U8 (pin 3 SWDIO_1V8 → R12 →
  P_SWDIO), U6 OUT → VIN_BAND → P4. No TVS or ESD part sits on P_SWCLK, P_SWDIO or VIN_BAND. TI
  TXS0101 page: A port 2500 V HBM, B port 8 kV. TI SN74LVC1T45 page: 2000 V HBM.
- **Fix:**
  - Add a low-capacitance ESD array on P_SWCLK and P_SWDIO (a 2-line part in SOT-23 or SOT-563 next
    to the pins), plus a 5–6 V TVS on VIN_BAND.
  - Raise R11 and R12 to about 100 Ω. SWD at ≤4 MHz tolerates this, and it limits the current from a
    5 V short into the clamps.
- **Confidence:** High that the protection is missing. Medium on the severity, since the band side
  also lacks it.

### D-E2: Minor: The band current limit is set higher than needed, the README's "part minimum 0.4 A" is wrong, and the PTC does not back up the switch
- **What:**
  - The SY6280AAC datasheet gives I_lim = 6800 / R_SET, adjustable from **0.13 A to 2 A**, with ±25 %
    accuracy (0.75–1.25 A at 6.8 k). So R6 = 15 k gives 0.34–0.57 A, and 0.4 A is not the part's
    minimum.
  - The band draws far less. Band rev B sets the BQ25125 input limit to 100 mA and charges at 30 mA,
    and band rev A charges at 30 mA.
  - F1 (FSMD050-0805) holds 0.5 A and trips at 1 A. With the switch limiting at most about 0.57 A plus
    roughly 40 mA for the probe, the PTC will not trip on a VIN short. The switch instead
    thermal-cycles: 130 °C shutdown with auto-retry, at about 2.5 W dissipated in SOT-23-5. The README
    line "the PTC backs it up" is optimistic.
- **Evidence:** `parts.py` R6 15k, F1; README "Board" and "Power notes" tables; SY6280AAC datasheet
  rev 0.3 (EN active high, I_lim 0.13–2 A, ±25 %, reverse blocking with no body diode, 150 Ω output
  discharge).
- **Fix:**
  - Set R_SET to about 33 k: 0.21 A typical, 0.15–0.26 A worst case, still above the band's 100 mA
    input limit. This cuts short-circuit dissipation and contact arcing.
  - Correct the README.
- **Confidence:** High.

### D-E3: Minor: The 74LVC1T45 SWCLK input floats after a debug session, and its output to the band is then undefined
- **What:** debugprobe's `probe_gpio_deinit()` calls `gpio_deinit(SWCLK)` and
  `gpio_disable_pulls(SWCLK)` when the host disconnects. GPIO12 then floats, so U7.A (SWCLK_3V3) has
  no defined level. TI says the 74LVC1T45 inputs "must be held at a valid level" or ICC rises, and
  U7.B then drives the band's SWCLK to whatever level it settles at. After reset, the RP2040's default
  pull-down holds the line until the first session. SWDIO is fine because the TXS0101 has internal
  pull-ups.
- **Evidence:** debugprobe `src/probe.pio` (`probe_gpio_deinit`); `parts.py` U7 pin 3 SWCLK_3V3, which
  has no pull resistor.
- **Fix:** Add a 100 k pull-down on SWCLK_3V3, or on SWCLK_1V8, which also matches the nRF's own
  pull-down.
- **Confidence:** High.

### D-E4: Minor: RP2040 decoupling is short of the HDG reference, and the caps on the bottom-edge supply pins are far from their pins
- **What:**
  - **Fitted caps:** 6 × 100 nF on +3V3 near the IOVDD pins (C8–C13), 1 µF on VREG_VIN (C14),
    1 µF + 1 × 100 nF on +1V1 (C15, C16), and C17 (labelled "flash", sitting between U1 and U2).
  - **Missing caps:** USB_VDD (48) and ADC_AVDD (43) have no dedicated 100 nF, and only one of the two
    DVDD pins has a 100 nF. The HDG minimal design (from memory) has 100 nF per IOVDD, DVDD,
    USB_VDD and ADC_AVDD.
  - **Distance from each pin to its nearest same-net cap**, computed from pad coordinates:
    - VREG_VOUT (45) → C15: 4.4 mm.
    - DVDD (50) → C15: 6.3 mm, with no 100 nF near it.
    - USB_VDD (48) → C17: 4.1 mm.
    - IOVDD (49) → C17: 4.3 mm.
    - IOVDD (22) → C10: 4.7 mm.
    - ADC_AVDD (43) → C13/C14: 3.3 mm.
  - The core regulator's stability depends on the VREG_VOUT 1 µF sitting close to its pin.
- **Evidence:** `parts.py` C8–C17; `.kicad_pcb` pad positions (U1 at 116, 106.6, rotated 180°).
- **Fix:**
  - Move C15 to the pin 45/50 corner.
  - Add 100 nF caps at DVDD pin 50, USB_VDD and ADC_AVDD (2–3 more 0402 parts).
  - Flag to the layout advisor.
- **Confidence:** Medium. The distances are from my pad transform, and the HDG is quoted from memory.

### D-E5: Minor (docs/process): The BOOTSEL procedure points to a poke hole the rev B case doesn't have; simpler re-flash routes exist
- **What:**
  - The PCB README step 2 says "Hold BOOTSEL (a pin through the poke hole)". The rev B case README
    says there is **no** hole: flash before fitting the top, and lift the top to re-flash.
  - SW1 itself is correct: R9 1 k from QSPI_SS to BOOT, then SW1 to GND, with R8 10 k pulling QSPI_SS
    up. That gives about 0.3 V when pressed.
  - Two facts make BOOTSEL rarely needed:
    - A factory-blank flash falls back to USB boot on its own (RP2040 bootrom, from memory), so the
      first flash needs no button.
    - Current debugprobe master exposes the RPi reset interface (`ITF_NUM_RESET`, `pico/usb_reset.h`
      in `usb_descriptors.c`), so `picotool reboot -u -f` should reboot it into the UF2 drive with no
      button. I did not check which release first shipped this.
- **Evidence:** `rev-b/pcb/README.md` "Flashing the dock"; `rev-b/case/README.md` "BOOTSEL";
  debugprobe `src/usb_descriptors.c`.
- **Fix:** Update the README: blank boards enumerate as RPI-RP2 directly; use picotool reboot for
  updates; lift the top, or use the SWD pads TP1–TP4, as the fallback. Optionally add a bottom-side
  pad on the BOOT net.
- **Confidence:** High on the doc mismatch. Medium on the picotool route (verify on hardware).

### D-E6: Note: The 1.8 V SWD level against the band's 2.0 V I/O works, and back-powering is small
- **What:**
  - Both bands run the nRF I/O at 2.0 V: band rev A uses VDD_2V0, and band rev B uses the TPS7A0220
    2.0 V LDO. 1.8 V clears VIH = 0.7 × 2.0 = 1.4 V with 0.4 V margin.
  - The band's 2.0 V high overdrives the TXS0101 A port (VCCA = 1.8 V) by 0.2 V. That is inside the
    absolute maximum but above the recommended VIH(max) = VCCA, and it pushes a few tens of µA into
    the dock's 1.8 V rail through the TXS internal pull-up.
  - When docked with the dock powered, the band's rail comes up from VIN within milliseconds. Before
    that, back-feed into the band's SWDIO is limited by the TXS A-side pull-up (about 10 k), so about
    0.1 mA.
  - When the dock is unpowered and the band sits on battery, both translators have Ioff / VCC
    isolation (TI pages). Whether the TXS internal pull-up still loads the band's SWDIO pull-up when
    VCCA = 0 is **unverified**. Measure the band's current on an unplugged dock.
  - Option: a 2.0 V regulator (XC6206P202) would match the band exactly. Its availability at JLC is
    unverified.
- **Confidence:** High on the logic levels. Medium on the leakage.

### D-E7: Note: The crystal's load caps and ESR are not matched to the Pico reference
- **What:**
  - Y1 (C2981639, Liming 3225-12-12-10-10/A) is CL 12 pF, ±10 ppm. C1/C2 are 15 pF C0G, giving
    about 7.5 pF + 3–5 pF stray ≈ 10.5–12.5 pF. That is acceptable, and the slight frequency offset
    is irrelevant for USB FS.
  - The JLC page lists no ESR. The RP2040 HDG's 1 k series resistor is sized for the Abracon
    ABM8-272-T3, so start-up margin with this crystal is unverified.
- **Fix:** Check the Liming datasheet ESR (≤ about 50–60 Ω is wanted) and verify start-up on the first
  boards. Consider 18 pF for CL = 12 pF.
- **Confidence:** Medium.

### D-E8: Note: The BOM manufacturer for U4 is wrong
- **What:** The BOM and `parts.py` say "Torex XC6206P332MR", but JLC C2897477 is a **YONGYUTAI**
  XC6206P332MR (second source, 300 mA). U5 C21659 is genuine Torex. The pinout assumed is
  1 = GND, 2 = VOUT, 3 = VIN; that is correct for the Torex part and likely for the clone, but I did
  not verify the clone's pinout.
- **Fix:** Correct the MPN field or switch to the Torex LCSC part, and confirm the clone's pinout.
- **Confidence:** High on the mismatch.

### D-E9: Note: Some regulator and protection input caps are missing or remote
- **What:**
  - U5 (1.8 V LDO) has no local input cap: the nearest +3V3 cap, C4, is about 6.6 mm away.
  - USBLC6-2SC6 pin 5 (VBUS) has no 100 nF. ST recommends one at the VBUS pin.
  - U8's VCCA and VCCB caps (C21, C20) are about 4.3–4.6 mm from its pins.
  - C3 is a 10 µF 10 V X5R 0603 (CL10A106KP8NNNC) on 5 V, so expect about 5 µF effective. Total VBUS
    capacitance stays under the USB 10 µF limit (OK).
- **Fix:** Add 100 nF caps at U5.IN and U3.5, and move C20/C21 closer to U8.
- **Confidence:** Medium (distances approximate).

### D-E10: Note: Documentation drifts from the board
- **What:**
  - The dock README says "nRF54L15" and "the band's nPM1304 does the charging". Band rev B is a
    nRF54L10 with a **BQ25125** charger.
  - `scripts/gen_sch.py` (rev B) still hard-codes the title "WakeBand dock rev A" and rev "A". The
    committed `.kicad_sch` says rev B, so it was hand-edited, and regenerating it would revert the
    title.
  - The `parts.py` docstring says rev A.
- **Confidence:** High.

### D-E11: Note: The RP2040 recovery pads have no 3.3 V reference
- **What:** TP1–TP4 are SWCLK, SWDIO, RUN and GND only. Probes that need VTref (J-Link, many
  CMSIS-DAP probes) can't sense the 3.3 V level.
- **Fix:** Add a +3V3 test pad.
- **Confidence:** High.

### D-E12: Note: The SWD clock ceiling is set by the TXS0101
- **What:** The TXS0101 is rated 24 Mbps push-pull. With 22 Ω, the spring contacts and the band's
  routing, keep SWD at ≤4 MHz: probe-rs `--speed`, pyOCD `-f`.
- **Fix:** Add the limit to the README.
- **Confidence:** Medium.

### D-E13: Note: The TXS0101 OE is tied straight to VCCA
- **What:** Power sequencing is safe, because +1V8 comes from +3V3 and so VCCA ≤ VCCB always holds.
  TI suggests a pull-down on OE for glitch-free power-up. The effect is small here.
- **Confidence:** Medium.

## Checked and OK

- **Schematic, PCB and `parts.py` parity:** all 201 pin/net assignments match in both files. There are
  no extra pads or pins, and the no-connects agree.
- **Rev A against rev B:** `parts.py` and the generators are identical, the schematic differs only in
  the title block and project name, and the PCB differs only in title-block date and company. The
  rev A `parts.py` already carries the -75 spring-pin part number.
- **RP2040 pin map (QFN-56):**
  - IOVDD on pins 1, 10, 22, 33, 42, 49; ADC_AVDD 43; VREG_VIN 44; USB_VDD 48: all on +3V3.
  - DVDD 23 and 50, and VREG_VOUT 45: on +1V1.
  - TESTEN 19 to GND; EP (57) to GND.
  - XIN 20 and XOUT 21, with R1 1 k → XOUT_X and C2 15 pF; C1 15 pF on XIN. The Y1 GND pins are 2
    and 4.
  - SWCLK 24 and SWDIO 25 go to TP1 and TP2; RUN 26 has a 10 k pull-up and TP3.
  - USB_DM 46 and DP 47 each go through 27 Ω (C25100, 1 %).
  - QSPI 51–56 to the W25Q16JVSNIQ (C2456211 confirmed as SOIC-8 150 mil): /CS 1, IO1 2, IO2 3,
    IO0 5, CLK 6, IO3 7, VCC 8. All correct.
- **debugprobe pin map:** the stock `debugprobe.uf2` (PICO_BOARD = debug_probe) uses:
  - SWCLK GPIO12, SWDI GPIO13 and SWDIO GPIO14 (PROBE_IO_SWDI mode, with GPIO14 driving through a
    resistor and GPIO13 reading the node).
  - LEDs: USB GPIO2, DAP_RUNNING GPIO16 (and DAP_CONNECTED GPIO15, which this board leaves out).
  - UART on GPIO4/5, with internal pull-ups set by the firmware, so leaving them unconnected is fine.
  - Boot stage 2: W25Q080, 2 MB flash.
  - The schematic matches (U1 pins 15, 16, 17, 4, 27), and R10 22 Ω implements the drive-through-
    resistor scheme. **No custom build is needed.** The README claim holds.
- **Translators:**
  - TXS0101DBV pinout: 1 VCCA = 1V8, 3 A = band side, 4 B = 3V3 side, 5 OE = VCCA, 6 VCCB = 3V3.
    This respects VCCA ≤ VCCB.
  - 74LVC1T45 (Diodes W6-7, SOT-26, C168856 confirmed): 1 VCCA = 3V3, 3 A, 4 B, DIR = VCCA (A→B),
    6 VCCB = 1V8. Correct.
  - Using an auto-direction part on SWDIO and a fixed-direction buffer on SWCLK is a sound choice.
    The nRF's SWDIO pull-up does not fight the TXS, and its SWCLK pull-down would fight one.
- **USB-C:**
  - 5.1 k pull-down on each of CC1 and CC2 separately (C25905).
  - D+ and D− joined A6/B6 and A7/B7; SBU left unconnected; shield to GND.
  - USBLC6-2SC6 pinout: I/O1 1/6 on D+, I/O2 3/4 on D−, VBUS 5, GND 2.
- **SY6280AAC:**
  - Pinout 1 OUT, 2 GND, 3 ISET, 4 EN, 5 IN matches the datasheet.
  - EN is active high, and tying it to VBUS_F is within the 6 V absolute maximum.
  - Reverse blocking with no body diode, plus the band's charger, means no reverse current from the
    band into the dock when USB is unplugged. The output discharges through 150 Ω.
- **F1:** 0.5 A hold, 1 A trip, 6 V (C181350): fine for USB 5 V.
- **XC6206 rails:**
  - 3.3 V load (RP2040 plus flash, about 40 mA) is well within rating, at about 0.1 W dissipation.
  - The 1.8 V LDO is fed from 3.3 V, so the sequencing suits the TXS.
- **LEDs:** red KT-0603R (Vf 1.8–2.4 V), anode on the GPIO, with 1 k to GND: about 1–1.4 mA, polarity
  correct (pin 1 = K). They may be dim through the case's 0.4 mm skin, so test that.
- **BOM/footprints:**
  - Resistor and capacitor LCSC numbers match their values and 0402/0603 packages: 27 Ω, 22 Ω, 15 k,
    15 pF C0G 50 V, 10 µF 10 V.
  - C52923 1 µF 25 V on the 5 V nets is fine.
  - TS-1088 (C720477) matches its footprint.
  - CPL rotations are not in my scope; the layout advisor covers them.
