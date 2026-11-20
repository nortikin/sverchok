# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone mesh/mesh surface intersections for Sverchok.

No Blender imports. Requires NumPy; SciPy and Numba are optional.

Scope: detect intersection segments, isolated contacts and coplanar overlaps.
This does NOT split faces or create a cut mesh (a separate topology step).
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import floor
from typing import Sequence

import numpy as np

try:
    from scipy.spatial import cKDTree as _cKDTree
except ImportError:
    _cKDTree = None

try:
    from numba import njit as _njit
except ImportError:
    _njit = None

HAS_NUMBA = _njit is not None
HAS_SCIPY = _cKDTree is not None


@dataclass
class IntersectionResult:
    """Intersection geometry and provenance.

    vertices: (N, 3) float64, in input coordinates.
    edges: (E, 2) int64. Includes proper intersection segments and
        coplanar *one-dimensional* contacts; excludes overlapping-area rims.
    edge_face_pairs: (E, 2) int64, first originating (A-face, B-face) pair.
    point_indices: (P,) int64, isolated point contacts, excluding segment
        endpoints and vertices of coplanar overlap regions.
    point_face_pairs: (P, 2) int64, first originating face pair.
    coplanar_polygons: list of int64 index arrays, one per overlapping
        triangle pair (not merged across faces or triangulation diagonals).
    coplanar_face_pairs: (C, 2) int64.
    intersecting_triangle_pairs: (I, 2) int64, pair for every raw hit.
    candidate_pairs: broad-phase AABB-overlapping triangle-pair count.
    """
    vertices: np.ndarray
    edges: np.ndarray
    edge_face_pairs: np.ndarray
    point_indices: np.ndarray
    point_face_pairs: np.ndarray
    coplanar_polygons: list[np.ndarray]
    coplanar_face_pairs: np.ndarray
    intersecting_triangle_pairs: np.ndarray
    candidate_pairs: int
    triangle_count_a: int
    triangle_count_b: int
    acceleration: str
    numba_used: bool


def _as_vertices(vertices: Sequence[Sequence[float]], label: str) -> np.ndarray:
    v = np.asarray(vertices, dtype=np.float64)
    if v.size == 0:
        return np.empty((0, 3), dtype=np.float64)
    if v.ndim != 2 or v.shape[1] != 3 or not np.all(np.isfinite(v)):
        raise ValueError(f'{label} must be a finite (N, 3) array')
    return np.ascontiguousarray(v)


def _signed_area2(poly: np.ndarray) -> float:
    return float(np.sum(poly[:, 0] * np.roll(poly[:, 1], -1)
                        - np.roll(poly[:, 0], -1) * poly[:, 1]))


def _cross2(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    return float((b[0] - a[0]) * (c[1] - a[1])
                 - (b[1] - a[1]) * (c[0] - a[0]))


def _earclip(face: np.ndarray, coords: np.ndarray, tolerance: float) -> list[list[int]]:
    """Ear-clip a simple polygon in its dominant-axis projection.

    Triangles preserve input winding. A nonplanar polygon is interpreted as
    a piecewise planar surface, as with typical mesh triangulation.
    """
    n = np.zeros(3)
    for i in range(len(coords)):
        n += np.cross(coords[i], coords[(i + 1) % len(coords)])
    k = int(np.argmax(np.abs(n)))
    ij = [i for i in range(3) if i != k]
    xy = coords[:, ij]
    area = _signed_area2(xy)
    if abs(area) <= tolerance * tolerance:
        raise ValueError('Degenerate polygon: cannot triangulate face')
    orientation = 1.0 if area > 0 else -1.0
    remain = list(range(len(face)))
    output: list[list[int]] = []
    # Scale 2D orientation tolerance to the local geometry.
    scale = float(np.max(np.ptp(xy, axis=0)))
    area_eps = max((tolerance * max(scale, tolerance)) * 1e-3,
                   32 * np.finfo(float).eps * scale * scale)
    while len(remain) > 3:
        found = False
        for pos, q in enumerate(remain):
            p, r = remain[pos - 1], remain[(pos + 1) % len(remain)]
            a, b, c = xy[p], xy[q], xy[r]
            signed = orientation * _cross2(a, b, c)
            if signed <= area_eps:
                continue
            blocked = False
            for other in remain:
                if other in (p, q, r):
                    continue
                x = xy[other]
                if (orientation * _cross2(a, b, x) >= -area_eps and
                    orientation * _cross2(b, c, x) >= -area_eps and
                    orientation * _cross2(c, a, x) >= -area_eps):
                    blocked = True
                    break
            if blocked:
                continue
            output.append([int(face[p]), int(face[q]), int(face[r])])
            remain.pop(pos)
            found = True
            break
        if not found:
            # The source is self-overlapping, has repeated edges, or its
            # projection is degenerate. Do not silently invent triangulation.
            raise ValueError('Cannot ear-clip face; check for self-intersections '
                             'or degenerate edges')
    output.append([int(face[i]) for i in remain])
    return output


def triangulate_faces(vertices: Sequence[Sequence[float]],
                      faces: Sequence[Sequence[int]],
                      tolerance: float = 1e-8) -> tuple[np.ndarray, np.ndarray]:
    """Triangulate polygon faces without Blender; return triangles + face IDs.

    For concave n-gons uses ear clipping. For triangulated input this is a
    fast index-preserving pass. Edges-only geometry is not supported.
    """
    v = _as_vertices(vertices, 'vertices')
    if tolerance <= 0 or not np.isfinite(tolerance):
        raise ValueError('tolerance must be positive and finite')

    # Fast vectorized paths for triangle / predominantly convex-quad meshes.
    # Keep face indices even though every quad becomes two triangles.
    try:
        dense = np.asarray(faces)
    except ValueError:  # Ragged n-gons; use the general ear clipping path.
        dense = None
    if dense is not None and dense.ndim == 2 and dense.shape[1] in (3, 4):
        if not np.issubdtype(dense.dtype, np.integer):
            raise ValueError('face indices must be integers')
        indices = np.asarray(dense, dtype=np.int64)
        if np.any(indices < 0) or np.any(indices >= len(v)):
            raise ValueError('face indices out of range')
        # Distinct indices in each polygon, without Python set creation.
        if np.any(np.sort(indices, axis=1)[:, 1:] ==
                  np.sort(indices, axis=1)[:, :-1]):
            raise ValueError('face contains invalid or repeated vertex indices')
        if indices.shape[1] == 3:
            return np.ascontiguousarray(indices), np.arange(len(indices), dtype=np.int64)
        p = v[indices]
        e = np.roll(p, -1, axis=1) - p
        n = (np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]) +
             np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0]))
        signed = np.einsum('mij,mj->mi', np.cross(e, np.roll(e, -1, axis=1)), n)
        convex = np.all(signed > 1e-25, axis=1)
        if np.all(convex):
            t = np.concatenate((indices[:, [0, 1, 2]], indices[:, [0, 2, 3]]), axis=1)
            return t.reshape(-1, 3), np.repeat(np.arange(len(indices), dtype=np.int64), 2)
        # A mixed convex/concave batch: process only the unusual quads slowly.
        tri = []
        origins = []
        for face_id, row in enumerate(indices):
            pieces = ([row[[0, 1, 2]].tolist(), row[[0, 2, 3]].tolist()]
                      if convex[face_id] else _earclip(row, p[face_id], tolerance))
            tri.extend(pieces)
            origins.extend([face_id] * len(pieces))
        return np.asarray(tri, dtype=np.int64).reshape(-1, 3), np.asarray(origins, dtype=np.int64)

    tri: list[list[int]] = []
    origins: list[int] = []
    for face_id, raw in enumerate(faces):
        face = np.asarray(raw)
        if face.ndim != 1 or len(face) < 3:
            raise ValueError(f'face {face_id} must have at least 3 vertices')
        if not np.issubdtype(face.dtype, np.integer):
            raise ValueError(f'face {face_id} must contain integer vertex indices')
        face = face.astype(np.int64, copy=False)
        if (np.any(face < 0) or np.any(face >= len(v)) or
                len(set(face.tolist())) != len(face)):
            raise ValueError(f'face {face_id}: invalid or repeated vertex index')
        if len(face) == 3:
            # Degenerate triangles silently contribute no intersections.
            tri.append(face.tolist())
            origins.append(face_id)
        else:
            new_tri = _earclip(face, v[face], tolerance)
            tri.extend(new_tri)
            origins.extend([face_id] * len(new_tri))
    return (np.asarray(tri, dtype=np.int64).reshape(-1, 3),
            np.asarray(origins, dtype=np.int64))


class _BVH:
    """Small pure-NumPy AABB hierarchy; no Blender's BVHTree dependency."""
    def __init__(self, mins: np.ndarray, maxs: np.ndarray, leaf_size: int = 12):
        self.mins, self.maxs = mins, maxs
        self.leaf_size = leaf_size
        self.nodes: list[tuple[np.ndarray, np.ndarray, int, int, np.ndarray | None]] = []
        self.root = self._build(np.arange(len(mins), dtype=np.int64)) if len(mins) else -1

    def _build(self, ids: np.ndarray) -> int:
        bbox_min, bbox_max = self.mins[ids].min(axis=0), self.maxs[ids].max(axis=0)
        index = len(self.nodes)
        self.nodes.append((bbox_min, bbox_max, -1, -1, None))
        if len(ids) <= self.leaf_size:
            self.nodes[index] = (bbox_min, bbox_max, -1, -1, ids)
        else:
            center = (self.mins[ids] + self.maxs[ids]) * 0.5
            spread = np.ptp(center, axis=0)
            axis = int(np.argmax(spread))
            order = np.argsort(center[:, axis], kind='stable')
            mid = len(ids) // 2
            left = self._build(ids[order[:mid]])
            right = self._build(ids[order[mid:]])
            self.nodes[index] = (bbox_min, bbox_max, left, right, None)
        return index


def _candidate_bvh(min_a: np.ndarray, max_a: np.ndarray,
                   min_b: np.ndarray, max_b: np.ndarray,
                   tolerance: float) -> np.ndarray:
    if not len(min_a) or not len(min_b):
        return np.empty((0, 2), dtype=np.int64)
    ta, tb = _BVH(min_a, max_a), _BVH(min_b, max_b)
    stack = [(ta.root, tb.root)]
    hits: list[np.ndarray] = []
    while stack:
        ia, ib = stack.pop()
        a0, a1, al, ar, ids_a = ta.nodes[ia]
        b0, b1, bl, br, ids_b = tb.nodes[ib]
        if np.any(a0 > b1 + tolerance) or np.any(b0 > a1 + tolerance):
            continue
        if ids_a is not None and ids_b is not None:
            mask = np.all((min_a[ids_a, None] <= max_b[None, ids_b] + tolerance) &
                          (min_b[None, ids_b] <= max_a[ids_a, None] + tolerance), axis=2)
            rows, cols = np.nonzero(mask)
            if len(rows):
                hits.append(np.column_stack((ids_a[rows], ids_b[cols])))
        elif ids_b is not None or (ids_a is None and
                                  np.prod(a1 - a0) >= np.prod(b1 - b0)):
            stack.extend(((al, ib), (ar, ib)))
        else:
            stack.extend(((ia, bl), (ia, br)))
    if not hits:
        return np.empty((0, 2), dtype=np.int64)
    out = np.concatenate(hits, axis=0)
    return out[np.lexsort((out[:, 1], out[:, 0]))]


def _candidate_brute(min_a: np.ndarray, max_a: np.ndarray,
                     min_b: np.ndarray, max_b: np.ndarray,
                     tolerance: float, batch: int = 256) -> np.ndarray:
    # Avoid allocating huge (batch, N_B, 3) temporary arrays.
    batch = max(1, min(batch, 262144 // max(len(min_b), 1)))
    hits = []
    for begin in range(0, len(min_a), batch):
        sl = slice(begin, begin + batch)
        m = np.all((min_a[sl, None] <= max_b[None] + tolerance) &
                   (min_b[None] <= max_a[sl, None] + tolerance), axis=2)
        i, j = np.nonzero(m)
        if len(i):
            hits.append(np.column_stack((i + begin, j)))
    return np.concatenate(hits, axis=0) if hits else np.empty((0, 2), dtype=np.int64)


def _candidate_scipy(min_a: np.ndarray, max_a: np.ndarray,
                      min_b: np.ndarray, max_b: np.ndarray,
                      tolerance: float) -> np.ndarray:
    if _cKDTree is None:
        raise ImportError('SciPy is not installed; select acceleration="bvh"')
    if not len(min_a) or not len(min_b):
        return np.empty((0, 2), dtype=np.int64)
    ca, cb = (min_a + max_a) * 0.5, (min_b + max_b) * 0.5
    ra = np.linalg.norm(max_a - min_a, axis=1) * 0.5
    rb = np.linalg.norm(max_b - min_b, axis=1) * 0.5
    tree = _cKDTree(ca)
    neighbors = tree.query_ball_point(cb, r=rb + np.max(ra) + tolerance)
    hits = []
    for ib, indices in enumerate(neighbors):
        if not indices:
            continue
        ids = np.asarray(indices, dtype=np.int64)
        dist2 = np.einsum('ij,ij->i', ca[ids] - cb[ib], ca[ids] - cb[ib])
        mask = (dist2 <= (ra[ids] + rb[ib] + tolerance) ** 2)
        mask &= np.all((min_a[ids] <= max_b[ib] + tolerance) &
                       (min_b[ib] <= max_a[ids] + tolerance), axis=1)
        if np.any(mask):
            a = ids[mask]
            hits.append(np.column_stack((a, np.full(len(a), ib, dtype=np.int64))))
    if not hits:
        return np.empty((0, 2), dtype=np.int64)
    out = np.concatenate(hits)
    return out[np.lexsort((out[:, 1], out[:, 0]))]


def _plane_prefilter(a: np.ndarray, b: np.ndarray, pairs: np.ndarray,
                     tolerance: float, batch_size: int = 16384) -> np.ndarray:
    """Vectorized conservative plane-sidedness test before the scalar kernel.

    Only rejects pairs demonstrably separated by a triangle's plane; the
    narrow-phase kernel makes the final intersection decision.
    """
    if not len(pairs):
        return pairs
    na = np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0])
    nb = np.cross(b[:, 1] - b[:, 0], b[:, 2] - b[:, 0])
    len_a = np.linalg.norm(na, axis=1)
    len_b = np.linalg.norm(nb, axis=1)
    valid_a = len_a >= 1e-30
    valid_b = len_b >= 1e-30
    np.divide(na, len_a[:, None], out=na, where=valid_a[:, None])
    np.divide(nb, len_b[:, None], out=nb, where=valid_b[:, None])
    # Slightly enlarge the rejection threshold to avoid rejecting a borderline
    # case due to different floating-point contraction/evaluation order.
    guard = 32 * np.finfo(np.float64).eps * max(
        float(np.max(np.abs(a))), float(np.max(np.abs(b))), 1.)
    t = tolerance + guard
    filtered = []
    for start in range(0, len(pairs), batch_size):
        sub = pairs[start:start + batch_size]
        ia, ib = sub[:, 0], sub[:, 1]
        da = np.einsum('nij,nj->ni', a[ia] - b[ib, :1], nb[ib])
        db = np.einsum('nij,nj->ni', b[ib] - a[ia, :1], na[ia])
        rejected_a = np.all(da > t, axis=1) | np.all(da < -t, axis=1)
        rejected_b = np.all(db > t, axis=1) | np.all(db < -t, axis=1)
        mask = valid_a[ia] & valid_b[ib] & ~rejected_a & ~rejected_b
        if np.any(mask):
            filtered.append(sub[mask])
    return (np.concatenate(filtered, axis=0) if filtered
            else np.empty((0, 2), dtype=np.int64))


def _triangle_pair_raw(a: np.ndarray, b: np.ndarray, tol: float):
    """Same scalar numerical kernel for NumPy/Python and optional Numba JIT.

    Return kind (0=no, 1=point, 2=segment, 3=coplanar) and 2 points.
    Coplanar polygons are clipped outside the JIT kernel.
    """
    result = np.zeros((2, 3), dtype=np.float64)
    na = np.cross(a[1] - a[0], a[2] - a[0])
    nb = np.cross(b[1] - b[0], b[2] - b[0])
    la = np.sqrt(np.dot(na, na))
    lb = np.sqrt(np.dot(nb, nb))
    if la < 1e-30 or lb < 1e-30:
        return 0, result
    na /= la
    nb /= lb
    db = np.empty(3, dtype=np.float64)
    da = np.empty(3, dtype=np.float64)
    for i in range(3):
        db[i] = np.dot(b[i] - a[0], na)
        da[i] = np.dot(a[i] - b[0], nb)
    if ((db[0] > tol and db[1] > tol and db[2] > tol) or
        (db[0] < -tol and db[1] < -tol and db[2] < -tol) or
        (da[0] > tol and da[1] > tol and da[2] > tol) or
        (da[0] < -tol and da[1] < -tol and da[2] < -tol)):
        return 0, result
    direction = np.cross(na, nb)
    norm_d = np.sqrt(np.dot(direction, direction))
    if norm_d <= 1e-12:
        if (np.max(np.abs(db)) <= tol and np.max(np.abs(da)) <= tol):
            return 3, result
        return 0, result

    # Two plane-section intervals. All scratch storage has static shape,
    # allowing the very same kernel to be @njit compiled.
    ends = np.zeros((2, 2, 3), dtype=np.float64)
    for side in range(2):
        tri = a if side == 0 else b
        d = da if side == 0 else db
        count = 0
        candidates = np.zeros((6, 3), dtype=np.float64)
        for i in range(3):
            j = (i + 1) % 3
            if abs(d[i]) <= tol:
                duplicate = False
                for k in range(count):
                    delta = candidates[k] - tri[i]
                    if np.dot(delta, delta) <= tol * tol:
                        duplicate = True
                        break
                if not duplicate:
                    candidates[count] = tri[i]
                    count += 1
            if (d[i] < -tol and d[j] > tol) or (d[i] > tol and d[j] < -tol):
                t = d[i] / (d[i] - d[j])
                point = tri[i] + t * (tri[j] - tri[i])
                duplicate = False
                for k in range(count):
                    delta = candidates[k] - point
                    if np.dot(delta, delta) <= tol * tol:
                        duplicate = True
                        break
                if not duplicate:
                    candidates[count] = point
                    count += 1
        if count == 0:
            return 0, result
        far = 0.0
        k0 = 0
        k1 = 0
        for i in range(count):
            for j in range(i + 1, count):
                delta = candidates[i] - candidates[j]
                dist2 = np.dot(delta, delta)
                if dist2 > far:
                    far = dist2
                    k0, k1 = i, j
        ends[side, 0] = candidates[k0]
        ends[side, 1] = candidates[k1]

    direction /= norm_d
    # A point on the intersection line of the two planes, computed in local
    # coordinates to avoid a loss of precision at large world coordinates.
    plane_offset = np.dot(b[0] - a[0], nb)
    line_origin = a[0] + (plane_offset / (norm_d * norm_d)) * np.cross(
        np.cross(na, nb), na)
    vals = np.empty((2, 2), dtype=np.float64)
    for side in range(2):
        for i in range(2):
            vals[side, i] = np.dot(ends[side, i] - line_origin, direction)
    lo = max(min(vals[0, 0], vals[0, 1]), min(vals[1, 0], vals[1, 1]))
    hi = min(max(vals[0, 0], vals[0, 1]), max(vals[1, 0], vals[1, 1]))
    if lo > hi + tol:
        return 0, result
    if hi - lo <= tol:
        result[0] = line_origin + ((lo + hi) * 0.5) * direction
        result[1] = result[0]
        return 1, result
    result[0] = line_origin + lo * direction
    result[1] = line_origin + hi * direction
    return 2, result


if HAS_NUMBA:
    _triangle_pair_jit = _njit(cache=True)(_triangle_pair_raw)
else:
    _triangle_pair_jit = None


def _clip_coplanar(a: np.ndarray, b: np.ndarray, tolerance: float):
    """Clip coplanar triangle A by triangle B in local 2D coordinates.

    Return (kind, array(K,3)). 3=positive-area overlap, 2=segment, 1=point.
    """
    n = np.cross(a[1] - a[0], a[2] - a[0])
    drop = int(np.argmax(np.abs(n)))
    axes = [q for q in range(3) if q != drop]
    poly = [p.copy() for p in a[:, axes]]
    cutter = b[:, axes]
    orient = 1.0 if _signed_area2(cutter) >= 0.0 else -1.0
    for k in range(3):
        p, q = cutter[k], cutter[(k + 1) % 3]
        # Cross products below have units of distance squared.
        eps2d = tolerance * float(np.linalg.norm(q - p))
        if not poly:
            break
        old = poly
        poly = []
        prev = old[-1]
        prev_d = orient * _cross2(p, q, prev)
        for current in old:
            d = orient * _cross2(p, q, current)
            in_current, in_prev = d >= -eps2d, prev_d >= -eps2d
            if in_current != in_prev:
                denom = prev_d - d
                if abs(denom) > 1e-30:
                    t = np.clip(prev_d / denom, 0., 1.)
                    poly.append(prev + t * (current - prev))
            if in_current:
                poly.append(current)
            prev, prev_d = current, d
    if not poly:
        return 0, np.empty((0, 3), dtype=np.float64)
    unique = []
    for p in poly:
        if not unique or np.linalg.norm(p - unique[-1]) > tolerance:
            unique.append(p)
    if len(unique) > 1 and np.linalg.norm(unique[0] - unique[-1]) <= tolerance:
        unique.pop()
    if not unique:
        return 0, np.empty((0, 3), dtype=np.float64)

    # The clipped polygon lies on A's plane. Reconstruct the dropped coordinate.
    projected = np.asarray(unique, dtype=np.float64)
    xyz = np.empty((len(projected), 3), dtype=np.float64)
    xyz[:, axes] = projected
    xyz[:, drop] = a[0, drop] - ((projected[:, 0] - a[0, axes[0]]) * n[axes[0]] +
                                  (projected[:, 1] - a[0, axes[1]]) * n[axes[1]]) / n[drop]
    if len(xyz) == 1:
        return 1, xyz
    # Collinear contact can yield more than 2 points after clipping.
    area = abs(_signed_area2(projected)) * 0.5 if len(projected) >= 3 else 0.
    scale = max(float(np.ptp(projected, axis=0).max()), tolerance)
    if len(xyz) >= 3 and area > tolerance * scale:
        return 3, xyz
    dist2 = np.sum((xyz[:, None, :] - xyz[None, :, :]) ** 2, axis=2)
    i, j = np.unravel_index(int(np.argmax(dist2)), dist2.shape)
    if dist2[i, j] <= tolerance ** 2:
        return 1, xyz[i:i + 1]
    return 2, xyz[[i, j]]


def _weld(points: list[np.ndarray], tolerance: float) -> tuple[np.ndarray, np.ndarray]:
    """Weld within Euclidean tolerance using 27 neighboring spatial bins.

    The first matching vertex wins; avoids transitive chain-merging across a cut.
    """
    if not points:
        return np.empty((0, 3), dtype=np.float64), np.empty((0,), dtype=np.int64)
    cell_size = tolerance
    bins: dict[tuple[int, int, int], list[int]] = {}
    vertices = []
    mapping = np.empty(len(points), dtype=np.int64)
    offsets = tuple(product((-1, 0, 1), repeat=3))
    tol2 = tolerance * tolerance
    origin = points[0]
    for k, p in enumerate(points):
        # Relative cells avoid int64 overflow and improve precision when the
        # input geometry has a large world-space translation.
        cell = tuple(floor((float(p[d]) - float(origin[d])) / cell_size)
                     for d in range(3))
        match = -1
        for dx, dy, dz in offsets:
            for idx in bins.get((cell[0] + dx, cell[1] + dy, cell[2] + dz), ()):
                diff = vertices[idx] - p
                if np.dot(diff, diff) <= tol2:
                    match = idx
                    break
            if match >= 0:
                break
        if match < 0:
            match = len(vertices)
            vertices.append(p.copy())
            bins.setdefault(cell, []).append(match)
        mapping[k] = match
    return np.asarray(vertices, dtype=np.float64).reshape(-1, 3), mapping


def _empty_result(n_a: int, n_b: int, backend: str, use_numba: bool,
                  candidates: int = 0) -> IntersectionResult:
    return IntersectionResult(
        vertices=np.empty((0, 3)), edges=np.empty((0, 2), dtype=np.int64),
        edge_face_pairs=np.empty((0, 2), dtype=np.int64),
        point_indices=np.empty((0,), dtype=np.int64),
        point_face_pairs=np.empty((0, 2), dtype=np.int64),
        coplanar_polygons=[], coplanar_face_pairs=np.empty((0, 2), dtype=np.int64),
        intersecting_triangle_pairs=np.empty((0, 2), dtype=np.int64),
        candidate_pairs=candidates, triangle_count_a=n_a, triangle_count_b=n_b,
        acceleration=backend, numba_used=use_numba)


def intersect_meshes(vertices_a: Sequence[Sequence[float]],
                     faces_a: Sequence[Sequence[int]],
                     vertices_b: Sequence[Sequence[float]],
                     faces_b: Sequence[Sequence[int]], *,
                     tolerance: float = 1e-8,
                     acceleration: str = 'bvh',
                     use_numba: bool | None = None,
                     include_coplanar: bool = True) -> IntersectionResult:
    """Detect mesh-mesh intersections without bpy, bmesh or mathutils.

    Parameters
    ----------
    vertices_a, vertices_b : (N,3) NumPy arrays or lists
    faces_a, faces_b : iterables of triangle / quad / simple n-gon index lists
    tolerance : absolute scene-space numerical/weld tolerance
    acceleration : 'bvh' (default), 'scipy' or 'brute'
    use_numba : True, False, None ('auto': Numba for >=128 plane-candidate pairs)
    include_coplanar : whether to return area overlaps (and 1D contacts)

    Notes
    -----
    Edges are raw surface intersection segments; edge crossing / T-junction
    splitting and face reconstruction are intentionally deferred to stage 2.
    """
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError('tolerance must be a positive finite number')
    if acceleration not in ('bvh', 'scipy', 'brute'):
        raise ValueError('acceleration must be bvh, scipy or brute')
    if use_numba is True and not HAS_NUMBA:
        raise ImportError('Numba requested but not installed')
    # In auto mode, do not pay Numba's initial JIT compilation cost for tiny
    # meshes. The decision uses pair count only, with no timing/probe overhead.
    auto_jit = use_numba is None
    use_jit = bool(use_numba) if not auto_jit else False
    va, vb = _as_vertices(vertices_a, 'vertices_a'), _as_vertices(vertices_b, 'vertices_b')
    fa, oa = triangulate_faces(va, faces_a, tolerance=tolerance)
    fb, ob = triangulate_faces(vb, faces_b, tolerance=tolerance)
    if not len(fa) or not len(fb):
        return _empty_result(len(fa), len(fb), acceleration, use_jit)
    a, b = va[fa], vb[fb]
    min_a, max_a = a.min(axis=1), a.max(axis=1)
    min_b, max_b = b.min(axis=1), b.max(axis=1)
    if acceleration == 'bvh':
        pairs = _candidate_bvh(min_a, max_a, min_b, max_b, tolerance)
    elif acceleration == 'scipy':
        pairs = _candidate_scipy(min_a, max_a, min_b, max_b, tolerance)
    else:
        pairs = _candidate_brute(min_a, max_a, min_b, max_b, tolerance)
    if not len(pairs):
        return _empty_result(len(fa), len(fb), acceleration, use_jit)

    # Cheap vectorized plane-sidedness rejection is used for both backends.
    # Preserve the AABB candidate count for profiling.
    num_aabb_candidates = len(pairs)
    pairs = _plane_prefilter(a, b, pairs, tolerance)
    if auto_jit:
        use_jit = HAS_NUMBA and len(pairs) >= 128
    if not len(pairs):
        return _empty_result(len(fa), len(fb), acceleration, use_jit,
                             num_aabb_candidates)
    kernel = _triangle_pair_jit if use_jit else _triangle_pair_raw
    # Intermediate vertices refer to indices in 'raw_points'. Welding occurs
    # once, after detecting all intersections, for consistent shared vertices.
    raw_points: list[np.ndarray] = []
    raw_segments: list[tuple[int, int, tuple[int, int]]] = []
    raw_contacts: list[tuple[int, tuple[int, int]]] = []
    raw_polys: list[tuple[list[int], tuple[int, int]]] = []
    hits = []
    for ia, ib in pairs:
        kind, endpoints = kernel(a[ia], b[ib], tolerance)
        face_pair = (int(oa[ia]), int(ob[ib]))
        if kind == 3:
            if not include_coplanar:
                continue
            kind, coords = _clip_coplanar(a[ia], b[ib], tolerance)
        else:
            coords = endpoints[:1] if kind == 1 else endpoints
        if kind == 0:
            continue
        if kind == 1:
            idx = len(raw_points)
            raw_points.append(coords[0].copy())
            raw_contacts.append((idx, face_pair))
        elif kind == 2:
            idx = len(raw_points)
            raw_points.extend((coords[0].copy(), coords[1].copy()))
            raw_segments.append((idx, idx + 1, face_pair))
        else:
            ids = list(range(len(raw_points), len(raw_points) + len(coords)))
            raw_points.extend(p.copy() for p in coords)
            raw_polys.append((ids, face_pair))
        hits.append((int(ia), int(ib)))

    if not raw_points:
        return _empty_result(len(fa), len(fb), acceleration, use_jit, num_aabb_candidates)
    xyz, inverse = _weld(raw_points, tolerance)
    edges = []
    edge_faces = []
    edge_keys = set()
    for i, j, pair in raw_segments:
        u, v = int(inverse[i]), int(inverse[j])
        if u == v:
            continue
        key = (min(u, v), max(u, v))
        if key not in edge_keys:
            edge_keys.add(key)
            edges.append(key)
            edge_faces.append(pair)
    point_ids, point_faces = [], []
    seen_points = set()
    used_in_other_geometry = {v for edge in edges for v in edge}
    used_in_other_geometry.update(int(inverse[i]) for ids, _ in raw_polys for i in ids)
    for idx, face_pair in raw_contacts:
        p = int(inverse[idx])
        if p not in seen_points and p not in used_in_other_geometry:
            seen_points.add(p)
            point_ids.append(p)
            point_faces.append(face_pair)
    polys, cop_faces = [], []
    seen_polys = set()
    for indices, face_pair in raw_polys:
        polygon = []
        for idx in indices:
            p = int(inverse[idx])
            if not polygon or p != polygon[-1]:
                polygon.append(p)
        if len(polygon) > 1 and polygon[0] == polygon[-1]:
            polygon.pop()
        if len(set(polygon)) < 3:
            continue
        # Only remove duplicates of geometrically identical clipped polygons.
        key = tuple(sorted(polygon))
        if key in seen_polys:
            continue
        seen_polys.add(key)
        polys.append(np.asarray(polygon, dtype=np.int64))
        cop_faces.append(face_pair)
    return IntersectionResult(
        vertices=xyz,
        edges=np.asarray(edges, dtype=np.int64).reshape(-1, 2),
        edge_face_pairs=np.asarray(edge_faces, dtype=np.int64).reshape(-1, 2),
        point_indices=np.asarray(point_ids, dtype=np.int64),
        point_face_pairs=np.asarray(point_faces, dtype=np.int64).reshape(-1, 2),
        coplanar_polygons=polys,
        coplanar_face_pairs=np.asarray(cop_faces, dtype=np.int64).reshape(-1, 2),
        intersecting_triangle_pairs=np.asarray(hits, dtype=np.int64).reshape(-1, 2),
        candidate_pairs=num_aabb_candidates, triangle_count_a=len(fa), triangle_count_b=len(fb),
        acceleration=acceleration, numba_used=use_jit)


__all__ = ['HAS_NUMBA', 'HAS_SCIPY', 'IntersectionResult',
           'triangulate_faces', 'intersect_meshes']
