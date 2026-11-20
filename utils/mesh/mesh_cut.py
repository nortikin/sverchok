# SPDX-License-Identifier: GPL-3.0-or-later
"""Blender-independent topological knife cutting of mesh A by surface mesh B.

NumPy required. SciPy broad phase and Numba triangle intersections are optional,
via mesh_intersections.py. The topological recovery phase is pure Python/NumPy.

The internal triangulation is dissolved back to original polygon regions wherever
possible. Cut edges and original source face boundaries are never dissolved.
No Boolean classification or caps are performed; ambiguous geometry fails explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import floor
import numpy as np

try:
    from .mesh_intersections import (
        HAS_NUMBA, HAS_SCIPY, _as_vertices, intersect_meshes, triangulate_faces
    )
except ImportError:  # Standalone tests, executed outside the Sverchok package.
    from mesh_intersections import (
        HAS_NUMBA, HAS_SCIPY, _as_vertices, intersect_meshes, triangulate_faces
    )


@dataclass
class CutResult:
    vertices: np.ndarray
    edges: np.ndarray
    faces: list[list[int]]
    cut_edge_mask: np.ndarray
    cut_vertex_mask: np.ndarray
    face_origins: np.ndarray
    intersection_vertices: np.ndarray
    intersection_edges: np.ndarray
    acceleration: str
    numba_used: bool


def _cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def _orient(a, b, c):
    return _cross(b - a, c - a)


def _edge_key(a, b):
    return (min(int(a), int(b)), max(int(a), int(b)))


def _on_edge(p, a, b, tolerance):
    v = b - a
    lv2 = float(np.dot(v, v))
    if lv2 < tolerance * tolerance:
        return np.linalg.norm(p - a) <= tolerance
    t = float(np.dot(p - a, v) / lv2)
    if t < -tolerance / np.sqrt(lv2) or t > 1 + tolerance / np.sqrt(lv2):
        return False
    return abs(_orient(a, b, p)) <= tolerance * np.sqrt(lv2)


def _clip_to_triangle(p, q, triangle, tol):
    """Liang-Barsky segment clipping against three 2D oriented halfplanes."""
    s = 1.0 if _orient(*triangle) > 0 else -1.0
    start, end = 0.0, 1.0
    d = q - p
    for i in range(3):
        a, b = triangle[i], triangle[(i + 1) % 3]
        edge = b - a
        fuzzy = 0.0  # strict clipping avoids almost-collinear off-edge points
        f0 = s * _orient(a, b, p) + fuzzy
        f1 = s * _orient(a, b, q) + fuzzy
        if f0 < 0 and f1 < 0:
            return None
        if f0 < 0 or f1 < 0:
            t = float(f0 / (f0 - f1))
            if f0 < 0:
                start = max(start, t)
            else:
                end = min(end, t)
            if start > end + 1e-12:
                return None
    x = p + np.clip(start, 0.0, 1.0) * d
    y = p + np.clip(end, 0.0, 1.0) * d
    return x, y


def _segment_hits(p, q, r, s, tol):
    """Intersection points of two 2D closed segments; overlap gives endpoints."""
    v, w = q - p, s - r
    den = _cross(v, w)
    length_v, length_w = np.linalg.norm(v), np.linalg.norm(w)
    if min(length_v, length_w) < tol * 1e-4:
        return []
    eps = tol * max(length_v, length_w) * 1e-3 + 1e-14 * length_v * length_w
    if abs(den) > eps:
        diff = r - p
        t, u = _cross(diff, w) / den, _cross(diff, v) / den
        dt = tol / length_v
        du = tol / length_w
        if -dt <= t <= 1 + dt and -du <= u <= 1 + du:
            t, u = np.clip(t, 0., 1.), np.clip(u, 0., 1.)
            return [(float(t), float(u), 0.5 * ((p + t * v) + (r + u * w)))]
        return []
    if abs(_orient(p, q, r)) > tol * length_v:
        return []
    hits = []
    for x in (r, s):
        if _on_edge(x, p, q, tol):
            t = float(np.dot(x - p, v) / np.dot(v, v))
            u = float(np.dot(x - r, w) / np.dot(w, w))
            hits.append((float(np.clip(t, 0, 1)), float(np.clip(u, 0, 1)), x))
    for x in (p, q):
        if _on_edge(x, r, s, tol):
            t = float(np.dot(x - p, v) / np.dot(v, v))
            u = float(np.dot(x - r, w) / np.dot(w, w))
            hits.append((float(np.clip(t, 0, 1)), float(np.clip(u, 0, 1)), x))
    return hits


def _planarize(triangle, constraints, extra_points, tol):
    """Unique 2D points and noncrossing constraints in one A triangle."""
    points = [p.copy() for p in triangle]
    def intern(p):
        for i, value in enumerate(points):
            if np.linalg.norm(value - p) <= tol:
                return i
        points.append(np.asarray(p, dtype=float).copy())
        return len(points) - 1

    raw = [(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
           for a, b in constraints if np.linalg.norm(a - b) > tol]
    for a, b in raw:
        intern(a)
        intern(b)
    for p in extra_points:
        intern(p)
    all_hits = [[] for _ in raw]
    for i, (a, b) in enumerate(raw):
        all_hits[i].extend(((0.0, intern(a)), (1.0, intern(b))))
        for j in range(i + 1, len(raw)):
            c, d = raw[j]
            for t, u, p in _segment_hits(a, b, c, d, tol):
                k = intern(p)
                all_hits[i].append((t, k))
                all_hits[j].append((u, k))

    # All added points, including those from neighboring triangle edges, must
    # split any constraint that passes through them.
    for i, (a, b) in enumerate(raw):
        direction = b - a
        len2 = float(np.dot(direction, direction))
        for k, p in enumerate(points):
            if _on_edge(p, a, b, tol):
                all_hits[i].append((float(np.clip(np.dot(p - a, direction) / len2, 0, 1)), k))

    edges = set()
    for hitlist in all_hits:
        hitlist.sort(key=lambda pair: pair[0])
        for (_, a), (_, b) in zip(hitlist, hitlist[1:]):
            if a != b and np.linalg.norm(points[a] - points[b]) > tol:
                edges.add(_edge_key(a, b))
    return np.asarray(points, dtype=np.float64), edges


def _triangulate_pslg(points, constraints, tolerance):
    """Insert points in a triangle, then recover constraint edges by flips.

    All points must lie inside the initial triangle. Return positively oriented
    local triangles. A failed recovery raises rather than dropping cut edges.
    """
    scale = max(float(np.ptp(points[:3], axis=0).max()), 1e-12)
    area_eps = tolerance * scale * 0.01
    tri0 = [0, 1, 2] if _orient(*points[:3]) > 0 else [0, 2, 1]
    if abs(_orient(*points[:3])) <= tolerance * tolerance:
        raise ValueError('Degenerate source triangle')
    triangles = [tri0]

    def oriented(a, b, c):
        area = _orient(points[a], points[b], points[c])
        if abs(area) <= area_eps:
            raise ValueError('Degenerate triangle during constrained triangulation')
        return [a, b, c] if area > 0 else [a, c, b]

    for k in range(3, len(points)):
        p = points[k]
        match = None
        for tid, (a, b, c) in enumerate(triangles):
            cr = [_orient(points[a], points[b], p),
                  _orient(points[b], points[c], p),
                  _orient(points[c], points[a], p)]
            if min(cr) >= -tolerance * scale * 1.5:
                match = (tid, (a, b, c), cr)
                break
        if match is None:
            raise ValueError('Intersection vertex lies outside source triangle')
        tid, (a, b, c), cr = match
        near_edges = [i for i, value in enumerate(cr) if abs(value) <= tolerance * scale]
        if near_edges:
            e = [(a, b), (b, c), (c, a)][near_edges[0]]
            # Split both incident triangles (boundary edge => only one).
            attached = []
            for j, old in enumerate(triangles):
                if e[0] in old and e[1] in old:
                    attached.append(j)
            if not attached:
                raise RuntimeError('Broken edge adjacency during point insertion')
            new = []
            for j in reversed(attached):
                old = triangles.pop(j)
                third = next(v for v in old if v not in e)
                new.extend([oriented(e[0], k, third), oriented(k, e[1], third)])
            triangles.extend(new)
        else:
            triangles.pop(tid)
            triangles.extend([oriented(a, b, k), oriented(b, c, k), oriented(c, a, k)])

    def edge_adjacency():
        adjacency = {}
        for ti, tri in enumerate(triangles):
            for i in range(3):
                key = _edge_key(tri[i], tri[(i+1)%3])
                adjacency.setdefault(key, []).append(ti)
        return adjacency

    # Deliberately use explicit signed sides; no tolerance-dependent booleans
    # that would classify a grazing vertex contact as a crossing.
    def proper_cross(a, b, c, d):
        p, q, r, s = points[[a, b, c, d]]
        v1, v2 = _orient(p, q, r), _orient(p, q, s)
        w1, w2 = _orient(r, s, p), _orient(r, s, q)
        eps = tolerance * scale * 1e-3
        return ((v1 > eps and v2 < -eps or v1 < -eps and v2 > eps) and
                (w1 > eps and w2 < -eps or w1 < -eps and w2 > eps))

    locked = set()
    for target in sorted(constraints):
        if target[0] == target[1]:
            continue
        limit = max(50, 16 * len(triangles) ** 2)
        for _ in range(limit):
            adj = edge_adjacency()
            if target in adj:
                locked.add(target)
                break
            flips = []
            a, b = target
            for edge, tids in adj.items():
                if edge in locked or len(tids) != 2:
                    continue
                c, d = edge
                if not proper_cross(a, b, c, d):
                    continue
                t0, t1 = tids
                other0 = next(x for x in triangles[t0] if x != c and x != d)
                other1 = next(x for x in triangles[t1] if x != c and x != d)
                if other0 == other1 or not proper_cross(c, d, other0, other1):
                    continue  # Non-convex quadrilateral or zero-area triangle.
                new_edge = _edge_key(other0, other1)
                new_cross = proper_cross(a, b, other0, other1)
                # Prefer a flip that removes a segment crossing.
                flips.append((int(new_cross), edge, t0, t1, other0, other1))
            if not flips:
                raise ValueError('Could not recover a cut segment; degenerate or near-coincident geometry')
            flips.sort(key=lambda x: (x[0], x[1]))
            _, edge, t0, t1, c, d = flips[0]
            x, y = edge
            triangles[t0] = oriented(c, d, x)
            triangles[t1] = oriented(d, c, y)
        else:
            raise ValueError('Exceeded edge recovery limit; cut geometry requires a smaller tolerance')

    # Full area check detects accidental loss of triangles.
    actual = sum(_orient(*points[tri]) for tri in triangles)
    target_area = abs(_orient(*points[:3]))
    if abs(actual - target_area) > max(tolerance * scale * 12, target_area * 1e-7):
        raise ValueError('Cut triangulation lost or duplicated area')
    return triangles


class _VertexStore:
    """Preserve original IDs (including deliberate duplicates), weld new points."""
    def __init__(self, original, tolerance):
        self.vertices = [p.copy() for p in original]
        self.original_count = len(original)
        self.tol = tolerance
        self.origin = original[0] if len(original) else np.zeros(3)
        self.buckets = {}
        for idx, p in enumerate(self.vertices):
            self.buckets.setdefault(self._cell(p), []).append(idx)
        self.neighbors = tuple(product((-1, 0, 1), repeat=3))

    def _cell(self, p):
        return tuple(floor((float(p[d]) - float(self.origin[d])) / self.tol)
                     for d in range(3))

    def intern(self, p):
        cell = self._cell(p)
        tol2 = self.tol * self.tol
        for dx, dy, dz in self.neighbors:
            for idx in self.buckets.get((cell[0] + dx, cell[1] + dy, cell[2] + dz), ()):
                diff = self.vertices[idx] - p
                if np.dot(diff, diff) <= tol2:
                    return idx
        idx = len(self.vertices)
        self.vertices.append(np.asarray(p, dtype=float).copy())
        self.buckets.setdefault(cell, []).append(idx)
        return idx


def _edges_from_faces(faces):
    keys = sorted({_edge_key(face[i], face[(i + 1) % len(face)])
                   for face in faces for i in range(len(face))})
    return np.asarray(keys, dtype=np.int64).reshape(-1, 2)



def _restore_polygons(vertices, faces, origins, cut_edges, source_faces, tolerance):
    """Dissolve internal triangulation without dissolving a source or cut edge.

    Only faces from the same original planar polygon may merge. A group is
    converted to a polygon when its boundary is exactly one simple oriented
    cycle and the recovered area is unchanged. Internal holes, dangling cuts,
    ambiguous fans and nonplanar source polygons safely stay triangulated.

    Returns (faces, origins). No vertices are changed or newly introduced.
    """
    count = len(faces)
    if count < 2:
        return faces, np.asarray(origins, dtype=np.int64)
    source_faces = [list(map(int, f)) for f in source_faces]
    origin_ids = np.asarray(origins, dtype=np.int64)
    can_merge = {}
    for oid in set(map(int, origin_ids)):
        face = source_faces[oid]
        if len(face) < 3:
            can_merge[oid] = False
            continue
        xyz = vertices[face]
        normal = None
        for i in range(1, len(face) - 1):
            normal = np.cross(xyz[i] - xyz[0], xyz[i + 1] - xyz[0])
            if np.linalg.norm(normal) > tolerance * tolerance:
                break
        if (normal is None or np.linalg.norm(normal) <= tolerance * tolerance or
            np.max(np.abs((xyz - xyz[0]) @ normal)) > tolerance * np.linalg.norm(normal) * 2):
            can_merge[oid] = False
        else:
            can_merge[oid] = True

    adjacency = {}
    for fi, face in enumerate(faces):
        for j in range(len(face)):
            key = _edge_key(face[j], face[(j + 1) % len(face)])
            adjacency.setdefault(key, []).append(fi)

    parent = list(range(count))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)

    for edge, incident in adjacency.items():
        if len(incident) != 2 or edge in cut_edges:
            continue
        a, b = incident
        oid = int(origin_ids[a])
        if oid == int(origin_ids[b]) and can_merge.get(oid, False):
            union(a, b)

    groups = {}
    for i in range(count):
        groups.setdefault(find(i), []).append(i)

    def boundary_polygon(indices):
        occurrences = {}
        for fi in indices:
            face = faces[fi]
            for j in range(len(face)):
                edge = (int(face[j]), int(face[(j + 1) % len(face)]))
                occurrences.setdefault(_edge_key(*edge), []).append(edge)
        boundary = []
        for edge, directed in occurrences.items():
            # A dangling cut/slit can lie inside the same connected region.
            # Merging across it would erase the seam and create invalid
            # topology even though the outer boundary is a simple polygon.
            if edge in cut_edges and len(directed) != 1:
                return None
            if len(directed) == 1:
                boundary.append(directed[0])
            elif len(directed) != 2 or directed[0] != directed[1][::-1]:
                return None
        if len(boundary) < 3:
            return None
        successor = {}
        incoming = set()
        for a, b in boundary:
            if a in successor or b in incoming:
                return None  # branched vertex or figure-eight / slit
            successor[a] = b
            incoming.add(b)
        if set(successor) != incoming:
            return None
        # Start at the oldest input vertex whenever it still belongs to the rim.
        oid = int(origin_ids[indices[0]])
        start = next((int(v) for v in source_faces[oid] if int(v) in successor), boundary[0][0])
        polygon = []
        v = start
        for _ in boundary:
            if v in polygon:
                return None
            polygon.append(v)
            v = successor[v]
        if v != start or len(polygon) != len(successor):
            return None  # multiple loops / hole, cannot express as one n-gon
        coords = vertices[polygon]
        total_area = np.zeros(3)
        for j in range(len(coords)):
            total_area += np.cross(coords[j], coords[(j + 1) % len(coords)])
        ng_area = .5 * np.linalg.norm(total_area)
        tri_area = 0.0
        for fi in indices:
            tri = faces[fi]
            for j in range(1, len(tri) - 1):
                tri_area += .5 * np.linalg.norm(np.cross(
                    vertices[tri[j]] - vertices[tri[0]],
                    vertices[tri[j + 1]] - vertices[tri[0]]))
        if abs(ng_area - tri_area) > max(tolerance * 10 * max(1.0, np.sqrt(tri_area)), tri_area * 1e-7):
            return None
        return polygon

    recovered = {}
    for ids in groups.values():
        oid = int(origin_ids[ids[0]])
        if not can_merge.get(oid, False) or len(ids) < 2:
            continue
        polygon = boundary_polygon(ids)
        if polygon is not None:
            recovered[ids[0]] = (polygon, ids)
    suppressed = {i for poly, ids in recovered.values() for i in ids[1:]}
    out_faces, out_origins = [], []
    for i, face in enumerate(faces):
        if i in suppressed:
            continue
        out_faces.append(recovered[i][0] if i in recovered else face)
        out_origins.append(int(origin_ids[i]))
    return out_faces, np.asarray(out_origins, dtype=np.int64)


def _simplify_interior_cut_vertices(vertices, faces, origins, cut_edges, original_vertex_count,
                                    source_faces, tolerance):
    """Remove redundant seam vertices left by temporary triangulation.

    Never remove source vertices or points shared by different source faces;
    only degree-two collinear seam vertices strictly inside a source n-gon.
    Removing a vertex updates every incident polygon at once, preventing
    T-junctions. The resulting cut-edge set is reconstructed accordingly.
    """
    source_faces = [list(map(int, f)) for f in source_faces]
    faces = [list(f) for f in faces]
    marked = set(cut_edges)
    while True:
        by_vertex = {}
        for idx, face in enumerate(faces):
            for v in face:
                by_vertex.setdefault(int(v), set()).add(idx)
        chain_neighbors = {}
        for a, b in marked:
            chain_neighbors.setdefault(a, set()).add(b)
            chain_neighbors.setdefault(b, set()).add(a)
        candidate = None
        for v in sorted(chain_neighbors):
            if v < original_vertex_count or v not in by_vertex:
                continue
            neighbors = chain_neighbors[v]
            if len(neighbors) != 2:
                continue
            n0, n1 = sorted(neighbors)
            incident = by_vertex[v]
            if len(incident) != 2 or len({int(origins[i]) for i in incident}) != 1:
                continue
            oid = int(origins[next(iter(incident))])
            if len(source_faces[oid]) < 3:
                continue
            # It must be strictly in the source face interior, never on an
            # original edge, including a boundary shared with another face.
            polygon = source_faces[oid]
            on_border = any(_on_edge_3d(vertices[v], vertices[polygon[j]],
                                     vertices[polygon[(j+1) % len(polygon)]], tolerance)
                            for j in range(len(polygon)))
            if on_border:
                continue
            if any(len(faces[i]) < 4 for i in incident):
                continue
            if any({faces[i][(faces[i].index(v)-1) % len(faces[i])],
                     faces[i][(faces[i].index(v)+1) % len(faces[i])]} != neighbors
                   for i in incident):
                continue
            a, b, p = vertices[n0], vertices[n1], vertices[v]
            vec = b-a
            dist_sq = float(np.dot(vec,vec))
            if dist_sq <= tolerance * tolerance:
                continue
            factor = float(np.dot(p-a,vec) / dist_sq)
            if not (0.0 < factor < 1.0) or np.linalg.norm(p-(a+factor*vec)) > tolerance:
                continue
            candidate = (v, n0, n1, incident)
            break
        if candidate is None:
            break
        v, n0, n1, incident = candidate
        for fi in incident:
            faces[fi].remove(v)
        marked.discard(_edge_key(v, n0))
        marked.discard(_edge_key(v, n1))
        marked.add(_edge_key(n0, n1))
    # Keep all original input IDs stable, remove unused *new* vertices.
    used = {int(x) for face in faces for x in face}
    kept = list(range(original_vertex_count)) + sorted(i for i in used if i >= original_vertex_count)
    rename = {old: new for new, old in enumerate(kept)}
    return (vertices[kept], [[rename[v] for v in face] for face in faces],
            {_edge_key(rename[a],rename[b]) for a,b in marked})


def _on_edge_3d(p,a,b,tolerance):
    vec=b-a
    length2=float(np.dot(vec,vec))
    if length2 < tolerance*tolerance:
        return np.linalg.norm(p-a)<=tolerance
    fraction=float(np.dot(p-a,vec)/length2)
    return -tolerance/np.sqrt(length2) <= fraction <= 1+tolerance/np.sqrt(length2) and np.linalg.norm(p-(a+fraction*vec))<=tolerance



def _mark_existing_intersection_edges(vertices, faces, origins, segments, marked,
                                      tolerance):
    """Keep cutter seams that coincide with an edge already present in A.

    The constrained triangulator only marks newly generated constraints. If an
    intersection follows an *original* A edge, a triangle can remain unchanged
    and its constraint is skipped. Such an edge still divides the two sides of
    the cutter, and must be marked for Split/Keep side selection.

    Work locally per original face rather than comparing all cut segments with
    every output edge. A full output edge must lie on a finite intersection
    segment (not merely on the infinite supporting line).
    """
    segments_by_face = {}
    for p, q, face_id in segments:
        if float(np.linalg.norm(q - p)) > tolerance:
            segments_by_face.setdefault(face_id, []).append((p, q))
    if not segments_by_face:
        return
    edges_by_face = {}
    for face, oid in zip(faces, origins):
        fid = int(oid)
        if fid not in segments_by_face:
            continue
        candidate_edges = edges_by_face.setdefault(fid, set())
        for j in range(len(face)):
            candidate_edges.add(_edge_key(face[j], face[(j + 1) % len(face)]))
    for fid, candidates in edges_by_face.items():
        local_segments = segments_by_face[fid]
        for edge in candidates:
            if edge in marked:
                continue
            a, b = vertices[list(edge)]
            for p, q in local_segments:
                if (_on_edge_3d(a, p, q, tolerance) and
                        _on_edge_3d(b, p, q, tolerance)):
                    marked.add(edge)
                    break

def cut_mesh(vertices_a, faces_a, vertices_b, faces_b, *,
             tolerance=1e-6, acceleration='auto', use_numba=None,
             include_coplanar=True, preserve_polygons=True):
    """Cut mesh A with surface B. Return a connected (not separated) mesh A.

    Open and closed cutter surfaces are supported, without Boolean inside/outside
    classification. The cutter's mesh is not included in the returned topology.
    Coplanar overlaps are traced at their per-triangle rim, not filled.
    """
    if tolerance <= 0 or not np.isfinite(tolerance):
        raise ValueError('tolerance must be positive and finite')
    backend = ('scipy' if HAS_SCIPY else 'bvh') if acceleration == 'auto' else acceleration
    if backend not in ('scipy', 'bvh', 'brute'):
        raise ValueError('Unknown search backend')
    va = _as_vertices(vertices_a, 'vertices_a')
    base_faces = [list(map(int, face)) for face in faces_a]
    base_edges = _edges_from_faces(base_faces)
    intersections = intersect_meshes(va, faces_a, vertices_b, faces_b,
                                    tolerance=tolerance, acceleration=backend,
                                    use_numba=HAS_NUMBA if use_numba is None else use_numba,
                                    include_coplanar=include_coplanar)
    # Point-only contacts do not cut a surface. Keep them available in the
    # separate Mesh Intersection node, but do not create triangle fans here.
    if not (len(intersections.edges) or len(intersections.coplanar_polygons)):
        return CutResult(va.copy(), base_edges, base_faces,
                         np.zeros(len(base_edges), dtype=bool),
                         np.zeros(len(va), dtype=bool),
                         np.arange(len(base_faces), dtype=np.int64),
                         intersections.vertices, intersections.edges,
                         backend, intersections.numba_used)

    triangles, origins = triangulate_faces(va, faces_a, tolerance)
    # Each mesh-A original polygon can yield several triangles.
    by_face = {}
    for i, oid in enumerate(origins):
        by_face.setdefault(int(oid), []).append(i)

    # Local A-triangle projections. New points are lifted onto the original
    # source triangle plane, guaranteeing no drift off mesh A.
    axes, local, normals = [], [], []
    for ids in triangles:
        tri = va[ids]
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        if np.linalg.norm(n) < tolerance * tolerance * 1e-4:
            raise ValueError('Degenerate triangle in mesh A')
        dropped = int(np.argmax(np.abs(n)))
        axes.append([j for j in range(3) if j != dropped])
        normals.append((n, dropped))
        local.append(tri[:, axes[-1]])

    segments = [[] for _ in triangles]
    raw_segments = []
    for (i, j), (fa, _) in zip(intersections.edges, intersections.edge_face_pairs):
        raw_segments.append((intersections.vertices[int(i)], intersections.vertices[int(j)], int(fa)))
    for polygon, (fa, _) in zip(intersections.coplanar_polygons, intersections.coplanar_face_pairs):
        for k in range(len(polygon)):
            raw_segments.append((intersections.vertices[int(polygon[k])],
                                 intersections.vertices[int(polygon[(k + 1) % len(polygon)])], int(fa)))

    for p, q, original_face in raw_segments:
        for ti in by_face.get(original_face, []):
            u = np.asarray(p)[axes[ti]]
            v = np.asarray(q)[axes[ti]]
            clipped = _clip_to_triangle(u, v, local[ti], tolerance)
            if clipped is None:
                continue
            a, b = clipped
            if np.linalg.norm(b - a) > tolerance:
                segments[ti].append((a, b))
            # A segment clipped to a single point cannot create a local
            # cut; genuine edge crossings are propagated by shared[] below.

    # A common mesh edge can lie in triangles with different local plane
    # projections; share exact parametric edge cuts before rebuilding topology.
    shared = {}
    for ti, tri in enumerate(triangles):
        candidates = [p for seg in segments[ti] for p in seg]
        for j in range(3):
            i0, i1 = (int(tri[j]), int(tri[(j + 1) % 3]))
            key = _edge_key(i0, i1)
            a, b = local[ti][j], local[ti][(j + 1) % 3]
            for p in candidates:
                if _on_edge(p, a, b, tolerance):
                    p3 = va[i0] + float(np.dot(p - a, b - a) / np.dot(b - a, b - a)) * (va[i1] - va[i0])
                    v0, v1 = va[key[0]], va[key[1]]
                    t = float(np.clip(np.dot(p3 - v0, v1 - v0) / np.dot(v1 - v0, v1 - v0), 0, 1))
                    if t > tolerance / np.linalg.norm(v1 - v0) and t < 1 - tolerance / np.linalg.norm(v1 - v0):
                        shared.setdefault(key, []).append(t)
    for key, params in shared.items():
        shared[key] = sorted(set(round(t, 12) for t in params))

    store = _VertexStore(va, tolerance)
    out_faces = []
    out_origin = []
    marked = set()
    for ti, tri in enumerate(triangles):
        points_extra = []
        for j in range(3):
            i0, i1 = int(tri[j]), int(tri[(j + 1) % 3])
            for t in shared.get(_edge_key(i0, i1), []):
                key = _edge_key(i0, i1)
                p3 = va[key[0]] + t * (va[key[1]] - va[key[0]])
                points_extra.append(p3[axes[ti]])
        pts, constraints = _planarize(local[ti], segments[ti], points_extra, tolerance)
        if len(pts) == 3:
            out_faces.append(list(map(int, tri)))
            out_origin.append(int(origins[ti]))
            continue
        local_tris = _triangulate_pslg(pts, constraints, tolerance)
        n, dropped = normals[ti]
        xyz = np.empty((len(pts), 3), dtype=np.float64)
        xyz[:, axes[ti]] = pts
        xyz[:, dropped] = va[tri[0], dropped] - (
            (pts[:, 0] - va[tri[0], axes[ti][0]]) * n[axes[ti][0]] +
            (pts[:, 1] - va[tri[0], axes[ti][1]]) * n[axes[ti][1]]
        ) / n[dropped]
        ids = [int(tri[0]), int(tri[1]), int(tri[2])]
        ids.extend(store.intern(xyz[i]) for i in range(3, len(pts)))
        if _orient(*local[ti]) < 0:
            local_tris = [[a, c, b] for a, b, c in local_tris]
        for face in local_tris:
            out_faces.append([ids[k] for k in face])
            out_origin.append(int(origins[ti]))
        for a, b in constraints:
            marked.add(_edge_key(ids[a], ids[b]))

    verts = np.asarray(store.vertices, dtype=np.float64)
    if preserve_polygons:
        out_faces, out_origin = _restore_polygons(
            verts, out_faces, out_origin, marked, base_faces, tolerance)
        verts, out_faces, marked = _simplify_interior_cut_vertices(
            verts, out_faces, out_origin, marked, len(va), base_faces, tolerance)

    _mark_existing_intersection_edges(verts, out_faces, out_origin,
                                      raw_segments, marked, tolerance)
    out_edges = _edges_from_faces(out_faces)
    used = {tuple(edge) for edge in out_edges}
    missing = marked - used
    if missing:
        raise ValueError(f'Missing {len(missing)} recovered cut edges from output topology')
    cut_mask = np.asarray([tuple(edge) in marked for edge in out_edges], dtype=bool)
    cut_vertices = np.zeros(len(verts), dtype=bool)
    for a, b in marked:
        cut_vertices[a] = True
        cut_vertices[b] = True
    # Identify inserted vertices even on A edges where constraints end.
    cut_vertices[len(va):] = True
    return CutResult(verts, out_edges, out_faces, cut_mask, cut_vertices,
                     np.asarray(out_origin, dtype=np.int64),
                     intersections.vertices.copy(), intersections.edges.copy(),
                     backend, intersections.numba_used)


__all__ = ['CutResult', 'cut_mesh', 'HAS_NUMBA', 'HAS_SCIPY']
