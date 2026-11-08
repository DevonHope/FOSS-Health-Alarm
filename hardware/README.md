# WakeBand hardware

Everything is grouped by **what it is** (band or dock), then **revision**, then **PCB or printed case**:
every revision folder carries its own `pcb/` and its own `case/` (the models to print).
Build **rev C** (rev B plus the 2026-11-08 review fixes; every part assembled by JLCPCB). Rev A and rev B are
kept unchanged for reference: a new revision always gets its own folder.

```
hardware/
├── band/                    the wristband
│   ├── rev-a/
│   │   ├── pcb/             rigid band board, ISP2454 module (rigid-rev-a.kicad_pro)
│   │   ├── case/            shell + wrist cover (print)
│   │   └── contact-carrier/ small PCB holding the 4 spring pins in the cover, + BUY-LIST.md
│   ├── rev-b/               superseded by rev C (as reviewed on 2026-11-08)
│   │   ├── pcb/             rigid band board, nRF54L10 bare chip (rigid-rev-b.kicad_pro)
│   │   ├── case/            rev B shell + wrist cover
│   │   └── contact-carrier/ same carrier as rev A
│   ├── rev-c/               rev B + 2026-11-08 review fixes: build this
│   │   ├── pcb/             rigid band board (rigid-rev-c.kicad_pro)
│   │   ├── case/            shell + wrist cover, same geometry as rev B (print)
│   │   └── contact-carrier/ same carrier as rev A and rev B
│   └── archive/flex-rev-a/  early flex-PCB design (not built)
├── dock/                    the charging / programming dock
│   ├── rev-a/
│   │   ├── pcb/             dock PCB (dock-pcb-rev-a.kicad_pro)
│   │   └── case/            dock housing rev A (superseded)
│   ├── rev-b/               superseded by rev C (as reviewed on 2026-11-08)
│   │   ├── pcb/             dock PCB, rev A circuit, stocked pins (dock-pcb-rev-b.kicad_pro)
│   │   └── case/            dock housing rev B
│   └── rev-c/               rev B + 2026-11-08 review fixes: build this
│       ├── pcb/             dock PCB with pin ESD, decoupling, no vias under paste (dock-pcb-rev-c.kicad_pro)
│       └── case/            dock housing rev C (print)
├── reviews/                 design reviews (latest: 2026-11-08, two advisors per board)
├── strap/                   strap sewing patterns
└── tools/                   printcheck.py (printability check for the printed parts)
```

## What to order and print (rev C)

| What | Where | How |
| --- | --- | --- |
| Band PCB, assembled | [`band/rev-c/pcb/fab/jlcpcb/`](band/rev-c/pcb/fab/jlcpcb) | JLCPCB Standard PCBA, 2 panels of 2 x 2 (see its README, "Ordering") |
| Contact carrier PCB | [`band/rev-c/contact-carrier/fab/`](band/rev-c/contact-carrier/fab) | bare PCB, panel of 6, 1.6 mm |
| Dock PCB, assembled | [`dock/rev-c/pcb/fab/dock-pcb-rev-c-fab.zip`](dock/rev-c/pcb/fab) | JLCPCB, top side (BOM + CPL inside the zip) |
| Spring pins, magnets, feet, glue | [`band/rev-a/contact-carrier/BUY-LIST.md`](band/rev-a/contact-carrier/BUY-LIST.md) | Mouser, Indigo |
| Band shell | [`band/rev-c/case/wakeband-case-rev-c-shell.stl`](band/rev-c/case) | PETG, top face down, no supports |
| Wrist cover | [`band/rev-c/case/wakeband-case-rev-c-cover.stl`](band/rev-c/case) | PETG, wrist face down, pause at z 1.25 mm for the magnets |
| Dock top plate and tray | [`dock/rev-c/case/`](dock/rev-c/case) (`-top.stl`, `-tray.stl`) | PETG, flat faces down, no supports |
| Strap | [`strap/`](strap) | sewing pattern PDFs |

Each folder's README has the details: firmware notes and antenna tuning (band PCB), assembly (case),
flashing the dock and programming the band (dock PCB).
