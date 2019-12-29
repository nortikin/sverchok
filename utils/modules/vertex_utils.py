# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils import Vector
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.matrix_utils import matrix_normal

def adjacent_edg_pol_num(verts, edg_pol):
    '''calculate number of adjacent faces '''
    adj_edg_pol = [0 for v in verts]
    for ep in edg_pol:
        for v in ep:
            adj_edg_pol[v] += 1

    return adj_edg_pol

def adjacent_edg_pol(verts, edg_pol):
    '''calculate of adjacent faces '''
    adj_edg_pol = [[] for v in verts]
    for ep in edg_pol:
        for v in ep:
            adj_edg_pol[v] += [ep]

    return adj_edg_pol

def vertex_normal(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [tuple(v.normal) for v in bm.verts]
    bm.free()
    return vals

def vertex_shell_factor(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.calc_shell_factor() for v in bm.verts]
    bm.free()
    return vals

def vertex_calc_angle(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.calc_edge_angle() for v in bm.verts]
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

def vertex_matrix(vertices, edges, faces, orientation):
    track, up = orientation
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    loc = [Vector(v) for v in vertices]
    normal = [v.normal for v in bm.verts]
    vals = matrix_normal([loc, normal], track, up)
    bm.free()
    return vals

vertex_modes_dict = {
    'Normal':             (0,  'v', '', '',   'vep', vertex_normal, 'Normal', 'Vertex normal'),
    'Matrix':             (10, 'm', 'u', 'mu', 'vep', vertex_matrix, 'Matrix', 'Matrix aligned with normal'),
    'Sharpness':          (20,  's', '', '',   'vep', vertex_shell_factor, 'Sharpness ', 'Curvature of mesh in vertex'),
    'Adjacent edges':     (30,  's', 'u', '',  've', adjacent_edg_pol, 'Edges', 'Adjacent edges'),
    'Adjacent faces ':    (31,  's', 'u', '',  'vp', adjacent_edg_pol, 'Faces ', 'Adjacent faces'),
    'Adjacent edges num': (40,  's', '', '',   've', adjacent_edg_pol_num, 'Number', 'Number of Adjacent edges'),
    'Adjacent faces num': (41,  's', '', '',   'vp', adjacent_edg_pol_num, 'Number', 'Number of adjacent faces'),
    'Edges Angle':        (50,  's', '', '',   'vep', vertex_calc_angle, 'Angle', 'angle between this vert’s two connected edges.'),
    'Is Boundary ':       (60,  's', '', '',   'vep', vertex_is_boundary, 'Is Boundary ', 'Is Vertex on mesh borders'),
    'Is Interior ':       (60,  's', '', '',   'vep', vertex_is_interior, 'Is Interior ', 'Is Vertex on mesh interiors'),
    'Is Manifold':        (61,  's', '', '',   'vep', vertex_is_manifold, 'Is Manifold', 'Is Vertex part of the Manifold'),
    'Is Wire':            (62,  's', '', '',   'vep', vertex_is_wire, 'Is Wire', 'Is vertex only connected by edges'),
 }
