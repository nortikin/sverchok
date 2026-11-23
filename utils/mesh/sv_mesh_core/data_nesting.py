# SPDX-License-Identifier: GPL-3.0-or-later
"""Tree matching for Merge by Distance's optional explicit edges and attributes.

No Blender imports. A single mesh's vertices/topology drive the interpretation
of attributes, which may contain arbitrary nested payloads. At ambiguous levels
whose item count equals the corresponding element count, data is per-element.
"""
from .nesting import _items, _leaf, _match, _mesh_co


def _attribute_leaf(value, *, expected=None):
    seq = _items(value)
    if seq is None or not seq:
        return True
    if all(_items(item) is None for item in seq):
        return True
    return expected is not None and len(seq) == expected


def map_mesh_tree_data(vertices, poly, face_data, mask, distance,
                       edges, vert_data, edge_data, operation, *, matching='REPEAT'):
    """Recursively map an 8-input / 11-output mesh operation.

    Input order: vertices, PolyEdge, FaceData, Mask, Distance, Edges,
    VertData, EdgeData. The first five arguments retain v9.1 semantics.
    Every output has the same mesh-group nesting.
    """
    kinds = ('vertices', 'poly', 'face_data', 'mask', 'distance',
             'edges', 'vert_data', 'edge_data')

    def visit(values, depth):
        if depth > 64:
            raise ValueError('Merge by Distance nested beyond 64 levels')
        leaves = [_leaf(v, kind) if kind in
                  ('vertices', 'poly', 'face_data', 'mask', 'distance') else
                  _leaf(v, 'poly') if kind == 'edges' else False
                  for v, kind in zip(values, kinds)]
        verts, poly_value, face_value, _, _, edge_value, vdata, edata = values
        if leaves[0]:
            verts_count = len(_items(verts) or [])
            poly_count = len(_items(poly_value) or []) if leaves[1] else None
            edge_count = len(_items(edge_value) or []) if leaves[5] else None
            if not leaves[2]:
                leaves[2] = _attribute_leaf(face_value, expected=poly_count)
            leaves[6] = _attribute_leaf(vdata, expected=verts_count)
            leaves[7] = _attribute_leaf(edata, expected=edge_count)
        else:
            # Flat arrays are attributes supplied to every leaf mesh.
            leaves[6] = _attribute_leaf(vdata)
            leaves[7] = _attribute_leaf(edata)
        if all(leaves):
            v,p,f,m,d,e,vd,ed = values
            return operation(_mesh_co(v),p,f,m,float(d),e,vd,ed)
        axes, varying = [], []
        for value, leaf in zip(values, leaves):
            if leaf:
                axes.append(None)
            else:
                seq = _items(value)
                if seq is None:
                    raise ValueError('Unexpected scalar in mesh collection')
                axes.append(seq)
                varying.append(seq)
        children = []
        for group in _match(varying, matching):
            iterator = iter(group)
            children.append(visit(tuple(value if axis is None else next(iterator)
                                        for value, axis in zip(values, axes)), depth+1))
        return tuple([child[index] for child in children] for index in range(11))

    return visit((vertices, poly, face_data, mask, distance,
                  edges, vert_data, edge_data), 0)
