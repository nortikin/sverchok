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
from sverchok.utils.modules.matrix_utils import matrix_normal, vectors_center_axis_to_matrix
from sverchok.utils.modules.vertex_utils import vertex_shell_factor, adjacent_edg_pol, adjacent_edg_pol_num
from sverchok.nodes.analyzer.mesh_filter import Edges

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

def connected_edges(verts, edges):
    '''edges conected to each edge'''
    v_adja = adjacent_edg_pol(verts, edges)
    vals = []
    for e in edges:
        adj = []
        for c in e:
            adj.extend(v_adja[c])
            adj.remove(e)
        vals.append(adj)
    return vals

def connected_edges_num(verts, edges):
    '''number of edges conected to each edge'''
    v_adja = adjacent_edg_pol_num(verts, edges)
    vals = []
    for e in edges:
        adj = 0
        for c in e:
            adj += v_adja[c] - 1
        vals.append(adj)
    return vals

def adjacent_faces_number(edges, pols):
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

def adjacent_faces(edges, pols):
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
def faces_angle_full(vertices, edges, faces):
    '''angle between faces of each edge (only first two faces)'''
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    vals = faces_angle(normals, edges, faces)
    return vals


def faces_angle(normals, edges, pols):
    '''angle between faces of each edge (only first two faces)'''
    ad_faces = adjacent_faces_number(edges, pols)
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

def edges_normals_full(vertices, edges, faces):
    '''Average of normals of the faces that share the edge (only the two first)'''
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    vals = edges_normal(vertices, normals, edges, faces)

    return vals

def edges_normal(vertices, normals, edges, pols):
    '''Average of normals of the faces that share the edge (only the two first)'''
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
            direc = (Vector(vertices[edg[1]]) - Vector(vertices[edg[0]])).normalized()
            edge_normal = direc @ rot_mat
        result.append(tuple(edge_normal))

    return result


def edges_vertices(vertices, edges):
    '''Explode edges'''
    verts = [[vertices[c] for c in e] for e in edges]
    eds = [[[0, 1]] for e in edges]
    vals = [verts, eds]
    return vals

def edge_is_filter(vertices, edges, faces, mode):
    '''acces to mesh_filter to get differnt bmesh edges filters'''
    mode = mode.split(' ')[1]
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    good, bad, mask = Edges.process(bm, mode, edges)
    bm.free()
    return mask, good, bad


def edges_shell_factor(vertices, edges, faces):
    '''Average of vertex shell_factor'''
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
    '''Matrix aligned with edge.'''
    origin, track, up = orientation
    normal = edges_direction(vertices, edges, out_numpy=False)
    normal_v = [Vector(n) for n in normal]
    center = edge_vertex(vertices, edges, origin)
    vals = matrix_normal([center, normal_v], track, up)
    return vals

def edges_matrix_normal(vertices, edges, faces, orientation):
    '''Matrix aligned with edge and edge normal (needs faces)'''
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

# Name: (index, input_sockets, func_options, output_options, function, output_sockets, output_sockets_names, description)
edges_modes_dict = {
    'Geometry':           (0,  've',  '',    'u', edges_vertices,        'vs',  'Vertices, Edges', 'Geometry of each edge. (explode)'),
    'Direction':          (1,  've',  '',    '',  edges_direction,       'v',   'Direction', 'Normalized Direction'),
    'Center':             (2,  've',  '',    '',  edges_center,          'v',   'Center', 'Edges Midpoint'),
    'Origin':             (3,  've',  '',    '',  edges_origin,          'v',   'Origin', 'Edges first point'),
    'End':                (4,  've',  '',    '',  edges_end,             'v',   'End', 'Edges End point'),
    'Normal':             (5,  'vep', '',    '',  edges_normals_full,    'v',   'Normal', 'Edge Normal'),
    'Matrix':             (10, 've',  'omu', 'u', edges_matrix,          'm',   'Matrix', 'Aligned with edge'),
    'Matrix Normal':      (11, 'vep', 'on',  'u', edges_matrix_normal,   'm',   'Matrix', 'Aligned with edge and Normal (Needs Faces)'),
    'Length':             (20, 've',  's',   '',  edges_length,          's',   'Length', 'Edge length'),
    'Sharpness':          (21, 'vep', '',    '',  edges_shell_factor,    's',   'Sharpness ', 'Average of curvature of mesh in edges vertices'),
    'Face Angle':         (22, 'vep', '',    '',  faces_angle_full,      's',   'Face Angle', 'Face angle'),
    'Inverted':           (30, 've',  '',    '',  edges_inverted,        'v',   'Edges', 'Reversed Edge'),
    'Adjacent Faces':     (31, 'ep',  '',    'u', adjacent_faces,        's',   'Faces', 'Adjacent faces'),
    'Connected Edges':    (32, 've',  '',    'u', connected_edges,       's',   'Number', 'Adjacent faces number'),
    'Adjacent Faces Num': (33, 'ep',  '',    '',  adjacent_faces_number, 's',   'Number', 'Adjacent faces number'),
    'Connected Edges Num':(34, 've',  '',    '',  connected_edges_num,   's',   'Number', 'Adjacent faces number'),
    'Is Boundary':        (40, 'vep', 'b',   '',  edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge on mesh borders'),
    'Is Interior':        (41, 'vep', 'b',   '',  edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge part of the Mainfold'),
    'Is Contiguous':      (42, 'vep', 'b',   '',  edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge  manifold and between two faces with the same winding'),
    'Is Convex':          (43, 'vep', 'b',   '',  edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge Convex'),
    'Is Concave':         (44, 'vep', 'b',   '',  edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge Concave'),
    'Is Wire':            (45, 'vep', 'b',   '',  edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Has no related faces'),
    }
