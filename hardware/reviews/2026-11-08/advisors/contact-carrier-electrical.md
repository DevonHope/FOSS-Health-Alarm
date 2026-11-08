# Contact carrier review: electrical and function (Advisor 1)

Scope: the dock → carrier → band path for VIN, GND, SWDCLK and SWDIO, with band rev A and band rev B.
This review was read-only. The KiCad files were parsed with sexpdata (KiCad 10 format; kiutils 1.4.8 fails on the new `(net "name")` form).
Datasheets checked (mill-max.com, 2026-11-08): 0906-2-15-20-75-14-11-0 and 0906-4-15-20-75-14-11-0.

## Summary

**No Blockers.** The net mapping is correct end to end for both band revisions. There is no swap and no mirror error.
The findings below are about how reliable the contacts are and how well they hold up to sweat and hot-plugging. None of them is a wiring error.

## Signal trace (verified)

All boards share one frame: KiCad x/y, with each board's F side facing +z (away from the wrist).
- The band board is F up (`case_rev_a.py`: "B.Cu at BOARD_B, F.Cu up").
- The carrier is F up. Its flange sits on the top pad and its tail points down to the wrist.
- The dock PCB is F up, below the band (`dock_rev_a.py` line 37: "same x/y as the band"). Its pins are on F.

All three are seen from the same side, so no mirror is needed. All 4 contacts lie on the single column x = 131.5. Only the order in y could be swapped, and it matches:

| y | Dock PCB rev B (pin → net) | Carrier pin (label) | Band rev A J601 (B.Cu Ø1.6) | Band rev B J601 (B.Cu Ø1.6) |
|---|---|---|---|---|
| 101.1 | P1 → /P_SWCLK → R11 22R → U7 74LVC1T45 | P1 "SWDCLK" | pad 3 /dock/PAD_SWDCLK → R601 100R → SWDCLK → U1.30 (ISP2454) | pad 3 /PAD_SWDCLK → R601 100R → /SWDCLK → U1.26 (nRF54L10) |
| 103.3 | P2 → /P_SWDIO → R12 22R → U8 TXS0101 | P2 "SWDIO" | pad 4 /dock/PAD_SWDIO → R602 → SWDIO → U1.28 | pad 4 /PAD_SWDIO → R602 → /SWDIO → U1.25 |
| 111.7 | P3 → /GND | P3 "GND" | pad 2 GND | pad 2 /GND |
| 113.9 | P4 → /VIN_BAND → U6 SY6280 OUT | P4 "VIN" | pad 1 VIN → D601 SMF12A, C201, U201.21 nPM1304 | pad 1 /VIN → D601 SMF12A, C201, R207, U201.A2 BQ25125 |

- The carrier has no traces, and each pin is one continuous conductor from tail to plunger. Its net labels are cosmetic only. Its hole pattern is symmetric about y 107.5 (1.15 mm from each end, pitches 2.2 / 8.4 / 2.2). Fitting it rotated 180° (which the case README allows) therefore cannot swap nets.
- Wrong seating: turning the band 180° in the recess puts its tails at x ≈ 106.6. The dock pins at x 131.5 then press on plastic, and the keyed magnets also repel. A misplaced band makes no electrical contact; it cannot connect VIN to an SWD contact.
- The case scripts agree with the PCBs: `case_rev_a.py` has SP_X 131.5 and SP_Y (101.1, 103.3, 111.7, 113.9) with the comment "SWDCLK, SWDIO, GND, VIN". Rev B imports rev A's case values.

## Findings

### C-E1 — Major — The dock contacts a solder tail tip of about 0.43 mm. Whether it is gold or solder-coated is not controlled, and it sits wet on the skin side
- **What:** The dock's mating surface is the end face of each band pin's solder tail. It is Ø0.43 mm and protrudes only 0.15 mm below the carrier, at z 0.55 against the carrier underside at 0.70 (`case_rev_a.py` CARRIER_Z/SP_TAIL; README stack-up table). The flange is soldered "from the inside" (case README, Home build step 5). Solder that wicks through the 0.6 mm plated hole to the Ø1.4 bottom pad will likely wet the 0.15 mm stub. The dock's 20 µin gold plunger (60 g) would then mate with tin or SAC solder and flux residue. That pairing is prone to fretting corrosion, and the surface is wetted by sweat through the cone window.
- **Pressure on a tiny area:** The 60 g dock force lands on a 0.145 mm² flat. The Ø1.07 dock plunger has only about ±0.32 mm of lateral margin before its edge slides off a Ø0.43 target (0.535 − 0.215). The band's recess clearance is already ±0.3 mm (`dock_rev_a.py` REC_CLR = 0.3).
- **Window clearance:** The cone window is about Ø1.38 at z 0.55. The plunger therefore has about 0.15 mm radial clearance before it lands on the plastic cone instead of the tail. This is a geometric estimate and is unverified; it overlaps the mechanical review.
- **Datasheet:** Mill-Max gives contact resistance ≤ 20 mΩ for the pin itself, but nothing for this mating interface.
- **Evidence:** `band/rev-a/case/case_rev_a.py` lines 38-52 and 243-246; `band/rev-a/case/README.md` lines 58-70 and 211-225; the 0906 datasheets.
- **Fix, either of:**
  - Use a defined gold target. For example, a Mill-Max target or receptacle pin, or an ENIG pad on the carrier underside that the dock pin lands on, with the spring pin's tail cut flush.
  - Or require tails that are free of solder and flux. Solder from the top only, use a small amount, clean with IPA, and inspect each window under magnification before applying epoxy. Add this to Home build.
- Also enlarge the target or the lateral guidance so that ±0.3 mm of band float cannot walk off it.
- **Confidence:** medium. Solder wicking depends on how the joint is made; the tolerance figures are computed from the scripts.

### C-E2 — Major — While worn, sweat bridges carry DC bias between adjacent tails. Off the dock, SWDIO and SWDCLK sit 2.2 mm apart
- **What:** At the wrist face the Ø2.0 windows on a 2.2 mm pitch leave a 0.2 mm plastic web. Sweat will bridge SWDCLK–SWDIO and GND–VIN.
  - **Off the dock:** SWDIO is pulled up internally to VDD (2.0 V) and SWDCLK is pulled down. That puts a steady DC bias across the sweat film all night. Electrolytic corrosion or migration of the tails follows, worse if they are tin-coated (C-E1). It also adds leakage to sleep current. The case README already flags the leakage ("Sweat and leakage") but not the corrosion.
  - **On the dock:** If the band is still wet, VIN (5 V) and GND are bridged 2.2 mm apart for the whole charge, and the dock's gold plungers corrode as well.
- **Evidence:** `case_rev_a.py` WIN_D0 2.0 at a 2.2 pitch; `band/rev-a/case/README.md` lines 85-91. The Nordic pull-up/pull-down behaviour on SWD is as the README states; it is not separately verified for the nRF54L10 or ISP2454.
- **Fix, any of:**
  - Smaller windows, or a raised rib between the windows of each pair.
  - Fill the windows to tail level with a conformal elastomer, leaving only the tail face exposed.
  - In firmware, disable the SWD pull-up and pull-down off the dock (debug-port control) if the part allows it.
  - Add an "SWDIO–SWDCLK resistance with a salt bridge" check alongside the existing sleep-current test.
- **Confidence:** medium (physics is clear; magnitude unmeasured).

### C-E3 — Minor — Hot-plug order is uncontrolled: all 8 pins are the same length, so SWD can make contact before GND
- **What:** The dock and band pins have the same nominal height. The band seats on magnets and may tilt, so any contact can make first.
- **Worst case:** VIN and an SWD line connect before GND. The band's input current then returns through its MCU's SWD clamp diode into the dock driver (74LVC1T45 output low). The 100 R band resistor plus the 22 R dock resistor limit this to roughly (5 − 0.6 − 0.6)/122 ≈ 30 mA.
- **Other order:** If the band is in ship mode (rev B: PMID off), the dock's 1.8 V SWDCLK back-powers the unpowered nRF through its clamp at about 10 mA until VIN wakes the BQ25125.
- **Duration and reach:** Both events are transient (ms), and the TPD1E10B06 (6 V bidirectional) does not conduct at these levels. They could exceed the MCU's injection limit, but this is not verified against the nRF54L10 or ISP2454 datasheets.
- **Evidence:** dock /P_SWCLK → R11 22R → U7 pin 4; band R601/R602 100R; P1-P4 use the same footprint and part (0906-4, A 5.994); band pins are all 0906-2.
- **Fix, either of:**
  - Make GND first-mate and last-break. Fit a 0906 one length longer for dock P3 and adjust that pin's bore or seat depth.
  - Or raise the band series resistors to about 330 R–1 k (SWD at ≤ 4 MHz tolerates this; R × C ≈ 1 k × 15 pF = 15 ns).
- The firmware could also keep the dock SWD outputs high-Z until VIN current is seen; debugprobe does not do this today (unverified).
- **Confidence:** medium.

### C-E4 — Minor — The dock's VIN pin is always live at 5 V and sits 2.2 mm from GND on the exposed top of the dock
- **What:** U6 SY6280AAC has EN (pad 4) tied to VBUS_F (pads 4 and 5 both on /VBUS_F), so P4 carries 5 V whenever USB is plugged in, band or no band. A wet band or spilled liquid on the empty dock electrolyses the P3/P4 plungers. Current is limited: SY6280 ISET 15 k gives about 0.45 A, backed by the F1 500 mA PTC, so this is a corrosion and annoyance issue, not a safety one.
- **Evidence:** `dock-pcb-rev-b.kicad_pcb` U6 pads, R6 15k, F1; dock README "Power notes".
- **Fix:** Drive the SY6280 EN from an RP2040 GPIO and enable VIN only when a band is detected. Detection could be an SWD line read, or a weak pull on the band side seen at the dock. Alternatively, accept and document it.
- **Confidence:** high (wiring), low (practical impact).

### C-E5 — Minor — The ESD and TVS parts are 13-20 mm of trace away from the contact pads
- **What:** The data TVS diodes and the VIN TVS sit along the bottom edge, while the landing pads are at x 131.5:
  - rev A: D602 at (118.75, 114.1), D603 at (116.25, 114.1), D601 at (122.5, 113.6)
  - rev B: D602 at (118.75, 111), D603 at (116.25, 111), D601 at (121, 113.8)
  - Route lengths per the rev A README: SWDCLK 27.3 mm, SWDIO 41.9 mm and VIN 23.8 mm in total. The TVS sits part-way along.
- **Effect:** The trace inductance of roughly 10-20 nH ahead of the TVS weakens clamping of fast skin-side ESD. The 100 R series resistors and the MCU's own ESD protection help.
- **Fix:** For a later revision, place the TVS parts next to J601 on F, directly above the pads. No change is needed for rev A or B bring-up.
- **Confidence:** medium.

### C-E6 — Minor — The footprint pad (Ø1.4) is smaller than the pin flange (Ø1.83)
- **What:** The flange covers the whole top pad, so no visible fillet can form. Solder must wick under the flange.
- **Electrical effect:** None. The pin is one conductor from tail to plunger, and the carrier joint only holds it in place.
- **Risk:** The flange-to-flange air gap between neighbours is only 0.37 mm (2.2 − 1.83). Hand soldering with flux on PETG can bridge VIN–GND or SWDCLK–SWDIO.
- **Datasheet hole:** The 0906 datasheet lists the mounting hole as 0.020" (0.51 mm); note 12 says the hole should be at least the tail diameter + 0.004". The 0.6 mm hole is fine for soldering, but it is not the catalogue figure.
- **Evidence:** `contact-carrier.pretty/SpringPin_Mill-Max_0906_PTH_D1.4mm_Drill0.6mm.kicad_mod`; Gerbers show F/B copper as C1.400 and mask as C1.500; datasheet.
- **Fix:**
  - Add a short check to Home build step 10: measure each adjacent pair from the window tails (VIN–GND, SWDIO–SWDCLK). A short should read > 1 MΩ before epoxy goes on.
  - Optionally cut the pad to about Ø1.2 so solder stays under the flange.
  - Leave the footprint's mechanical fit to the manufacturing review.
- **Confidence:** high (geometry).

### C-E7 — Note — The carrier finish documents disagree
- `BUY-LIST.md` says "lead-free HASL or ENIG … HASL is fine here: the carrier pads are only soldered to, nothing presses on them."
- The carrier README and the case README parts table say ENIG.
- Electrically, HASL is fine only if the dock never touches pad or solder (see C-E1). With HASL there is more solder near the tail stub.
- **Fix:** Pick ENIG everywhere, or reword the buy list.
- **Confidence:** high.

### C-E8 — Note — The rev B VIN TVS has little clamp margin (outside the carrier)
- The SMF12A clamps at 19.9 V at 10 A. The rev A README checked it against the nPM1304's 22 V absolute maximum.
- Rev B uses a BQ25125. Its IN absolute maximum is thought to be about 20 V; this was not checked in this review.
- **Fix:** Confirm against the BQ25125 datasheet. Consider an SMF10A or a lower-clamp part.
- **Confidence:** low (unverified).

## Checked and OK
- **Rev A vs rev B carrier copies:** `rev-b/contact-carrier` is byte-identical to rev A for the board, the panel, the `.pretty` folder and `fab/` (diff -r and cmp). The only differences are the README, missing `.kicad_prl` files and no BUY-LIST, which the rev B README points to.
- **Net order:** VIN, GND, SWDCLK and SWDIO are in the same order and at the same coordinates on:
  - the carrier, panel (all 6 copies: P1-P24 at x 131.5 / 138.7 / … / 167.5, same y order)
  - band rev A J601 1-4
  - band rev B J601 1-4
  - dock PCB rev B P1-P4
  - case scripts (SP_X, SP_Y)
  - the case README table
- **Gerbers:** The PTH drill files list 4 (single) and 24 (panel) holes of 0.600 mm at the right positions, and the NPTH file is empty. F/B copper are C1.4 and mask is C1.5. The zips are byte-identical to the loose Gerber folders.
- **Layout:** VIN is adjacent only to GND; the nearest SWD contact is 10.6 mm away. A sweat or object short at VIN can only reach GND, and that is current-limited at the dock.
- **Current-limit chain:** USB → F1 FSMD050 PTC → U6 SY6280 (Rset 15 k, about 0.45 A) → P4. The band also has a VIN TVS (SMF12A) and a 1 µF input capacitor.
- **Current rating:** The 0906 is rated 6.5 A (30 °C rise) / 5.2 A derated. The worst-case path is two pins in series at about 40 mΩ plus two interfaces. Charge current is 30 mA (rev A nPM1304 set by firmware; rev B BQ25125 R202 6.65 k, ILIM 100 mA), and the dock limit is 0.45 A. The margin is very large, and the drop at 30 mA is a few mV. VIN traces are 0.3 mm on both band revisions and on the dock.
- **SWD signal integrity:**
  - The series path is 22 R (dock) + 100 R (band) plus ≤ 0.1 Ω of contacts. Contact resistance is negligible, and the RC with a TPD1E10B06 (~12 pF) plus the pin is about 2 ns.
  - Levels: 1.8 V from the dock against the band's 2.0 V I/O exceeds 0.7 × VDD = 1.4 V. The direction scheme (74LVC1T45 on CLK, TXS0101 on DIO) suits SWD.
  - The real risk to the signals is intermittent contact (C-E1), not resistance.
- **Parts and stroke:**
  - BUY-LIST, the carrier README and the case README all agree on 4 × 0906-2-15-20-75-14-11-0 per band. The dock README and BUY-LIST agree on 4 × 0906-4-15-20-75-14-11-0.
  - The datasheets confirm A = 5.004 / 5.994 mm, a 1.397 mm stroke, flange Ø1.829 / 0.406, body Ø1.499 × 2.286 (so SP_BODY_L 2.69 is correct), plunger Ø1.067, tail Ø0.432 × 1.753, 60 g at mid-stroke, and 20 µin gold on shell and plunger.
  - Band-side compression is 0.60 mm and dock-side 0.70 mm, both within the stroke.
- **Band ESD:** There is one TVS per contact line (D601 VIN, D602/D603 SWD), and the GND contact has a via into the GND pour (rev A README).
