# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Implementation of Catmull-Clark subdivision algorithm in pure Python, with use
of NumPy and Blender's bmesh library.
"""

import numpy as np

import bmesh

from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh

def calc_new_verts(bm):
    """
    Calculate coordinates of new vertices by Catmull-Clark algorithm.

    Args:
        bm: input mesh, as Blender's bmesh object.

    Returns:
        Lists of new vertices, all as np.ndarray of shape (x, 3):

        * new vertices to replace vertices of original mesh
        * new vertices to be placed in the middles of edges
        * new vertices to be placed in the middles of faces
    """
    verts, edges, faces = pydata_from_bmesh(bm)
    verts = np.asarray(verts)
    face_centers = np.array([tuple(f.calc_center_median()) for f in bm.faces])
    edge_verts = np.array([verts[e] for e in edges])

    points_by_edge = np.array([np.vstack(([face_centers[f.index] for f in e.link_faces], edge_verts[e.index])) for e in bm.edges])
    edge_points = np.array([np.mean(pts, axis=0) if len(pts) == 4 else np.mean(pts[1:], axis=0) for pts in points_by_edge])
    edge_centers = np.mean(edge_verts, axis=1)

    new_verts_from_faces = face_centers
    new_verts_from_edges = edge_points

    new_verts_from_verts = np.zeros((len(bm.verts), 3))

    for vert in bm.verts:
        n = len(vert.link_faces)
        linked_face_idxs = [f.index for f in vert.link_faces]
        linked_edge_idxs = [e.index for e in vert.link_edges]
        
        P = np.array(vert.co)
        F = np.mean(face_centers[linked_face_idxs], axis=0)
        R = np.mean(edge_centers[linked_edge_idxs], axis=0)

        if n >= 3:
            new_verts_from_verts[vert.index] = (F + 2*R + (n-3)*P) / n
        elif n == 2:
            new_verts_from_verts[vert.index] = P
        else:
            new_verts_from_verts[vert.index] = (R + P) / 2

    return new_verts_from_verts, new_verts_from_edges, new_verts_from_faces

def subdivide_once(bm, normal_update = False):
    """
    Subdivide mesh by use of Catmull-Clark algorithm, one time.

    Args:
        bm: input mesh - as bmesh object.
        normal_update: if True, recalculate mesh normals in the end.

    Returns:
        new bmesh object.
    """
    points_from_verts, points_from_edges, points_from_faces = calc_new_verts(bm)

    new_bm = bmesh.new()

    new_vert_verts = [new_bm.verts.new(v) for v in points_from_verts]
    new_face_verts = [new_bm.verts.new(v) for v in points_from_faces]
    new_edge_verts = [new_bm.verts.new(v) for v in points_from_edges]

    new_bm.verts.index_update()
    new_bm.verts.ensure_lookup_table()

    for orig_face in bm.faces:
        n_edges = len(orig_face.edges)
        face_vert = new_face_verts[orig_face.index]
        loop = orig_face.loops[0]
        for i in range(n_edges):
            edge = loop.edge
            prev_edge = loop.link_loop_prev.edge
            edge_vert = new_edge_verts[edge.index]
            prev_edge_vert = new_edge_verts[prev_edge.index]
            vert_vert = new_vert_verts[loop.vert.index]
            new_bm.faces.new([vert_vert, edge_vert, face_vert, prev_edge_vert])
            loop = loop.link_loop_next
            
    new_bm.edges.index_update()
    new_bm.edges.ensure_lookup_table()
    new_bm.faces.index_update()
    new_bm.faces.ensure_lookup_table()
    if normal_update:
        new_bm.normal_update()

    return new_bm

def subdivide(bm, iterations=1):
    """
    Subdivide mesh by use of Catmull-Clark algorithm, one or several times.

    Args:
        bm: input mesh - as bmesh object.
        iterations: number of times the subdivision is to be applied.

    Returns:
        new bmesh object.
    """
    for i in range(iterations):
        bm = subdivide_once(bm)
    bm.normal_update()
    return bm

