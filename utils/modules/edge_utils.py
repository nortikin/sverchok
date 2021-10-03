# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import acos, pi
from mathutils import Vector
import numpy as np
from numpy.linalg import norm as np_norm
from sverchok.data_structure import has_element
from sverchok.utils.math import np_normalize_vectors
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.matrix_utils import matrix_normal, vectors_center_axis_to_matrix
from sverchok.utils.modules.vertex_utils import vertex_shell_factor, adjacent_edg_pol, adjacent_edg_pol_num, adjacent_edg_pol_idx
from sverchok.nodes.analyzer.mesh_filter import Edges

def get_v_edges(vertices, edges):
    if isinstance(vertices, np.ndarray):
        np_verts = vertices
    else:
        np_verts = np.array(vertices)
    if isinstance(edges, np.ndarray):
        np_edges = edges
    else:
        np_edges = np.array(edges)
    return np_verts[np_edges]

def edges_aux(vertices):
    '''
    vertices: list as [[vertex,vertex,..], [vertex,..],..]
    returns edges array with the maximum length of the vertices list supplied as [np.array]
    '''
    v_len = len(vertices)

    np_in = np.arange(v_len - 1)
    np_edges = np.array([np_in, np_in + 1]).T

    return np_edges

def edges_length(vertices, edges, sum_length=False, out_numpy=False):
    '''
    calculate edges length using numpy
    vertices: list as [vertex, vertex, ...] being each vertex [float, float, float]. Also accept numpy arrays with two axis
    edges: list as [edge, edge,..] being each edge [int, int]. Also accept numpy arrays with one axis
    sum_length: boolean to determine if outputtig each length or the sum of all
    out_numpy: boolean to determine if outputtig  np_array or regular python list
    returns length of edges or sum of lengths
    '''
    if not has_element(vertices):
        return
    if not has_element(edges):
        edges = edges_aux(vertices)
    v_edges = get_v_edges(vertices, edges)
    vect = v_edges[:, 1, :] - v_edges[:, 0, :]
    length = np.linalg.norm(vect, axis=1)
    if sum_length:
        length = np.sum(length)[np.newaxis]

    return length if out_numpy else length.tolist()



def edges_direction(vertices, edges, out_numpy=False):
    '''
    calculate edges direction
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float]. Also accepts numpy arrays with two axis
    edges: list as [edge, edge,..], being each edge [int, int]. Also accept numpy arrays with one axis.
    out_numpy: boolean to determine if outputtig  np_array or regular python list
    returns edges direction as [vertex, vertex,...] or numpy array with two axis
    '''
    v_edges = get_v_edges(vertices, edges)
    if out_numpy:
        return np_normalize_vectors(v_edges[:,1,:] - v_edges[:,0,:])

    return np_normalize_vectors(v_edges[:, 1, :] - v_edges[:, 0, :]).tolist()

def connected_edges(verts, edges):
    '''
    edges connected to each edge
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    returns edges connected to each edge as [[edge, edge,...],[edge,...],...]
    '''
    v_adjacent = adjacent_edg_pol(verts, edges)
    vals = []
    for edge in edges:
        adj_edges = []
        for v_ind in edge:
            adj_edges.extend(v_adjacent[v_ind])
            adj_edges.remove(edge)
        vals.append(adj_edges)
    return vals

def connected_edges_idx(verts, edges):
    '''
    edges connected to each edge
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    returns edges connected to each edge as [[edge, edge,...],[edge,...],...]
    '''
    v_adjacent = adjacent_edg_pol_idx(verts, edges)
    vals = []
    for idx, edge in enumerate(edges):
        adj_edges = []
        for v_ind in edge:
            adj_edges.extend(v_adjacent[v_ind])
            adj_edges.remove(idx)
        vals.append(adj_edges)
    return vals


def connected_edges_num(verts, edges):
    '''
    number of edges connected to each edge
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    returns number of edges connected to each edge as [int, int,...]
    '''
    v_adja = adjacent_edg_pol_num(verts, edges)
    vals = []
    for edge in edges:
        adj = 0
        for c in edge:
            adj += v_adja[c] - 1
        vals.append(adj)
    return vals


def adjacent_faces_number(edges, pols):
    """
    calculate number of adjacent faces
    edges: list as [edge, edge,..], being each edge [int, int].
    pols: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns number of faces connected to each edge as [int, int,...]
    """
    return [len(face_indexes) for face_indexes in adjacent_faces_idx(edges, pols)]


def adjacent_faces(edges, pols):
    """
    calculates of adjacent faces
    edges: list as [edge, edge,..], being each edge [int, int].
    pols: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns polygon connected to each edge as [[polygon, polygon, ...], [polygon, ...],...]
    """
    edge_to_adj_face = [[] for _ in edges]
    for adj_faces, face_indexes in zip(edge_to_adj_face, adjacent_faces_idx(edges, pols)):
        for fi in face_indexes:
            adj_faces.append(pols[fi])
    return edge_to_adj_face


def adjacent_faces_idx(edges, pols):
    """
    calculates of adjacent faces
    edges: list as [edge, edge,..], being each edge [int, int]. Optional, it can be empty lies
    pols: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns polygon connected to each edge as [[polygon, polygon, ...], [polygon, ...],...]
    """
    edge_to_index = {tuple(sorted(e)): i for i, e in enumerate(edges)}
    ad_faces = [[] for e in edges]
    for p_idx, pol in enumerate(pols):
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = tuple(sorted(edge))
            try:
                e_idx = edge_to_index[e_s]
            except KeyError:
                pass
            else:
                ad_faces[e_idx].append(p_idx)
    return ad_faces


def faces_angle_full(vertices, edges, faces):
    '''
    angle between faces of each edge (only first two faces)
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns angle of faces (in radians) connected to each edge as [int, int,...]
    '''
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normals = [tuple(face.normal) for face in bm.faces]
    bm.free()
    vals = faces_angle(normals, edges, faces)
    return vals


def faces_angle(normals, edges, pols):
    """
    angle between faces of each edge (only first two faces)
    normals: list as [vertex, vertex, ...], being each vertex Vector([float, float, float]).
    edges: list as [edge, edge,..], being each edge [int, int].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns angle of faces (in radians) connected to each edge as [int, int,...]
    """
    angles = []
    for face_indexes in adjacent_faces_idx(edges, pols):
        if len(face_indexes) > 1:
            dot_p = Vector(normals[face_indexes[0]]).dot(Vector(normals[face_indexes[1]]))
            if dot_p >= 1.0:
                # Floating-point maths calculation error workaround
                ang = 0.0
            else:
                ang = acos(dot_p)
        else:
            ang = 2*pi
        angles.append(ang)
    return angles


def edges_normal(vertices, edges, faces):
    '''
    Average of vertex normals of the edge
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns normal vector to each edge as [vertex, vertex,...]
    algorithm by Durman
    '''

    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    normal = []
    for edge in edges:
        y = (Vector(vertices[edge[1]]) - Vector(vertices[edge[0]])).normalized()
        _normal = (bm.verts[edge[0]].normal + bm.verts[edge[1]].normal).normalized()
        x = y.cross(_normal)
        normal.append(tuple(x.cross(y)))
    bm.free()
    return normal

def edges_vertices(vertices, edges):
    '''
    Explode edges
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    returns verts as  [vertex, vertex,...] and edges as [[0, 1], [0, 1], ...]
    '''
    verts = [[vertices[c] for c in e] for e in edges]
    edges_out = [[[0, 1]] for e in edges]
    return verts, edges_out

def edge_is_filter(vertices, edges, faces, mode):
    '''
    access to mesh_filter to get different bmesh edges filters
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns mask as [bool, bool,...],  good and bad as [edge, edge]
    '''
    mode = mode.split(' ')[1]
    if not edges:
        return [], [], []

    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    good, bad, mask = Edges.process(bm, mode, edges)
    bm.free()
    return mask, good, bad


def edges_shell_factor(vertices, edges, faces):
    '''
    Average of vertex shell_factor
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list as [edge, edge,..], being each edge [int, int].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    returns vals as [float, float,...]
    '''
    v_shell = vertex_shell_factor(vertices, edges, faces)
    vals = [(v_shell[e[0]] + v_shell[e[1]])/2 for e in edges]
    return vals

def edges_center(vertices, edges, output_numpy=False):
    '''
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list with edges [[int, int], [int,int]...]
    outputs the center point of each edge [vertex, vertex..]
    '''
    v_edges = get_v_edges(vertices, edges)
    if output_numpy:
        return ((v_edges[:, 0,:] + v_edges[:, 1,:])/2)
    return ((v_edges[:, 0,:] + v_edges[:, 1,:])/2).tolist()


def edges_origin(vertices, edges):
    '''
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list with edges [[int, int], [int,int]...]
    outputs the first point of each edge [vertex, vertex..]
    '''
    vals = [vertices[e[0]] for e in edges]
    return vals

def edges_end(vertices, edges):
    '''
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list with edges [[int, int], [int,int]...]
    outputs the end point of each edge [vertex, vertex..]
    '''
    vals = [vertices[e[1]] for e in edges]
    return vals


def edges_inverted(edges):
    '''
    edges: list with edges [[int, int], [int,int]...]
    outputs the same list with inverted index [[0, 1],[1, 2]] ---> [[1, 0], [2, 1]]
    '''
    vals = [[e[1], e[0]] for e in edges]
    return vals

def edge_vertex(vertices, edges, origin):
    '''
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list with edges [[int, int], [int,int]...]
    origin: String  that can be First, Center, Last
    outputs the desired point of each edge [vertex, vertex..]
    '''
    if origin == 'Center':
        center = [(Vector(vertices[e[0]])+Vector(vertices[e[1]]))/2 for e in edges]
    elif origin == 'First':
        center = [Vector(vertices[e[0]]) for e in edges]
    else:
        center = [Vector(vertices[e[1]]) for e in edges]
    return center

def edges_matrix(vertices, edges, origin, track, up_axis):
    '''
    Matrix aligned with edge.
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list with edges [[int, int], [int,int]...]
    orientation: contains origin track and up_axis
    origin: String  that can be First, Center, Last
    track: String  that can be X, Y, Z, -X, -Y or -Z
    up_axis: String  that can be X, Y, Z, -X, -Y or -Z
    outputs each edge matrix [matrix, matrix, matrix]
    '''

    normal = edges_direction(vertices, edges, out_numpy=False)
    normal_v = [Vector(n) for n in normal]
    center = edge_vertex(vertices, edges, origin)
    vals = matrix_normal([center, normal_v], track, up_axis)
    return vals

def edges_matrix_normal(vertices, edges, faces, origin, track):
    '''
    Matrix aligned with edge and edge normal (needs faces)
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edges: list with edges [[int, int], [int,int]...]
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    orientation: contains origin track and up
    origin: String  that can be First, Center, Last
    track: String  that can be X, Y, Z, -X, -Y or -Z
    up: String  that can be X, Y, Z, -X, -Y or -Z
    outputs each edge matrix [matrix, matrix, matrix]
    '''

    direction = edges_direction(vertices, edges, out_numpy=False)
    center = edge_vertex(vertices, edges, origin)
    ed_normals = edges_normal(vertices, edges, faces)

    if track == 'Z':
        vals = vectors_center_axis_to_matrix(center, direction, ed_normals)
    if track == 'X':
        vals = vectors_center_axis_to_matrix(center, ed_normals, direction)
    return vals

# Name: (index, input_sockets, func_options, output_options, function, output_sockets, output_sockets_names, description)
edges_modes_dict = {
    'Geometry':           (0,  've',  '',   'u', edges_vertices,        'vs',  'Vertices, Edges', 'Geometry of each edge. (explode)'),
    'Direction':          (1,  've',  'a',   '', edges_direction,       'v',   'Direction', 'Normalized Direction'),
    'Center':             (2,  've',  '',    '', edges_center,          'v',   'Center', 'Edges Midpoint'),
    'Origin':             (3,  've',  '',    '', edges_origin,          'v',   'Origin', 'Edges first point'),
    'End':                (4,  've',  '',    '', edges_end,             'v',   'End', 'Edges End point'),
    'Normal':             (5,  'vep', '',    '', edges_normal,          'v',   'Normal', 'Edge Normal'),
    'Matrix':             (10, 've',  'omu','u', edges_matrix,          'm',   'Matrix', 'Aligned with edge'),
    'Matrix Normal':      (11, 'vep', 'on', 'u', edges_matrix_normal,   'm',   'Matrix', 'Aligned with edge and Normal (Needs Faces)'),
    'Length':             (20, 've',  'sa',  '', edges_length,          's',   'Length', 'Edge length'),
    'Sharpness':          (21, 'vep', '',    '', edges_shell_factor,    's',   'Sharpness', 'Average of curvature of mesh in edges vertices'),
    'Face Angle':         (22, 'vep', '',    '', faces_angle_full,      's',   'Face Angle', 'Face angle'),
    'Inverted':           (30, 'e',  '',     '', edges_inverted,        's',   'Edges', 'Reversed Edge'),
    'Adjacent Faces':     (31, 'ep',  '',   'u', adjacent_faces,        's',   'Faces', 'Adjacent faces'),
    'Connected Edges':    (32, 've',  '',   'u', connected_edges,       's',   'Number', 'Connected edges'),
    'Adjacent Faces Num': (33, 'ep',  '',    '', adjacent_faces_number, 's',   'Number', 'Adjacent faces number'),
    'Connected Edges Num':(34, 've',  '',    '', connected_edges_num,   's',   'Number', 'Connected edges number'),
    'Adjacent Faces Idx' :(35, 'ep',  '',    '', adjacent_faces_idx,    's',   'Faces Idx', 'Adjacent faces Index'),
    'Connected Edges Idx':(36, 've',  '',    '', connected_edges_idx,   's',   'Edges Idx', 'Connected edges Index'),
    'Is Boundary':        (40, 'vep', 'b',   '', edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge on mesh borders'),
    'Is Interior':        (41, 'vep', 'b',   '', edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge part of the Mainfold'),
    'Is Contiguous':      (42, 'vep', 'b',   '', edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge  manifold and between two faces with the same winding'),
    'Is Convex':          (43, 'vep', 'b',   '', edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge Convex'),
    'Is Concave':         (44, 'vep', 'b',   '', edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Is Edge Concave'),
    'Is Wire':            (45, 'vep', 'b',   '', edge_is_filter,        'sss', 'Mask, True Edges, False Edges', 'Has no related faces'),
    }
