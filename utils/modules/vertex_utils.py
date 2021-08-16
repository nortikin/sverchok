# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import numpy as np
from mathutils import Vector
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.matrix_utils import matrix_normal
from sverchok.utils.math import np_normalize_vectors

def center(verts):
    '''
    verts: list as [vertex, vertex, ...], being each vertex [float, float, float].
    returns the verts centered around [0,0,0]
    '''
    verts_out = []
    for vec in verts:

        avr = list(map(sum, zip(*vec)))
        avr = [n/len(vec) for n in avr]
        vec = [[v[0]-avr[0], v[1]-avr[1], v[2]-avr[2]] for v in vec]
        verts_out.append(vec)
    return verts_out

def center_of_many(verts):
    '''
    verts: list as [[vertex, vertex, ...],[vertex,...]], being each vertex [float, float, float].
    returns the verts centered around [0,0,0] calculating the mean of all lists
    '''
    verts_out = []
    verts_ungrouped = [[v for vec in group for v in vec] for group in verts]

    for vec_g, vec_ung in zip(verts, verts_ungrouped):
        avr = list(map(sum, zip(*vec_ung)))
        avr = [n/len(vec_ung) for n in avr]
        vec = [[[v[0]-avr[0], v[1]-avr[1], v[2]-avr[2]] for v in vec] for vec in vec_g]
        verts_out.append(vec)
    return verts_out

def adjacent_edg_pol(verts, edgs_pols):
    '''
    returns adjacent faces or edges as [[edge,edge,...], [edge, ...], ...]
    verts: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edg_pol: list as [edge, edge,..], being each edge [int, int].
                  or [polygon, polygon,...] being each polygon [int, int, int, ...].
    '''
    adj_edgs_pols = [[] for v in verts]
    for ep in edgs_pols:
        for v_id in ep:
            adj_edgs_pols[v_id] += [ep]

    return adj_edgs_pols


def adjacent_edg_pol_num(verts, edgs_pols):
    '''
    calculate the number of adjacent faces  or edges as [int, int,...]
    verts: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edg_pol: list as [edge, edge,..], being each edge [int, int].
                  or [polygon, polygon,...] being each polygon [int, int, int, ...].
    '''
    adj_edgs_pols = [0 for v in verts]
    for edg_pol in edgs_pols:
        for v_id in edg_pol:
            adj_edgs_pols[v_id] += 1

    return adj_edgs_pols

def adjacent_edg_pol_idx(verts, edgs_pols):
    '''
    calculate the number of adjacent faces  or edges as [int, int,...]
    verts: list as [vertex, vertex, ...], being each vertex [float, float, float].
    edg_pol: list as [edge, edge,..], being each edge [int, int].
                  or [polygon, polygon,...] being each polygon [int, int, int, ...].
    '''
    adj_edgs_pols = [[] for v in verts]
    for idx, edg_pol in enumerate(edgs_pols):
        for v_id in edg_pol:
            adj_edgs_pols[v_id] += [idx]

    return adj_edgs_pols
'''
The functions below expect:
vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
edges: list as [edge, edge,..], being each edge [int, int].
faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
returns value of each vertex as [value, value,...]
'''
def vertex_normal(vertices, faces, algorithm='MWE', output_numpy=True):
    if len(faces) == 0 or algorithm == 'BMESH':
        bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
        vals = [tuple(v.normal) for v in bm.verts]
        bm.free()
        return vals

    return np_vertex_normals(vertices, faces, algorithm, output_numpy=output_numpy)

def np_faces_normals(v_pols):
    pol_sides = v_pols.shape[1]
    if pol_sides > 3:
        f_normals = np.zeros((len(v_pols), 3), dtype=np.float64)
        for i in range(pol_sides - 2):
            f_normals += np.cross(v_pols[::, (1+i)%pol_sides] - v_pols[::, 0], v_pols[::, (2+i)%pol_sides] - v_pols[::, 0])
    else:
        f_normals = np.cross(v_pols[::, 1] - v_pols[::, 0], v_pols[::, 2] - v_pols[::, 0])
    np_normalize_vectors(f_normals)

    return f_normals
# based in this article https://www.researchgate.net/publication/220067106_A_comparison_of_algorithms_for_vertex_normal_computation
def add_faces_normals(v_pols, np_faces_g, algorithm, pol_sides, v_normals):
    if algorithm in ('MWE', 'MWAT'):
        if algorithm == 'MWE': #weighted equally
            f_normal_g = np_normalize_vectors(np_faces_normals(v_pols))
        else: #weighted by area of triangle
            f_normal_g = np_faces_normals(v_pols)
        for i in range(pol_sides):
            np.add.at(v_normals, np_faces_g[:, i], f_normal_g)
    else:
        if algorithm == 'MWELR':  #weighted edge length reciprocal
            f_normal_g = np_normalize_vectors(np_faces_normals(v_pols))
        else:  # algorithm == 'MWS': #weighted by sine
            f_normal_g = np_faces_normals(v_pols)
        edges_length = np.linalg.norm(v_pols - np.roll(v_pols, 1, axis=1), axis=2)
        factor = edges_length * np.roll(edges_length, -1, axis=1)

        for i in range(pol_sides):
            np.add.at(v_normals, np_faces_g[:, i], f_normal_g * factor[:, i, np.newaxis])

def np_vertex_normals(vertices, faces, algorithm='MWE', output_numpy=False):

    if isinstance(vertices, np.ndarray):
        np_verts = vertices
    else:
        np_verts = np.array(vertices)

    if isinstance(faces, np.ndarray):
        np_faces = faces
    else:
        np_faces = np.array(faces)

    v_normals = np.zeros(np_verts.shape, dtype=np_verts.dtype)

    if np_faces.dtype == object:
        np_len = np.vectorize(len)
        lens = np_len(np_faces)
        pol_types = np.unique(lens)
        for pol_sides in pol_types:
            mask = lens == pol_sides
            np_faces_g = np.array(np_faces[mask].tolist())
            v_pols = np_verts[np_faces_g]
            add_faces_normals(v_pols, np_faces_g, algorithm, pol_sides, v_normals)

    else:
        pol_sides = np_faces.shape[1]
        v_pols = np_verts[np_faces]
        add_faces_normals(v_pols, np_faces, algorithm, pol_sides, v_normals)


    if output_numpy:
        return np_normalize_vectors(v_normals)
    return np_normalize_vectors(v_normals).tolist()


def vertex_shell_factor(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.calc_shell_factor() for v in bm.verts]
    bm.free()
    return vals

def vertex_calc_angle(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    num_edges = adjacent_edg_pol_num(vertices, edges)


    vals = [v.calc_edge_angle() if n == 2 else -1 for v, n in zip(bm.verts, num_edges) ]
    bm.free()
    return vals

def vertex_is_boundary(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.is_boundary for v in bm.verts]
    bm.free()
    return vals

def vertex_is_interior(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.is_manifold and not v.is_boundary for v in bm.verts]
    bm.free()
    return vals

def vertex_is_manifold(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.is_manifold for v in bm.verts]
    bm.free()
    return vals

def vertex_is_wire(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.is_wire for v in bm.verts]
    bm.free()
    return vals

def vertex_matrix(vertices, edges, faces, track, up):
    '''
    orientation: contains origin track and up
    origin: String  that can be First, Center, Last
    track: String  that can be X, Y, Z, -X, -Y or -Z
    up: String  that can be X, Y, Z, -X, -Y or -Z
    outputs each vertex matrix [matrix, matrix, matrix]
    '''

    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    loc = [Vector(v) for v in vertices]
    normal = [v.normal for v in bm.verts]
    vals = matrix_normal([loc, normal], track, up)
    bm.free()
    return vals

# Name: (index, input_sockets, func_options, output_options, function, output_sockets, output_sockets_names, description)
vertex_modes_dict = {
    'Normal':             (0,  'vp', 'va',  '',  vertex_normal,        'v', 'Normal', 'Vertex normal'),
    'Matrix':             (10, 'vep', 'mu', 'u', vertex_matrix,        'm', 'Matrix', 'Matrix aligned with normal'),
    'Sharpness':          (20, 'vep', '',   '',  vertex_shell_factor,  's', 'Sharpness', 'Curvature of mesh in vertex'),
    'Adjacent edges':     (30, 've',  '',   'u', adjacent_edg_pol,     's', 'Edges', 'Adjacent edges'),
    'Adjacent faces ':    (31, 'vp',  '',   'u', adjacent_edg_pol,     's', 'Faces ', 'Adjacent faces'),
    'Adjacent edges num': (40, 've',  '',   '',  adjacent_edg_pol_num, 's', 'Number', 'Number of Adjacent edges'),
    'Adjacent faces num': (41, 'vp',  '',   '',  adjacent_edg_pol_num, 's', 'Number', 'Number of adjacent faces'),
    'Adjacent edges Idx': (42, 've',  '',   '',  adjacent_edg_pol_idx, 's', 'Edges Idx', 'Index of Adjacent edges'),
    'Adjacent faces Idx': (43, 'vp',  '',   '',  adjacent_edg_pol_idx, 's', 'Faces Idx', 'Index of adjacent faces'),
    'Edges Angle':        (50, 'vep', '',   '',  vertex_calc_angle,    's', 'Angle', 'angle between this vert’s two connected edges.'),
    'Is Boundary ':       (60, 'vep', '',   '',  vertex_is_boundary,   's', 'Is Boundary ', 'Is Vertex on mesh borders'),
    'Is Interior ':       (63, 'vep', '',   '',  vertex_is_interior,   's', 'Is Interior ', 'Is Vertex on mesh interiors'),
    'Is Manifold':        (61, 'vep', '',   '',  vertex_is_manifold,   's', 'Is Manifold', 'Is Vertex part of the Manifold'),
    'Is Wire':            (62, 'vep', '',   '',  vertex_is_wire,       's', 'Is Wire', 'Is vertex only connected by edges'),
    }
