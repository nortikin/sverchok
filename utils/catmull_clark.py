# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bmesh

from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh

def calc_new_verts(bm):
    verts, edges, faces = pydata_from_bmesh(bm)
    verts = np.asarray(verts)
    face_centers = np.array([tuple(f.calc_center_median()) for f in bm.faces])
    edge_verts = np.array([verts[e] for e in edges])

    face_centers_by_edge = np.array([[face_centers[f.index] for f in e.link_faces] for e in bm.edges])
    points_by_edge = [np.vstack(([face_centers[f.index] for f in e.link_faces], edge_verts[e.index])) for e in bm.edges]
    edge_points = np.mean(points_by_edge, axis=1)
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

        new_verts_from_verts[vert.index] = (F + 2*R + (n-3)*P) / n

    return new_verts_from_verts, new_verts_from_edges, new_verts_from_faces

def subdivide_once(bm, normal_update = False):
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
    for i in range(iterations):
        bm = subdivide_once(bm)
    bm.normal_update()
    return bm

