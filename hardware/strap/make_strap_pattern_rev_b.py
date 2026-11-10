# WakeBand strap rev B: elastic edges + 5/8 in side-release buckle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import sys
out=sys.argv[1]
c=canvas.Canvas(out,pagesize=letter); c.setTitle("WakeBand strap pattern rev B (elastic edges, buckle)")
def line(x1,y1,x2,y2,dash=None,w=0.6):
    c.setLineWidth(w); c.setDash(dash) if dash else None; c.line(x1*mm,y1*mm,x2*mm,y2*mm); c.setDash()
def rect(x,y,w,h,dash=None,lw=0.8):
    c.setLineWidth(lw); c.setDash(dash) if dash else None; c.rect(x*mm,y*mm,w*mm,h*mm); c.setDash()
def txt(x,y,s,size=7,rot=0,bold=False):
    c.saveState(); c.setFont("Helvetica-Bold" if bold else "Helvetica",size); c.translate(x*mm,y*mm); c.rotate(rot); c.drawString(0,0,s); c.restoreState()
# sizes: name, mid wrist, range
SZ=[("S",150,"wrist 140-160"),("M",165,"wrist 155-175"),("L",180,"wrist 170-190")]
BUCKLE=38   # 5/8 in side-release buckle, closed length incl. bars
POD=50      # between the case's loop bars
WRAP=15     # strap length used folding round a bar
TURN=8      # raw end turned under
TAIL=45     # adjustable tail past the slider
rows=[]
for n,W,r in SZ:
    P=0.92*W-POD-BUCKLE           # strap that shows round the wrist
    a=round(0.4*P); b=round(0.6*P)
    Afin=WRAP+a+WRAP; Bfin=WRAP+b+WRAP+TAIL
    rows.append(dict(n=n,W=W,r=r,a=a,b=b,Acut=Afin+2*TURN,Bcut=Bfin+2*TURN,ea=round(0.8*a),eb=round(0.8*b)))
y0=15
txt(12,268,"WakeBand strap pattern, rev B: elastic edges + buckle (print at 100% / Actual size)",10,bold=True)
rect(150,240,50,20); txt(151,235.5,"Check: this box is 50 x 20 mm",7)
line(150,232,200.8,232,w=1); line(150,230.5,150,233.5); line(200.8,230.5,200.8,233.5); txt(151,227.5,"2 inches",7)
def piece(x,label,key,elkey,startwrap):
    top=y0+max(R[key] for R in rows)
    c.setLineWidth(0.9); c.rect(x*mm,y0*mm,40*mm,(top-y0)*mm)
    line(x+20,y0,x+20,top,dash=[6,2,1,2]); 
    line(x+4,y0,x+4,top,dash=[2,2],w=0.4); line(x+36,y0,x+36,top,dash=[2,2],w=0.4)
    line(x,y0+TURN,x+40,y0+TURN,dash=[4,2]); 
    line(x,y0+TURN+WRAP,x+40,y0+TURN+WRAP,dash=[1,1.5],w=0.9)
    txt(x+18.5,y0+26,label,7,rot=90,bold=True)
    for R in rows:
        yc=y0+R[key]; line(x-6,yc,x+40,yc,w=0.8); txt(x-11,yc-1,"cut "+R['n'],6)
        # elastic zone marks (finished coords from the case end)
        e0=y0+TURN+WRAP; e1=e0+(R['a'] if key=='Acut' else R['b'])
        line(x+40,e1,x+44,e1,w=0.6); txt(x+45,e1-1,f"{R['n']}: elastic zone ends",5.5)
    txt(x+45,y0+TURN+WRAP-1,"fold round case bar;",5.5); txt(x+45,y0+TURN+WRAP-4,"elastic zone starts",5.5)
    txt(x+45,y0+TURN-1,"turn under 8 mm",5.5)
    return top
piece(22,"A  SHORT STRAP  cut 1 (knit)","Acut","ea",True)
piece(95,"B  LONG STRAP  cut 1 (knit)","Bcut","eb",True)
txt(22,y0-6,"A: male buckle end at top. B: buckle slider end at top.  Long dash-dot = fold line (fold lengthwise, right sides in). Short dashes 4 mm in = seam line.",6)
# table
tx=160; ty=150
txt(tx,ty+12,"Cut lengths (mm)",8,bold=True)
txt(tx,ty+6,"size  A    B    elastic A  elastic B",6.5)
for i,R in enumerate(rows):
    txt(tx,ty-i*5,f"{R['n']}      {R['Acut']}   {R['Bcut']}    2 x {R['ea']}     2 x {R['eb']}",6.5)
txt(tx,ty-20,"Elastic: 1/8 in (3 mm) flat elastic,",6.5); txt(tx,ty-24,"two pieces per strap, one per edge.",6.5)
txt(tx,ty-30,"Keeper: 1/4 in elastic, 45 mm, 1 piece.",6.5)
c.showPage()
L=[("WakeBand strap rev B: elastic edges and a buckle",11,True),("",6,False),
("Materials",9,True),
("- Soft, thin knit (cotton or bamboo jersey, or nylon-spandex), about 30 x 5 cm.",8,False),
("- 1/8 in (3 mm) flat braided elastic, about 30 cm. 1/4 in elastic, 5 cm, for the keeper.",8,False),
("- One 5/8 in (16 mm) plastic side-release buckle with an adjuster bar (the low-profile 'contoured' kind is kinder at night).",8,False),
("  Alternative: a 16 mm magnetic snap clasp; then make B the same length as A plus 10 mm and skip the tail and keeper.",8,False),
("- Polyester thread, a bodkin or small safety pin for threading elastic.",8,False),
("",6,False),
("How it goes together",9,True),
("- A runs from one case loop to the buckle's male half. B runs from the other case loop, through the buckle's",8,False),
("  female half and its adjuster, and ends in a tail held by the keeper. The buckle sits under your wrist.",8,False),
("- Each strap is a 16 mm tube with a 3 mm elastic channel along both edges, so the edges gather and stretch",8,False),
("  slightly. The ends that wrap the case bars and buckle bars have no elastic, so they stay thin enough for the",8,False),
("  16.6 x 2.2 mm slots.",8,False),
("",6,False),
("Steps (same for A and B)",9,True),
("1. Print page 1 at 100%, check the 50 x 20 mm box, cut A and B at your size. Cut elastic from the table.",8,False),
("2. Fold lengthwise right sides together and sew the long edge 4 mm in (stretch or narrow zigzag stitch). Trim to 2 mm.",8,False),
("3. Turn right side out with a bodkin and press so the seam sits on one edge; the tube is now 16 mm wide.",8,False),
("4. Mark the elastic zone from page 1 (from the fold line by the case end to your size's 'elastic zone ends' mark).",8,False),
("5. Sew a line along the full length 3.5 mm in from each edge. This makes two 3 mm channels.",8,False),
("6. Thread one elastic piece into each channel. Pin its ends at the start and end of the elastic zone, so the fabric",8,False),
("   gathers evenly. Bar-tack across the channel at both ends of the zone (several back-and-forth stitches).",8,False),
("7. Turn both raw ends in 8 mm and stitch across.",8,False),
("8. A: wrap one end round a case loop bar at the fold mark and box-X stitch. Wrap the other end round the",8,False),
("   buckle's male bar the same way.",8,False),
("9. B: wrap one end round the other case loop bar and box-X stitch. Thread the other end up through the",8,False),
("   female half's adjuster, back down, and through the keeper.",8,False),
("10. Keeper: overlap the 1/4 in elastic ends by 5 mm round two layers of strap and stitch; slide it onto B.",8,False),
("",6,False),
("Fit and care",9,True),
("- Adjust so the case back sits flat on your wrist and you can slide one finger under the strap; the elastic edges",8,False),
("  take up movement during sleep. Unclip the buckle to lay the band on the dock.",8,False),
("- Test a scrap of the finished tube end through a printed loop before sewing the bar folds.",8,False),
("- Hand wash with the strap removed from the band.",8,False)]
y=262
for s,sz,b in L:
    txt(15,y,s,sz,bold=b); y-= sz*0.55+1.8
c.showPage(); c.save()
for R in rows: print(R)
