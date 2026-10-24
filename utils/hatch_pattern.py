# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
AutoCAD / Revit .pat hatch patterns: parsing, and generating hatch lines clipped to planar regions.
Pure python + numpy (no bpy), so it can be tested outside Blender.

.pat line family:   angle, x, y, delta-x, delta-y [, dash, dash, ...]

    line k of a family passes through  O + k * (dx * u + dy * n)
        u = (cos angle, sin angle)   direction of the lines
        n = (-sin angle, cos angle)  perpendicular; the delta is given in this rotated frame
    the dash sequence starts at that point and repeats along the line.
    dash > 0 pen down, dash < 0 gap, dash == 0 a dot. No dashes: continuous lines.

A region is any set of boundary edges in which every vertex is shared by an even number of edges
(closed boundaries). Inside is decided by the even-odd rule, so holes need no special treatment.
"""

import math
import re
from dataclasses import dataclass, field

import numpy as np


# --------------------------------------------------------------------------- parsing

@dataclass
class PatFamily:
    angle: float
    x: float
    y: float
    dx: float
    dy: float
    dashes: tuple = ()


@dataclass
class Pattern:
    name: str
    description: str = ""
    families: list = field(default_factory=list)
    directives: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)


def parse_pat(text):
    """
    returns (patterns, issues). Handles several *NAME blocks per file, ;; comments,
    Revit ;%KEY=VALUE directives (file level ones are inherited by the patterns that follow)
    and the DOS end-of-file marker (Ctrl-Z) found in older files.
    """
    text = re.sub(r"\x1a[\s\S]*$", "", text)
    patterns, issues = [], []
    file_directives = {}
    current = None

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";%"):
            m = re.match(r"^([A-Za-z_]+)\s*=\s*(.*)$", line[2:])
            if m:
                target = current.directives if current else file_directives
                target[m.group(1).upper()] = m.group(2).strip()
            continue
        if line.startswith(";"):
            continue
        if line.startswith("*"):
            name, _, description = line[1:].partition(",")
            current = Pattern(name.strip(), description.strip(), directives=dict(file_directives))
            patterns.append(current)
            continue

        if current is None:
            issues.append(f"line {line_no}: data before any *NAME header")
            continue
        parts = [p.strip() for p in line.split(";")[0].split(",") if p.strip()]
        try:
            values = [float(p) for p in parts]
        except ValueError:
            current.issues.append(f"line {line_no}: not a number in '{line}'")
            continue
        if len(values) < 5:
            current.issues.append(f"line {line_no}: needs angle, x, y, delta-x, delta-y")
            continue
        angle, x, y, dx, dy, *dashes = values
        current.families.append(PatFamily(angle, x, y, dx, dy, tuple(dashes)))

    for p in patterns:
        if not p.families:
            p.issues.append("no line families defined")
    if not patterns:
        issues.append("no *NAME header found")
    return patterns, issues


# --------------------------------------------------------------------------- regions and planes

class RegionError(ValueError):
    pass


class HatchTooDense(ValueError):
    pass


def loops_to_edges(loops):
    """index loops -> (E, 2) index pairs"""
    pairs = []
    for loop in loops:
        loop = list(loop)
        if len(loop) >= 3:
            pairs.extend(zip(loop, loop[1:] + loop[:1]))
    return np.array(pairs, dtype=np.int64).reshape(-1, 2)


def check_closed(edges):
    """every vertex used by the boundary must be shared by an even number of edges"""
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    edges = edges[edges[:, 0] != edges[:, 1]]
    if not len(edges):
        raise RegionError("no boundary edges")
    ids, counts = np.unique(edges.ravel(), return_counts=True)
    odd = ids[counts % 2 == 1]
    if len(odd):
        shown = ", ".join(str(int(i)) for i in odd[:6])
        raise RegionError(f"boundary is not closed, open at vertex {shown}{' …' if len(odd) > 6 else ''}")
    return edges


def newell_normal(points):
    """unnormalized normal of a closed loop, its length is twice the loop area"""
    p = np.asarray(points, dtype=np.float64)
    q = np.roll(p, -1, axis=0)
    return np.array([
        np.sum((p[:, 1] - q[:, 1]) * (p[:, 2] + q[:, 2])),
        np.sum((p[:, 2] - q[:, 2]) * (p[:, 0] + q[:, 0])),
        np.sum((p[:, 0] - q[:, 0]) * (p[:, 1] + q[:, 1])),
    ])


def _upright(n):
    """a fixed facing for normals that come without winding: up, else +Y, else +X"""
    for axis in (2, 1, 0):
        if abs(n[axis]) > 1e-9:
            return n if n[axis] > 0 else -n
    return n


def frame_from_normal(n, points):
    """
    origin: the point of the plane closest to the world origin, so coplanar regions share one
    continuous hatch. Axes: on (near) horizontal planes x follows world X; otherwise y runs up the
    plane (world Z projected) and x runs level, which suits walls and roof slopes.
    """
    n = n / np.linalg.norm(n)
    origin = n * float(np.dot(np.mean(points, axis=0), n))
    if abs(n[2]) > 0.99:
        x = np.array([1.0, 0.0, 0.0]) - n * n[0]
        x /= np.linalg.norm(x)
        y = np.cross(n, x)
    else:
        y = np.array([0.0, 0.0, 1.0]) - n * n[2]
        y /= np.linalg.norm(y)
        x = np.cross(y, n)
    return origin, x, y, n


def plane_from_loops(verts, loops):
    """normal follows the winding of the largest loop, like a Blender face normal"""
    verts = np.asarray(verts, dtype=np.float64)
    normals = [newell_normal(verts[list(loop)]) for loop in loops if len(loop) >= 3]
    if not normals:
        raise RegionError("no polygon with 3 or more vertices")
    n = max(normals, key=lambda v: float(np.dot(v, v)))
    if np.linalg.norm(n) < 1e-12:
        raise RegionError("polygon has no area")
    used = np.unique(np.concatenate([np.asarray(list(l), dtype=np.int64) for l in loops]))
    return frame_from_normal(n, verts[used])


def plane_from_edges(verts, edges):
    """best fit plane through the boundary vertices; edges carry no winding, so the facing is fixed"""
    verts = np.asarray(verts, dtype=np.float64)
    pts = verts[np.unique(np.asarray(edges, dtype=np.int64))]
    if len(pts) < 3:
        raise RegionError("a region needs at least 3 boundary vertices")
    centred = pts - pts.mean(axis=0)
    _, sv, vt = np.linalg.svd(centred, full_matrices=False)
    if sv[1] < 1e-9 * max(sv[0], 1e-30):
        raise RegionError("boundary vertices are collinear")
    return frame_from_normal(_upright(vt[2]), pts)


# --------------------------------------------------------------------------- hatching

def hatch_edges_2d(A, B, pattern, scale=1.0, offset=(0.0, 0.0), max_segments=1_000_000):
    """
    A, B: (E, 2) boundary edge endpoints in plane coordinates (closed boundaries, even-odd inside).
    returns (segments (M, 2, 2), dots (D, 2))
    """
    A = np.asarray(A, dtype=np.float64).reshape(-1, 2)
    B = np.asarray(B, dtype=np.float64).reshape(-1, 2)
    if not len(A) or scale <= 0:
        return np.zeros((0, 2, 2)), np.zeros((0, 2))
    num_edges = len(A)
    segments, dots = [], []
    total = 0

    def too_dense():
        return HatchTooDense(f"pattern '{pattern.name}' would produce more than {max_segments:,} dashes, "
                             f"raise Scale or Max Segments")

    for fam in pattern.families:
        a = math.radians(fam.angle)
        u = np.array([math.cos(a), math.sin(a)])
        n = np.array([-math.sin(a), math.cos(a)])
        o = np.array([fam.x * scale + offset[0], fam.y * scale + offset[1]])
        dx, dy = fam.dx * scale, fam.dy * scale
        dashes = np.array(fam.dashes, dtype=np.float64) * scale

        # edges in the family frame: s along the lines, t across them
        As, At = (A - o) @ u, (A - o) @ n
        Bs, Bt = (B - o) @ u, (B - o) @ n
        tmin, tmax = min(At.min(), Bt.min()), max(At.max(), Bt.max())

        if abs(dy) > 1e-12:
            lo, hi = sorted((tmin / dy, tmax / dy))
            ks = np.arange(math.ceil(lo), math.floor(hi) + 1)
        else:
            ks = np.array([0]) if tmin <= 0 <= tmax else np.array([], dtype=np.int64)
        if not len(ks):
            continue
        if len(ks) > max_segments:
            raise too_dense()

        # crossings of every hatch line with every edge, chunked to bound memory.
        # half-open rule (t <= line) counts a vertex lying on a line exactly once.
        iv_k, iv_a, iv_b = [], [], []
        chunk = max(1, 4_000_000 // num_edges)
        for start in range(0, len(ks), chunk):
            kk = ks[start:start + chunk]
            tk = kk * dy
            cross = (At[None, :] <= tk[:, None]) != (Bt[None, :] <= tk[:, None])
            ki, ei = np.nonzero(cross)
            if not len(ki):
                continue
            t = tk[ki]
            s = As[ei] + (t - At[ei]) * (Bs[ei] - As[ei]) / (Bt[ei] - At[ei])
            order = np.lexsort((s, ki))
            ki, s = ki[order], s[order]
            # closed boundaries cross each line an even number of times: pair them up
            iv_k.append(kk[ki[0::2]])
            iv_a.append(s[0::2])
            iv_b.append(s[1::2])
        if not iv_k:
            continue
        k = np.concatenate(iv_k)
        ia = np.concatenate(iv_a)
        ib = np.concatenate(iv_b)
        keep = ib > ia
        k, ia, ib = k[keep], ia[keep], ib[keep]
        if not len(k):
            continue

        period = float(np.abs(dashes).sum()) if len(dashes) else 0.0
        if not len(dashes) or period <= 1e-12:
            seg_k, seg_a, seg_b = k, ia, ib
            dot_k = dot_s = np.zeros(0)
        else:
            shift = k * dx
            r0 = np.floor((ia - shift) / period).astype(np.int64)
            r1 = np.floor((ib - shift) / period).astype(np.int64)
            reps = r1 - r0 + 1
            expanded = int(reps.sum())
            if total + expanded * len(dashes) > max_segments:
                raise too_dense()
            idx = np.repeat(np.arange(len(k)), reps)
            first = np.repeat(np.cumsum(reps) - reps, reps)
            r = r0[idx] + (np.arange(expanded) - first)
            base = shift[idx] + r * period
            lo_s, hi_s, kx = ia[idx], ib[idx], k[idx]

            starts = np.concatenate(([0.0], np.cumsum(np.abs(dashes))[:-1]))
            seg_k, seg_a, seg_b, dot_k, dot_s = [], [], [], [], []
            for d, c in zip(dashes, starts):
                p = base + c
                if d > 0:
                    sa, sb = np.maximum(p, lo_s), np.minimum(p + d, hi_s)
                    ok = sb > sa
                    seg_k.append(kx[ok]); seg_a.append(sa[ok]); seg_b.append(sb[ok])
                elif d == 0:
                    ok = (p >= lo_s) & (p <= hi_s)
                    dot_k.append(kx[ok]); dot_s.append(p[ok])
            cat = lambda xs: np.concatenate(xs) if xs else np.zeros(0)
            seg_k, seg_a, seg_b, dot_k, dot_s = map(cat, (seg_k, seg_a, seg_b, dot_k, dot_s))

        total += len(seg_k) + len(dot_k)
        if total > max_segments:
            raise too_dense()

        line_pt = lambda kk, ss: o + np.outer(ss, u) + np.outer(kk * dy, n)
        if len(seg_k):
            segments.append(np.stack([line_pt(seg_k, seg_a), line_pt(seg_k, seg_b)], axis=1))
        if len(dot_k):
            dots.append(line_pt(dot_k, dot_s))

    seg = np.concatenate(segments) if segments else np.zeros((0, 2, 2))
    dot = np.concatenate(dots) if dots else np.zeros((0, 2))
    return seg, dot


@dataclass
class HatchResult:
    segments: np.ndarray        # (M, 2, 3)
    dots: np.ndarray            # (D, 3)
    frame: tuple                # origin, x, y, normal


def hatch_region(verts, pattern, loops=None, edges=None, scale=1.0, offset=(0.0, 0.0),
                 min_length=0.0, max_segments=1_000_000):
    """
    one planar region given as polygon loops (index lists) or as boundary edges (index pairs).
    loops win when both are given; with neither, the vertices form one loop in order.
    """
    verts = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
    if loops is not None and len(loops):
        loops = [list(l) for l in loops if len(l) >= 3]
        frame = plane_from_loops(verts, loops)
        bnd = loops_to_edges(loops)
    else:
        if edges is None or not len(edges):
            if len(verts) < 3:
                raise RegionError("a region needs at least 3 vertices")
            edges = loops_to_edges([list(range(len(verts)))])
        bnd = check_closed(edges)
        frame = plane_from_edges(verts, bnd)

    origin, x, y, _ = frame
    p2 = np.stack([(verts - origin) @ x, (verts - origin) @ y], axis=1)
    seg, dot = hatch_edges_2d(p2[bnd[:, 0]], p2[bnd[:, 1]], pattern, scale, offset, max_segments)
    if min_length > 0 and len(seg):
        seg = seg[np.linalg.norm(seg[:, 1] - seg[:, 0], axis=1) >= min_length]

    to3d = lambda q: origin + np.outer(q[:, 0], x) + np.outer(q[:, 1], y)
    seg3 = to3d(seg.reshape(-1, 2)).reshape(-1, 2, 3) if len(seg) else np.zeros((0, 2, 3))
    dot3 = to3d(dot) if len(dot) else np.zeros((0, 3))
    return HatchResult(seg3, dot3, frame)


# --------------------------------------------------------------------------- plotting

def chain_segments(segments, tol=1e-6, simplify=True):
    """
    join segments that share endpoints into polylines (pen strokes). Collinear interior points are
    removed when simplify is on, so touching dashes on one line become a single stroke.
    returns a list of (N, D) arrays; closed strokes repeat their first point at the end.
    """
    segments = np.asarray(segments, dtype=np.float64)
    if not len(segments):
        return []
    dim = segments.shape[2]
    pts = segments.reshape(-1, dim)
    keys = np.round(pts / tol).astype(np.int64)
    _, node, inverse = np.unique(keys, axis=0, return_index=True, return_inverse=True)
    inverse = inverse.ravel()
    ends = inverse.reshape(-1, 2)
    coords = pts[node]

    adjacency = [[] for _ in range(len(node))]
    for e, (a, b) in enumerate(ends):
        adjacency[a].append(e)
        adjacency[b].append(e)
    used = np.zeros(len(ends), dtype=bool)
    degree = np.array([len(a) for a in adjacency])

    def walk(start):
        path = [start]
        cur = start
        while True:
            nxt = None
            for e in adjacency[cur]:
                if not used[e]:
                    nxt = e
                    break
            if nxt is None:
                return path
            used[nxt] = True
            a, b = ends[nxt]
            cur = b if a == cur else a
            path.append(cur)

    strokes = []
    # open chains first (start at odd-degree nodes), then what is left are closed loops
    for start in np.nonzero(degree % 2 == 1)[0]:
        if any(not used[e] for e in adjacency[start]):
            strokes.append(walk(start))
    for e in range(len(ends)):
        if not used[e]:
            strokes.append(walk(ends[e][0]))

    out = []
    for path in strokes:
        poly = coords[path]
        if simplify and len(poly) > 2:
            poly = _drop_collinear(poly, tol)
        out.append(poly)
    return out


def _drop_collinear(poly, tol):
    keep = [poly[0]]
    for i in range(1, len(poly) - 1):
        a, b, c = keep[-1], poly[i], poly[i + 1]
        ab, bc = b - a, c - b
        lab, lbc = np.linalg.norm(ab), np.linalg.norm(bc)
        if lab < tol:
            continue
        if lbc > tol and np.dot(ab, bc) > 0:
            cross = np.linalg.norm(np.cross(ab, bc)) if len(ab) == 3 else abs(ab[0] * bc[1] - ab[1] * bc[0])
            if cross <= tol * lbc:
                continue
        keep.append(b)
    keep.append(poly[-1])
    return np.array(keep)


def order_strokes(strokes, start=None):
    """
    greedy nearest-neighbour ordering to cut pen travel: from the current pen position pick the
    closest stroke end, reversing the stroke when its far end is nearer.
    """
    if not strokes:
        return []
    firsts = np.array([s[0] for s in strokes])
    lasts = np.array([s[-1] for s in strokes])
    remaining = np.ones(len(strokes), dtype=bool)
    pos = firsts[0] * 0 if start is None else np.asarray(start, dtype=np.float64)
    ordered = []
    for _ in range(len(strokes)):
        d_first = np.where(remaining, np.sum((firsts - pos) ** 2, axis=1), np.inf)
        d_last = np.where(remaining, np.sum((lasts - pos) ** 2, axis=1), np.inf)
        i_f, i_l = int(np.argmin(d_first)), int(np.argmin(d_last))
        if d_first[i_f] <= d_last[i_l]:
            i, stroke = i_f, strokes[i_f]
        else:
            i, stroke = i_l, strokes[i_l][::-1]
        remaining[i] = False
        ordered.append(stroke)
        pos = stroke[-1]
    return ordered


def pen_travel(strokes, start=None):
    """total pen-up distance, for comparing orderings"""
    if not strokes:
        return 0.0
    pos = strokes[0][0] * 0 if start is None else np.asarray(start, dtype=np.float64)
    total = 0.0
    for s in strokes:
        total += float(np.linalg.norm(s[0] - pos))
        pos = s[-1]
    return total
