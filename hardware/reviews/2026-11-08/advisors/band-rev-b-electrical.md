# WakeBand band rigid rev B: electrical / schematic review (Advisor 1)

Scope: `hardware/band/rev-b/pcb/` (rigid-rev-b.kicad_sch, .kicad_pcb, wakeband.kicad_sym, wakeband.pretty, scripts/parts.py, fab/jlcpcb/bom.csv + pos.csv, scripts/nordic_ref_qfaa_0_8.kicad_pcb), README read and checked separately. Read-only; nothing in the repo was changed.

Method: parsed the schematic with sexpdata (symbol pins resolved to the net labels at their pin ends, 219 labels, 22 no-connects, no wires), parsed every PCB pad net, compared both with each other, with parts.py, with the BOM and CPL, and the nRF54L10 pin map and support parts with the pad nets of Nordic's own QFAA reference layout in the repo. Datasheet facts came from the TI BQ25125 and DRV2605L datasheets, the Johanson 2450AT18A0100001E Rev 4.0 datasheet, the IS31FL3193 pin table, a Nordic DevZone answer and a BL54L15 module datasheet (nRF54L clock pins), the nRF54L15 LFXO parameter table, and LCSC part pages for the MPN behind each LCSC number I checked. KiCad was not run. TI and LCSC PDFs could not be downloaded directly (the proxy returned 403), so I read them through a web fetcher. Where a figure could not be confirmed it is marked **unverified**.

**Bottom line:** I found nothing that would leave the board dead on arrival or impossible to program. The schematic, the PCB and the BOM/CPL agree. The nRF54L10 support circuit matches Nordic's QFAA reference part for part. The BQ25125 resistors are correct for a 60 mAh cell. The findings below are one Major (cell over-discharge path) and several Minor or Note items.

---

## Findings

### B-E1 · Major · DRV2605L on raw VBAT bypasses the BQ25125's battery cut-off (BUVLO and ship mode), so it can drain the cell to 0 V
- **What:** U501's supply pins VDD (10) and VDD/NC (6) are on VBAT, after JP201 and before the BQ25125's battery FET. When the BQ cuts PMID at BUVLO, or the user puts the band in ship mode for storage, the DRV2605L still draws its shutdown current from the cell. EN has a 2 MΩ internal pull-down, so with the nRF unpowered it sits in shutdown: **4 µA typical, 7 µA maximum** (TI datasheet, EN = 0, VDD = 3.6 V). Once BUVLO trips (3.0 V, per the README), only about 1-2 % of 60 mAh is left above 2.5 V. At 4-7 µA that is gone in roughly 1-3 weeks, and the drain carries on after that. A band left flat in a drawer, or "stored" in ship mode, will deep-discharge the cell unless the cell has its own protection board.
- **Evidence:** schematic and PCB U501 pins 6 and 10 on net VBAT. parts.py: "LRA driver ... powered from the cell". The README's power-budget and ship-mode text says "up to 4 uA ... datasheet max", but TI gives 4 µA as the typical and 7 µA as the maximum.
- **Fix (pick one):**
  1. Confirm that the 60 mAh cell has a protection circuit (PCM) that cuts off around 2.5-3.0 V, and record that in the BOM or README.
  2. Move the DRV2605L VDD to PMID, which the BQ switches off. PMID while docked is the dock's 5 V minus drops, within the 5.2 V recommended / 5.5 V absolute maximum as long as the dock stays at or below 5.2 V.
  3. Feed it through a small load switch enabled by HAPT_EN.
  
  Also correct the README figure to 4 µA typical / 7 µA maximum.
- **Confidence:** High on the circuit and the datasheet currents. Medium on the impact, because whether the cell has a PCM is unknown.

### B-E2 · Minor · The VIN TVS (SMF12A) clamps above the TS pin's 5.5 V absolute maximum; the TS divider is fed from VIN
- **What:** R207 (14 k, VIN to TS) and R208 (14.3 k) || TH201 (10 k NTC) put TS at 29.6 % of VIN at 25 °C and up to 50.5 % with the NTC cold or open. The SMF12A (LCSC C207255: Vrwm 12 V, breakdown 14.7 V, clamp 19.9 V) lets VIN reach 12-20 V before clamping. TS is rated 5.5 V absolute maximum, so it is overstressed above about 18.6 V at 25 °C and above about 11 V when cold. That is still below the BQ IN rating of 20 V, so the TS pin, not the charger input, sets the real limit. The BQ IN rating of 20 V also leaves almost no margin at the TVS's 19.9 V clamp.
- **Evidence:** U201 C3 = TS; R207 1 = VIN; D601 1 = VIN. BQ25125 absolute maximum ratings: TS 5.5 V, IN 20 V.
- **Fix:** Use a lower-voltage TVS on VIN (for example an SMF6.0A or 6.5A class part, breakdown about 6.7-7.2 V, still above the 5.55 V OVP), or add a series resistor (about 10 k) into TS. The dock delivers 5 V, so this matters only for a faulty dock or a wrong charger touched to the pads.
- **Confidence:** High on the numbers. Low likelihood in normal use.

### B-E3 · Minor · TH201 measures the board, not the cell
- **What:** The schematic description says "NTC at the cell", but TH201 is an 0402 on F.Cu at (124, 108), next to U201 (121.2, 105.4). The cell pads TP201/TP202 are on B.Cu. The TS thresholds work out to a correct JEITA window (my calculation: cold 1.6 °C, cool 10.9 °C, warm 45.5 °C, hot 60.6 °C, from 39.8 / 36 / 20.5 / 15 % of VIN), but they apply to board temperature. At 30 mA charge the board barely warms, so this is mostly fine.
- **Fix:** Accept it and correct the description, or place the NTC on the B side under the cell.
- **Confidence:** High on placement; I don't have the cell position in the case.

### B-E4 · Minor · Blue and green LEDs may be dim or dark on battery
- **What:** On battery, VLED (LS/LDO in load-switch mode) is about PMID ≈ VBAT, so 3.0-4.2 V. The 1615 RGB's blue (460 nm) and green (520 nm) chips are InGaN, typically 2.8-3.2 V at a few mA, and the IS31FL3193 sink also needs some headroom. Below a cell of about 3.4-3.5 V, blue and green will dim or go out. On the dock (PMID about 4.9 V) they are fine.
- **Evidence:** D702 1 = VLED; U201 C5 = VLED; U202 VCC = PMID.
- **Fix:** Accept it (the LED is mainly a charge indicator) and note it in the README, or use red/amber for on-battery status. I could not read the LED's Vf table (the LCSC datasheet needs JavaScript), so the exact threshold is **unverified**.
- **Confidence:** Medium.

### B-E5 · Minor · An LRA buzz on a low cell can trip BUVLO and reset the nRF mid-alarm
- **What:** The DRV2605L draws its pulse current straight from VBAT, which also feeds PMID, then the LDO, then the nRF. A 60 mAh LiPo has roughly 1-2 Ω internal resistance, so 60-100 mA of drive sags it by 0.1-0.2 V. Near a 3.1-3.2 V rest voltage that crosses BUVLO (3.0 V), the BQ cuts PMID and the nRF loses power during the wake alarm.
- **Fix:** In firmware, skip or soften the buzz when VBMON is low. Optionally lower BUVLO over I2C (2.2-3.0 V range), keeping the cell's limits in mind.
- **Confidence:** Medium (cell resistance assumed).

### B-E6 · Minor · The DRV2605L I2C pins can sit above its VDD when no cell is fitted
- **What:** TI says SDA and SCL must not exceed the DRV2605L's VDD. The bus is pulled up to VDD_2V0, which the dock powers through PMID even with no cell. Without a cell, VBAT is whatever the BQ's battery-detect cycle puts there, possibly near 0 V at times. The DRV2605L's ESD diodes then clamp the bus, and I2C to the BQ, LIS2DW12 and IS31 may fail during bring-up on the dock with no cell.
- **Fix:** Bring the board up with a cell (or a bench supply on TP201) fitted, and say so in the README. B-E1 fix 2 (DRV on PMID) removes this too.
- **Confidence:** Medium (the BAT behaviour with no cell is not characterised here).

### B-E7 · Minor · 32 MHz crystal ESR may exceed Nordic's limit (unverified)
- **What:** X2, Yangxing XL7EL89CKI-111YLC-32M (C2965582), is 2016, CL 8 pF, ±10 ppm / ±20 ppm, **ESR 80 Ω** per LCSC. Nordic's older nRF5 parts specify a 60 Ω maximum ESR at this load. I could not retrieve the nRF54L10/L15 HFXO parameter table (robots-blocked). If the nRF54L limit is also 60 Ω, start-up margin is reduced. Its tolerance is fine for BLE (±50 ppm).
- **Fix:** Check the nRF54L10 datasheet's HFXO table. If the limit is 60 Ω or below, choose a 2016 32 MHz crystal of 8 pF with 40-60 Ω ESR from JLC (or Nordic's reference part).
- **Confidence:** Low-Medium. Flagged for checking only.
- X1 (Epson X1A0000610008, C96341: 32.768 kHz, CL 9 pF, ±20 ppm, ESR 90 kΩ) is inside the nRF54L15 LFXO table (CL up to 9 pF, ESR up to 100 kΩ). OK.

### B-E8 · Minor · Stale or contradictory descriptions around the SYS buck
- **What:** The brief and the README ("leave it on", because the BQ's /CD and LSCTRL thresholds are 0.25 / 0.75 × VSYS) say the SYS buck must never be turned off. The schematic and parts.py description for L201 says "buck output unused; firmware may turn it off". The TI datasheet confirms that CD and LSCTRL VIH/VIL are 0.75 / 0.25 × VSYS. With SYS off, the nRF could not reliably drive /CD or LSCTRL.
- **Evidence:** parts.py L201 description; schematic L201 Description property.
- **Fix:** Change the L201 description to "SYS buck must stay enabled (CD/LSCTRL thresholds ref. VSYS); output unloaded".
- **Confidence:** High.

### B-E9 · Note · Antenna match: Johanson's own eval match is 3 elements with net inductance; the board starts at 0 Ω
- **What:** The Johanson 2450AT18A0100001E datasheet's eval-board match is 1.0 pF + 2.7 nH + 3.9 nH, and Johanson recommends leaving slots for a tee (series-shunt-series) network. The board has a pi network: C14 (DNP) shunt, R2 = 0 Ω series, C15 (DNP) shunt. A 3-element pi can cover most loads, so the topology is acceptable. Expect the as-built 0 Ω / DNP / DNP state to be noticeably mismatched, and a tee will not fit these pads.
- **Antenna pads:** AE1 pad 2 ("PCB_Trace" in KiCad's footprint) is unconnected. That is correct: Johanson lists terminal 2 as NC, soldered for anchoring only.
- **Fix:** None needed for spin 1; the README's tuning procedure is appropriate. Optionally swap the RSSI-method starting values to Johanson's (series about 3-4 nH, shunt about 1 pF).
- **Confidence:** High.

### B-E10 · Note · Dock pads on the skin: SWDIO sits at 2.0 V through the nRF's internal pull-up
- **What:** J601 3/4 (PAD_SWDCLK/PAD_SWDIO) reach SWDCLK/SWDIO through R601/R602 (100 Ω). The nRF54L's SWDIO has an internal pull-up and SWDCLK an internal pull-down. In sweat, the SWDIO pad leaks a few µA to the GND pad (galvanic corrosion of the ENIG pads, a little extra drain), and noise on SWDCLK can wake the debug domain. VIN carries no voltage off the dock (the BQ IN blocks reverse current; the TS divider goes to 0 V), which is good. ESD parts (TPD1E10B06 ×2, SMF12A) are present and the right way round (D601 K = VIN).
- **Fix:** None required. Keep the pads conformal or recessed, and watch idle current with a wet wrist in the bench tests.
- **Confidence:** Medium.

### B-E11 · Note · No nRESET on the dock; recovery depends on SWD CTRL-AP
- **What:** nRESET goes only to TP701, and the dock has no reset line. On the nRF54L the SWD pins are dedicated (pins 25/26), and ERASEALL through CTRL-AP works without nRESET, so a bricked image or APPROTECT can still be recovered from the dock. Docking does **not** power-cycle the nRF while a cell is fitted (PMID stays up from the cell), so "unplug to reset" doesn't exist; MR (TP203, 5-15 s hold) or TP701 are the hardware resets.
- **Fix:** None; record the recovery path in the README.
- **Confidence:** Medium-High.

### B-E12 · Note · Dock README is stale about the band's charger
- **What:** hardware/dock/rev-b/pcb/README.md, about line 81: "the band's nPM1304 does the charging (firmware sets the charge current)". Rev B uses a BQ25125 with a hardware-set 30 mA (R202). The dock's SWD shifting (74LVC1T45 for SWCLK and TXS0101 for SWDIO, 1.8 V band side) works with the band's 2.0 V I/O: the nRF's VIH is 0.7 × 2.0 = 1.4 V, below the dock's 1.8 V, and the TXS0101 accepts 2.0 V on its 1.8 V side.
- **Confidence:** High.

### B-E13 · Note · PMID / VINLS capacitance after DC-bias derating is near the minimum
- **What:** The BQ wants at least 3 µF on PMID, and VINLS at about 10 × the LS/LDO output capacitor. PMID carries C206, 10 µF 0603 X5R 25 V (C96446 = CL10A106MA8NRNC), plus C210 (1 µF 0201, 16 V) and C209 (100 nF). At about 5 V docked, the 0603 10 µF gives roughly 4-5 µF effective, which meets the 3 µF minimum. Against C208 (1 µF 0402 25 V), VINLS ends up at about 6-8 × the output capacitor, not 10 ×.
- **Fix:** Optional: make C206 a 22 µF 0603, or add a second 10 µF.
- **Confidence:** Medium (derating estimated, not taken from a curve).

---

## Checked and found OK

**Schematic, PCB and BOM parity**
- Every schematic pin's net matches the PCB pad net, for all 74 parts. No parts are missing or extra, footprints and values match, and the only extra pads are unnamed paste/thermal sub-pads.
- BOM and CPL: every part with an LCSC number is in both, with matching value and LCSC number. C14/C15 are DNP and excluded; test pads, J601 and JP201 are excluded.
- parts.py agrees with the schematic.

**nRF54L10 (U1) against Nordic's QFAA reference layout v0.8 (pad nets compared)**
- Pin names and numbers in the symbol match Nordic's footprint: VDD on 10/22/36/47/48; VSS 44 and EP 49; VSS_PA 32; DECA 43 and 33 (DECRF tied to DECA as in the reference); DECD 45; DCC 46; XC1/XC2 34/35; XL1/XL2 1/2; ANT 31; nRESET 30; SWDIO 25; SWDCLK 26.
- Support parts are identical in value and net to the reference:

| Function | Parts |
| --- | --- |
| DC/DC | L1 4.7 µH (MLZ1608M4R7WT000, confirmed) |
| DECD / DECA | C1 and C2 2.2 µF (GRM033R61A225KE47D, 10 V); FB1 120 Ω (BLM03AG121SN1D, confirmed) |
| DECA / DECRF | C12 10 nF; C5 2.2 nF |
| VDD decoupling | C3 10 µF; C4, C7, C8, C10 100 nF |
| nRESET filter | R1 1 k; C13 3.9 pF |
| RF ladder | L2 2.7 nH (LQP03HQ2N7B02D, confirmed); L3 and L4 3.5 nH (LQP03HQ3N5B02D, confirmed); C6 1.5 pF; C9 2.0 pF; C11 0.3 pF |
| Crystals | X1 and X2 pin order as in the reference; no external load caps, as in the reference |

- LCSC C44800139 is the NRF54L10-QFAA-R7 (1.7-3.6 V).
- Supply: 2.0 V ±1.5 % from the TPS7A0220 is inside 1.7-3.6 V and clears the 1.75 V POR minimum the README cites (that POR figure itself unverified).
- Crystal load capacitance: X2 at CL 8 pF and X1 at CL 9 pF fall within the internal capacitor ranges (HFXO 4-17 pF, LFXO up to 18 pF).

**nRF54L10 GPIO assignment**
- SCL on P1.04, a clock pin (Nordic: TWIM SCL must be on a clock pin; SDA can be any pin of the same port). SDA on P1.08, also a clock pin. Both are on P1, as TWIM20-22 require.
- Wake-capable inputs are on P0 or P1: PMIC_INT P1.05, DOCK_PG P1.06, ACC_INT1 P0.02, ACC_INT2 P0.01.
- LS_CTRL is on P2.02 as a plain output; P2 has no sense or wake, which is fine for an output.
- NFC pins P1.02/P1.03 are unconnected.
- No signal uses a fixed-function pin.

**BQ25125 (U201)**
- Ball map in the symbol matches the TI pin table (A1 GND, A2 IN, A3/B3 PMID, A4 SW, A5 PGND, B1/B2 BAT, B4/C4 VINLS, B5 SYS, C1 ISET, C2 ILIM, C3 TS, C5 LS/LDO, D1 IPRETERM, D2 INT, D3 RESET, D4 PG, D5 GND, E1 MR, E2 CD, E3 LSCTRL, E4 SDA, E5 SCL). The DSBGA footprint has A1 at top-left, rows A-E down and columns 1-5 across.
- ISET: R202 6.65 k gives 200 / 6.65 k = 30 mA, about 0.5 C for 60 mAh, inside the 5-300 mA / 665 Ω-39.2 kΩ range. ILIM and IPRETERM to GND select the register defaults (termination 2 mA; ILIM default unverified, but harmless at 30 mA). VBATREG defaults to 4.2 V.
- TS gives a sensible JEITA window (see B-E3), and the divider sits at 0 V off the dock.
- /CD: 900 kΩ internal pull-down, so with the nRF in reset it defaults to "charge when docked, Hi-Z on battery". In Hi-Z, the battery FET stays on and PMID stays powered (TI Table 9-10, section 9.3.19).
- /MR: internal 120 kΩ pull-up to BAT, on TP203.
- /INT and /PG are open drain, pulled up by the nRF's internal pull-ups. I2C pull-ups R203/R204 (4.7 k) go to VDD_2V0, which comes from the LDO on PMID. That rail is up whenever the BQ battery FET is on or VIN is present, so the bus is powered while the MCU sleeps.
- Input thresholds: CD and LSCTRL VIH = 0.75 × VSYS = 1.35 V against the nRF's 2.0 V output. I2C VIH = 0.75 × VPULLUP = 1.5 V. All logic pins are rated 5.5 V absolute maximum.
- Ship mode: the dock's VIN exits it, and so does MR held low when the cell is above 3.0 V (TI section 9.3.1.1). On first battery connection the part starts in active battery mode, not ship mode.
- PMID ≤ OVP (5.55 V typical) protects the TPS7A0220 (6.0 V operating) and the IS31FL3193 (6.0 V absolute maximum).
- Capacitors: SYS C205 10 µF 25 V, BAT C202 2.2 µF, IN C201 1 µF 25 V, L201 2.2 µH.

**Board start-up without a cell**
- With no cell fitted, the dock's VIN feeds PMID, then the LDO and the nRF, so the board can be programmed without a cell (but see B-E6 for I2C).

**TPS7A0220 (U203)**
- LCSC C2860934 = TPS7A0220PDQNR (2.0 V, 200 mA, 25 nA, 1.5-6 V in).
- Pin map: 1 OUT, 2 GND, 3 EN, 4 IN, with the pad to GND. The footprint numbering is counter-clockwise from top view, consistent with that map (confirmed only from memory of the DQN package).
- EN is tied to IN. C210 is on the input and C211 plus about 11 µF of rail capacitance is on the output (stable with 1 µF or more).

**IS31FL3193 (U202)**
- DFN-10 pin map matches: 1 SDB, 2 VCC, 3-5 OUT1-3, 6 GND, 7 AD, 8 SCL, 9 SDA, 10 V_BM. V_BM is left NC.
- VCC on PMID keeps the inputs (rated to VCC + 0.3 V) above the 2.0 V bus. VIH is 1.4 V. SDB has the R211 pull-down.
- AD to GND gives address 0x68 (README; exact AD-to-address mapping unverified).
- Typical application shows 1 µF + 0.1 µF on VCC; the board has 100 nF local plus the PMID bulk capacitance. Acceptable.

**DRV2605L (U501)**
- VSSOP-10 pin map is correct; pin 6 VDD/NC is tied to VDD, which is allowed.
- REG and VDD each have 1 µF as required. IN/TRIG goes to GND. EN has an internal 2 MΩ pull-down.
- VIH is 1.3 V, below the 2.0 V bus. Address 0x5A.

**LIS2DW12 (U401)**
- CS to VDD (I2C mode), SA0 to VDD (address 0x19), RES (pin 7) to GND, NC (pin 5) to GND. VDD and VDD_IO are on 2.0 V. INT1 and INT2 go to wake-capable P0 pins.

**I2C and dock interface**
- I2C addresses do not clash: 0x19, 0x5A, 0x68, 0x6A.
- Dock: VIN TVS orientation is correct. SWD has ESD diodes plus 100 Ω series resistors. The dock's 1.8 V SWD levels are compatible with the band's 2.0 V I/O.

**Antenna**
- AE1 LCSC C17430588 = Johanson 2450AT18A0100001E. Feed is pin 1; pin 2 is NC.

## Not verified
- nRF54L10 HFXO ESR limit (B-E7) and the 1.75 V POR figure.
- BUVLO and ILIM default register values.
- D702 pin order (1 A, 2 B, 3 G, 4 R) and its Vf: I could not read the LED datasheet.
- IS31FL3193 AD address mapping.
- TPS7A02 DQN pin map, which I took from memory.
- Contact-carrier spring-pin order against J601.
