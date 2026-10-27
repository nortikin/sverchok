# This file is part of Sverchok (GPL-3.0-or-later).
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exact point-to-edge-network queries and nesting-aware object matching.

Pure Python/NumPy module; it can be tested without importing Blender.
A network consists of indexed finite segments plus any unreferenced vertices.
"""

import numpy as np

try:
    from numba import njit, prange
except ImportError:
    njit = None
    prange = None

HAS_NUMBA = njit is not None


def _as_rows(value, width, dtype, name):
    arr = np.asarray(value, dtype=dtype)
    if arr.size == 0:
        return np.empty((0, width), dtype=dtype)
    if arr.ndim == 1 and arr.size == width:
        arr = arr.reshape((1, width))
    if arr.ndim != 2 or arr.shape[1] != width:
        raise ValueError(f"{name} must be a list/array of {width}-component rows")
    return np.ascontiguousarray(arr)


def _prepare_targets(vertices, edges, include_loose):
    verts = _as_rows(vertices, 3, np.float64, "Target Verts")
    edge_ids = _as_rows(edges, 2, np.int64, "Target Edges")
    if not np.all(np.isfinite(verts)):
        raise ValueError("Target Verts must contain finite coordinates")
    if edge_ids.size and (np.any(edge_ids < 0) or np.any(edge_ids >= len(verts))):
        raise ValueError("Target Edges contain out-of-range vertex indices")

    starts = verts[edge_ids[:, 0]]
    ends = verts[edge_ids[:, 1]]
    edge_numbers = np.arange(len(edge_ids), dtype=np.int64)

    if include_loose and len(verts):
        used = np.zeros(len(verts), dtype=np.bool_)
        used[edge_ids.ravel()] = True
        loose = verts[~used]
        if len(loose):
            starts = np.concatenate((starts, loose), axis=0)
            ends = np.concatenate((ends, loose), axis=0)
            edge_numbers = np.concatenate(
                (edge_numbers, np.full(len(loose), -1, dtype=np.int64)))

    directions = np.ascontiguousarray(ends - starts)
    length_squared = np.einsum("ij,ij->i", directions, directions)
    return (np.ascontiguousarray(starts), directions,
            np.ascontiguousarray(length_squared),
            np.ascontiguousarray(edge_numbers))


def _numpy_query(points, starts, directions, length_squared, edge_numbers,
                 pair_budget):
    """Chunk both axes: intermediate arrays never scale as all points * edges."""
    count = len(points)
    distances2 = np.full(count, np.inf, dtype=np.float64)
    locations = np.full((count, 3), np.nan, dtype=np.float64)
    indices = np.full(count, -1, dtype=np.int64)
    factors = np.full(count, -1.0, dtype=np.float64)
    if not len(starts) or not count:
        return np.sqrt(distances2), locations, indices, factors

    point_block = max(1, min(count, 128, pair_budget))
    edge_block = max(1, pair_budget // point_block)
    for ps in range(0, count, point_block):
        p = points[ps:ps + point_block]
        best_d2 = distances2[ps:ps + len(p)]
        best_location = locations[ps:ps + len(p)]
        best_index = indices[ps:ps + len(p)]
        best_factor = factors[ps:ps + len(p)]
        rows = np.arange(len(p))
        for es in range(0, len(starts), edge_block):
            a = starts[es:es + edge_block]
            ab = directions[es:es + edge_block]
            l2 = length_squared[es:es + edge_block]
            ap = p[:, None, :] - a[None, :, :]
            dots = np.einsum("nkj,kj->nk", ap, ab)
            t = np.divide(dots, l2[None, :], out=np.zeros_like(dots),
                          where=l2[None, :] > 0.0)
            np.clip(t, 0.0, 1.0, out=t)
            closest = a[None, :, :] + t[:, :, None] * ab[None, :, :]
            residual = p[:, None, :] - closest
            d2 = np.einsum("nkj,nkj->nk", residual, residual)
            minima = np.min(d2, axis=1)
            # First nearly tied target wins, independent of roundoff order.
            tolerance = 1.e-13 * np.maximum(minima, np.finfo(np.float64).tiny)
            local_idx = np.argmax(d2 <= minima[:, None] + tolerance[:, None], axis=1)
            candidates = d2[rows, local_idx]
            better = np.isinf(best_d2)
            finite = ~better
            if np.any(finite):
                old_tolerance = 1.e-13 * np.maximum(
                    candidates[finite], best_d2[finite])
                better[finite] = (candidates[finite] <
                                  best_d2[finite] - old_tolerance)
            if np.any(better):
                selected = es + local_idx[better]
                best_d2[better] = candidates[better]
                best_location[better] = closest[rows[better], local_idx[better]]
                best_index[better] = edge_numbers[selected]
                selected_t = t[rows[better], local_idx[better]]
                best_factor[better] = np.where(edge_numbers[selected] >= 0,
                                               selected_t, -1.0)

    return np.sqrt(distances2), locations, indices, factors


if HAS_NUMBA:
    @njit(cache=True, parallel=True)
    def _numba_query(points, starts, directions, length_squared, edge_numbers):
        count = len(points)
        dist = np.empty(count, dtype=np.float64)
        location = np.empty((count, 3), dtype=np.float64)
        indices = np.empty(count, dtype=np.int64)
        factors = np.empty(count, dtype=np.float64)
        for i in prange(count):
            bx, by, bz = np.nan, np.nan, np.nan
            best = np.inf
            best_i = -1
            best_t = -1.0
            px, py, pz = points[i, 0], points[i, 1], points[i, 2]
            for j in range(len(starts)):
                ax, ay, az = starts[j, 0], starts[j, 1], starts[j, 2]
                dx, dy, dz = directions[j, 0], directions[j, 1], directions[j, 2]
                d2_segment = length_squared[j]
                t = 0.0
                if d2_segment > 0.0:
                    t = ((px - ax) * dx + (py - ay) * dy +
                         (pz - az) * dz) / d2_segment
                    if t < 0.0:
                        t = 0.0
                    elif t > 1.0:
                        t = 1.0
                x, y, z = ax + t * dx, ay + t * dy, az + t * dz
                rx, ry, rz = px - x, py - y, pz - z
                candidate = rx * rx + ry * ry + rz * rz
                # Tolerant ties select the first target despite rounding.
                tolerance = 1.e-13 * max(candidate, best)
                if np.isinf(best) or candidate < best - tolerance:
                    best = candidate
                    bx, by, bz = x, y, z
                    best_i = edge_numbers[j]
                    best_t = t if best_i >= 0 else -1.0
            dist[i] = np.sqrt(best)
            location[i, 0], location[i, 1], location[i, 2] = bx, by, bz
            indices[i] = best_i
            factors[i] = best_t
        return dist, location, indices, factors


def _empty_hits():
    """Empty, typed results for a query with no matching targets."""
    return (np.empty(0, dtype=np.float64),
            np.empty((0, 3), dtype=np.float64),
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=np.float64))


def _distance_order(distances2, target_ids):
    """Sort ascending, resolving floating-point near-ties by target order.

    This mirrors the tolerant tie convention of the original nearest mode.
    A tie tolerance is relative, so tiny nonzero distances stay distinguishable.
    """
    order = np.lexsort((target_ids, distances2))
    if len(order) < 2:
        return order
    sorted_d2 = distances2[order]
    cutoff = 1.e-13 * np.maximum(
        np.maximum(sorted_d2[:-1], sorted_d2[1:]),
        np.finfo(np.float64).tiny)
    boundaries = np.flatnonzero(np.diff(sorted_d2) > cutoff) + 1
    group_starts = np.r_[0, boundaries]
    group_ends = np.r_[boundaries, len(order)]
    tied = group_ends - group_starts > 1
    for first, last in zip(group_starts[tied], group_ends[tied]):
        group = order[first:last]
        order[first:last] = group[np.argsort(target_ids[group], kind='stable')]
    return order


def _numpy_query_many(points, starts, directions, lengths2, numbers,
                      mode, max_distance, count, pair_budget):
    """Block-limited vectorized multi-query; keep only hits or top-k candidates."""
    num_points, num_targets = len(points), len(starts)
    if not num_points or not num_targets:
        return tuple([_empty_hits()[i] for _ in range(num_points)] for i in range(4))

    point_block = max(1, min(num_points, 128, pair_budget))
    edge_block = max(1, pair_budget // point_block)
    k_per_point = np.minimum(count, num_targets)
    radius2_per_point = max_distance * max_distance
    answers = [[] for _ in range(num_points)]
    for ps in range(0, num_points, point_block):
        p = points[ps:ps + point_block]
        for es in range(0, num_targets, edge_block):
            a = starts[es:es + edge_block]
            ab = directions[es:es + edge_block]
            l2 = lengths2[es:es + edge_block]
            ap = p[:, None, :] - a[None, :, :]
            dot = np.einsum('nkj,kj->nk', ap, ab)
            t = np.divide(dot, l2[None, :], out=np.zeros_like(dot),
                          where=l2[None, :] > 0.0)
            np.clip(t, 0.0, 1.0, out=t)
            loc = a[None, :, :] + t[:, :, None] * ab[None, :, :]
            residual = p[:, None, :] - loc
            d2 = np.einsum('nkj,nkj->nk', residual, residual)
            target_ids = np.arange(es, es + len(a))
            for row in range(len(p)):
                if mode == 'RANGE':
                    selected = np.flatnonzero(d2[row] <= radius2_per_point[ps + row])
                else:
                    # Stable argsort retains edge order when distances tie.
                    selected = _distance_order(d2[row], target_ids)[:k_per_point[ps + row]]
                if not len(selected):
                    continue
                indices = target_ids[selected]
                chunk = (d2[row, selected], indices,
                         loc[row, selected], t[row, selected])
                if mode == 'NEAREST_N' and answers[ps + row]:
                    previous = answers[ps + row][0]
                    merged = tuple(np.concatenate((previous[i], chunk[i]))
                                   for i in range(4))
                    order = _distance_order(merged[0], merged[1])[:k_per_point[ps + row]]
                    chunk = tuple(channel[order] for channel in merged)
                    answers[ps + row][0] = chunk
                else:
                    answers[ps + row].append(chunk)

    result = [[], [], [], []]
    for chunks in answers:
        if not chunks:
            hits = _empty_hits()
        else:
            all_d2, target_ids, coords, factors = (
                np.concatenate([chunk[i] for chunk in chunks], axis=0)
                for i in range(4))
            order = _distance_order(all_d2, target_ids)
            if mode == 'NEAREST_N':
                order = order[:k_per_point[len(result[0])]]
            ids = numbers[target_ids[order]]
            hits = (np.sqrt(all_d2[order]), coords[order], ids,
                    np.where(ids >= 0, factors[order], -1.0))
        for destination, value in zip(result, hits):
            destination.append(value)
    return tuple(result)


if HAS_NUMBA:
    @njit(inline='always')
    def _distance_to_segment(px, py, pz, starts, directions, lengths2, j):
        ax, ay, az = starts[j, 0], starts[j, 1], starts[j, 2]
        dx, dy, dz = directions[j, 0], directions[j, 1], directions[j, 2]
        t = 0.0
        if lengths2[j] > 0.0:
            t = ((px-ax)*dx + (py-ay)*dy + (pz-az)*dz) / lengths2[j]
            if t < 0.0:
                t = 0.0
            elif t > 1.0:
                t = 1.0
        x, y, z = ax+t*dx, ay+t*dy, az+t*dz
        return (px-x)**2 + (py-y)**2 + (pz-z)**2, x, y, z, t


    @njit(parallel=True, cache=True)
    def _numba_query_n(points, starts, directions, lengths2, numbers,
                       offsets):
        # Ragged compact arrays: each query uses exactly its own Count slots.
        # No memory allocation proportional to max(Count) * num_points.
        total = offsets[-1]
        d2 = np.full(total, np.inf)
        loc = np.full((total, 3), np.nan)
        indices = np.full(total, -1, dtype=np.int64)
        factors = np.full(total, -1.0)
        target_positions = np.full(total, -1, dtype=np.int64)
        for i in prange(len(points)):
            first, last = offsets[i], offsets[i+1]
            if first == last:
                continue
            px, py, pz = points[i, 0], points[i, 1], points[i, 2]
            for j in range(len(starts)):
                dist2, x, y, z, t = _distance_to_segment(
                    px, py, pz, starts, directions, lengths2, j)
                pos = last
                for m in range(first, last):
                    old = d2[m]
                    tol = 1.e-13 * max(dist2, old)
                    if (np.isinf(old) or dist2 < old - tol or
                        (abs(dist2 - old) <= tol and j < target_positions[m])):
                        pos = m
                        break
                if pos < last:
                    for m in range(last-1, pos, -1):
                        d2[m] = d2[m-1]
                        loc[m, 0] = loc[m-1, 0]
                        loc[m, 1] = loc[m-1, 1]
                        loc[m, 2] = loc[m-1, 2]
                        indices[m] = indices[m-1]
                        factors[m] = factors[m-1]
                        target_positions[m] = target_positions[m-1]
                    d2[pos] = dist2
                    loc[pos, 0], loc[pos, 1], loc[pos, 2] = x, y, z
                    indices[pos] = numbers[j]
                    factors[pos] = t if numbers[j] >= 0 else -1.0
                    target_positions[pos] = j
        return np.sqrt(d2), loc, indices, factors


    @njit(parallel=True, cache=True)
    def _numba_range_counts(points, starts, directions, lengths2, radius2):
        counts = np.zeros(len(points), dtype=np.int64)
        for i in prange(len(points)):
            px, py, pz = points[i, 0], points[i, 1], points[i, 2]
            n = 0
            for j in range(len(starts)):
                dist2, _, _, _, _ = _distance_to_segment(
                    px, py, pz, starts, directions, lengths2, j)
                if dist2 <= radius2[i]:
                    n += 1
            counts[i] = n
        return counts


    @njit(parallel=True, cache=True)
    def _numba_range_collect(points, starts, directions, lengths2,
                             radius2, offsets):
        total = offsets[-1]
        all_d2 = np.empty(total, dtype=np.float64)
        target_indices = np.empty(total, dtype=np.int64)
        all_loc = np.empty((total, 3), dtype=np.float64)
        all_t = np.empty(total, dtype=np.float64)
        for i in prange(len(points)):
            px, py, pz = points[i, 0], points[i, 1], points[i, 2]
            dest = offsets[i]
            for j in range(len(starts)):
                d2, x, y, z, t = _distance_to_segment(
                    px, py, pz, starts, directions, lengths2, j)
                if d2 <= radius2[i]:
                    all_d2[dest] = d2
                    target_indices[dest] = j
                    all_loc[dest, 0] = x
                    all_loc[dest, 1] = y
                    all_loc[dest, 2] = z
                    all_t[dest] = t
                    dest += 1
        return all_d2, target_indices, all_loc, all_t


def _numba_query_many(points, starts, directions, lengths2, numbers,
                      mode, max_distance, count):
    """JIT top-k or two-pass compact radius search, output one array per point."""
    num_points, num_targets = len(points), len(starts)
    if not num_points or not num_targets:
        return tuple([_empty_hits()[i] for _ in range(num_points)] for i in range(4))

    if mode == 'NEAREST_N':
        slots = np.minimum(count, num_targets)
        offsets = np.empty(num_points + 1, dtype=np.int64)
        offsets[0] = 0
        offsets[1:] = np.cumsum(slots)
        dense = _numba_query_n(points, starts, directions, lengths2,
                               numbers, offsets)
        return tuple([data[offsets[i]:offsets[i+1]] for i in range(num_points)]
                     for data in dense)

    radius2 = max_distance * max_distance
    counts = _numba_range_counts(points, starts, directions, lengths2, radius2)
    offsets = np.empty(num_points + 1, dtype=np.int64)
    offsets[0] = 0
    offsets[1:] = np.cumsum(counts)
    all_d2, target_ids, coords, t = _numba_range_collect(
        points, starts, directions, lengths2, radius2, offsets)
    result = [[], [], [], []]
    for i in range(num_points):
        first, last = int(offsets[i]), int(offsets[i+1])
        order = _distance_order(all_d2[first:last], target_ids[first:last])
        selected = first + order
        ids = numbers[target_ids[selected]]
        hits = (np.sqrt(all_d2[selected]), coords[selected], ids,
                np.where(ids >= 0, t[selected], -1.0))
        for destination, value in zip(result, hits):
            destination.append(value)
    return tuple(result)


def _point_parameters(value, num_points, name, match):
    """Expand one scalar or an object-level list to per-query values.

    Matching is only within the query point set. A single value broadcasts;
    SHORT with multiple values may intentionally reduce the number of points.
    """
    if np.isscalar(value):
        values = np.asarray([value], dtype=np.float64)
    else:
        values = np.asarray(value, dtype=np.float64)
        if values.ndim == 0:
            values = values.reshape(1)
        if values.ndim != 1:
            raise ValueError(f'{name} must be one scalar or a flat point-value list')
    if not len(values):
        raise ValueError(f'{name} must contain at least one value')
    if not np.all(np.isfinite(values)):
        raise ValueError(f'{name} values must be finite')
    if np.any(values < 0):
        raise ValueError(f'{name} values must be non-negative')
    if match not in {'REPEAT', 'CYCLE', 'SHORT'}:
        raise ValueError(f'Unknown point list-match mode: {match}')
    if match == 'SHORT' and len(values) > 1:
        size = min(num_points, len(values))
    else:
        size = num_points
    if size == 0:
        return np.empty(0, dtype=np.float64)
    if len(values) >= size:
        return np.ascontiguousarray(values[:size])
    if match == 'CYCLE':
        return np.ascontiguousarray(np.resize(values, size))
    return np.ascontiguousarray(values[np.minimum(np.arange(size), len(values)-1)])


def distance_to_edges(points, target_verts, target_edges, *, engine="AUTO",
                      include_loose=True, pair_budget=65536, mode="NEAREST",
                      max_distance=1.0, count=3, point_match='REPEAT'):
    """Query an indexed edge network.

    NEAREST returns four dense per-point arrays (backwards compatible).
    RANGE / NEAREST_N return four lists of per-point arrays, each containing
    zero or more sorted hits. Hits are unique per target edge, not per location.
    Loose vertices have Edge Index and Factor = -1.
    """
    points = _as_rows(points, 3, np.float64, "Points")
    if not np.all(np.isfinite(points)):
        raise ValueError("Points must contain finite coordinates")
    starts, directions, lengths2, numbers = _prepare_targets(
        target_verts, target_edges, include_loose)
    if engine not in {"AUTO", "NUMPY", "NUMBA"}:
        raise ValueError(f"Unknown engine: {engine}")
    if engine == "NUMBA" and not HAS_NUMBA:
        raise RuntimeError("Numba engine selected, but Numba is not installed")
    if pair_budget < 1:
        raise ValueError("pair_budget must be positive")
    if mode not in {"NEAREST", "RANGE", "NEAREST_N"}:
        raise ValueError(f"Unknown query mode: {mode}")
    # Controls can be scalar or have one value per query point. Only the active
    # input is read, so inactive linked data never changes query behavior.
    if mode == 'RANGE':
        max_distance = _point_parameters(max_distance, len(points),
                                         'Max Distance', point_match)
        points = points[:len(max_distance)]
    elif mode == 'NEAREST_N':
        count = _point_parameters(count, len(points), 'Count', point_match)
        points = points[:len(count)]
        # Sverchok number sockets may carry float values; truncate to integers.
        count = np.ascontiguousarray(np.minimum(count, len(starts)).astype(np.int64))
    # Auto favors the compiled backend for every input size when available.
    use_numba = engine == "NUMBA" or (engine == "AUTO" and HAS_NUMBA)
    if mode == "NEAREST":
        if use_numba:
            return _numba_query(points, starts, directions, lengths2, numbers)
        return _numpy_query(points, starts, directions, lengths2, numbers,
                            int(pair_budget))
    if use_numba:
        return _numba_query_many(points, starts, directions, lengths2, numbers,
                                 mode, max_distance, count)
    return _numpy_query_many(points, starts, directions, lengths2, numbers,
                             mode, max_distance, count, int(pair_budget))


def _row_like(row, width):
    if isinstance(row, np.ndarray):
        return row.ndim == 1 and row.shape[0] == width
    if isinstance(row, (str, bytes)):
        return False
    try:
        return len(row) == width and all(np.isscalar(x) for x in row)
    except (TypeError, ValueError):
        return False


def _is_object(data, width):
    if isinstance(data, np.ndarray):
        return ((data.ndim == 2 and data.shape[1] == width) or
                (data.ndim == 1 and data.size == 0))
    if not isinstance(data, (list, tuple)):
        return False
    return len(data) == 0 or _row_like(data[0], width)


def _as_group(data, width):
    if _is_object(data, width):
        return [data]
    if isinstance(data, np.ndarray):
        if data.ndim < 3:
            raise ValueError("Unsupported array nesting for points/geometry")
        return list(data)
    if isinstance(data, (list, tuple)):
        return list(data)
    raise ValueError("Expected nested lists of points, vertices and edges")


def _match_groups(groups, mode):
    if mode not in {"REPEAT", "CYCLE", "SHORT"}:
        raise ValueError(f"Unknown list-match mode: {mode}")
    if any(len(g) == 0 for g in groups):
        return []
    count = min(map(len, groups)) if mode == "SHORT" else max(map(len, groups))
    out = []
    for i in range(count):
        out.append(tuple(g[i] if i < len(g) else
                         (g[i % len(g)] if mode == "CYCLE" else g[-1])
                         for g in groups))
    return out


def recursive_distance_to_edges(points, vertices, edges, *,
                                list_match="REPEAT", engine="AUTO",
                                include_loose=True, output_numpy=False,
                                pair_budget=65536, mode="NEAREST",
                                max_distance=1.0, count=3):
    """Map whole point sets to whole edge networks at any nesting level.

    Only outer object/group levels are matched; point and edge rows are
    never list-matched against each other. Results preserve group structure.
    """
    def scalar_leaf(data):
        if np.isscalar(data):
            return True
        if isinstance(data, np.ndarray):
            return data.ndim <= 1
        if isinstance(data, (list, tuple)):
            return not data or all(np.isscalar(item) for item in data)
        return False

    def scalar_group(data):
        if scalar_leaf(data):
            return [data]
        if isinstance(data, (list, tuple, np.ndarray)):
            return list(data)
        raise ValueError('Expected nested numeric control lists')

    def visit(p, v, e, control):
        leaves = (_is_object(p, 3), _is_object(v, 3), _is_object(e, 2))
        if all(leaves) and (mode == 'NEAREST' or scalar_leaf(control)):
            kwargs = {'max_distance': control} if mode == 'RANGE' else (
                {'count': control} if mode == 'NEAREST_N' else {})
            result = distance_to_edges(p, v, e, engine=engine,
                                       include_loose=include_loose,
                                       pair_budget=pair_budget,
                                       mode=mode, point_match=list_match,
                                       **kwargs)
            if output_numpy:
                return result
            if mode == 'NEAREST':
                return tuple(x.tolist() for x in result)
            return tuple([row.tolist() for row in x] for x in result)

        groups = [_as_group(p, 3), _as_group(v, 3), _as_group(e, 2)]
        if mode != 'NEAREST':
            groups.append(scalar_group(control))
        branches = _match_groups(groups, list_match)
        outputs = ([], [], [], [])
        for sub in branches:
            result = visit(*sub) if mode != 'NEAREST' else visit(*sub, None)
            for out, value in zip(outputs, result):
                out.append(value)
        return outputs

    active_control = (max_distance if mode == 'RANGE'
                      else count if mode == 'NEAREST_N' else None)
    return visit(points, vertices, edges, active_control)
