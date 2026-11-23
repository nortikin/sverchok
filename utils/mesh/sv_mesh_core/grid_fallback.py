# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Uncompiled implementations of the independent GRID weld policy.

Neither implementation imports Blender or Numba.  SciPy is optional and only
used for the compiled spatial search; the clustering and representatives are
computed in NumPy/Python with the same non-transitive, seed-order policy as the
Numba GRID backend.
"""
from itertools import product

import numpy as np

from .optional import scipy_tree

_NEIGHBOR_OFFSETS = tuple(product((-1, 0, 1), repeat=3))


def _exact_map(points):
    """Stable first-occurrence representatives for exactly equal coordinates."""
    representatives = {}
    result = np.empty(len(points), dtype=np.intp)
    for i, p in enumerate(points):
        key = (float(p[0]), float(p[1]), float(p[2]))
        result[i] = representatives.setdefault(key, i)
    return result


def _choose_group(points64, seed, candidates, radius_squared, target):
    """Apply one seed's non-transitive cluster to the global representative map.

    Candidate order is normalized to input order: this is important when the
    centroid is exactly midway between multiple candidates (smallest index
    wins).  This function is shared by both uncompiled spatial searches.
    """
    indices = np.asarray(candidates, dtype=np.intp)
    if not len(indices):
        target[seed] = seed
        return
    indices = indices[target[indices] < 0]
    if not len(indices):
        target[seed] = seed
        return
    indices.sort()
    differences = points64[indices] - points64[seed]
    squared = np.einsum('ij,ij->i', differences, differences)
    indices = indices[squared <= radius_squared]
    if len(indices) > 1:
        centroid = points64[indices].mean(axis=0)
        differences = points64[indices] - centroid
        squared = np.einsum('ij,ij->i', differences, differences)
        # np.argmin chooses the first; indices have been sorted above.
        representative = int(indices[np.argmin(squared)])
    else:
        representative = seed
    target[indices] = representative


def _exact_groups_if_isolated(points, radius, tree_constructor):
    """Fast path for repeated coordinates with *no* close distinct positions.

    Common in regular procedural tile meshes, for which creating thousands of
    range query result lists is unnecessary. A nearest-neighbor check on the
    unique positions proves that no different coordinate lies within radius.
    For dense or noisy positions this returns None and general GRID is used.
    """
    if len(points) < 256:
        return None
    sample = points[:min(len(points), 1024)]
    if len(np.unique(sample, axis=0)) * 4 >= len(sample) * 3:
        return None
    unique, first, inverse = np.unique(points, axis=0,
                                       return_index=True, return_inverse=True)
    if len(unique) == len(points):
        return None
    if len(unique) > 1:
        tree = tree_constructor(unique)
        nearest = tree.query(unique, k=2, workers=1)[0][:, 1]
        # Strictly larger means there are no pairs of distinct coordinates
        # inside the weld threshold.  Inexact boundary cases fall through.
        if np.any(nearest <= radius * (1 + 1e-12)):
            return None
    return first[inverse].astype(np.intp, copy=False)



def _clique_component_map(tree, points64, radius, query_radius, average):
    """Fast exact solution for isolated complete radius-neighborhood groups.

    A connected component whose every vertex pair is within the radius is a
    clique. Since no edge joins it to any other component, GRID's first
    unassigned seed must select the entire component. Therefore the whole
    component can be resolved in vectorized batches, with the same centroid
    representative and original-index tie breaking as the sequential code.

    Reject dense neighborhoods before allocating a potentially quadratic pair
    array. If *any* component isn't a clique, return None and let the standard
    seed-order algorithm handle every point. Correctness never depends on the
    heuristic that decides whether this optimization is worth trying.
    """
    n = len(points64)
    if n < 2048 or average > 16:
        return None
    # count_neighbors includes n self-pairs and counts other pairs twice.
    # It is a scalar query in compiled SciPy and needs no O(pairs) allocation.
    max_pairs = min(12 * n, 750_000)
    if (int(tree.count_neighbors(tree, query_radius)) - n) // 2 > max_pairs:
        return None
    pairs = tree.query_pairs(query_radius, output_type='ndarray')
    if len(pairs) == 0:
        return np.arange(n, dtype=np.intp)
    # cKDTree provides the broad phase. Resolve threshold boundaries with the
    # same float64 squared-distance predicate as the ordinary GRID backend.
    difference = points64[pairs[:, 0]] - points64[pairs[:, 1]]
    pairs = pairs[np.einsum('ij,ij->i', difference, difference) <= radius * radius]
    if len(pairs) == 0:
        return np.arange(n, dtype=np.intp)
    # Import sparse modules only for data that qualifies for the fast path.
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    rows = np.concatenate((pairs[:, 0], pairs[:, 1]))
    cols = np.concatenate((pairs[:, 1], pairs[:, 0]))
    adjacency = coo_matrix((np.ones(len(rows), dtype=np.uint8), (rows, cols)),
                           shape=(n, n)).tocsr()
    component_count, labels = connected_components(adjacency, directed=False)
    sizes = np.bincount(labels, minlength=component_count)
    edges_in_component = np.bincount(labels[pairs[:, 0]],
                                     minlength=component_count)
    if np.any(edges_in_component != sizes * (sizes - 1) // 2):
        return None
    # Entire components are known to be valid disjoint GRID groups. Choosing
    # the original member closest to the group's centroid matches _choose_group.
    center = np.empty((component_count, 3), dtype=np.float64)
    for axis in range(3):
        center[:, axis] = (np.bincount(labels, weights=points64[:, axis],
                                       minlength=component_count) / sizes)
    difference = points64 - center[labels]
    scores = np.einsum('ij,ij->i', difference, difference)
    order = np.lexsort((np.arange(n, dtype=np.intp), scores, labels))
    first = np.r_[True, labels[order][1:] != labels[order][:-1]]
    representatives = order[first]
    return representatives[labels]

def _grid_map_scipy_small(points64, radius, tree_constructor):
    """Low-overhead GRID grouping for small, irregular point clouds.

    cKDTree supplies complete radius neighborhoods in input-index order. For
    relatively small clouds it is faster to do scalar work on the returned
    small groups than to allocate many temporary NumPy arrays per seed.

    The algorithm uses the SAME squared-distance test, non-transitive
    seed-order grouping, centroid representative and lowest-index tie break
    as the general GRID implementations. This is not a BMesh fallback.
    """
    count = len(points64)
    radius_squared = radius * radius
    coordinates = points64.tolist()
    tree = tree_constructor(points64)
    neighbors = tree.query_ball_point(
        points64, np.nextafter(radius, np.inf),
        return_sorted=True, workers=1)
    target = [-1] * count
    for seed, near in enumerate(neighbors):
        if target[seed] >= 0:
            continue
        px, py, pz = coordinates[seed]
        group = []
        cx = cy = cz = 0.0
        for other in near:
            if target[other] >= 0:
                continue
            x, y, z = coordinates[other]
            dx, dy, dz = x - px, y - py, z - pz
            if dx*dx + dy*dy + dz*dz <= radius_squared:
                group.append(other)
                cx += x
                cy += y
                cz += z
        if len(group) > 1:
            group_count = len(group)
            cx /= group_count
            cy /= group_count
            cz /= group_count
            best = -1
            best_distance = np.inf
            for other in group:
                x, y, z = coordinates[other]
                dx, dy, dz = x - cx, y - cy, z - cz
                squared = dx*dx + dy*dy + dz*dz
                if squared < best_distance or (squared == best_distance and other < best):
                    best, best_distance = other, squared
        else:
            best = seed
        for other in group:
            target[other] = best
    return np.asarray(target, dtype=np.intp)


def grid_map_scipy(points, distance):
    """Batch cKDTree search, no JIT and no Blender dependency.

    Process seed vertices *in input order*, never as connected components.
    Chunked ball queries prevent memory from scaling with all neighborhood
    lists at once. This matches GRID's independent policy, not BMesh's KD
    traversal/representative policy.
    """
    points = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    if not len(points):
        return np.empty(0, dtype=np.intp)
    if distance == 0:
        return _exact_map(points)
    tree_constructor = scipy_tree()
    radius = float(distance)
    radius_squared = radius * radius
    points64 = points.astype(np.float64)
    isolated = _exact_groups_if_isolated(points64, radius, tree_constructor)
    if isolated is not None:
        return isolated
    # Dense, jittered large tile meshes use the v5 clique fast path below.
    # Small irregular point clouds instead benefit from scalar seed loops,
    # with no per-group NumPy allocations.
    if len(points64) <= 2048:
        return _grid_map_scipy_small(points64, radius, tree_constructor)
    tree = tree_constructor(points64)
    target = np.full(len(points), -1, dtype=np.intp)
    # Slightly expand the broad-phase search, then apply an exact float64
    # squared-distance predicate.  This keeps radius-boundary points.
    query_radius = np.nextafter(radius, np.inf)
    # Bound temporary Python neighborhood lists (especially for dense input).
    sample = tree.query_ball_point(points64[:min(len(points), 32)],
                                   query_radius, return_length=True)
    average = max(1, float(np.mean(sample)))
    clique_result = _clique_component_map(tree, points64, radius, query_radius,
                                          average)
    if clique_result is not None:
        return clique_result
    chunk_size = max(16, min(2048, int(32768 / average)))
    for start in range(0, len(points), chunk_size):
        neighborhoods = tree.query_ball_point(
            points64[start:start + chunk_size], query_radius,
            return_sorted=True, workers=1)
        for offset, near in enumerate(neighborhoods):
            seed = start + offset
            if target[seed] < 0:
                _choose_group(points64, seed, near, radius_squared, target)
    return target


def grid_map_python(points, distance):
    """Cell-hash GRID backend requiring only NumPy.

    Uses O(N) persistent memory and O(N) average-time neighborhoods for
    spatially spread points, though dense buckets can be quadratic. The
    uncompiled SciPy backend is usually faster when available.
    """
    points = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    if not len(points):
        return np.empty(0, dtype=np.intp)
    if distance == 0:
        return _exact_map(points)
    radius = float(distance)
    radius_squared = radius * radius
    points64 = points.astype(np.float64)
    origin = points64.min(axis=0)
    scaled = (points64 - origin) / radius
    # Extremely tiny distances/large coordinate ranges cannot be stored in
    # int64 cell indices; use 1-D sorted-axis broad phase instead.
    if np.max(scaled) >= 2**50:
        return _grid_map_sweep_python(points64, radius)
    cells = np.floor(scaled).astype(np.int64)
    bins = {}
    for index, (cx, cy, cz) in enumerate(cells):
        bins.setdefault((cx, cy, cz), []).append(index)
    target = np.full(len(points), -1, dtype=np.intp)
    for i, (cx, cy, cz) in enumerate(cells):
        if target[i] >= 0:
            continue
        candidates = []
        for dx, dy, dz in _NEIGHBOR_OFFSETS:
            candidates.extend(bins.get((cx + dx, cy + dy, cz + dz), ()))
        _choose_group(points64, i, candidates, radius_squared, target)
    return target


def _grid_map_sweep_python(points64, radius):
    order_axis = int(np.argmax(np.ptp(points64, axis=0)))
    order = np.argsort(points64[:, order_axis], kind='stable')
    sorted_axis = points64[order, order_axis]
    target = np.full(len(points64), -1, dtype=np.intp)
    squared = radius * radius
    for i in range(len(points64)):
        if target[i] >= 0:
            continue
        coordinate = points64[i, order_axis]
        lo = np.searchsorted(sorted_axis, coordinate - radius, side='left')
        hi = np.searchsorted(sorted_axis, coordinate + radius, side='right')
        _choose_group(points64, i, order[lo:hi], squared, target)
    return target
