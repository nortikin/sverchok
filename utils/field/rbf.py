
import numpy as np
from mathutils import Matrix, Vector

from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.vector import SvVectorField

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

def register():
    pass

def unregister():
    pass


