# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils import Vector, Matrix
from sverchok.data_structure import match_long_repeat
import numpy as np
def vectors_to_matrix(centrs, normals, p0_xdirs):
    mat_collect = []

    for cen, nor, p0 in zip(centrs, normals, p0_xdirs):
        zdir = nor
        xdir = (Vector(p0) - Vector(cen)).normalized()
        ydir = Vector(zdir).cross(xdir)
        lM = [(xdir[0], ydir[0], zdir[0], cen[0]),
              (xdir[1], ydir[1], zdir[1], cen[1]),
              (xdir[2], ydir[2], zdir[2], cen[2]),
              (0.0, 0.0, 0.0, 1.0)]
        mat_collect.append(Matrix(lM))
    return  mat_collect

def vectors_center_axis_to_matrix(centrs, normals, xdirs):
    mat_collect = []

    for cen, nor, p0 in zip(centrs, normals, xdirs):
        zdir = nor
        xdir = Vector(p0).normalized()
        ydir = Vector(zdir).cross(xdir)
        lM = [(xdir[0], ydir[0], zdir[0], cen[0]),
              (xdir[1], ydir[1], zdir[1], cen[1]),
              (xdir[2], ydir[2], zdir[2], cen[2]),
              (0.0, 0.0, 0.0, 1.0)]
        mat_collect.append(Matrix(lM))
    return  mat_collect

def matrix_normal(params, T, U):
    loc, nor = params
    out = []
    loc, nor = match_long_repeat([loc, nor])
    for V, N in zip(loc, nor):
        n = N.to_track_quat(T, U)
        m = Matrix.Translation(V) @ n.to_matrix().to_4x4()
        out.append(m)
    return out

def matrix_apply_np(verts, matrix):
    '''
    taken from https://blender.stackexchange.com/a/139517
    verts should be a numpy array with shape (n,3)
    matrix can be a regular mathultis matrix'''

    verts_co_4d = np.ones(shape=(verts.shape[0], 4), dtype=np.float)
    verts_co_4d[:, :-1] = verts  # cos v (x,y,z,1) - point,   v(x,y,z,0)- vector
    return np.einsum('ij,aj->ai', matrix, verts_co_4d)[:, :-1]
