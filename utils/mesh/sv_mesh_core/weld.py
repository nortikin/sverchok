# SPDX-License-Identifier: GPL-3.0-or-later
# KD layout/search port based on Blender Authors' GPL-2.0-or-later code:
# Blender v4.3.2 blenlib/intern/kdtree_impl.h and v5.1.0 BLI_kdtree.hh,
# bmesh/operators/bmo_removedoubles.cc. See REFERENCES.md in the package.
"""Versioned duplicate maps, independent of mesh topology and Blender.

GRID is the default portable policy, with Numba, SciPy or Python search.
The explicit legacy policies use a versioned Blender KD layout for comparison.
Duplicate maps have runtime regression tests in Blender 4.3.2 and 5.1.0.
This does not certify complete mesh topology or the node's other outputs.
"""
import numpy as np

from .optional import njit, numba, scipy_tree, has_scipy


def _balanced_layout(points):
    count = len(points)
    order = np.arange(count, dtype=np.intp)
    axes = np.zeros(count, dtype=np.intp)
    left_child = np.full(count, -1, dtype=np.intp)
    right_child = np.full(count, -1, dtype=np.intp)
    parents = np.full(count, -1, dtype=np.intp)
    # Explicit stack also works in plain Python and avoids recursion limits.
    stack = [(0, count, 0)]
    while stack:
        begin, length, axis = stack.pop()
        if length <= 1:
            continue
        left, right, median = begin, begin+length-1, begin+length//2
        while right > left:
            pivot = points[order[right], axis]
            i, j = left-1, right
            while True:
                i += 1
                while points[order[i], axis] < pivot:
                    i += 1
                j -= 1
                while points[order[j], axis] > pivot and j > left:
                    j -= 1
                if i >= j:
                    break
                order[i], order[j] = order[j], order[i]
            order[i], order[right] = order[right], order[i]
            if i >= median:
                right = i-1
            if i <= median:
                left = i+1
        axes[median] = axis
        left_length, right_length = length//2, length-length//2-1
        if left_length:
            child = begin+left_length//2
            left_child[median] = child
            parents[child] = median
        if right_length:
            child = median+1+right_length//2
            right_child[median] = child
            parents[child] = median
        stack.append((median+1, right_length, (axis+1)%3))
        stack.append((begin, left_length, (axis+1)%3))
    return order, axes, left_child, right_child, parents


_balanced_layout_numba = njit(cache=True)(_balanced_layout)


def _range_candidates(points, order, axes, left, right, search, distance, modern):
    stack = [len(order)//2]
    found = []
    threshold = np.float32(distance*distance)
    while stack:
        node = stack.pop()
        index = order[node]
        axis = axes[node]
        high = np.float32(points[search, axis]+distance)
        low = np.float32(points[search, axis]-distance)
        coordinate = points[index, axis]
        below = high < coordinate if modern else high <= coordinate
        above = low > coordinate if modern else low >= coordinate
        if below:
            if left[node] >= 0:
                stack.append(left[node])
        elif above:
            if right[node] >= 0:
                stack.append(right[node])
        else:
            x = np.float32(points[index, 0]-points[search, 0])
            y = np.float32(points[index, 1]-points[search, 1])
            z = np.float32(points[index, 2]-points[search, 2])
            squared = np.float32(np.float32(x*x+y*y)+z*z)
            if squared <= threshold:
                found.append(index)
            # 4.3 uses recursive left-first; 5.1 uses a right-first stack.
            first = left[node] if modern else right[node]
            second = right[node] if modern else left[node]
            if first >= 0:
                stack.append(first)
            if second >= 0:
                stack.append(second)
    return found


_range_candidates_numba = njit(cache=True)(_range_candidates)


def _central_target(points, cluster):
    if len(cluster) == 2:
        return min(cluster[0], cluster[1])
    centroid = np.zeros(3, dtype=np.float32)
    for index in cluster:
        for axis in range(3):
            centroid[axis] = np.float32(centroid[axis]+points[index, axis])
    for axis in range(3):
        centroid[axis] = np.float32(centroid[axis]/np.float32(len(cluster)))
    best = cluster[-1]
    x = np.float32(centroid[0]-points[best, 0])
    y = np.float32(centroid[1]-points[best, 1])
    z = np.float32(centroid[2]-points[best, 2])
    best_distance = np.float32(np.float32(x*x+y*y)+z*z)
    for index in cluster[:-1]:
        x = np.float32(centroid[0]-points[index, 0])
        y = np.float32(centroid[1]-points[index, 1])
        z = np.float32(centroid[2]-points[index, 2])
        distance = np.float32(np.float32(x*x+y*y)+z*z)
        if distance > best_distance:
            continue
        if distance == best_distance and index > best:
            continue
        best, best_distance = index, distance
    return best


_central_target_numba = njit(cache=True)(_central_target)


def _duplicate_map(points, distance, order, axes, left, right, modern):
    targets = np.full(len(points), -1, dtype=np.intp)
    for search in order:
        if targets[search] != -1:
            continue
        candidates = _range_candidates(points, order, axes, left, right, search, distance, modern)
        if modern:
            cluster = [index for index in candidates if targets[index] == -1]
            if len(cluster):
                # Preserve the literal 5.1 implementation, including the
                # search index appended after the callback's range results.
                cluster.append(search)
                target = _central_target(points, cluster)
                for index in cluster:
                    targets[index] = target
        else:
            found = False
            for index in candidates:
                if index != search and targets[index] == -1:
                    targets[index] = search
                    found = True
            if found:
                targets[search] = search
    for index in range(len(targets)):
        if targets[index] < 0:
            targets[index] = index
    return targets


if numba is not None:
    # These remain ordinary Python functions when called from the NumPy
    # backend; Numba compiles their bodies when reached from compiled code.
    numba.extending.register_jitable(_range_candidates)
    numba.extending.register_jitable(_central_target)
_duplicate_map_numba = njit(cache=True)(_duplicate_map)


@njit(cache=True)
def _filter_scipy_candidates(points, near, distance, order, axes, parents, positions, search, modern):
    valid = []
    threshold = np.float32(distance*distance)
    for index in near:
        x = np.float32(points[index,0]-points[search,0])
        y = np.float32(points[index,1]-points[search,1])
        z = np.float32(points[index,2]-points[search,2])
        if np.float32(np.float32(x*x+y*y)+z*z) > threshold:
            continue
        child = node = positions[index]
        allowed = True
        while node >= 0:
            axis = axes[node]
            coordinate = points[order[node],axis]
            high = np.float32(points[search,axis]+distance)
            low = np.float32(points[search,axis]-distance)
            below = high < coordinate if modern else high <= coordinate
            above = low > coordinate if modern else low >= coordinate
            if (below and child >= node) or (above and child <= node):
                allowed = False
                break
            child, node = node, parents[node]
        if allowed:
            valid.append(index)
    return valid


def _scipy_map(points, distance, order, axes, left, right, parents, modern, compiled):
    tree = scipy_tree()(points)
    # Broad phase in float64, followed by Blender's float32 predicates.
    threshold = np.float32(distance*distance)
    # Float32 squared distances can underflow to zero or overflow to infinity.
    # A float64 radius equal to distance would then miss Blender candidates.
    rounded_upper = np.nextafter(threshold, np.float32(np.inf))
    radius = max(float(distance), np.sqrt(float(rounded_upper)))*(1+8*np.finfo(np.float32).eps)
    positions = np.empty(len(order), dtype=np.intp)
    positions[order] = np.arange(len(order))
    ranks = np.empty(len(order), dtype=np.intp)
    traversal, stack = [], [len(order)//2]
    while stack:
        node = stack.pop()
        traversal.append(node)
        first = left[node] if modern else right[node]
        second = right[node] if modern else left[node]
        if first >= 0:
            stack.append(first)
        if second >= 0:
            stack.append(second)
    ranks[np.asarray(traversal)] = np.arange(len(order))
    targets = np.full(len(points), -1, dtype=np.intp)
    for search in order:
        if targets[search] != -1:
            continue
        near = np.asarray(tree.query_ball_point(points[search], radius, eps=0,
                                               return_sorted=False), dtype=np.intp)
        if not len(near):
            continue
        near = near[targets[near] == -1]
        # Reproduce ancestor pruning too, including exact threshold planes.
        filter_candidates = _filter_scipy_candidates if compiled else getattr(_filter_scipy_candidates,'py_func',_filter_scipy_candidates)
        valid = filter_candidates(points,near,distance,order,axes,parents,positions,search,modern)
        if modern:
            if valid:
                valid.sort(key=lambda index: int(ranks[positions[index]]))
                valid.append(search)
                target = _central_target(points, valid)
                targets[valid] = target
        else:
            valid = [index for index in valid if index != search]
            if valid:
                targets[valid] = search
                targets[search] = search
    return np.where(targets < 0, np.arange(len(targets)), targets)


def duplicate_map(vertices, distance, *, reference_version='4.3', backend='AUTO', use_numba=True):
    """Return a vertex-aligned representative map. Coordinates are float32.

    AUTO/GRID use the independent, deterministic GRID policy. Explicit
    NUMPY/NUMBA/SCIPY retain the old Blender 4.3/5.1 KD-tree policies.
    """
    points = np.asarray(vertices, dtype=np.float32).reshape(-1, 3)
    if not np.isfinite(distance) or distance < 0 or not np.all(np.isfinite(points)):
        raise ValueError('Finite coordinates and nonnegative finite distance required')
    if reference_version not in ('4.3', '5.1'):
        raise ValueError('Unsupported Blender merge policy: '+str(reference_version))
    distance = np.float32(distance)
    if not np.isfinite(distance):
        raise ValueError('Distance must fit float32')
    if backend not in ('NUMPY', 'NUMBA', 'SCIPY', 'GRID', 'GRID_SCIPY', 'GRID_PY', 'AUTO'):
        raise ValueError('Unknown neighbor backend: '+str(backend))
    if not len(points):
        return np.empty(0, dtype=np.intp)
    if backend in ('GRID', 'GRID_SCIPY', 'GRID_PY', 'AUTO'):
        # Independent GRID policy is now the default in *all* environments;
        # Numba only changes how its candidate search is accelerated.
        # Explicit NUMPY/NUMBA/SCIPY remain for old Blender KD-policy tests.
        if backend in ('GRID', 'AUTO') and use_numba and numba is not None:
            from .grid_weld import grid_duplicate_map
            return grid_duplicate_map(points, distance)
        from .grid_fallback import grid_map_python, grid_map_scipy
        if backend == 'GRID_PY':
            return grid_map_python(points, distance)
        if backend == 'GRID_SCIPY':
            return grid_map_scipy(points, distance)
        if has_scipy():
            return grid_map_scipy(points, distance)
        return grid_map_python(points, distance)
    numba_enabled = use_numba and numba is not None
    compiled = numba_enabled and backend in ('NUMBA','SCIPY')
    layout = (_balanced_layout_numba if compiled else _balanced_layout)(points)
    order, axes, left, right, parents = layout
    modern = reference_version == '5.1'
    if backend == 'SCIPY':
        return _scipy_map(points, distance, order, axes, left, right, parents, modern, compiled)
    kernel = _duplicate_map_numba if backend == 'NUMBA' and compiled else _duplicate_map
    return kernel(points, distance, order, axes, left, right, modern)
