# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later

from itertools import chain

import numpy as np

from sverchok.dependencies import numba
from sverchok.utils.decorators_compilation import njit


def _normalize_indices(indices, vertex_count):
    negative = indices < 0
    if negative.any():
        indices = indices.copy()
        indices[negative] += vertex_count
    if np.any(indices < 0) or np.any(indices >= vertex_count):
        raise IndexError("Smooth Vertices: vertex index out of range")
    return indices


@njit(cache=True)
def _smooth_unique_edges_numba(all_edges, vertex_count, face_edge_count):
    seen = {}
    output = np.empty_like(all_edges)
    counts = np.zeros(len(all_edges), dtype=np.intp)
    size = 0
    for i in range(len(all_edges)):
        a, b = all_edges[i]
        key = min(a, b) * vertex_count + max(a, b)
        if key not in seen:
            seen[key] = size
            output[size] = all_edges[i]
            size += 1
        if i < face_edge_count:
            counts[seen[key]] += 1
    return output[:size], counts[:size]


def _mesh_topology(vertex_count, edges, faces, compiled=False, need_incidence=False):
    """Build the undirected edge set in face-first, first-encounter order."""
    face_edges = np.empty((0, 2), dtype=np.intp)
    output_faces = []
    corners = np.empty(0, dtype=np.intp)
    lengths = np.empty(0, dtype=np.intp)
    if len(faces):
        try:
            regular_faces = np.asarray(faces, dtype=np.intp)
        except ValueError:
            lengths = np.fromiter(map(len, faces), dtype=np.intp, count=len(faces))
            if np.any(lengths < 3):
                raise ValueError("Smooth Vertices: a face needs at least three vertices")
            corners = np.fromiter(chain.from_iterable(faces), dtype=np.intp)
            corners = _normalize_indices(corners, vertex_count)
            previous = np.roll(corners, 1)
            ends = lengths.cumsum() - 1
            previous[np.r_[0, ends[:-1] + 1]] = corners[ends]
            face_edges = np.column_stack((previous, corners))
            output_faces = np.split(corners, ends[:-1] + 1)
        else:
            if regular_faces.shape[1] < 3:
                raise ValueError("Smooth Vertices: a face needs at least three vertices")
            regular_faces = _normalize_indices(regular_faces, vertex_count)
            lengths = np.full(len(regular_faces), regular_faces.shape[1], dtype=np.intp)
            corners = regular_faces.ravel()
            previous = np.roll(regular_faces, 1, axis=1)
            face_edges = np.column_stack((previous.ravel(), regular_faces.ravel()))
            output_faces = regular_faces

    explicit_edges = np.asarray(edges, dtype=np.intp).reshape(-1, 2)
    explicit_edges = _normalize_indices(explicit_edges, vertex_count)
    all_edges = np.concatenate((face_edges, explicit_edges))
    if not len(all_edges):
        return all_edges, output_faces, corners, lengths, np.empty(0, dtype=np.intp)

    if np.any(all_edges[:, 0] == all_edges[:, 1]):
        raise ValueError("Smooth Vertices: an edge needs two distinct vertices")

    # Only face incidences classify boundary edges; explicit edges add no faces.
    if compiled:
        face_count = len(face_edges) if need_incidence else 0
        mesh_edges, counts = _smooth_unique_edges_numba(all_edges, vertex_count, face_count)
    else:
        low = np.minimum(all_edges[:, 0], all_edges[:, 1]).astype(np.int64, copy=False)
        high = np.maximum(all_edges[:, 0], all_edges[:, 1]).astype(np.int64, copy=False)
        keys = low * vertex_count + high
        if need_incidence:
            _, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
        else:
            _, first = np.unique(keys, return_index=True)
        order = np.argsort(first)
        mesh_edges = all_edges[first[order]]
        counts = (np.bincount(inverse[:len(face_edges)], minlength=len(first))[order]
                  if need_incidence else np.empty(0, dtype=np.intp))
    return mesh_edges, output_faces, corners, lengths, counts


def _selected_neighbors(edges, selected):
    """Return selected vertex indices and their neighbors in CSR order."""
    starts = edges.ravel()
    ends = edges[:, ::-1].ravel()
    order = np.argsort(starts, kind='stable')
    starts = starts[order]
    ends = ends[order]
    counts = np.bincount(starts, minlength=len(selected))
    active = np.flatnonzero(selected & (counts > 0))
    keep = selected[starts]
    offsets = np.empty(len(active) + 1, dtype=np.intp)
    offsets[0] = 0
    np.cumsum(counts[active], out=offsets[1:])
    return active, offsets, ends[keep]


@njit(cache=True)
def _smooth_neighbors_numba(edges, selected):
    counts = np.zeros(len(selected), dtype=np.intp)
    for a, b in edges:
        counts[a] += 1
        counts[b] += 1
    active = np.nonzero(selected & (counts > 0))[0]
    offsets = np.zeros(len(active) + 1, dtype=np.intp)
    index = np.full(len(selected), -1, dtype=np.intp)
    for i in range(len(active)):
        index[active[i]] = i
        offsets[i + 1] = offsets[i] + counts[active[i]]
    neighbors = np.empty(offsets[-1], dtype=np.intp)
    cursor = offsets[:-1].copy()
    for a, b in edges:
        for vertex, neighbor in ((a, b), (b, a)):
            i = index[vertex]
            if i >= 0:
                neighbors[cursor[i]] = neighbor
                cursor[i] += 1
    return active, offsets, neighbors


def _smooth_numpy(vertices, active, offsets, neighbors, inverse_degree, axes, clip,
                  clip_dist, factor, iterations):
    for _ in range(iterations):
        for axis in np.flatnonzero(axes):
            coords = vertices[:, axis]
            current = coords[active]
            average = np.add.reduceat(coords[neighbors], offsets[:-1]) * inverse_degree
            updated = current * (np.float32(1) - factor) + average * factor
            if clip[axis]:
                updated[np.abs(current) <= clip_dist] = 0
            coords[active] = updated


@njit(cache=True)
def _smooth_vertices_numba(vertices, active, offsets, neighbors, inverse_degree, axes, clip,
                           clip_dist, factor, iterations):
    updated = np.empty((len(active), 3), dtype=np.float32)
    for _ in range(iterations):
        for i in range(len(active)):
            tx, ty, tz = np.float32(0), np.float32(0), np.float32(0)
            for j in range(offsets[i], offsets[i + 1]):
                neighbor = neighbors[j]
                tx += vertices[neighbor, 0]
                ty += vertices[neighbor, 1]
                tz += vertices[neighbor, 2]
            total = (tx, ty, tz)
            for axis in range(3):
                current = vertices[active[i], axis]
                if clip[axis] and abs(current) <= clip_dist:
                    updated[i, axis] = 0
                else:
                    average = total[axis] * inverse_degree[i]
                    updated[i, axis] = current * (np.float32(1) - factor) + average * factor
        for i in range(len(active)):
            for axis in range(3):
                if axes[axis]:
                    vertices[active[i], axis] = updated[i, axis]


def smooth_vertices(verts, edges, faces, mask, axes, clip, clip_dist, factor, iterations,
                    use_numba=False, laplacian=False, border_factor=0.5, preserve_volume=True,
                    output_vertices=True, output_edges=True, output_faces=True,
                    numpy_vertices=False, numpy_edges=False):
    """Smooth selected vertices over mesh edges and return Sverchok mesh data."""
    vertices = np.array(verts, dtype=np.float32, copy=True).reshape(-1, 3)
    compiled = use_numba and numba is not None
    mesh_edges, polygons, corners, lengths, incidence = _mesh_topology(
        len(vertices), edges, faces, compiled, need_incidence=laplacian)
    mask = np.asarray(mask, dtype=np.bool_)[:len(vertices)]
    selected = np.full(len(vertices), mask[-1] if len(mask) else False, dtype=np.bool_)
    selected[:len(mask)] = mask
    axes = np.asarray(axes, dtype=np.bool_)
    clip = np.asarray(clip, dtype=np.bool_)

    if output_vertices and iterations > 0 and axes.any() and selected.any() and len(mesh_edges):
        if laplacian:
            from sverchok.utils.mesh.smooth_laplacian import laplacian_smooth
            laplacian_smooth(vertices, mesh_edges, polygons, corners, lengths, incidence,
                             selected, axes, factor, border_factor, preserve_volume,
                             iterations, compiled)
        else:
            neighbors_kernel = _smooth_neighbors_numba if compiled else _selected_neighbors
            active, offsets, neighbors = neighbors_kernel(mesh_edges, selected)
            if len(active):
                inverse_degree = np.float32(1) / np.diff(offsets).astype(np.float32)
                kernel = _smooth_vertices_numba if compiled else _smooth_numpy
                kernel(vertices, active, offsets, neighbors, inverse_degree, axes, clip,
                       np.float32(clip_dist), np.float32(factor), iterations)

    faces_result = None
    if output_faces:
        faces_result = (polygons.tolist() if isinstance(polygons, np.ndarray)
                        else [face.tolist() for face in polygons])
    vertices_result = None
    if output_vertices:
        vertices_result = vertices if numpy_vertices else list(map(tuple, vertices.tolist()))
    edges_result = None
    if output_edges:
        edges_result = mesh_edges if numpy_edges else mesh_edges.tolist()
    return vertices_result, edges_result, faces_result
