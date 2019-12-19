# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils import Vector
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.matrix_utils import matrix_normal

def adjacent_edg_pol(verts, edg_pol):
    '''calculate number of adjacent faces '''
    adj_edg_pol = [0 for v in verts]
    for ep in edg_pol:
        for v in ep:
            adj_edg_pol[v] += 1

    return adj_edg_pol

def adjacent_edg_pol_comp(verts, edg_pol):
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

def vertex_is_boundary(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vals = [v.is_boundary for v in bm.verts]
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

def vertex_matrix_ZY(vertices, edges, faces):
    '''Matrix, Z in normal, Y up'''
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    loc = [Vector(v) for v in vertices]
    normal = [v.normal for v in bm.verts]
    vals = matrix_normal([loc, normal], "Z", "Y")
    bm.free()
    return vals

def vertex_matrix_YX(vertices, edges, faces):
    '''Matrix, Y in normal, X up'''
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    loc = [Vector(v) for v in vertices]
    normal = [v.normal for v in bm.verts]
    vals = matrix_normal([loc, normal], "Y", "X")
    bm.free()
    return vals

def vertex_matrix_XZ(vertices, edges, faces):
    '''Matrix, X in normal, Z up'''
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    loc = [Vector(v) for v in vertices]
    normal = [v.normal for v in bm.verts]
    vals = matrix_normal([loc, normal], "X", "Z")
    bm.free()
    return vals



vertex_modes_dict = {
    'Normal':             (0, 'v', '',   'vep', vertex_normal, 'Normal', 'Vertex normal'),
    'Adjacent edges num': (1, 's', '',   've', adjacent_edg_pol, 'Number', 'Number of Adjacent edges'),
    'Adjacent faces num': (2, 's', '',   'vp', adjacent_edg_pol, 'Number', 'Number of adjacent faces'),
    'Adjacent edges':     (4, 's', 'u',  've', adjacent_edg_pol_comp, 'Edges', 'Adjacent edges'),
    'Adjacent faces ':    (5, 's', 'u',  'vp', adjacent_edg_pol_comp, 'Faces ', 'Adjacent faces'),
    'Sharpness':         (6, 's', '',   'vep', vertex_shell_factor, 'Sharpness ', 'Curvature of mesh in vertex'),
    'Is Boundary ':       (7, 's', '',   'vep', vertex_is_boundary, 'Is_Boundary ', 'Is Vertex on mesh borders'),
    'Is Manifold':        (8, 's', '',   'vep', vertex_is_manifold, 'Is_Manifold', 'Is Vertex part of the Manifold'),
    'Is Wire':            (9, 's', '',   'vep', vertex_is_wire, 'Is_Wire', 'Is vertex only connected by edges'),
    'Matrix ZY':          (10, 'm', 'u', 'vep', vertex_matrix_ZY, 'Matrix', 'Matrix, Z in normal, Y up'),
    'Matrix YX':          (11, 'm', 'u', 'vep', vertex_matrix_YX, 'Matrix', 'Matrix, Y in normal, X up'),
    'Matrix XZ':          (12, 'm', 'u', 'vep', vertex_matrix_XZ, 'Matrix', 'Matrix, X in normal, Z up'),
}
