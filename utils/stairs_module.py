# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Stairs from a plan sketch. Pure numpy, no bpy, so it can be tested outside Blender.

The sketch is read in plan (XY), Z comes from the two levels:

    boundaries   two polylines, the sides of the flight, sorted by the user
    risers       riser lines in plan; each connected chain of edges is one riser,
                 a single edge is a straight riser. The top one is the landing edge.
    path         the walking line, first vertex at the bottom, last at the top.
                 It orders the risers and the goings are measured along it.

N riser lines give N risers and N - 1 treads; the last riser steps up onto the landing.
"""

import math
from dataclasses import dataclass, field

import numpy as np


class StairError(ValueError):
    pass


EPS = 1e-9

# rule of thumb limits in metres: (rise min, rise max, going min, 2R+G min, 2R+G max)
STANDARDS = {
    'PRIVATE': (0.150, 0.220, 0.220, 0.550, 0.700),
    'PUBLIC': (0.150, 0.170, 0.280, 0.550, 0.700),
    'NONE': None,
}


# --------------------------------------------------------------------------- polylines (2D)

def as_xy(points):
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        raise StairError("a polyline needs at least two vertices")
    return pts[:, :2].copy()


def cumulative(poly):
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(seg)])


def point_at(poly, t):
    """point at arc length t (clamped to the polyline)"""
    cum = cumulative(poly)
    t = min(max(t, 0.0), cum[-1])
    i = min(np.searchsorted(cum, t, side='right') - 1, len(poly) - 2)
    span = cum[i + 1] - cum[i]
    f = 0.0 if span < EPS else (t - cum[i]) / span
    return poly[i] + f * (poly[i + 1] - poly[i])


def direction_at(poly, t):
    cum = cumulative(poly)
    i = min(max(np.searchsorted(cum, t, side='right') - 1, 0), len(poly) - 2)
    d = poly[i + 1] - poly[i]
    return d / (np.linalg.norm(d) or 1.0)


def interior(poly, t0, t1):
    """the polyline's own vertices strictly between arc lengths t0 and t1, in t0 -> t1 order"""
    cum = cumulative(poly)
    lo, hi = min(t0, t1), max(t0, t1)
    idx = [i for i in range(len(poly)) if lo + 1e-7 < cum[i] < hi - 1e-7]
    pts = [poly[i] for i in idx]
    return pts if t0 <= t1 else pts[::-1]


def sub_polyline(poly, t0, t1):
    return [point_at(poly, t0)] + interior(poly, t0, t1) + [point_at(poly, t1)]


def intersections(a, b):
    """all crossings of polylines a and b as (arc length on a, arc length on b, point)"""
    ca, cb = cumulative(a), cumulative(b)
    hits = []
    for i in range(len(a) - 1):
        p, r = a[i], a[i + 1] - a[i]
        for j in range(len(b) - 1):
            q, s = b[j], b[j + 1] - b[j]
            den = r[0] * s[1] - r[1] * s[0]
            if abs(den) < EPS:
                continue
            qp = q - p
            u = (qp[0] * s[1] - qp[1] * s[0]) / den
            v = (qp[0] * r[1] - qp[1] * r[0]) / den
            if -1e-9 <= u <= 1 + 1e-9 and -1e-9 <= v <= 1 + 1e-9:
                hits.append((ca[i] + u * (ca[i + 1] - ca[i]), cb[j] + v * (cb[j + 1] - cb[j]), p + u * r))
    # a crossing exactly on a shared vertex shows up twice
    out = []
    for h in sorted(hits, key=lambda h: h[0]):
        if not out or abs(out[-1][0] - h[0]) > 1e-7 or abs(out[-1][1] - h[1]) > 1e-7:
            out.append(h)
    return out


def extend(poly, d):
    """lengthen both end segments by d"""
    d0 = poly[0] - poly[1]
    d1 = poly[-1] - poly[-2]
    d0 = d0 / (np.linalg.norm(d0) or 1.0)
    d1 = d1 / (np.linalg.norm(d1) or 1.0)
    return np.vstack([poly[0] + d * d0, poly, poly[-1] + d * d1])


def offset(poly, d):
    """shift a polyline sideways by d (positive = to the left of its direction), mitred corners"""
    seg = np.diff(poly, axis=0)
    seg = seg / np.maximum(np.linalg.norm(seg, axis=1)[:, None], EPS)
    nrm = np.stack([-seg[:, 1], seg[:, 0]], axis=1)
    out = []
    for k in range(len(poly)):
        if k == 0:
            n = nrm[0]
        elif k == len(poly) - 1:
            n = nrm[-1]
        else:
            m = nrm[k - 1] + nrm[k]
            ln = np.linalg.norm(m)
            if ln < EPS:
                n = nrm[k]
            else:
                m = m / ln
                n = m / max(float(np.dot(m, nrm[k])), 0.25)
        out.append(poly[k] + d * n)
    return np.array(out)


def signed_area(ring):
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


# --------------------------------------------------------------------------- risers

def chains(verts, edges):
    """split riser edges into ordered vertex chains, one per riser"""
    verts = np.asarray(verts, dtype=float)
    adj = {}
    for e in edges:
        a, b = int(e[0]), int(e[1])
        if a == b:
            continue
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen, out = set(), []
    for start in sorted(adj):
        if start in seen:
            continue
        comp, stack = set(), [start]
        while stack:
            v = stack.pop()
            if v in comp:
                continue
            comp.add(v)
            stack.extend(adj[v] - comp)
        seen |= comp
        ends = [v for v in comp if len(adj[v]) == 1]
        if any(len(adj[v]) > 2 for v in comp) or len(ends) != 2:
            raise StairError(f"riser through vertex {start} branches or is closed, each riser must be an open chain")
        order, prev, v = [], None, min(ends)
        while v is not None:
            order.append(v)
            nxt = [w for w in adj[v] if w != prev]
            prev, v = v, (nxt[0] if nxt else None)
        out.append(verts[order][:, :2])
    if not out:
        raise StairError("no riser edges")
    return out


@dataclass
class Chord:
    """a riser line trimmed to the two boundaries, running from boundary A to boundary B"""
    pts: np.ndarray
    ta: float          # arc length of its A end along boundary A
    tb: float          # arc length of its B end along boundary B
    s: float = 0.0     # arc length along the path where the path crosses it


def _nearest_hit(hits, lo, hi):
    def gap(h):
        t = h[0]
        return 0.0 if lo <= t <= hi else min(abs(t - lo), abs(t - hi))
    return min(hits, key=gap)


def trim(line, a, b, reach, label="riser"):
    """extend or cut a sketched line so it runs exactly from boundary a to boundary b"""
    ext = extend(line, reach)
    lo, hi = reach, reach + cumulative(line)[-1]
    ha, hb = intersections(ext, a), intersections(ext, b)
    if not ha or not hb:
        raise StairError(f"{label} does not reach both boundaries")
    # the end nearest boundary A is cut against A, the other against B
    da = min(np.linalg.norm(line[0] - point_at(a, h[1])) for h in ha)
    db = min(np.linalg.norm(line[0] - point_at(b, h[1])) for h in hb)
    start_on_a = da <= db
    near_lo = lambda hits: min(hits, key=lambda h: abs(h[0] - lo) if h[0] <= hi else 1e18)
    near_hi = lambda hits: min(hits, key=lambda h: abs(h[0] - hi) if h[0] >= lo else 1e18)
    if start_on_a:
        hit_a, hit_b = near_lo(ha), near_hi(hb)
    else:
        hit_a, hit_b = near_hi(ha), near_lo(hb)
    if abs(hit_a[0] - hit_b[0]) < 1e-9:
        raise StairError(f"{label} touches both boundaries in one point")
    pts = np.array(sub_polyline(ext, hit_a[0], hit_b[0]))
    return Chord(pts, hit_a[1], hit_b[1])


def retrim(chord_pts, a, b, reach, original):
    """
    move only the two end points back onto the boundaries, keeping the vertex count.
    an end that finds no boundary (a riser line ending in a boundary corner) stays where the
    original riser line ended, so the offset pinches into that corner.
    """
    ext = extend(chord_pts, reach)
    first = np.array([ext[0], ext[2]])
    last = np.array([ext[-3], ext[-1]])
    ha, hb = intersections(first, a), intersections(last, b)
    pts = chord_pts.copy()
    if ha:
        hit = min(ha, key=lambda h: abs(h[0] - reach))
        pts[0], ta = hit[2], hit[1]
    else:
        pts[0], ta = original.pts[0], original.ta
    if hb:
        l_last = cumulative(last)[-1]
        hit = min(hb, key=lambda h: abs(h[0] - (l_last - reach)))
        pts[-1], tb = hit[2], hit[1]
    else:
        pts[-1], tb = original.pts[-1], original.tb
    return Chord(pts, ta, tb, original.s)


# --------------------------------------------------------------------------- the flight

@dataclass
class Flight:
    a: np.ndarray
    b: np.ndarray
    path: np.ndarray
    chords: list
    z0: float
    rise: float
    up: float                      # offset sign that moves a riser line towards the top
    reach: float
    landing: bool                  # the boundaries carry on past the top riser
    messages: list = field(default_factory=list)

    @property
    def n_risers(self):
        return len(self.chords)

    def z(self, k):
        return self.z0 + k * self.rise

    @property
    def goings(self):
        return [self.chords[i + 1].s - self.chords[i].s for i in range(len(self.chords) - 1)]

    def shifted(self, chord, d):
        """the riser line moved d towards the top (negative: towards the bottom)"""
        if abs(d) < EPS:
            return chord
        return retrim(offset(chord.pts, self.up * d), self.a, self.b, self.reach, chord)


def build_flight(boundaries, riser_verts, riser_edges, path, level_start, level_end):
    if len(boundaries) != 2:
        raise StairError("Boundaries needs exactly two vertex lists, one per side")
    a, b = as_xy(boundaries[0]), as_xy(boundaries[1])
    path = as_xy(path)
    lines = chains(riser_verts, riser_edges)
    if len(lines) < 2:
        raise StairError("at least two riser lines are needed")
    span = np.ptp(np.vstack([a, b, path] + lines), axis=0).max()
    reach = 10.0 * max(span, 1.0)

    chords = []
    for i, line in enumerate(lines):
        chord = trim(line, a, b, reach, f"riser {i}")
        hits = intersections(chord.pts, path)
        if not hits:
            raise StairError(f"the path does not cross riser {i}")
        if len(hits) > 1:
            raise StairError(f"the path crosses riser {i} more than once")
        chord.s = hits[0][1]
        chords.append(chord)
    chords.sort(key=lambda c: c.s)
    for i in range(len(chords) - 1):
        if chords[i + 1].s - chords[i].s < 1e-6:
            raise StairError(f"risers {i} and {i + 1} cross the path at the same spot")

    for side, key in (("A", "ta"), ("B", "tb")):
        ts = [getattr(c, key) for c in chords]
        d = np.diff(ts)
        # equal is fine: winders may fan out from one point on the inner boundary
        if not ((np.all(d > -1e-9) or np.all(d < 1e-9)) and abs(ts[-1] - ts[0]) > 1e-9):
            raise StairError(f"riser lines cross each other or boundary {side} doubles back")

    # which side of a riser line is uphill
    c0 = chords[0]
    mid = len(c0.pts) // 2
    seg = c0.pts[min(mid, len(c0.pts) - 1)] - c0.pts[max(mid - 1, 0)]
    left = np.array([-seg[1], seg[0]])
    up = 1.0 if float(np.dot(left, direction_at(path, c0.s))) > 0 else -1.0

    total = float(level_end) - float(level_start)
    if total <= 0:
        raise StairError("Level End must be above Level Start")

    last = chords[-1]
    landing = (cumulative(a)[-1] - last.ta > 1e-6 and cumulative(b)[-1] - last.tb > 1e-6
               if chords[0].ta < last.ta and chords[0].tb < last.tb else False)

    return Flight(a, b, path, chords, float(level_start), total / len(chords), up, reach, landing)


def check(flight, standard):
    """plain language notes when the flight falls outside the chosen limits"""
    limits = STANDARDS.get(standard)
    if not limits:
        return []
    rmin, rmax, gmin, pmin, pmax = limits
    notes = []
    total = flight.rise * flight.n_risers
    r = flight.rise
    if r > rmax + 1e-9:
        need = math.ceil(total / rmax - 1e-9)
        notes.append(f"rise {r * 1000:.0f} mm is steep: {need - flight.n_risers} more riser(s) reach Level End at {rmax * 1000:.0f} mm max")
    elif r < rmin - 1e-9:
        fit = max(int(total / rmin + 1e-9), 1)
        notes.append(f"rise {r * 1000:.0f} mm is shallow: {flight.n_risers - fit} fewer riser(s) give at least {rmin * 1000:.0f} mm")
    goings = flight.goings
    short = [i for i, g in enumerate(goings) if g < gmin - 1e-9]
    if short:
        notes.append(f"going under {gmin * 1000:.0f} mm on tread {', '.join(map(str, short[:5]))}{'...' if len(short) > 5 else ''}"
                     f" (smallest {min(goings) * 1000:.0f} mm)")
    off = [i for i, g in enumerate(goings) if not pmin - 1e-9 <= 2 * r + g <= pmax + 1e-9]
    if off and not short and not notes:
        notes.append(f"2R+G outside {pmin * 1000:.0f}-{pmax * 1000:.0f} mm on tread {', '.join(map(str, off[:5]))}{'...' if len(off) > 5 else ''}")
    return notes


# --------------------------------------------------------------------------- plan regions

def _drop_repeats(ring, tags):
    """merge repeated points; a front end meeting a back end becomes ('both', None)"""
    keep, out_tags = [], []
    for k in range(len(ring)):
        if np.linalg.norm(ring[k] - ring[k - 1]) > 1e-9:
            keep.append(k)
            out_tags.append(tags[k])
        elif out_tags or k == 0:
            j = len(out_tags) - 1 if out_tags else None
            if j is None:
                continue  # k == 0 repeats the last point, merged when that one is reached
            if {out_tags[j][0], tags[k][0]} == {'front', 'back'}:
                out_tags[j] = ('both', None)
    if len(ring) and np.linalg.norm(ring[0] - ring[-1]) <= 1e-9 and keep and keep[0] == 0:
        pass
    elif len(ring) and np.linalg.norm(ring[0] - ring[-1]) <= 1e-9:
        # point 0 was dropped as a repeat of the last point: fold its tag into the last kept one
        if {out_tags[-1][0], tags[0][0]} == {'front', 'back'}:
            out_tags[-1] = ('both', None)
    return ring[keep], out_tags


def region(flight, front, back, merge=True):
    """
    closed plan outline between two trimmed riser lines, counter clockwise seen from above.
    returns (ring (n, 2), tags) where a tag is ('front', k), ('back', k) or ('side', None).
    merge drops repeated points, where winders meet in one point on a boundary.
    """
    pts, tags = [], []
    for k, p in enumerate(front.pts):
        pts.append(p); tags.append(('front', k))
    for p in interior(flight.b, front.tb, back.tb):
        pts.append(p); tags.append(('side', None))
    for k in range(len(back.pts) - 1, -1, -1):
        pts.append(back.pts[k]); tags.append(('back', k))
    for p in interior(flight.a, back.ta, front.ta):
        pts.append(p); tags.append(('side', None))
    ring = np.array(pts)
    if signed_area(ring) < 0:
        ring, tags = ring[::-1].copy(), tags[::-1]
    return _drop_repeats(ring, tags) if merge else (ring, tags)


def end_region(flight, front):
    """landing outline from the top riser line to the far ends of the boundaries"""
    a_end, b_end = len(flight.a) - 1, len(flight.b) - 1
    pts = list(front.pts) + interior(flight.b, front.tb, cumulative(flight.b)[-1])
    pts += [flight.b[b_end], flight.a[a_end]]
    pts += interior(flight.a, cumulative(flight.a)[-1], front.ta)
    tags = [('front', k) for k in range(len(front.pts))] + [('side', None)] * (len(pts) - len(front.pts))
    # the cap between the two boundary ends is the back edge
    nb = len(front.pts) + len(interior(flight.b, front.tb, cumulative(flight.b)[-1]))
    tags[nb] = ('back', 0)
    tags[nb + 1] = ('back', 1)
    ring = np.array(pts)
    if signed_area(ring) < 0:
        ring, tags = ring[::-1].copy(), tags[::-1]
    return ring, tags


def triangulate(ring):
    """ear clipping for a simple counter clockwise polygon, returns index triangles"""
    idx = list(range(len(ring)))
    tris = []

    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        for k in range(n):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % n]
            p0, p1, p2 = ring[i0], ring[i1], ring[i2]
            if cross(p0, p1, p2) <= 1e-12:
                continue
            ear = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                q = ring[j]
                if cross(p0, p1, q) >= -1e-12 and cross(p1, p2, q) >= -1e-12 and cross(p2, p0, q) >= -1e-12:
                    ear = False
                    break
            if ear:
                tris.append((i0, i1, i2))
                idx.pop(k)
                break
        else:
            # degenerate leftovers (collinear points): fan the rest
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
            return tris
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


# --------------------------------------------------------------------------- solids

def profile(toe, size, z_bot, z_top):
    """(set back from the front, height) pairs from the bottom to the top of the front edge"""
    size = min(max(size, 0.0), (z_top - z_bot) * 0.95)
    if toe == 'SQUARE' or size < 1e-6:
        return [(0.0, z_bot), (0.0, z_top)]
    if toe == 'CHAMFER':
        return [(0.0, z_bot), (0.0, z_top - size), (size, z_top)]
    pts = [(0.0, z_bot)]
    for k in range(7):
        phi = math.pi - k * (math.pi / 2) / 6
        pts.append((size + size * math.cos(phi), z_top - size + size * math.sin(phi)))
    return pts


def loft(flight, front, back, prof):
    """
    a solid between two riser lines; prof shapes its front edge as rings of (set back, z).
    the rings keep one vertex count, so the sides are quads.
    """
    base_ring, tags = region(flight, front, back, merge=False)
    rings = []
    for d, z in prof:
        f = flight.shifted(front, d) if d > 1e-9 else front
        ring = base_ring.copy()
        for k, (kind, i) in enumerate(tags):
            if kind == 'front':
                ring[k] = f.pts[i]
        rings.append(np.column_stack([ring, np.full(len(ring), z)]))
    # points that coincide (winders meeting on a boundary) are merged, faces shrink to suit
    n = len(base_ring)
    mesh = _Mesh()
    ids = [[mesh.v(p, p[2]) for p in ring] for ring in rings]
    mesh.face(ids[0][::-1])
    for r in range(len(rings) - 1):
        for k in range(n):
            k1 = (k + 1) % n
            mesh.face([ids[r][k], ids[r][k1], ids[r + 1][k1], ids[r + 1][k]])
    mesh.face(ids[-1])
    return mesh.verts, mesh.faces


def precast(flight, toe='SQUARE', toe_size=0.0, nosing=0.0, lap=0.05):
    """one block per step, each one rise tall, lapping under the block above"""
    pieces = []
    ch = flight.chords
    for i in range(len(ch) - 1):
        front = flight.shifted(ch[i], -nosing)
        back = flight.shifted(ch[i + 1], lap if i + 1 < len(ch) - 1 or flight.landing else 0.0)
        pieces.append(loft(flight, front, back, profile(toe, toe_size, flight.z(i), flight.z(i + 1))))
    return pieces


def timber(flight, toe='SQUARE', toe_size=0.0, nosing=0.025, tread=0.04, riser=0.02, risers=True):
    """separate tread boards, and riser boards unless the risers are open"""
    pieces = []
    ch = flight.chords
    tread = min(tread, flight.rise * 0.9)
    for i in range(len(ch) - 1):
        front = flight.shifted(ch[i], -nosing)
        # the top riser board sits in the landing; without one the last tread stops at the line
        top_board = risers and (i + 1 < len(ch) - 1 or flight.landing)
        back = flight.shifted(ch[i + 1], riser) if top_board else ch[i + 1]
        top = flight.z(i + 1)
        pieces.append(loft(flight, front, back, profile(toe, toe_size, top - tread, top)))
    if risers:
        for i in range(len(ch) if flight.landing else len(ch) - 1):
            bottom, top = flight.z(i), flight.z(i + 1) - tread
            if top - bottom < 1e-6:
                continue
            pieces.append(loft(flight, ch[i], flight.shifted(ch[i], riser), [(0.0, bottom), (0.0, top)]))
    return pieces


class _Mesh:
    def __init__(self):
        self.verts, self.faces, self.lookup = [], [], {}

    def v(self, p, z):
        key = (round(float(p[0]), 7), round(float(p[1]), 7), round(float(z), 7))
        i = self.lookup.get(key)
        if i is None:
            i = self.lookup[key] = len(self.verts)
            self.verts.append([float(p[0]), float(p[1]), float(z)])
        return i

    def face(self, idx):
        out = []
        for i in idx:
            if not out or out[-1] != i:
                out.append(i)
        if len(out) > 1 and out[0] == out[-1]:
            out.pop()
        if len(out) >= 3:
            self.faces.append(out)


def concrete(flight, waist=0.15):
    """
    one watertight solid: steps on top, a sloping soffit below at `waist` from the step roots
    (measured square to the pitch). A landing is added when the boundaries carry on past the
    top riser, otherwise the flight stops at the top riser line.
    """
    ch = flight.chords
    n = len(ch)
    goings = flight.goings
    pitch = math.atan2(flight.rise, max(sum(goings) / len(goings), 1e-6))
    w = waist / max(math.cos(pitch), 0.2)
    top = flight.z(n)
    roots_s = np.array([c.s for c in ch])
    roots_z = np.array([flight.z(i) for i in range(n)])
    slope = flight.rise / max(goings[-1], 1e-6)
    path_cum = cumulative(flight.path)

    def s_of(p):
        best, best_d = 0.0, 1e18
        for j in range(len(flight.path) - 1):
            q0, q1 = flight.path[j], flight.path[j + 1]
            d = q1 - q0
            L = float(np.dot(d, d))
            u = 0.0 if L < EPS else min(max(float(np.dot(p - q0, d)) / L, 0.0), 1.0)
            dist = float(np.linalg.norm(q0 + u * d - p))
            if dist < best_d:
                best_d, best = dist, path_cum[j] + u * math.sqrt(L)
        return best

    cache = {}

    def soffit(p):
        # one height per plan point: a point equally far from two path legs must not flip
        key = (round(float(p[0]), 7), round(float(p[1]), 7))
        if key not in cache:
            cache[key] = _soffit(p)
        return cache[key]

    def _soffit(p):
        s = s_of(p)
        if s <= roots_s[0]:
            z = roots_z[0] + (s - roots_s[0]) * flight.rise / max(goings[0], 1e-6)
        elif s >= roots_s[-1]:
            z = roots_z[-1] + (s - roots_s[-1]) * slope
        else:
            z = float(np.interp(s, roots_s, roots_z))
        return min(max(z - w, flight.z0), top - w)

    mesh = _Mesh()

    # every riser end on a boundary has corners at its bottom and top height. Side faces list all
    # of them on their vertical edges, so winders fanning out of one point close up cleanly.
    levels = {}
    for k, c in enumerate(ch):
        for p in (c.pts[0], c.pts[-1]):
            levels.setdefault((round(float(p[0]), 7), round(float(p[1]), 7)), set()).update(
                {flight.z(k), flight.z(k + 1)})

    def column(p, low, top_z):
        hs = levels.get((round(float(p[0]), 7), round(float(p[1]), 7)), set()) | {top_z}
        return sorted(h for h in hs if low + 1e-9 < h <= top_z + 1e-9)

    is_front = lambda t: t[0] in ('front', 'both')
    is_back = lambda t: t[0] in ('back', 'both')

    def body(ring, tags, top_z, front_low, back_face):
        """front_low: bottom of the front face (None = down to the soffit)"""
        soff = [soffit(p) for p in ring]
        m = len(ring)
        mesh.face([mesh.v(p, top_z) for p in ring])
        for t in triangulate(ring):
            mesh.face([mesh.v(ring[t[2]], soff[t[2]]), mesh.v(ring[t[1]], soff[t[1]]), mesh.v(ring[t[0]], soff[t[0]])])
        for k in range(m):
            k1 = (k + 1) % m
            pa, pb = ring[k], ring[k1]
            ta, tb = tags[k], tags[k1]
            if is_front(ta) and is_front(tb):
                lo_a = soff[k] if front_low is None else front_low
                lo_b = soff[k1] if front_low is None else front_low
                mesh.face([mesh.v(pa, lo_a), mesh.v(pb, lo_b), mesh.v(pb, top_z), mesh.v(pa, top_z)])
            elif is_back(ta) and is_back(tb):
                if back_face is not None:
                    mesh.face([mesh.v(pa, soff[k]), mesh.v(pb, soff[k1]), mesh.v(pb, back_face), mesh.v(pa, back_face)])
            else:
                idx = [mesh.v(pa, soff[k]), mesh.v(pb, soff[k1])]
                idx += [mesh.v(pb, z) for z in column(pb, soff[k1], top_z)]
                idx += [mesh.v(pa, z) for z in reversed(column(pa, soff[k], top_z))]
                mesh.face(idx)

    for i in range(n - 1):
        ring, tags = region(flight, ch[i], ch[i + 1])
        last = i == n - 2
        back_face = flight.z(i + 1) if (last and not flight.landing) else None
        body(ring, tags, flight.z(i + 1), None if i == 0 else flight.z(i), back_face)
    if flight.landing:
        ring, tags = end_region(flight, ch[-1])
        body(ring, tags, top, flight.z(n - 1), top)
    else:
        flight.messages.append("no landing: the boundaries stop at the top riser, so the last riser is the floor's edge")
    return [(mesh.verts, mesh.faces)]


def build(kind, flight, **settings):
    if kind == 'CONCRETE':
        return concrete(flight, waist=settings.get('waist', 0.15))
    if kind == 'PRECAST':
        return precast(flight, settings.get('toe', 'SQUARE'), settings.get('toe_size', 0.0),
                       settings.get('nosing', 0.0), settings.get('lap', 0.05))
    return timber(flight, settings.get('toe', 'SQUARE'), settings.get('toe_size', 0.0),
                  settings.get('nosing', 0.025), settings.get('tread', 0.04),
                  settings.get('riser', 0.02), settings.get('risers', True))
