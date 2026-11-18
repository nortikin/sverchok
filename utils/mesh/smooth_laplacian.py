# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Cotangent weights and edge validation follow Blender's
# source/blender/bmesh/operators/bmo_smooth_laplacian.cc (GPL-2.0-or-later).

import numpy as np

from sverchok.utils.decorators_compilation import njit


def _laplacian_weights_numpy(vertices, loops):
    count = len(vertices)
    prev, curr, following = loops.T
    a, b, c = vertices[prev], vertices[curr], vertices[following]
    ab, ac = b - a, c - a
    cross = np.cross(ab, ac)
    twice_area = np.sqrt((cross * cross).sum(axis=1))
    area = twice_area * np.float32(0.5)
    # w1, w2, w3 are opposite (prev,next), (prev,curr), (curr,next).
    numerators = np.column_stack((((a-b)*(c-b)).sum(axis=1),
                                  ((a-c)*(b-c)).sum(axis=1),
                                  (ab*ac).sum(axis=1)))
    weights = np.zeros_like(numerators)
    np.divide(numerators, twice_area[:, None] * np.float32(2), out=weights,
              where=twice_area[:, None] > np.finfo(np.float32).eps)
    w1, w2, w3 = weights.T
    ring = np.zeros(count, dtype=np.float32)
    sums = np.zeros(count, dtype=np.float32)
    np.add.at(ring, loops.ravel(), np.repeat(area, 3))
    np.add.at(sums, loops.ravel(),
              np.column_stack((w1+w2, w2+w3, w1+w3)).ravel())
    zero = np.zeros(count, dtype=np.bool_)
    zero[curr[area < np.float32(1e-5)]] = True
    return weights, ring, sums, zero


@njit(cache=True)
def _laplacian_weights_numba(vertices, loops):
    count = len(vertices)
    weights = np.zeros((len(loops), 3), dtype=np.float32)
    ring = np.zeros(count, dtype=np.float32)
    sums = np.zeros(count, dtype=np.float32)
    zero = np.zeros(count, dtype=np.bool_)
    for i in range(len(loops)):
        p, c, n = loops[i]
        ab = vertices[c] - vertices[p]
        ac = vertices[n] - vertices[p]
        cross = np.cross(ab, ac)
        length = np.sqrt(np.sum(cross * cross))
        area = length * np.float32(0.5)
        if area < np.float32(1e-5):
            zero[c] = True
        if length > np.float32(1.1920929e-7):
            weights[i, 0] = np.sum((vertices[p]-vertices[c]) *
                                   (vertices[n]-vertices[c])) / (np.float32(2)*length)
            weights[i, 1] = np.sum((vertices[p]-vertices[n]) *
                                   (vertices[c]-vertices[n])) / (np.float32(2)*length)
            weights[i, 2] = np.sum(ab*ac) / (np.float32(2)*length)
        w1, w2, w3 = weights[i]
        for vertex in (p, c, n):
            ring[vertex] += area
        sums[p] += w1+w2
        sums[c] += w2+w3
        sums[n] += w1+w3
    return weights, ring, sums, zero


def _laplacian_cgls_impl(rows, cols, values, rhs, initial, inverse_diagonal):
    """Solve the rectangular least-squares system without a dense matrix."""
    row_count = len(rhs)
    column_count = len(initial)

    def multiply(x, transpose):
        size = column_count if transpose else row_count
        result = np.empty((size, 3), dtype=np.float64)
        target = cols if transpose else rows
        source = rows if transpose else cols
        for axis in range(3):
            result[:, axis] = np.bincount(
                target, weights=values * x[source, axis], minlength=size)
        return result

    x = initial.copy()
    normal_rhs = multiply(rhs, True)
    residual = normal_rhs - multiply(multiply(x, False), True)
    threshold = np.maximum(np.sum(normal_rhs*normal_rhs, axis=0) * 1e-20, 1e-28)
    preconditioned = residual * inverse_diagonal[:, None]
    direction = preconditioned.copy()
    rho = np.sum(residual * preconditioned, axis=0)
    for _ in range(min(4 * column_count + 32, 10000)):
        done = np.sum(residual*residual, axis=0) <= threshold
        if np.all(done):
            return x, True
        projected = multiply(direction, False)
        denominator = np.sum(projected*projected, axis=0)
        alpha = np.zeros(3, dtype=np.float64)
        for axis in range(3):
            if not done[axis] and denominator[axis] > 0:
                alpha[axis] = rho[axis] / denominator[axis]
        x += direction * alpha
        residual -= multiply(projected, True) * alpha
        preconditioned = residual * inverse_diagonal[:, None]
        next_rho = np.sum(residual * preconditioned, axis=0)
        beta = np.zeros(3, dtype=np.float64)
        for axis in range(3):
            if not done[axis] and rho[axis] > 0:
                beta[axis] = next_rho[axis] / rho[axis]
        direction = preconditioned + direction * beta
        rho = next_rho
    return x, False


_laplacian_cgls_numba = njit(cache=True)(_laplacian_cgls_impl)


def _ngon_triangles(coords, normal):
    """Ear clipping in Blender's alternating traversal order."""
    remaining = list(range(len(coords)))
    candidate = 0
    reverse = False
    triangles = []
    while len(remaining) > 3:
        signs = []
        for i, vertex in enumerate(remaining):
            a, b, c = coords[remaining[i-1]], coords[vertex], coords[remaining[(i+1) % len(remaining)]]
            signs.append(np.sign(np.dot(np.cross(b-a, c-b), normal)))
        chosen = None
        for wanted in (1, 0):
            for step in range(len(remaining)):
                i = (candidate + (-step if reverse else step)) % len(remaining)
                if all(sign == 1 for sign in signs):
                    chosen = i
                    break
                if signs[i] != wanted:
                    continue
                a, b, c = (remaining[(i-1) % len(remaining)], remaining[i],
                           remaining[(i+1) % len(remaining)])
                inside = False
                for j, vertex in enumerate(remaining):
                    if vertex in (a, b, c) or signs[j] == 1:
                        continue
                    point = coords[vertex]
                    if all(np.dot(np.cross(coords[v]-coords[u], point-coords[u]), normal) >= 0
                           for u, v in ((c,a), (a,b), (b,c))):
                        inside = True
                        break
                if not inside:
                    chosen = i
                    break
            if chosen is not None:
                break
        if chosen is None:
            chosen = next((i for i, sign in enumerate(signs) if sign >= 0), candidate)
        i = chosen
        prev, vertex, following = remaining[i-1], remaining[i], remaining[(i+1) % len(remaining)]
        triangles.append((prev, vertex, following))
        remaining.pop(i)
        # Removing the first list element also updates Blender's list head.
        candidate_vertex = remaining[(remaining.index(prev)-1) % len(remaining)] if reverse else (
            remaining[(remaining.index(following)+1) % len(remaining)])
        candidate = remaining.index(candidate_vertex)
        a, b, c = coords[remaining[candidate-1]], coords[candidate_vertex], coords[
            remaining[(candidate+1) % len(remaining)]]
        if np.dot(np.cross(b-a, c-b), normal) <= 0:
            candidate = (candidate + (-1 if reverse else 1)) % len(remaining)
            reverse = not reverse
    triangles.append(tuple(remaining))
    return np.asarray(triangles, dtype=np.intp)


def _volume(vertices, groups, normals):
    triangle_faces, quad_faces, ngons = groups
    parts = [vertices[triangle_faces]]
    if len(quad_faces):
        faces, face_indices = quad_faces
        coords = vertices[faces]
        turn = np.cross(coords - np.roll(coords, 1, axis=1),
                        np.roll(coords, -1, axis=1) - coords)
        signs = (turn * normals[face_indices, None, :]).sum(axis=2)
        chosen = np.full(len(coords), -1, dtype=np.intp)
        all_convex = np.all(signs > 0, axis=1)
        chosen[all_convex] = 0
        for wanted in (1, 0):
            for i in range(4):
                if np.all(chosen >= 0):
                    break
                a, b, c, other = (i-1) % 4, i, (i+1) % 4, (i+2) % 4
                inside = np.ones(len(coords), dtype=np.bool_)
                for u, v in ((c,a), (a,b), (b,c)):
                    side = np.cross(coords[:,v]-coords[:,u], coords[:,other]-coords[:,u])
                    inside &= (side * normals[face_indices]).sum(axis=1) >= 0
                blocked = (signs[:,other] <= 0) & inside
                accept = (chosen < 0) & (np.sign(signs[:,i]) == wanted) & ~blocked
                chosen[accept] = i
        fallback = np.argmax(signs >= 0, axis=1)
        chosen[chosen < 0] = fallback[chosen < 0]
        alternate = chosen % 2 == 1
        tri = np.empty((len(faces), 2, 3), dtype=np.intp)
        tri[:] = ((3,0,1), (1,2,3))
        tri[alternate] = ((0,1,2), (0,2,3))
        parts.append(coords[np.arange(len(coords))[:,None,None], tri].reshape(-1,3,3))
    for face_index, face in ngons:
        coords = vertices[face]
        parts.append(coords[_ngon_triangles(coords, normals[face_index])])
    coords = np.concatenate(parts).astype(np.float64)
    terms = (coords[:, 0] * np.cross(coords[:, 1], coords[:, 2])).sum(axis=1)
    return np.float32(abs(terms.sum() / 6))


def laplacian_smooth(vertices, edges, polygons, corners, lengths, incidence, selected,
                     axes, factor, border_factor, preserve_volume, iterations, compiled):
    if not len(corners):
        return
    count = len(vertices)
    factor, border_factor = np.float32(factor), np.float32(border_factor)
    ends = np.cumsum(lengths)
    starts = np.r_[0, ends[:-1]]
    previous = np.roll(corners, 1)
    following = np.roll(corners, -1)
    previous[starts] = corners[ends-1]
    following[ends-1] = corners[starts]
    loops = np.column_stack((previous, corners, following))
    boundary_edges = edges[incidence == 1]
    boundary = np.zeros(count, dtype=np.bool_)
    boundary[boundary_edges.ravel()] = True
    # Sverchok selects every face before the BMesh operator. That also selects
    # its edges, which Blender excludes from inverse-length boundary weights.
    active = np.flatnonzero(selected)
    column_index = np.full(count, -1, dtype=np.intp)
    column_index[active] = np.arange(len(active))
    # Match Blender's least-squares mask semantics. Locked variables start at
    # zero in its solver, while their mesh coordinates remain unchanged.

    # Entries match Blender's six cotangent contributions per face corner.
    p, c, n = loops.T
    face_rows = np.column_stack((p, p, c, c, n, n)).ravel()
    face_cols = np.column_stack((c, n, n, p, c, p)).ravel()
    rows = np.concatenate((active, face_rows))
    cols = column_index[np.concatenate((active, face_cols))]
    keep = cols >= 0
    # Aggregate duplicates once. Only numerical values change per iteration.
    keys, inverse = np.unique(rows[keep] * len(active) + cols[keep], return_inverse=True)
    rows, cols = keys // len(active), keys % len(active)
    weight_kernel = _laplacian_weights_numba if compiled else _laplacian_weights_numpy
    solver = _laplacian_cgls_numba if compiled else _laplacian_cgls_impl

    volume_groups = None
    if preserve_volume:
        triangle_faces = np.asarray(
            [face for face in polygons if len(face) == 3], dtype=np.intp).reshape(-1, 3)
        quad_indices = np.flatnonzero(lengths == 4)
        quad_faces = ()
        if len(quad_indices):
            quad_faces = (np.asarray([polygons[i] for i in quad_indices], dtype=np.intp),
                          quad_indices)
        ngons = [(i, face) for i, face in enumerate(polygons) if len(face) > 4]
        volume_groups = triangle_faces, quad_faces, ngons

    for _ in range(iterations):
        normals = None
        if preserve_volume:
            delta = vertices[previous] - vertices[corners]
            total = vertices[previous] + vertices[corners]
            newell = delta[:, (1,2,0)] * total[:, (2,0,1)]
            normals = np.add.reduceat(newell, starts)
        weights, ring, sums, zero = weight_kernel(vertices, loops)
        valid = selected & ~zero & (ring != 0)
        vertex_scale = sums.copy()
        divisor = np.float32(4) * (sums[valid] * ring[valid])
        vertex_scale[valid] = np.divide(-factor, divisor, out=np.zeros_like(divisor),
                                       where=divisor != 0)
        diagonal = np.ones(count, dtype=np.float32)
        interior = valid & ~boundary
        diagonal[interior] += factor / (np.float32(4)*ring[interior])
        diagonal[valid & boundary] += border_factor * np.float32(2)
        w1, w2, w3 = weights.T
        face_values = np.column_stack((w2, w1, w3, w2, w3, w1)).ravel()
        face_values *= vertex_scale[face_rows]
        face_values[zero[face_rows] | boundary[face_rows]] = 0
        values = np.concatenate((diagonal[active], face_values))
        values = np.bincount(inverse, weights=values[keep], minlength=len(keys))
        diagonal_normal = np.bincount(cols, weights=values*values, minlength=len(active))
        inverse_diagonal = np.divide(1, diagonal_normal, out=np.ones_like(diagonal_normal),
                                     where=diagonal_normal != 0)
        rhs = np.zeros((count, 3), dtype=np.float64)
        rhs[active] = vertices[active]
        solution, converged = solver(rows, cols, values, rhs,
                                     vertices[active].astype(np.float64), inverse_diagonal)
        if not converged and count * len(active) <= 262144:
            # Small, badly conditioned systems can stagnate in normal-equation
            # CG. An SVD solve avoids squaring their condition number.
            matrix = np.zeros((count, len(active)), dtype=np.float64)
            matrix[rows, cols] = values
            solution = np.linalg.lstsq(matrix, rhs, rcond=None)[0]
            converged = True
        if not converged or not np.all(np.isfinite(solution)):
            raise RuntimeError("Laplacian solver did not converge; try a smaller Factor")
        proposed = np.zeros_like(vertices)
        proposed[active] = solution
        old_delta = vertices[edges[:, 0]] - vertices[edges[:, 1]]
        new_delta = proposed[edges[:, 0]] - proposed[edges[:, 1]]
        old_length = np.sqrt((old_delta*old_delta).sum(axis=1))
        new_length = np.sqrt((new_delta*new_delta).sum(axis=1))
        rejected = (new_length > old_length*np.float32(1.8)) | (
            new_length < old_length*np.float32(0.15))
        zero[edges[rejected].ravel()] = True
        volume_before = _volume(vertices, volume_groups, normals) if preserve_volume else np.float32(0)
        moving = np.flatnonzero(selected & ~zero)
        for axis in np.flatnonzero(axes):
            vertices[moving, axis] = proposed[moving, axis]
        if preserve_volume:
            volume_after = _volume(vertices, volume_groups, normals)
            if volume_after != 0:
                scale = np.float32(float(volume_before/volume_after) ** float(np.float32(1)/3))
                for axis in np.flatnonzero(axes):
                    vertices[active, axis] *= scale
