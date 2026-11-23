# SPDX-License-Identifier: GPL-3.0-or-later
"""Shape-aware, portable mesh tree matching.

Mesh leaves have shape (n, 3), including an empty mesh. Non-mesh inputs
are repeated/cycled/truncated at object levels and are NEVER matched against
individual vertices, polygon indices or face attributes. This module has no
Blender dependency.

Distance is explicitly a single *scalar per mesh*, not a radius per vertex.
The caller may remove Sverchok's outer numerical-socket wrapper once before
passing it to :func:`map_mesh_tree`.
"""
from numbers import Real

import numpy as np


def _items(value):
    if isinstance(value, np.ndarray):
        return list(value) if value.ndim else None
    if isinstance(value, (list, tuple)):
        return value
    # mathutils.Vector and other sequence-valued vertex rows are supported
    # without importing Blender. Strings/dicts remain atomic FaceData values.
    if isinstance(value, (str, bytes, dict)):
        return None
    if hasattr(value, '__len__') and hasattr(value, '__iter__'):
        return list(value)
    return None


def _real(value):
    return isinstance(value, Real) or (isinstance(value, np.ndarray) and value.ndim == 0
                                       and np.issubdtype(value.dtype, np.number))


def _vector(value):
    if isinstance(value, np.ndarray):
        return value.ndim == 1 and value.shape[0] == 3 and np.issubdtype(value.dtype, np.number)
    seq = _items(value)
    return seq is not None and len(seq) == 3 and all(_real(x) for x in seq)


def _mesh(value):
    if isinstance(value, np.ndarray):
        return (value.ndim == 2 and value.shape[1] == 3 and
                np.issubdtype(value.dtype, np.number)) or _vector(value) or (
                value.ndim == 1 and value.dtype == object and
                (not len(value) or all(_vector(v) for v in value)))
    seq = _items(value)
    return seq is not None and (not seq or _vector(value) or all(_vector(v) for v in seq))


def _polygons(value):
    """A polygon batch is a sequence of rows of integral indices."""
    if isinstance(value, np.ndarray):
        if value.ndim == 2 and np.issubdtype(value.dtype, np.integer):
            return True
        if value.ndim == 1 and value.dtype == object:
            return all(_polygons([row]) for row in value)
        return False
    seq = _items(value)
    if seq is None:
        return False
    if not seq:
        return True
    for row in seq:
        line = _items(row)
        if line is None or any(not isinstance(x, (int, np.integer)) for x in line):
            return False
    return True


def _flat(value):
    if isinstance(value, np.ndarray):
        return value.ndim <= 1
    seq = _items(value)
    return seq is not None and (not seq or all(_items(item) is None for item in seq))


def _leaf(value, kind):
    if kind == 'vertices':
        return _mesh(value)
    if kind == 'poly':
        return _polygons(value)
    if kind in ('face_data', 'mask'):
        return _flat(value)
    if kind == 'distance':
        return _real(value)
    raise ValueError('Unknown mesh input: '+kind)


def _match(sequences, mode):
    sizes = [len(x) for x in sequences]
    limit = min(sizes) if mode == 'SHORT' else max(sizes)
    if mode not in ('REPEAT', 'CYCLE', 'SHORT'):
        raise ValueError('Unsupported list matching: '+str(mode))
    if not limit or (mode != 'SHORT' and any(not x for x in sequences)):
        # Explicitly supplied empty group yields no meshes. Empty mesh-related
        # leaves are handled above and are NOT confused with this case.
        return []
    result = []
    for index in range(limit):
        row = []
        for seq in sequences:
            position = (min(index, len(seq)-1) if mode == 'REPEAT' else
                        index % len(seq) if mode == 'CYCLE' else index)
            row.append(seq[position])
        result.append(row)
    return result


def _mesh_co(value):
    if _vector(value):
        return np.asarray(value, np.float32).reshape(1, 3)
    if isinstance(value, np.ndarray):
        if value.ndim == 1 and value.dtype == object:
            return np.asarray([list(row) for row in value], dtype=np.float32).reshape(-1, 3)
        return value
    if value and _vector(value[0]) and not isinstance(value[0], (list, tuple, np.ndarray)):
        return [list(row) for row in value]
    return value


def map_mesh_tree(vertices, poly, face_data, mask, distance, operation, *, matching='REPEAT'):
    """Map a 5-input mesh operation recursively, preserving its output structure.

    ``operation`` receives (vertices, poly, face_data, mask, scalar_distance)
    and must return exactly six corresponding mesh outputs.

    In every dimension, optional data may be leaf/broadcast or an explicitly
    nested collection of leaves. A one-mesh input may be expanded to match a
    larger Distance list, as usual in Sverchok list matching. A short Mask or
    FaceData leaf is never repeated as a *mesh collection*.
    """
    kinds = ('vertices', 'poly', 'face_data', 'mask', 'distance')

    def visit(values, depth):
        if depth > 64:
            raise ValueError('Mesh data nested beyond 64 collection levels')
        is_leaf = [_leaf(value, kind) for value, kind in zip(values, kinds)]
        # FaceData is allowed to hold non-scalar payloads (e.g. RGB arrays
        # or variable-length attributes). At a mesh leaf, a collection whose
        # length equals the source polygon count is face-level data, not a
        # new level of *mesh* collections.
        if is_leaf[0] and is_leaf[1] and not is_leaf[2]:
            attrs = _items(values[2])
            polys = _items(values[1])
            if attrs is not None and polys is not None and len(attrs) == len(polys):
                is_leaf[2] = True
        if all(is_leaf):
            v, p, f, m, d = values
            return operation(_mesh_co(v), p, f, m, float(d))
        # Match only axes that represent *mesh collections*. A leaf is a
        # broadcast value (for instance an unlinked optional input), not a
        # one-item collection. Otherwise SHORT would truncate two meshes to
        # one merely because an unconnected socket supplies a leaf default.
        axes = []
        varying = []
        for value, leaf in zip(values, is_leaf):
            if leaf:
                axes.append(None)
            else:
                seq = _items(value)
                if seq is None:
                    raise ValueError('Unexpected non-sequence in nested mesh data')
                axes.append(seq)
                varying.append(seq)
        matched = _match(varying, matching)
        children = []
        for group in matched:
            next_child = iter(group)
            child_values = tuple(value if axis is None else next(next_child)
                                 for value, axis in zip(values, axes))
            children.append(visit(child_values, depth+1))
        return tuple([child[i] for child in children] for i in range(6))

    return visit((vertices, poly, face_data, mask, distance), 0)
