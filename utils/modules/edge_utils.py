# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from mathutils import Vector, Matrix
from math import acos, pi
import numpy as np
from numpy.linalg import norm as np_norm
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.matrix_utils import matrix_normal, vectors_to_matrix, vectors_center_axis_to_matrix
from sverchok.utils.modules.vertex_utils import vertex_shell_factor
def edges_aux(vertices):
    '''create auxiliary edges array '''
    v_len = [len(v) for v in vertices]
    v_len_max = max(v_len)
    np_in = np.arange(v_len_max - 1)
    np_edges = np.array([np_in, np_in + 1]).T

    return [np_edges]

def edges_length(vertices, edges, sum_length=False, out_numpy=False):
    '''calculate edges length '''

    np_verts = np.array(vertices)
    if type(edges[0]) in (list, tuple):
        np_edges = np.array(edges)
    else:
        np_edges = edges[:len(vertices)-1, :]

    vect = np_verts[np_edges[:, 0], :] - np_verts[np_edges[:, 1], :]
    length = np.linalg.norm(vect, axis=1)
    if sum_length:
        length = np.sum(length)[np.newaxis]

    return length if out_numpy else length.tolist()


def edges_direction(vertices, edges, out_numpy=False):
    '''calculate edges direction '''

    np_verts = np.array(vertices)
    if type(edges[0]) in (list, tuple):
        np_edges = np.array(edges)
    else:
        np_edges = edges[:len(vertices)-1, :]

    vect = np_verts[np_edges[:, 1], :] - np_verts[np_edges[:, 0], :]
    dist = np_norm(vect, axis=1)
    vect_norm = vect/dist[:, np.newaxis]
    return vect_norm if out_numpy else vect_norm.tolist()

def adjacent_faces(edges, pols):
    '''calculate number of adjacent faces '''
    e_sorted = [sorted(e) for e in edges]
    ad_faces = [0 for e in edges]
    for pol in pols:
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = sorted(edge)
            if e_s in e_sorted:
                idx = e_sorted.index(e_s)
                ad_faces[idx] += 1
    return ad_faces

def adjacent_faces_comp(edges, pols):
    '''calculate adjacent faces '''
    e_sorted = [sorted(e) for e in edges]
    ad_faces = [[] for e in edges]
    for pol in pols:
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = sorted(edge)
            if e_s in e_sorted:
                idx = e_sorted.index(e_s)
                ad_faces[idx] += [pol]
    return ad_faces

def faces_angle(normals, edges, pols):
    ad_faces = adjacent_faces(edges, pols)
    e_sorted = [sorted(e) for e in edges]
    ad_faces = [[] for e in edges]
    for idp, pol in enumerate(pols):
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = sorted(edge)
            if e_s in e_sorted:
                idx = e_sorted.index(e_s)
                ad_faces[idx].append(idp)
    angles = []
    for edg in ad_faces:
        if len(edg) > 1:
            dot_p = Vector(normals[edg[0]]).dot(Vector(normals[edg[1]]))
            ang = acos(dot_p)
        else:
            ang = 2*pi
        angles.append(ang)
    return angles

def edges_normal(vertices, normals, edges, pols):
    # ad_faces = adjacent_faces(edges, pols)
    e_sorted = [sorted(e) for e in edges]
    ad_faces = [[] for e in edges]
    for idp, pol in enumerate(pols):
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = sorted(edge)
            if e_s in e_sorted:
                idx = e_sorted.index(e_s)
                ad_faces[idx].append(idp)
    result = []

    for edg_f, edg in zip(ad_faces, edges):
        if len(edg_f) > 1:
            edge_normal = ((Vector(normals[edg_f[0]])+Vector(normals[edg_f[1]]))/2).normalized()
        elif len(edg_f) == 1:
            edge_normal = Vector(normals[edg_f[0]])
        else:
            rot_mat = Matrix.Rotation(pi/2, 4, "Z")
            direc = (Vector(vertices[edg[1]])-Vector(vertices[edg[0]])).normalized()
            edge_normal = direc @ rot_mat
        result.append(tuple(edge_normal))
    return result


def edges_vertices(vertices, edges):
    verts = [[vertices[c] for c in e] for e in edges]
    eds = [[[0, 1]] for e in edges]
    vals = [verts, eds]
    return vals

def edges_normals_full(vertices, edges, faces):

    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    vals = edges_normal(vertices, normals, edges, faces)

    return vals

def faces_angle_full(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    vals = faces_angle(normals, edges, faces)
    return vals

def edge_is_boundary(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [edge.is_boundary for edge in bm.edges]
    bm.free()
    return vals

def edge_is_contiguous(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [edge.is_contiguous for edge in bm.edges]
    bm.free()
    return vals

def edge_is_convex(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [edge.is_convex for edge in bm.edges]
    vals = [sorted((edge.verts[0].index, edge.verts[1].index)) for edge in bm.edges if edge.is_convex]
    mask = []
    for e in edges:
        if sorted(e) in vals:
            mask.append(True)
        else:
            mask.append(False)
    bm.free()
    return mask

def edge_is_manifold(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [edge.is_manifold for edge in bm.edges]
    bm.free()
    return vals

def edges_is_wire(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [edge.is_wire for edge in bm.edges]
    bm.free()
    return vals

def edges_shell_factor(vertices, edges, faces):
    v_shell = vertex_shell_factor(vertices, edges, faces)
    vals = [(v_shell[e[0]] + v_shell[e[1]])/2 for e in edges]
    return vals

def edges_center(vertices, edges):
    vals = [tuple((Vector(vertices[e[0]])+Vector(vertices[e[1]]))/2) for e in edges]
    return vals

def edges_origin(vertices, edges):
    vals = [vertices[e[0]] for e in edges]
    return vals

def edges_end(vertices, edges):
    vals = [vertices[e[1]] for e in edges]
    return vals

def edges_inverted(vertices, edges):
    vals = [[e[1], e[0]] for e in edges]
    return vals

def edge_vertex(vertices, edges, origin):
    if origin == 'Center':
        center = [(Vector(vertices[e[0]])+Vector(vertices[e[1]]))/2 for e in edges]
    elif origin == 'First':
        center = [Vector(vertices[e[0]]) for e in edges]
    else:
        center = [Vector(vertices[e[1]]) for e in edges]
    return center

def edges_matrix(vertices, edges, orientation):
    origin, track, up = orientation
    normal = edges_direction(vertices, edges, out_numpy=False)
    normal_v = [Vector(n) for n in normal]
    center = edge_vertex(vertices, edges, origin)

    vals = matrix_normal([center, normal_v], track, up)
    return vals

def edges_matrix_ZY(vertices, edges, origin):
    normal = edges_direction(vertices, edges, out_numpy=False)
    normal_v = [Vector(n) for n in normal]
    center = edge_vertex(vertices, edges, origin)


    vals = matrix_normal([center, normal_v], "Z", "Y")
    return vals
def edges_matrix_normal(vertices, edges, faces, orientation):
    origin, track = orientation
    direction = edges_direction(vertices, edges, out_numpy=False)
    center = edge_vertex(vertices, edges, origin)
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    ed_normals = edges_normal(vertices, normals, edges, faces)
    if track == 'Z':
        vals = vectors_center_axis_to_matrix(center, direction, ed_normals)
    if track == 'X':
        vals = vectors_center_axis_to_matrix(center, ed_normals, direction)
    return vals

def edges_matrix_Z(vertices, edges, faces, origin):
    direction = edges_direction(vertices, edges, out_numpy=False)
    center = edge_vertex(vertices, edges, origin)
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    ed_normals = edges_normal(vertices, normals, edges, faces)
    vals = vectors_center_axis_to_matrix(center, direction, ed_normals)
    return vals

def edges_matrix_X(vertices, edges, faces, origin):
    p0 = [vertices[e[1]] for e in edges] if origin == 'First' else [vertices[e[0]] for e in edges]
    center = edge_vertex(vertices, edges, origin)
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    ed_normals = edges_normal(vertices, normals, edges, faces)
    vals = vectors_to_matrix(center, ed_normals, p0)
    return vals

edges_modes_dict = {
    'Geometry':           (0, 'vs',  'u', '', 've',  edges_vertices, 'Vertices, Faces', 'Geometry of each edge. (explode)'),
    'Direction':          (1, 'v', '',  '',   've',  edges_direction, 'Direction', 'Normalized Direction'),
    'Center':             (2, 'v', '',  '',   've', edges_center, 'Center', 'Edges Midpoint'),
    'Origin':             (3, 'v', '',  '',   've', edges_origin, 'Origin', 'Edges first point'),
    'End':                (4, 'v', '',  '',   've', edges_end, 'End', 'Edges End point'),
    'Normal':             (5, 'v', '',  '',   'vep', edges_normals_full, 'Normal', 'Edge Normal'),
    'Matrix':             (10, 'm', 'u',  'omu',  've', edges_matrix, 'Matrix', 'Aligned with edge'),
    'Matrix Normal':      (11, 'm', 'u',  'on',  'vep', edges_matrix_normal,  'Matrix', 'Aligned with edge and Normal (Needs Faces)'),
    'Length':             (20, 's', '',  's',  've', edges_length, 'Length', 'Edge length'),
    'Sharpness':          (21, 's', '',  '',   'vep', edges_shell_factor, 'Sharpness ', 'Average of curvature of mesh in edges vertices'),
    'Face Angle':         (22, 's', '',  '',   'vep', faces_angle_full, 'Face Angle', 'Face angle'),
    'Inverted':           (30, 'v', '',  '',   've', edges_inverted, 'Edges', 'Reversed Edge'),
    'Adjacent faces':     (31, 's', 'u',  '',  'ep', adjacent_faces_comp, 'Faces', 'Adjacent faces'),
    'Adjacent faces Num': (32, 's', '',  '',   'ep', adjacent_faces, 'Number', 'Adjacent faces number'),
    'Is Boundary':        (40, 's', '',  '',   'vep', edge_is_boundary, 'Is Boundary', 'Is Edge on mesh borders'),
    'Is Contiguous':      (41, 's', '',  '',   'vep', edge_is_contiguous, 'Is Contuguous', 'Is Edge  manifold and between two faces with the same winding'),
    'Is Convex':          (42, 's', '',  '',   'vep', edge_is_convex, 'Is Convex', 'Is Edge Convex'),
    'Is Mainfold':        (43, 's', '',  '',   'vep', edge_is_manifold, 'Is Mainfold', 'Is Edge part of the Mainfold'),
    'Is Wire':            (44, 's', '',  '',   'vep', edges_is_wire, 'Is Wire', 'Has no related faces'),
}
