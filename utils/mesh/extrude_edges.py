# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle
from mathutils import Matrix, Vector
import bmesh.ops
from numpy import(
    array as np_array,
    zeros as np_zeros,
    unique as np_unique,
    concatenate as np_concatenate,
    ndarray as np_ndarray,
    transpose as np_transpose
)
from sverchok.data_structure import match_long_repeat, repeat_last_for_length
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh, bmesh_edges_from_edge_mask
from sverchok.utils.modules.matrix_utils import matrix_apply_np
from sverchok.utils.bvh_tree import bvh_tree_from_polygons


def extrude_edges(vertices, edges, faces, edge_mask, face_data, matrices):
    if not matrices:
        matrices = [Matrix()]
    if face_data:
        face_data_matched = repeat_last_for_length(face_data, len(faces))
    if edge_mask:
        edge_mask_matched = repeat_last_for_length(edge_mask, len(edges))

    if isinstance(edges, np_ndarray):
        if edge_mask:
            np_edges = edges[edge_mask_matched]
        else:
            np_edges = edges
    else:
        if edge_mask:
            np_edges = np_array(edges)[edge_mask_matched]
        else:
            np_edges = np_array(edges)
    if isinstance(vertices, np_ndarray):
        np_verts = vertices
    else:
        np_verts = np_array(vertices)

    affeced_verts_idx = np_unique(np_edges)
    if len(matrices) == 1:
        extruded_verts = matrix_apply_np(np_verts[affeced_verts_idx], matrices[0])
        new_vertices = np_concatenate([np_verts, extruded_verts]).tolist()
    else:
        extruded_verts = [m @ Vector(v)
                          for v, m in zip(np_verts[affeced_verts_idx].tolist(), cycle(matrices))]
        new_vertices = vertices + extruded_verts

    top_edges = np_edges + len(vertices)
    mid_edges = np_zeros((len(affeced_verts_idx), 2), dtype=int)
    mid_edges[:, 0] = affeced_verts_idx
    mid_edges[:, 1] = affeced_verts_idx + len(vertices)
    extruded_edges_py = (np_concatenate([top_edges, mid_edges])).tolist()
    extruded_faces = np_zeros((len(np_edges), 4), dtype=int)
    extruded_faces[:, : 2] = np_edges
    extruded_faces[:, 2] = top_edges[:, 1]
    extruded_faces[:, 3] = top_edges[:, 0]
    extruded_faces_py = extruded_faces.tolist()
    if isinstance(edges, np_ndarray):
        new_edges = np_concatenate([edges, top_edges, mid_edges]).tolist()
    else:
        new_edges = edges + extruded_edges_py

    if faces and faces[0]:
        if isinstance(faces, np_ndarray):
            new_faces = np_concatenate([faces, extruded_faces]).tolist()
        else:
            new_faces = faces + extruded_faces_py
    else:
        new_faces = extruded_faces_py

    if face_data:
        bvh = bvh_tree_from_polygons(vertices, faces, all_triangles=False, epsilon=0.0, safe_check=True)
        mid_points = (np_verts[np_edges[:, 1]] + np_verts[np_edges[:, 0]])/2
        face_idx = [bvh.find_nearest(P)[2] for P in mid_points.tolist()]
        new_face_data = face_data_matched+ [face_data_matched[p] for p in face_idx]
    else:
        new_face_data = []

    return (new_vertices, new_edges, new_faces,
            extruded_verts, extruded_edges_py, extruded_faces_py,
            new_face_data)

def extrude_edges_bmesh(vertices, edges, faces, edge_mask, face_data, matrices):
    if not matrices:
        matrices = [Matrix()]
    if face_data:
        face_data_matched = repeat_last_for_length(face_data, len(faces))

    bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True, markup_edge_data=True)
    if edge_mask:
        b_edges = bmesh_edges_from_edge_mask(bm, edge_mask)
    else:
        b_edges = bm.edges

    new_geom = bmesh.ops.extrude_edge_only(bm, edges=b_edges, use_select_history=False)['geom']

    extruded_verts = [v for v in new_geom if isinstance(v, bmesh.types.BMVert)]
    if len(matrices) == 1:
        bmesh.ops.transform(bm, verts=extruded_verts, matrix=matrices[0], space=Matrix())
    else:
        for vertex, matrix in zip(*match_long_repeat([extruded_verts, matrices])):
            bmesh.ops.transform(bm, verts=[vertex], matrix=matrix, space=Matrix())

    extruded_verts = [tuple(v.co) for v in extruded_verts]

    extruded_edges = [e for e in new_geom if isinstance(e, bmesh.types.BMEdge)]
    extruded_edges = [tuple(v.index for v in edge.verts) for edge in extruded_edges]

    extruded_faces = [f for f in new_geom if isinstance(f, bmesh.types.BMFace)]
    extruded_faces = [[v.index for v in edge.verts] for edge in extruded_faces]

    if face_data:
        new_vertices, new_edges, new_faces, new_face_data = pydata_from_bmesh(bm, face_data_matched)
    else:
        new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
        new_face_data = []
    bm.free()
    return (new_vertices, new_edges, new_faces,
            extruded_verts, extruded_edges, extruded_faces,
            new_face_data)
