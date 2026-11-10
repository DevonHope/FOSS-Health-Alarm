from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import sys
out=sys.argv[1]
c=canvas.Canvas(out,pagesize=letter)
c.setTitle("WakeBand strap pattern rev A")
W,H=letter
SIZES=[("S",180,"wrist 135-160 mm"),("M",195,"wrist 150-175 mm"),("L",210,"wrist 165-190 mm")]
y0=12  # bottom cut edge of backing (mm)
def line(x1,y1,x2,y2,dash=None,w=0.6):
    c.setLineWidth(w); c.setDash(*(dash or [])); c.line(x1*mm,y1*mm,x2*mm,y2*mm); c.setDash()
def rect(x,y,w,h,dash=None,lw=0.8):
    c.setLineWidth(lw); c.setDash(*(dash or [])); c.rect(x*mm,y*mm,w*mm,h*mm); c.setDash()
def txt(x,y,s,size=7,rot=0,bold=False):
    c.saveState(); c.setFont("Helvetica-Bold" if bold else "Helvetica",size); c.translate(x*mm,y*mm); c.rotate(rot); c.drawString(0,0,s); c.restoreState()
# ---- page 1: pieces at 1:1
txt(12,268,"WakeBand strap pattern, rev A  (print at 100% / Actual size, no scaling)",10,bold=True)
# calibration
rect(150,240,50,20); txt(151,235.5,"Check: this box is 50 x 20 mm",7)
line(150,232,150+50.8,232,w=1); line(150,230.5,150,233.5); line(200.8,230.5,200.8,233.5); txt(151,227.5,"2 inches",7)
# piece A: backing
xa=20; wa=24
top=max(L for _,L,_ in SIZES)+20+y0
c.setLineWidth(0.9); c.rect(xa*mm,y0*mm,wa*mm,(top-y0)*mm)
txt(xa+wa/2-1.5,y0+60,"A  BACKING (soft fabric)  cut 1   grain along length",8,rot=90,bold=True)
line(xa+4,y0,xa+4,top,dash=[2,2]); line(xa+wa-4,y0,xa+wa-4,top,dash=[2,2])
txt(xa+wa+1,y0+3,"fold lines: wrap 4 mm over tape edges",6)
line(xa,y0+10,xa+wa,y0+10,dash=[4,2]); txt(xa+wa+1,y0+9,"turn under 10 mm (anchor end)",6)
line(xa,y0+30,xa+wa,y0+30,dash=[1,1.5],w=0.9); txt(xa+wa+1,y0+29,"FOLD around loop bar A here; box-X stitch below",6)
for name,L,desc in SIZES:
    fin=y0+10+L; cut=fin+10
    line(xa-6,cut,xa+wa,cut,w=0.8); txt(xa-11,cut-1,f"cut {name}",6)
    line(xa,fin,xa+wa,fin,dash=[4,2]); 
    rect(xa+4,fin-3-35,16,35,dash=[1,1],lw=0.4); txt(xa+wa+1,fin-4,f"{name}: hook tab C top",5.5)
txt(xa+wa+1,y0+150,"TIP END: cut at your size, turn under 10 mm",6)
txt(xa+wa+1,y0+146,"(dashed line). Dotted box = hook tab C,",6)
txt(xa+wa+1,y0+142,"sewn on this backing side, 3 mm from tip.",6)
# piece B: loop tape
xb=100; wb=16
for i,(name,L,desc) in enumerate(SIZES):
    pass
Lmax=max(L for _,L,_ in SIZES)
rect(xb,y0+10,wb,Lmax,lw=0.9)
txt(xb+wb/2-1.5,y0+60,"B  LOOP TAPE 16 mm (5/8 in), soft side out  cut 1",8,rot=90,bold=True)
for name,L,desc in SIZES:
    yy=y0+10+L; line(xb,yy,xb+wb+5,yy,w=0.8); txt(xb+wb+6,yy-1,f"cut {name}",6)
# piece C: hook tab
xc=138
rect(xc,y0+10,16,35,lw=0.9); txt(xc+18,y0+25,"C  HOOK TAPE 16 x 35 mm",8,bold=True); txt(xc+18,y0+21,"cut 1, round all corners (r 4 mm)",6)
# corner template
c.setLineWidth(0.8); p=c.beginPath(); x=xc; y=y0+60
p.moveTo(x*mm,y*mm); p.lineTo(x*mm,(y+16)*mm); p.lineTo((x+16-8)*mm,(y+16)*mm)
p.arcTo((x+16-16)*mm,(y+16-16)*mm,(x+16)*mm,(y+16)*mm,startAng=90,extent=-90)
p.lineTo((x+16)*mm,y*mm); p.close(); c.drawPath(p)
txt(xc+18,y0+70,"D  TIP TEMPLATE (r 8 mm)",8,bold=True); txt(xc+18,y0+66,"optional: round the tip of A and B together",6)
# sizes legend
yy=y0+110
txt(xc,yy+16,"Sizes (finished strap length):",8,bold=True)
for i,(name,L,desc) in enumerate(SIZES):
    txt(xc,yy+10-5*i,f"{name}: {L} mm   {desc}",7)
txt(xc,yy-12,"Measure your wrist snugly where you'll wear it.",7)
txt(xc,yy-16,"Between sizes: pick the larger one.",7)
c.showPage()
# ---- page 2: instructions
lines=[("WakeBand strap: materials and steps",11,True),("",7,False),
("Materials",9,True),
("- 16 mm (5/8 in) sew-on hook-and-loop tape: loop (soft) side about 25 cm, hook side 4 cm. Pick the thin, soft 'sew-on' kind, not adhesive.",8,False),
("- Soft, thin, breathable fabric for the backing (cotton or bamboo jersey, or thin brushed nylon), about 26 x 4 cm.",8,False),
("- Polyester thread, a fabric marker, sharp scissors, a lighter for synthetic edges.",8,False),
("",7,False),
("Why this shape",9,True),
("- The strap attaches only at the case's two end loops and never runs under the case, so the charging contacts stay",8,False),
("  clear and the motor sits directly on your skin. The finished strap must stay 16 mm wide and under 2 mm thick to",8,False),
("  fit the 16.6 x 2.2 mm slots. Aim for 1 mm or less: two layers pass a slot at the bar folds. Test a scrap",8,False),
("  through a printed loop before you sew the whole strap.",8,False),
("",7,False),
("Steps",9,True),
("1. Print page 1 at 100% (Actual size). Check the 50 x 20 mm box with a ruler.",8,False),
("2. Cut piece A from fabric, piece B from loop tape, piece C from hook tape, at your size's cut lines.",8,False),
("3. Seal cut ends of the synthetic tapes with a quick pass of a lighter flame (don't melt the soft face).",8,False),
("4. Lay B on A, soft side up, centred between A's fold lines, its anchor end on A's 'turn under' line.",8,False),
("5. Fold A's 4 mm edges over B's edges, pin or clip, and topstitch each side about 1.5 mm from the edge.",8,False),
("   Use a long stitch (3 mm) and a walking foot or tissue paper if the tape drags.",8,False),
("6. Turn both ends of A under 10 mm (over B's ends) and stitch across.",8,False),
("7. Sew C (hook) onto the BACKING side at the tip, 3 mm from the end, inside the dotted box. Stitch all the way round.",8,False),
("8. Anchor end: thread it through case loop A (either end of the case), fold it back onto the soft side at the 'fold' line,",8,False),
("   and sew a box with an X through both layers (about 14 x 14 mm). Do this before you seal the case if the",8,False),
("   bar is hard to reach, or sew it with the case already assembled; the slot is open.",8,False),
("9. To wear: wrap around your wrist, pass the tip through the other loop, fold it back and press the hook onto the soft side.",8,False),
("",7,False),
("Fit",9,True),
("- Snug, so the case back touches your wrist, but loose enough to slide one finger under the strap.",8,False),
("- The hook tab only touches the soft side when folded back, so it never scratches you.",8,False),
("- Hand wash the strap; remove it from the band first.",8,False),
("",7,False),
("Variations",9,True),
("- Stretchier: use 16 mm soft elastic for B and a short sewn-on loop patch where the hook lands.",8,False),
("- Quick, no-sew: 5/8 in VELCRO ONE-WRAP strap cut to length, ends sealed, looped the same way.",8,False),
]
y=262
for s,sz,b in lines:
    txt(15,y,s,sz,bold=b); y-= sz*0.55+1.8
c.showPage(); c.save()
