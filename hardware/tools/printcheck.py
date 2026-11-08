"""Printability check for the printed WakeBand parts (build123d / OCP; no mesh libraries needed).

For a solid in its print orientation (z up, bed at its lowest z) it reports:
  - bodies: number of solids and any tiny ones (leftover fragments);
  - overhangs: down-facing surface more than 45 degrees past vertical that is not on the bed. Flat
    down-facing faces are reported as bridges with their short span; other faces as overhang areas;
  - thin walls: sampled points at least EDGE_SKIP from their face's edges whose inward ray leaves the part
    again within MIN_WALL (0.8 mm), except where the point lies in an ALLOW box (intentional thin skins);
  - knife edges: convex edges whose two faces meet at less than KNIFE degrees (slivers, feather edges).
Faces at exactly 45 degrees (chamfers, countersinks) count as printable: the overhang limit is OVERHANG.
usage: from printcheck import check; check(name, solid, flip=False, allow=[(x0,x1,y0,y1,z0,z1), ...])
       (boxes are in the part's design frame, before any flip)"""
import math
from build123d import Axis, Location, Pos, Rot
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN
from build123d import Edge, Face, Vector

MIN_WALL, BRIDGE_MAX, SAMPLE, EDGE_SKIP, KNIFE, OVERHANG = 0.795, 5.0, 0.6, 0.6, 30.0, 47.0


def _samples(face, step):
    bb = face.bounding_box()
    n = max(2, min(40, int(max(bb.size.X, bb.size.Y, bb.size.Z) / step) + 1))
    for i in range(n):
        for j in range(n):
            u, v = (i + 0.5) / n, (j + 0.5) / n
            try:
                p = face.position_at(u, v)
                if not face.is_inside(p, tolerance=1e-4):
                    continue
                yield p, face.normal_at(u, v)
            except Exception:
                continue


def check(name, solid, flip=False, allow=(), bridge_ok=()):
    s = solid
    if flip:
        s = Rot(180, 0, 0) * s
    zmin = s.bounding_box().min.Z
    s = Pos(0, 0, -zmin) * s
    report = {"name": name, "solids": len(s.solids()), "tiny": [], "bridges": [], "overhangs": [], "thin": [], "knife": []}
    for so in s.solids():
        if so.volume < 1.0:
            report["tiny"].append(round(so.volume, 4))
    def design(p):                      # back to the design frame for the ALLOW boxes / reporting
        q = (p.X, p.Y, p.Z + zmin)
        return (q[0], -q[1], -q[2]) if flip else q
    def allowed(q, boxes):
        return any(b[0] <= q[0] <= b[1] and b[2] <= q[1] <= b[3] and b[4] <= q[2] <= b[5] for b in boxes)
    inter = IntCurvesFace_ShapeIntersector()
    inter.Load(s.wrapped, 1e-4)
    thin = []
    for f in s.faces():
        area_down = 0.0
        flat = True
        pts = list(_samples(f, SAMPLE))
        if not pts:
            continue
        edges = f.edges()
        for p, nrm in pts:
            near_edge = min(e.distance_to(p) for e in edges) < EDGE_SKIP
            # thin wall: ray from just inside the surface, against the outward normal
            o = p - nrm * 1e-3
            inter.Perform(gp_Lin(gp_Pnt(o.X, o.Y, o.Z), gp_Dir(-nrm.X, -nrm.Y, -nrm.Z)), 0.0, MIN_WALL)
            if inter.NbPnt() > 0 and not near_edge:
                d = min(inter.WParameter(k) for k in range(1, inter.NbPnt() + 1))
                q = design(p)
                if d > 0.02 and not allowed(q, allow):
                    thin.append((round(d, 2), tuple(round(c, 2) for c in q)))
            if nrm.Z < -math.sin(math.radians(OVERHANG)) and p.Z > 0.05:   # face tilted more than OVERHANG from vertical
                area_down += 1
                if nrm.Z > -0.999:
                    flat = False
        if area_down / len(pts) < 0.5:
            continue
        bb = f.bounding_box()
        c = design(bb.center())
        if flat:
            span = min(min(bb.size.X, bb.size.Y), 4 * f.area / sum(e.length for e in f.edges()))   # strip: ~2 x width, disc: diameter
            if span > BRIDGE_MAX and not allowed(c, bridge_ok):
                report["bridges"].append((round(span, 2), tuple(round(v, 2) for v in c)))
        else:
            report["overhangs"].append((round(f.area, 2), tuple(round(v, 2) for v in c)))
    # knife edges: convex edges whose faces meet at a sharp angle
    owners = {}
    for f in s.faces():
        for e in f.edges():
            owners.setdefault(e, [e, []])[1].append(f)
    cls = BRepClass3d_SolidClassifier(s.wrapped)
    for e, fl in owners.values():
        if len(fl) != 2 or e.length < 0.05:
            continue
        f1, f2 = fl
        try:
            p = e.position_at(0.5)
            n1, n2 = f1.normal_at(p), f2.normal_at(p)
        except Exception:
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, n1.dot(n2)))))   # 180 = faces folded flat onto each other
        if 180 - ang < KNIFE:
            out = p + (n1 + n2).normalized() * 0.02 if (n1 + n2).length > 1e-6 else p
            cls.Perform(gp_Pnt(out.X, out.Y, out.Z), 1e-5)
            if cls.State() != TopAbs_IN:                                    # convex: a feather of material
                q = design(p)
                if not allowed(q, allow):
                    report["knife"].append((round(180 - ang, 1), round(e.length, 2), tuple(round(c, 2) for c in q)))
    # keep one thin sample per 1 mm cell
    seen = {}
    for d, q in sorted(thin):
        k = tuple(round(v) for v in q)
        seen.setdefault(k, (d, q))
    report["thin"] = sorted(seen.values())
    return report


def show(r):
    ok = r["solids"] == 1 and not any(r[k] for k in ("tiny", "bridges", "overhangs", "thin", "knife"))
    print(f"{r['name']}: solids {r['solids']}, tiny {r['tiny']}, bridges>{BRIDGE_MAX}mm {len(r['bridges'])}, "
          f"overhang faces {len(r['overhangs'])}, thin(<{MIN_WALL}) spots {len(r['thin'])}, knife edges {len(r['knife'])} -> {'OK' if ok else 'CHECK'}")
    for k in ("bridges", "overhangs", "thin", "knife"):
        for x in r[k][:12]:
            print(f"   {k[:-1]}: {x}")
    return ok
