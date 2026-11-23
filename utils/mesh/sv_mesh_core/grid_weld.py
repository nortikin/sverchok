# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fast portable non-transitive merge using a Numba spatial hash.

This intentionally does NOT reproduce BMesh's KD-tree traversal or vertex
representative selection.  Features are the same, but borderline chains and
clusters can choose different vertices and generate different topology.
The old versioned KD policy is retained as a separate compatibility backend.
"""
import numpy as np

from .optional import njit, numba

if numba is not None:
    from numba import types
    from numba.typed import Dict
    _CELL_TYPE = types.UniTuple(types.int64, 3)
    _POINT_TYPE = types.UniTuple(types.float32, 3)


@njit(cache=True)
def _exact_map(points):
    # Exact distance=0 matches coordinates including +/-0.0.  There is no
    # float32 squared-distance underflow rule in this independent algorithm.
    index = Dict.empty(key_type=_POINT_TYPE, value_type=types.int64)
    target = np.empty(len(points), dtype=np.intp)
    for i in range(len(points)):
        # Numba's typed-dict hashes signed zero bitwise in some versions.
        # Canonicalize it so +0.0 and -0.0 compare as equal coordinates.
        x = points[i, 0] if points[i, 0] != 0 else np.float32(0)
        y = points[i, 1] if points[i, 1] != 0 else np.float32(0)
        z = points[i, 2] if points[i, 2] != 0 else np.float32(0)
        key = (x, y, z)
        if key in index:
            target[i] = index[key]
        else:
            index[key] = i
            target[i] = i
    return target


@njit(cache=True)
def _grid_map(points, distance):
    count = len(points)
    result = np.full(count, -1, dtype=np.intp)
    # Relative-origin cell coordinates avoid overflows and precision loss
    # for meshes located far from world origin.
    origin = np.empty(3, dtype=np.float64)
    for axis in range(3):
        origin[axis] = np.min(points[:, axis])
    cells = np.empty((count, 3), dtype=np.int64)
    for i in range(count):
        for axis in range(3):
            cells[i, axis] = np.int64(np.floor((np.float64(points[i, axis]) - origin[axis])/distance))
    head = Dict.empty(key_type=_CELL_TYPE, value_type=types.int64)
    next_item = np.full(count, -1, dtype=np.intp)
    # Insertion backwards keeps stable order inside a cell.
    for i in range(count-1, -1, -1):
        key = (cells[i, 0], cells[i, 1], cells[i, 2])
        if key in head:
            next_item[i] = head[key]
        head[key] = i
    radius_squared = distance*distance
    for i in range(count):
        if result[i] != -1:
            continue
        cx, cy, cz = cells[i, 0], cells[i, 1], cells[i, 2]
        group = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    key = (cx+dx, cy+dy, cz+dz)
                    if key not in head:
                        continue
                    j = head[key]
                    while j != -1:
                        if result[j] == -1:
                            a = np.float64(points[j, 0]) - np.float64(points[i, 0])
                            b = np.float64(points[j, 1]) - np.float64(points[i, 1])
                            c = np.float64(points[j, 2]) - np.float64(points[i, 2])
                            if a*a+b*b+c*c <= radius_squared:
                                group.append(j)
                        j = next_item[j]
        # Use a true (float64) centroid rather than whichever input happened
        # to be first, to minimize representative displacement in a cluster.
        if len(group) <= 1:
            best = i
        else:
            mx = my = mz = 0.0
            for j in group:
                mx += points[j, 0]; my += points[j, 1]; mz += points[j, 2]
            inv = 1.0/len(group)
            mx *= inv; my *= inv; mz *= inv
            best = group[0]
            best_distance = np.inf
            for j in group:
                a = np.float64(points[j, 0])-mx
                b = np.float64(points[j, 1])-my
                c = np.float64(points[j, 2])-mz
                squared = a*a+b*b+c*c
                if squared < best_distance or (squared == best_distance and j < best):
                    best, best_distance = j, squared
        for j in group:
            result[j] = best
    return result


@njit(cache=True)
def _sweep_map(points, distance):
    """Precision-safe fallback for cell ranges exceeding the hash limit.

    Sweep in the widest axis and retain GRID's input-order, non-transitive
    membership and centroid representative policy. This only runs when
    relative-origin cells cannot be represented precisely as int64 indices.
    """
    count=len(points)
    lower=np.empty(3,dtype=np.float64)
    upper=np.empty(3,dtype=np.float64)
    for axis in range(3):
        lower[axis]=np.min(points[:,axis]);upper[axis]=np.max(points[:,axis])
    axis=np.argmax(upper-lower)
    order=np.argsort(points[:,axis])
    coords=points[order,axis]
    target=np.full(count,-1,dtype=np.intp)
    distance_squared=distance*distance
    for i in range(count):
        if target[i]!=-1:continue
        x=np.float64(points[i,axis])
        begin=np.searchsorted(coords,x-distance,'left')
        end=np.searchsorted(coords,x+distance,'right')
        group=[]
        for position in range(begin,end):
            j=order[position]
            if target[j]!=-1:continue
            a=np.float64(points[j,0])-np.float64(points[i,0])
            b=np.float64(points[j,1])-np.float64(points[i,1])
            c=np.float64(points[j,2])-np.float64(points[i,2])
            if a*a+b*b+c*c <= distance_squared:
                group.append(j)
        if len(group)<=1:
            representative=i
        else:
            mx=my=mz=0.0
            for j in group:
                mx+=points[j,0];my+=points[j,1];mz+=points[j,2]
            factor=1.0/len(group)
            mx*=factor;my*=factor;mz*=factor
            representative=group[0]
            best_distance=np.inf
            for j in group:
                a=np.float64(points[j,0])-mx
                b=np.float64(points[j,1])-my
                c=np.float64(points[j,2])-mz
                squared=a*a+b*b+c*c
                if squared<best_distance or (squared==best_distance and j<representative):
                    representative,best_distance=j,squared
        for j in group:
            target[j]=representative
    return target


def grid_duplicate_map(vertices, distance):
    """Representative per input vertex, deterministic for a given input order.

    Grid cells have side ``distance``. Only still-unassigned points within
    a *Euclidean* radius of each seed are grouped; chains are not unioned
    transitively. Representative is the group member closest to its centroid.
    """
    if numba is None:
        raise ImportError('The GRID merge backend requires Numba')
    points = np.asarray(vertices, dtype=np.float32).reshape(-1, 3)
    radius = float(distance)
    if not np.isfinite(radius) or radius < 0 or not np.all(np.isfinite(points)):
        raise ValueError('GRID requires finite vertices and nonnegative finite radius')
    if not len(points):
        return np.empty(0, dtype=np.intp)
    if radius == 0:
        return _exact_map(points)
    # A cell index must be exact in float64 and fit into signed int64.
    # For extremely large dynamic ranges, use a sort/sweep with identical
    # GRID clustering semantics rather than silently change its policy.
    extent = np.ptp(points.astype(np.float64), axis=0)
    if np.max(extent) / radius >= 2**50:
        return _sweep_map(points, radius)
    return _grid_map(points, radius)
