# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from mathutils import Matrix, Vector

from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.vector import SvVectorField
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.interpolate import Rbf

##################
#                #
#  Scalar Fields #
#                #
##################

class SvRbfScalarField(SvScalarField):
    def __init__(self, rbf):
        self.rbf = rbf

    def evaluate(self, x, y, z):
        return self.rbf(x, y, z)

    def evaluate_grid(self, xs, ys, zs):
        value = self.rbf(xs, ys, zs)
        return value

##################
#                #
#  Vector Fields #
#                #
##################

class SvRbfVectorField(SvVectorField):
    def __init__(self, rbf, relative = True):
        self.rbf = rbf
        self.relative = relative

    def evaluate(self, x, y, z):
        v = self.rbf(x, y, z) 
        if self.relative:
            v = v - np.array([x, y, z])
        return v

    def evaluate_grid(self, xs, ys, zs):
        value = self.rbf(xs, ys, zs)
        vx = value[:,0]
        vy = value[:,1]
        vz = value[:,2]
        if self.relative:
            vx = vx - xs
            vy = vy - ys
            vz = vz - zs
        return vx, vy, vz

class SvBvhRbfNormalVectorField(SvVectorField):
    def __init__(self, bvh, rbf):
        self.bvh = bvh
        self.rbf = rbf

    def evaluate(self, x, y, z):
        vertex = Vector((x,y,z))
        nearest, normal, idx, distance = self.bvh.find_nearest(vertex)
        x0, y0, z0 = nearest
        return self.rbf(x0, y0, z0)
    
    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, normal, idx, distance = self.bvh.find_nearest(v)
            if nearest is None:
                raise Exception("No nearest point on mesh found for vertex %s" % v)
            x0, y0, z0 = nearest
            return self.rbf(x0, y0, z0)

        points = np.stack((xs, ys, zs)).T
        vectors = np.vectorize(find, signature='(3)->(3)')(points)
        R = vectors.T
        return R[0], R[1], R[2]

def mesh_field(bm, function, smooth, epsilon, scale, use_verts=True, use_edges=False, use_faces=False):
    src_points = []
    dst_values = []
    if use_verts:
        for bm_vert in bm.verts:
            src_points.append(tuple(bm_vert.co))
            dst_values.append(0.0)
            src_points.append(tuple(bm_vert.co + scale * bm_vert.normal))
            dst_values.append(1.0)

    if use_edges:
        for bm_edge in bm.edges:
            pt1 = 0.5*(bm_edge.verts[0].co + bm_edge.verts[1].co)
            normal = (bm_edge.verts[0].normal + bm_edge.verts[1].normal).normalized()
            pt2 = pt1 + scale * normal
            src_points.append(tuple(pt1))
            dst_values.append(0.0)
            src_points.append(tuple(pt2))
            dst_values.append(1.0)

    if use_faces:
        for bm_face in bm.faces:
            pt1 = bm_face.calc_center_median()
            pt2 = pt1 + scale * bm_face.normal
            src_points.append(tuple(pt1))
            dst_values.append(0.0)
            src_points.append(tuple(pt2))
            dst_values.append(1.0)

    src_points = np.array(src_points)
    dst_values = np.array(dst_values)

    xs_from = src_points[:,0]
    ys_from = src_points[:,1]
    zs_from = src_points[:,2]

    rbf = Rbf(xs_from, ys_from, zs_from, dst_values,
            function = function,
            smooth = smooth,
            epsilon = epsilon,
            mode = '1-D')

    return SvRbfScalarField(rbf)

def register():
    pass

def unregister():
    pass


