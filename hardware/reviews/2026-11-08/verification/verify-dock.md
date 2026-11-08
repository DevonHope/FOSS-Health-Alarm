# Dock PCB rev B: independent check of the 2026-11-08 review fixes

Repo state checked: HEAD c4c6c1e. The dock files are unchanged since eefb655. The baseline is 25262a1.
Method: I parsed the board, the schematic and the Gerber/drill files in Python (sexpdata, shapely,
gerbonara). Pad, track, via and zone-fill geometry was rebuilt as polygons. The scripts are in
`scratch/verify-dock/`
(pcbparse.py, geom.py, conn.py, holes.py, viapad.py, parity.py, sch.py, route.py, decap.py, drill.py,
gpaste.py, glayer.py, crt.py, pth.py, cmp.py). Nothing in the repo was changed. The working tree
already had an edit in `hardware/band/rev-b/case/README.md`, which I did not make or touch.

Sanity check of the parser: 217 track ends sit exactly on pad centres with matching nets, and
rebuilt copper vs. the Gerbers gives a symmetric difference of 0.009 / 0 / 0 / 0 mm² on F/In1/In2/B.Cu.

## 1. Claimed fixes

| Item | Result | Evidence |
| --- | --- | --- |
| No open via under paste (board) | **PASS** (with notes) | No via drill intersects any paste aperture, checked in the board and again in the Gerbers (F_Paste vs PTH.drl). The closest holes to paste: U3.4 USB_DM via (107.55,114.45) at 0.050 mm; SW1.2 GND at 0.075; U4.1/U5.1 at 0.081; C8.1 0.086; U8.2 0.087; C12/C14 0.090. These are pad-edge dog-bones: each via's annulus touches or nearly touches the pad, and the hole is tented by a mask web only 0.05–0.09 mm wide. U3 pin 5 has no via any more. |
| RP2040 EP paste windows | **PASS** | 16 windows, all inside the EP. Coverage 57.4 %, stencil webs ≥0.200 mm. All 9 EP vias (3x3 at 115/116/117 x 105.6/106.6/107.6; the review README said "four") are 0.099 mm hole-to-window and 0.024 mm annulus-to-window. The Gerber gives the same numbers. Note: the 9 vias are open (inside the EP mask opening, as F_Mask confirms), so molten solder can still reach them. That is standard, accepted practice. |
| U9 USBLC6-2SC6 pinout/nets | **PASS** | 1,6 = P_SWCLK; 3,4 = P_SWDIO; 2 = GND; 5 = VIN_BAND. This matches ST's I/O1/GND/I/O2/I/O2/VBUS/I/O1. Schematic, PCB and parts.py agree. |
| U9 "between the pins and the shifters" | **PARTIAL** | Electrically yes: it is on the pin side of R11/R12. Physically no: U9 sits at x 134.8, on the far side of the pins (x 131.5) from the shifters (x 125.6), on a branch. Routed lengths: P1→U9.1 2.01 mm, P1→R11 1.34 mm, P2→U9.3 2.01, P2→R12 1.79. ESD on the pin reaches R11 without passing U9. The 100 Ω makes this tolerable (Minor). |
| D3 SMF6.0A polarity/rating | **PASS** | D_Zener pin 1 (K) = pad 1 = VIN_BAND at (137.3,111.8); pad 2 = GND. The silkscreen cathode bar is at y 110.95, on the pad 1 side. SMF6.0A: VRWM 6.0 V, VBR ≥6.67 V vs a 5–5.25 V rail, which is sensible. The trace runs P4 → D3 (6.67 mm) → U9.5 (9.89 mm further). |
| R11/R12 = 100 Ω, R6 = 33 kΩ, R15 = 100 kΩ | **PASS** | Board values, schematic values and BOM agree (C25076, C25779, C106224). R15: pad 1 = SWCLK_3V3 (U7 pin 3, the A input; DIR = +3V3, so A→B), pad 2 = GND. Routed 2.39 mm to U7.3. 6800/33 k = 0.21 A. |
| SWDIO_DRV off the crystal | **PASS** (note) | No SWDIO_DRV copper and no foreign via anywhere near Y1 (only its own XIN/XOUT_X/GND copper plus GND vias at 117.25,99.12 and 119.35,99.05). The net now runs F.Cu pin 17 → via (117.8,102.35) → B.Cu → via (120.8,103) → R10. Note: that B.Cu run lies 0.75 mm (in plan) beside XOUT on In2 for about 2.1 mm, and In2 and B are the adjacent 0.2 mm-prepreg pair. Much weaker coupling than before, but not zero. |
| VBUS_F width | **PASS** | All 20.44 mm on In2 is 0.45 mm wide; 21.36 mm on F.Cu is 0.3 mm. See new problem N2 for the side effect. |
| RP2040 decoupling at the pins (routed copper distance) | **PASS for the claimed caps, partial overall** | Pin 45 VREG_VOUT → C15 1 µF **1.03 mm** (was 9.75). Pin 43 ADC_AVDD → C22 1.44. Pin 48 USB_VDD → C23 1.35. Pin 49 IOVDD → C23 1.75. Pin 50 DVDD → C24 1.19 (pin 23 DVDD → C16 2.08). Pin 44 VREG_VIN → C22 (100 nF) 1.84, but its 1 µF (C14) is 5.89 mm away through vias. Pins 1/10/33 → C8/C9/C10 1.3–1.5. **Pin 22 IOVDD: nearest cap C9 at 6.85 mm (not fixed). Pin 42: C13 at 4.0 mm through vias.** GND pads of the new caps sit in the F.Cu GND pour, with a GND via 0.6–0.8 mm away (C15 1.6 mm). |
| U2 flash turned, QSPI | **PASS** | U2 rotation 90 → -90, moved to (119.9,115.65). QSPI lengths SS 8.72 / SCLK 13.35 / SD0 8.33 / SD1 5.12 / SD2 4.25 / SD3 15.82 = 55.6 mm, no vias (was 26.8/3.9/4.3/18.5/16.7/3.6 = 73.8). This matches the README's "4–16 mm, 56 total". SCLK itself got longer (3.9 → 13.4 mm); harmless at these speeds. |
| Silkscreen present and on the board | **PASS with one error** | Present: 9 pin-1 dots, 3 cathode bars, P1–P4 labels, "WakeBand dock rev B". From the Gerber (clear polarity applied): 0 mm² outside the outline (≥0.56 mm from the edge), 0 mm² over mask openings (≥0.148 mm away), nothing clipped. **But the U2 pin-1 dot is stale**: it sits at (115.495,119.75), which is the old U2 pin 1 position plus 1.275 mm. The real pin 1 is now at (121.81,113.18), 9.1 mm away. `relayout.py` moved U2 but not the dot. U2 has no correct marking. (Problem N1.) |

## 2. Regressions

| Check | Result | Evidence |
| --- | --- | --- |
| Schematic vs PCB net parity (own parse) | **PASS** | Pin endpoints from the schematic's lib_symbols matched to labels: 38 nets, every pin labelled or no-connect. They equal the PCB pad nets exactly, apart from the 27 single-pin `unconnected-*` NC nets. Footprints, values and LCSC fields are the same in both. parts.py matches the PCB on every pin. 63 parts. |
| Net split / short | **PASS** | Union-find over pads, tracks, vias, PTH and saved zone fills on all four layers: 0 shorts, 0 nets split, 0 copper islands. |
| Track/via clearance < 0.1 mm | **PASS** | Minimum non-zone gap 0.109 mm (J1 shield slot annulus vs VBUS_F on In2). The others are ≥0.110 (C23 vs USB_DP_MCU 0.110, U1 EP vs +1V1 0.112, R14 vs VBUS_F 0.118, P4 vs LED_USB on In2 0.119, J1.A7 vs USB_DP 0.120, C24 vs QSPI_SD3 0.125). Zone fills are ≥0.2 mm from other nets. Inner-layer via-to-copper ≥0.2 (.dru rule). |
| Via hole-to-copper < 0.2 mm | **PASS (at the limit)** | One case at exactly 0.200 mm: the LED_ACT via at (116.4,122.7) under D2's body vs D2 pad 1 (LED_ACT_K); copper gap 0.125. Hole-to-hole minimum ≥0.25. PTH hole-to-other-net track: J1 SH slot ↔ VBUS_F 0.309 (was 0.384); see N2. |
| Off board outline | **PASS** | Copper ≥0.300 mm from the edge on all four layers (board and Gerbers). Silkscreen inside. Courtyards inside except J1, which overhangs by design (same as before). No courtyard overlaps. |
| USB D+/D- | **PASS** | USB_DP: 15.2 mm F.Cu, no vias. USB_DM: 7.1 mm F.Cu + 4.76 mm In2, through-vias to cross. Series parts: R4/R5 → U1 46/47 at 5.95/4.56 mm. Connector to MCU about 21 vs 16 mm, which is irrelevant at USB full speed. Both J1 rows joined; U3 in path. Similar to before. |
| Spring pins P1–P4 | **PASS** | (131.5,101.1) P_SWCLK, (131.5,103.3) P_SWDIO, (131.5,111.7) GND, (131.5,113.9) VIN_BAND. Unchanged from 25262a1. |

## 3. Fab package

| Check | Result | Evidence |
| --- | --- | --- |
| Zip vs `fab/gerbers` + CSVs | **PASS** | All 18 files are byte-identical; nothing missing on either side. |
| Gerbers vs board | **PASS** | KiCad 10.0.3, plotted 2026-11-08 11:20:50 (commit 11:21:13). Copper symmetric difference ≈0 on all four layers. Job file: 4 layers, 1.6 mm, 40.05 x 26.55 (outline 100–140 x 97.5–124, r 1 mm corners). |
| Drill | **PASS** | PTH: 90 vias at 0.3 mm + 4 spring pins at 0.6 mm + 4 J1 slots (0.6 x 1.7 and 0.6 x 1.2, G85). NPTH: 2 x 0.65 mm J1 pegs. Matches the board exactly. |
| BOM vs CPL vs board | **PASS** | 55 designators in each; the board's 63 minus P1–P4 and TP1–TP4. Qty column correct. Re-running `gen_bom.py` and `gen_cpl.py` into a scratch copy reproduces both CSVs byte for byte. |
| New-part rotations | **PASS (logic)** | U9 SOT-23-6: 0 + 180 = 180 (same as U3/U7/U8). D3 SOD-123F: no rule, so KiCad -90 → 270; cathode is at the top in KiCad. Check D3 and U9 in JLC's preview, as the README says. |
| LCSC numbers | **Unverified** | LCSC and JLC are blocked from this sandbox. C7519 (USBLC6-2SC6) and C25076 (100 Ω 0402) match well-known parts. C123790 (SMF6.0A), C106224 (0201 100 k) and C160831 (0201 100 nF) are in a plausible format but could not be checked. C160831 is a third new extended part; the fix log mentions only two. |

## 4. Dock case fit

| Check | Result | Evidence |
| --- | --- | --- |
| Headroom | **PASS** | PCB_TOP = 0.55 + 0.70 − 5.99 = −4.74. PLATE_Z0 = −2.05, so 2.69 mm. New parts: USBLC6 SOT-23-6 ≤1.45 mm, SMF SOD-123F about 1.1 mm, 0402 ≤0.55, 0201 ≤0.33. All have ≥1.2 mm clearance. The plate underside is flat; magnets (z −1.72…−0.22) sit inside the plate. |
| Tray stops/pads | **PASS** | Rear stops (x 102–106 / 134–138, y 96.05–97.3) and corner stops are all outside the board edge. No top-side part or courtyard overhangs y < 97.5 (U9 pads start at y 100.9). Support pads are underneath only. The pad at (102,99.5) still covers TP1 (old D-L13, unchanged, not caused by these fixes). |
| LED windows | **PASS** | `A.LEDS` (133.0,122.6) and (116.4,122.8) still match D1 and D2 exactly. The cathode bars are 1.56 mm from the window centres, outside the 1.3 mm pockets. |

## New problems

| # | Severity | Problem |
| --- | --- | --- |
| N1 | **Minor** (fix before ordering, one line) | **Stale U2 pin-1 silkscreen dot** at (115.495,119.75), 9.1 mm from U2's real pin 1 (121.81,113.18). It points at nothing (nearest pads are R3/R14), and U2 has no correct marker. Cause: `review_fixes.fix_silkscreen` placed it from the old U2 position, and `relayout.py` moved U2 afterwards. Re-run the dot with the new pin-1 position (x, y − 0.975 − 0.3 for the new rotation), then re-plot. |
| N2 | Minor | Widening VBUS_F to 0.45 mm brought the In2 track to **0.109 mm copper / 0.309 mm hole edge from J1's rear-left shield slot** (was 0.184/0.384). DRC accepts it, but it is below the 0.33 mm PTH-to-track figure in JLCPCB's capability table (please verify that figure). Fix by moving that In2 segment about 0.1 mm or necking it at the slot. |
| N3 | Minor | ESD layout: U9 is on a 2 mm branch beyond the pins rather than in the path to R11/R12. D3 is 6.7 mm of trace from P4, and U9's VBUS reference (VIN_BAND) is 16.6 mm from P4. The protection works, but the clamps are not the first thing the pin current meets. |
| N4 | Minor | Pad-edge vias with holes 0.05–0.09 mm from pasted pads, tented by very thin mask webs: U3.4 USB_DM 0.050, SW1.2 0.075, U4.1/U5.1 0.081, C8.1 0.086, U8.2 0.087, C12/C14 0.090. JLC's mask registration (about ±0.05 mm) can expose the U3.4 one. |
| N5 | Minor | Decoupling still not at every pin. IOVDD pin 22 has no cap within 6.85 mm. Pin 42 has one at 4.0 mm through vias. The VREG_VIN 1 µF (C14) is 5.9 mm away through vias; only 100 nF (C22) is close. |
| N6 | Minor | The LED_ACT via under D2's body is exactly at the 0.200 mm hole-to-copper limit to the cathode pad (0.125 mm copper). |
| N7 | Minor / Note | SWDIO_DRV's new B.Cu run sits 0.75 mm (plan) from XOUT on In2 for about 2.1 mm, on adjacent layers 0.2 mm apart, and it breaks the B.Cu GND under XOUT. Far better than before; not ideal for the 12 MHz clock. |
| N8 | Minor (docs) | Stale text. README: "Same circuit and layout as dock PCB rev A", the BOOTSEL poke hole (D-E5 still open), "XOUT about 7 mm" (actually 9.2 mm routed, 9.5 mm total), and the trace audit's "no segment under 0.3 mm" (now 42, mostly 0.01–0.03 mm pad-entry stubs). Title-block comment "Same circuit as dock PCB rev A". parts.py P4 description says "0.45 A limit" (now 0.21 A). The fix log counts 2 new extended parts; there are 3 (C160831). |
| N9 | Note | With the dock unpowered and a band docked, the band's SWDIO pull-up can back-feed VIN_BAND through U9's I/O-to-VBUS diode (µA-level). A sustained VIN-to-SWD bridge (sweat, C-E2) pushes about 30 mA through 100 Ω into the +1V8 rail. The XC6206 cannot sink that, so the rail rises toward about 3.9 V through U5's body diode, past TXS0101's VCCA ≤ VCCB rule. Probably survivable. |
| N10 | Note | Three 0201 parts (R15, C23, C24): check the JLC assembly tier supports 0201. |

**Bottom line:** every claimed fix is in the files and correct as stated: vias out of paste, U9/D3 nets and polarity, 100 Ω, 33 k, R15, crystal, VBUS_F width, C15/C22/C23/C24 at their pins, U2/QSPI, silkscreen. Board, schematic, parts.py and the fab package all agree; nothing is shorted, split or off the board; the spring pins are unchanged; and the case still fits. One small error is worth fixing before ordering: the stale U2 pin-1 dot (N1). N2 is worth a 0.1 mm nudge. Everything else is Minor or a Note.
