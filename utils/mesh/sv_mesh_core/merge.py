# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
import numpy as np

from .buffers import RaggedArray
from .weld import duplicate_map


def mesh_edges(faces, extra_edges=()):
    pairs = []
    for face in faces:
        # Array slicing uses elementwise addition, not concatenation; use a
        # list here so the final closing edge is never silently omitted.
        ring = list(face)
        pairs.extend(zip(ring, ring[1:] + ring[:1]))
    pairs.extend(extra_edges)
    result, seen = [], set()
    for a, b in pairs:
        if a == b:
            continue
        key = (min(a, b), max(a, b))
        if key not in seen:
            seen.add(key)
            result.append([int(a), int(b)])
    return result


def _split_face(face):
    """Split a pinched loop and remove collapsed edges and polygons."""
    stack, positions, polygons = [], {}, []
    for vertex in face + face[:1]:
        if vertex in positions:
            start = positions[vertex]
            polygon = stack[start:]
            if len(polygon) >= 3:
                polygons.append(polygon)
            for removed in stack[start+1:]:
                positions.pop(removed)
            stack = stack[:start+1]
        else:
            positions[vertex] = len(stack)
            stack.append(vertex)
    return polygons


def _regular_topology(poly_edge, remap, count, face_data, output_numpy=False, *,
                      output_edges=True, output_faces=True, output_face_data=True):
    """Vectorized reconstruction for regular, noncollapsed polygon batches."""
    if not len(poly_edge):
        return [], [], []
    try:
        indices = np.asarray(poly_edge, dtype=np.intp)
    except ValueError:
        return None
    if indices.ndim != 2:
        return None
    indices = np.where(indices < 0, indices+count, indices)
    if np.any(indices < 0) or np.any(indices >= count):
        raise IndexError("Merge by Distance vertex index out of range")
    mapped = remap[indices]
    faces, data = [], []
    if mapped.shape[1] != 2:
        if mapped.shape[1] < 3 or np.any(np.diff(np.sort(mapped,axis=1),axis=1) == 0):
            return None
        if output_faces or output_face_data:
            # Canonical cyclic/winding-independent keys avoid dropping the
            # source FaceData for the first retained polygon.
            rows = np.arange(len(mapped))[:,None]
            starts = np.argmin(mapped,axis=1)[:,None]
            shifts = np.arange(mapped.shape[1])[None,:]
            forward = mapped[rows,(starts+shifts) % mapped.shape[1]]
            backward = mapped[rows,(starts-shifts) % mapped.shape[1]]
            canonical = np.where((forward[:,1] < backward[:,1])[:,None],forward,backward)
            _, first = np.unique(canonical,axis=0,return_index=True)
            first.sort()
            if output_faces:
                faces = mapped[first] if output_numpy else mapped[first].tolist()
            if output_face_data and len(face_data):
                data = [face_data[i] if i < len(face_data) else None for i in first]
    if not output_edges:
        return faces, data, np.empty((0,2), dtype=np.intp) if output_numpy else []
    if mapped.shape[1] == 2:
        pairs = mapped
    else:
        pairs = np.column_stack((mapped.ravel(),np.roll(mapped,-1,axis=1).ravel()))
    pairs = pairs[pairs[:,0] != pairs[:,1]]
    low, high = np.minimum(pairs[:,0],pairs[:,1]), np.maximum(pairs[:,0],pairs[:,1])
    _, first = np.unique(low.astype(np.int64)*max(count,1)+high,return_index=True)
    result_edges = pairs[np.sort(first)]
    return faces, data, result_edges if output_numpy else result_edges.tolist()


def merge_by_distance(vertices, poly_edge, distance, face_data=(), mask=(),
                      output_doubles=True, output_mask=True, use_numba=True, *,
                      backend='AUTO', reference_version='4.3', output_numpy=False,
                      output_edges=True, output_polygons=True, output_face_data=True):
    """Independent mesh weld with a speed-first GRID clustering default.

    This is the *portable* backend: it never constructs a BMesh. It exposes
    the original node's features (mask, face data, wires, ngons and doubles),
    without promising Blender's element indexing or output ordering.
    Unlinked topology outputs may be omitted for faster node evaluation.
    """
    vertices = np.asarray(vertices, dtype=np.float32).reshape(-1, 3)
    if not np.all(np.isfinite(vertices)) or not np.isfinite(distance) or distance < 0:
        raise ValueError("Merge by Distance needs finite coordinates and a nonnegative Distance")
    if isinstance(poly_edge, RaggedArray):
        poly_edge = list(poly_edge)
    count = len(vertices)
    selected = np.ones(count, dtype=np.bool_)
    input_mask = np.asarray(mask)
    if input_mask.ndim > 1:
        raise ValueError('Mask must be a flat sequence')
    if input_mask.size:
        full_mask = np.empty(count, dtype=input_mask.dtype)
        used = min(count, len(input_mask))
        full_mask[:used] = input_mask[:used]
        full_mask[used:] = input_mask[-1]
        selected[:] = full_mask.astype(np.bool_)
    else:
        full_mask = np.empty(0, dtype=np.bool_)
    selected_indices = np.flatnonzero(selected)
    target = np.arange(count, dtype=np.intp)
    if len(selected_indices) > 1:
        # No vertex copy when the whole array is selected.  Particularly
        # useful for large meshes whose input is already an ndarray.
        if len(selected_indices) == count:
            target = duplicate_map(vertices, distance, reference_version=reference_version,
                                   backend=backend, use_numba=use_numba)
        else:
            local_targets = duplicate_map(vertices[selected_indices], distance,
                                          reference_version=reference_version,
                                          backend=backend, use_numba=use_numba)
            target[selected_indices] = selected_indices[local_targets]

    representatives = np.flatnonzero(target == np.arange(count))
    compact = np.full(count, -1, dtype=np.intp)
    compact[representatives] = np.arange(len(representatives))
    remap = compact[target]
    want_faces = output_polygons or output_face_data
    output_faces, output_data, seen_faces, extra_edges = [], [], set(), []
    edge_mode = len(poly_edge) > 0 and len(poly_edge[0]) == 2
    if output_edges or want_faces:
        regular = _regular_topology(poly_edge, remap, count, face_data, output_numpy,
                                    output_edges=output_edges, output_faces=output_polygons,
                                    output_face_data=output_face_data)
    else:
        regular = ([], [], np.empty((0,2), dtype=np.intp) if output_numpy else [])
    for source, element in enumerate(poly_edge if regular is None else ()):
        indices = np.asarray(element, dtype=np.intp)
        indices = np.where(indices < 0, indices+count, indices)
        if np.any(indices < 0) or np.any(indices >= count):
            raise IndexError("Merge by Distance vertex index out of range")
        mapped = remap[indices].tolist()
        if edge_mode:
            if output_edges: extra_edges.append(mapped)
            continue
        if output_edges: extra_edges.extend(zip(mapped, mapped[1:]+mapped[:1]))
        if not want_faces: continue
        for face in _split_face(mapped):
            start = face.index(min(face))
            forward = face[start:]+face[:start]
            backward = forward[:1]+forward[:0:-1]
            key = min(tuple(forward), tuple(backward))
            if key not in seen_faces:
                seen_faces.add(key)
                if output_polygons: output_faces.append(face)
                if output_face_data and len(face_data):
                    output_data.append(face_data[source] if source < len(face_data) else None)
    if regular is None:
        # The source-loop edges are already present in extra_edges, including
        # the closing edges of any pinched face split by _split_face.
        # Do not seed mesh_edges from output_faces: that changes edge order
        # depending on whether the Polygons socket is linked.
        result_edges = mesh_edges([], extra_edges) if output_edges else []
    else:
        output_faces, output_data, result_edges = regular
    doubles = vertices[target != np.arange(count)] if output_doubles else np.empty((0, 3),dtype=np.float32)
    mask_result = full_mask[representatives] if output_mask and len(full_mask) else np.empty(0, dtype=bool)
    output_vertices = vertices[representatives]
    if output_numpy:
        return (output_vertices, np.asarray(result_edges, dtype=np.intp).reshape(-1, 2),
                RaggedArray.from_rows(output_faces), output_data,
                doubles.astype(np.float32, copy=False), mask_result)
    return (output_vertices.tolist(), result_edges, output_faces,
            output_data, doubles.tolist(), mask_result.tolist())
