# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sqrt, copysign, pi
from mathutils import Matrix, Vector
from mathutils import noise
from mathutils import kdtree
from mathutils import bvhtree

from sverchok.utils.geom import autorotate_householder, autorotate_track, autorotate_diff, diameter, LineEquation, CircleEquation3D
from sverchok.utils.math import from_cylindrical, from_spherical

from sverchok.utils.curve import SvCurveLengthSolver, SvNormalTrack

##################
#                #
#  Vector Fields #
#                #
##################

class SvVectorField(object):
    def __repr__(self):
        if hasattr(self, '__description__'):
            description = self.__description__
        else:
            description = self.__class__.__name__
        return "<{} vector field>".format(description)

    def evaluate(self, point):
        raise Exception("not implemented")

    def evaluate_grid(self, xs, ys, zs):
        raise Exception("not implemented")

class SvMatrixVectorField(SvVectorField):

    def __init__(self, matrix):
        self.matrix = matrix
        self.__description__ = "Matrix"

    def evaluate(self, x, y, z):
        v = Vector((x, y, z))
        v = (self.matrix @ v) - v
        return np.array(v)

    def evaluate_grid(self, xs, ys, zs):
        matrix = np.array(self.matrix.to_3x3())
        translation = np.array(self.matrix.translation)
        points = np.stack((xs, ys, zs)).T
        R = np.apply_along_axis(lambda v : matrix @ v + translation - v, 1, points).T
        return R[0], R[1], R[2]

class SvConstantVectorField(SvVectorField):

    def __init__(self, vector):
        self.vector = np.array(vector)
        self.__description__ = "Constant = {}".format(vector)

    def evaluate(self, x, y, z):
        return self.vector
    
    def evaluate_grid(self, xs, ys, zs):
        x, y, z = self.vector
        rx = np.full_like(xs, x)
        ry = np.full_like(ys, y)
        rz = np.full_like(zs, z)
        return rx, ry, rz

class SvComposedVectorField(SvVectorField):
    def __init__(self, coords, sfield1, sfield2, sfield3):
        self.coords = coords
        self.sfield1 = sfield1
        self.sfield2 = sfield2
        self.sfield3 = sfield3
        self.__description__ = "{}({}, {}, {})".format(coords, sfield1, sfield2, sfield3)

    def evaluate(self, x, y, z):
        v1 = self.sfield1.evaluate(x, y, z)
        v2 = self.sfield2.evaluate(x, y, z)
        v3 = self.sfield3.evaluate(x, y, z)
        if self.coords == 'XYZ':
            return np.array((v1, v2, v3))
        elif self.coords == 'CYL':
            return np.array(from_cylindrical(v1, v2, v3, mode='radians'))
        else: # SPH:
            return np.array(from_spherical(v1, v2, v3, mode='radians'))

    def evaluate_grid(self, xs, ys, zs):
        v1s = self.sfield1.evaluate_grid(xs, ys, zs)
        v2s = self.sfield2.evaluate_grid(xs, ys, zs)
        v3s = self.sfield3.evaluate_grid(xs, ys, zs)
        if self.coords == 'XYZ':
            return v1s, v2s, v3s
        elif self.coords == 'CYL':
            vectors = np.stack((v1s, v2s, v3s)).T
            vectors = np.apply_along_axis(lambda v: np.array(from_cylindrical(*tuple(v), mode='radians')), 1, vectors).T
            return vectors[0], vectors[1], vectors[2]
        else: # SPH:
            vectors = np.stack((v1s, v2s, v3s)).T
            vectors = np.apply_along_axis(lambda v: np.array(from_spherical(*tuple(v), mode='radians')), 1, vectors).T
            return vectors[0], vectors[1], vectors[2]

class SvAbsoluteVectorField(SvVectorField):
    def __init__(self, field):
        self.field = field
        self.__description__ = "Absolute({})".format(field)

    def evaluate(self, x, y, z):
        r = self.field.evaluate(x, y, z)
        return r + np.array([x, y, z])
    
    def evaluate_grid(self, xs, ys, zs):
        rxs, rys, rzs = self.field.evaluate_grid(xs, ys, zs)
        return rxs + xs, rys + ys, rzs + zs

class SvRelativeVectorField(SvVectorField):
    def __init__(self, field):
        self.field = field
        self.__description__ = "Relative({})".format(field)

    def evaluate(self, x, y, z):
        r = self.field.evaluate(x, y, z)
        return r - np.array([x, y, z])
    
    def evaluate_grid(self, xs, ys, zs):
        rxs, rys, rzs = self.field.evaluate_grid(xs, ys, zs)
        return rxs - xs, rys - ys, rzs - zs

class SvVectorFieldLambda(SvVectorField):

    __description__ = "Formula"

    def __init__(self, function, variables, in_field, function_numpy = None):
        self.function = function
        self.function_numpy = function_numpy
        self.variables = variables
        self.in_field = in_field

    def evaluate_grid(self, xs, ys, zs):
        if self.in_field is None:
            Vs = np.zeros(xs.shape[0])
        else:
            vx, vy, vz = self.in_field.evaluate_grid(xs, ys, zs)
            Vs = np.stack((vx, vy, vz)).T
        if self.function_numpy is None:
            return np.vectorize(self.function,
                        signature = "(),(),(),(3)->(),(),()")(xs, ys, zs, Vs)
        else:
            return self.function_numpy(xs, ys, zs, Vs)

    def evaluate(self, x, y, z):
        if self.in_field is None:
            V = None
        else:
            V = self.in_field.evaluate(x, y, z)
        return np.array(self.function(x, y, z, V))

class SvVectorFieldBinOp(SvVectorField):
    def __init__(self, field1, field2, function):
        self.function = function
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        return self.function(self.field1.evaluate(x, y, z), self.field2.evaluate(x, y, z))

    def evaluate_grid(self, xs, ys, zs):
        def func(xs, ys, zs):
            vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
            vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
            R = self.function(np.array([vx1, vy1, vz1]), np.array([vx2, vy2, vz2]))
            return R[0], R[1], R[2]
        return np.vectorize(func, signature="(m),(m),(m)->(m),(m),(m)")(xs, ys, zs)

class SvAverageVectorField(SvVectorField):

    def __init__(self, fields):
        self.fields = fields
        self.__description__ = "Average"

    def evaluate(self, x, y, z):
        vectors = np.array([field.evaluate(x, y, z) for field in self.fields])
        return np.mean(vectors, axis=0)

    def evaluate_grid(self, xs, ys, zs):
        def func(xs, ys, zs):
            data = []
            for field in self.fields:
                vx, vy, vz = field.evaluate_grid(xs, ys, zs)
                vectors = np.stack((vx, vy, vz)).T
                data.append(vectors)
            data = np.array(data)
            mean = np.mean(data, axis=0).T
            return mean[0], mean[1], mean[2]
        return np.vectorize(func, signature="(m),(m),(m)->(m),(m),(m)")(xs, ys, zs)

class SvVectorFieldCrossProduct(SvVectorField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "{} x {}".format(field1, field2)

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x, y, z)
        v2 = self.field2.evaluate(x, y, z)
        return np.cross(v1, v2)

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1)).T
        vectors2 = np.stack((vx2, vy2, vz2)).T
        R = np.cross(vectors1, vectors2).T
        return R[0], R[1], R[2]

class SvVectorFieldMultipliedByScalar(SvVectorField):
    def __init__(self, vector_field, scalar_field):
        self.vector_field = vector_field
        self.scalar_field = scalar_field
        self.__description__ = "{} * {}".format(scalar_field, vector_field)

    def evaluate(self, x, y, z):
        scalar = self.scalar_field.evaluate(x, y, z)
        vector = self.vector_field.evaluate(x, y, z)
        return scalar * vector

    def evaluate_grid(self, xs, ys, zs):
        def product(xs, ys, zs):
            scalars = self.scalar_field.evaluate_grid(xs, ys, zs)
            vx, vy, vz = self.vector_field.evaluate_grid(xs, ys, zs)
            vectors = np.stack((vx, vy, vz))
            R = (scalars * vectors)
            return R[0], R[1], R[2]
        return np.vectorize(product, signature="(m),(m),(m)->(m),(m),(m)")(xs, ys, zs)

class SvVectorFieldsLerp(SvVectorField):

    def __init__(self, vfield1, vfield2, scalar_field):
        self.vfield1 = vfield1
        self.vfield2 = vfield2
        self.scalar_field = scalar_field
        self.__description__ = "Lerp"

    def evaluate(self, x, y, z):
        scalar = self.scalar_field.evaluate(x, y, z)
        vector1 = self.vfield1.evaluate(x, y, z)
        vector2 = self.vfield2.evaluate(x, y, z)
        return (1 - scalar) * vector1 + scalar * vector2

    def evaluate_grid(self, xs, ys, zs):
            scalars = self.scalar_field.evaluate_grid(xs, ys, zs)
            vx1, vy1, vz1 = self.vfield1.evaluate_grid(xs, ys, zs)
            vectors1 = np.stack((vx1, vy1, vz1))
            vx2, vy2, vz2 = self.vfield2.evaluate_grid(xs, ys, zs)
            vectors2 = np.stack((vx2, vy2, vz2))
            R = (1 - scalars) * vectors1 + scalars * vectors2
            return R[0], R[1], R[2]

class SvNoiseVectorField(SvVectorField):
    def __init__(self, noise_type, seed):
        self.noise_type = noise_type
        self.seed = seed
        self.__description__ = "{} noise".format(noise_type)

    def evaluate(self, x, y, z):
        noise.seed_set(self.seed)
        return noise.noise_vector((x, y, z), noise_basis=self.noise_type)

    def evaluate_grid(self, xs, ys, zs):
        noise.seed_set(self.seed)
        def mk_noise(v):
            r = noise.noise_vector(v, noise_basis=self.noise_type)
            return r[0], r[1], r[2]
        vectors = np.stack((xs,ys,zs)).T
        return np.vectorize(mk_noise, signature="(3)->(),(),()")(vectors)

class SvKdtVectorField(SvVectorField):

    def __init__(self, vertices=None, kdt=None, falloff=None, negate=False):
        self.falloff = falloff
        self.negate = negate
        if kdt is not None:
            self.kdt = kdt
        elif vertices is not None:
            self.kdt = kdtree.KDTree(len(vertices))
            for i, v in enumerate(vertices):
                self.kdt.insert(v, i)
            self.kdt.balance()
        else:
            raise Exception("Either kdt or vertices must be provided")
        self.__description__ = "KDT Attractor"

    def evaluate(self, x, y, z):
        nearest, i, distance = self.kdt.find((x, y, z))
        vector = np.array(nearest) - np.array([x, y, z])
        if self.falloff is not None:
            value = self.falloff(np.array([distance]))[0]
            if self.negate:
                value = - value
            norm = np.linalg.norm(vector)
            return value * vector / norm
        else:
            if self.negate:
                return - vector
            else:
                return vector

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, i, distance = self.kdt.find(v)
            dv = np.array(nearest) - np.array(v)
            if self.negate:
                return - dv
            else:
                return dv

        points = np.stack((xs, ys, zs)).T
        vectors = np.vectorize(find, signature='(3)->(3)')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            lens = self.falloff(norms)
            nonzero = (norms > 0)[:,0]
            lens = self.falloff(norms)
            vectors[nonzero] = vectors[nonzero] / norms[nonzero]
            R = (lens * vectors).T
            return R[0], R[1], R[2]
        else:
            R = vectors.T
            return R[0], R[1], R[2]

class SvVectorFieldPointDistance(SvVectorField):
    def __init__(self, center, metric='EUCLIDEAN', falloff=None):
        self.center = center
        self.falloff = falloff
        self.metric = metric
        self.__description__ = "Distance from {}".format(tuple(center))

    def evaluate_grid(self, xs, ys, zs):
        x0, y0, z0 = tuple(self.center)
        xs = x0 - xs
        ys = y0 - ys
        zs = z0 - zs
        vectors = np.stack((xs, ys, zs))
        if self.metric == 'EUCLIDEAN':
            norms = np.linalg.norm(vectors, axis=0)
        elif self.metric == 'CHEBYSHEV':
            norms = np.max(np.abs(vectors), axis=0)
        elif self.metric == 'MANHATTAN':
            norms = np.sum(np.abs(vectors), axis=0)
        else:
            raise Exception('Unknown metric')
        if self.falloff is not None:
            lens = self.falloff(norms)
            R = lens * vectors / norms
        else:
            R = vectors
        return R[0], R[1], R[2]

    def evaluate(self, x, y, z):
        point = np.array([x, y, z]) - self.center
        if self.metric == 'EUCLIDEAN':
            norm = np.linalg.norm(point)
        elif self.metric == 'CHEBYSHEV':
            norm = np.max(point)
        elif self.metric == 'MANHATTAN':
            norm = np.sum(np.abs(point))
        else:
            raise Exception('Unknown metric')
        if self.falloff is not None:
            value = self.falloff(np.array([norm]))[0]
            return value * point / norm
        else:
            return point

class SvLineAttractorVectorField(SvVectorField):

    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff
        self.__description__ = "Line Attractor"

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        dv = to_center - projection
        if self.falloff is not None:
            norm = np.linalg.norm(dv)
            dv = self.falloff(norm) * dv / norm
        return dv

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            dv = to_center - projection
            return dv

        points = np.stack((xs, ys, zs)).T
        vectors = np.vectorize(func, signature='(3)->(3)')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            lens = self.falloff(norms)
            vectors[nonzero] = vectors[nonzero] / norms[nonzero][:,0][np.newaxis].T
            R = (lens * vectors).T
            return R[0], R[1], R[2]
        else:
            R = vectors.T
            return R[0], R[1], R[2]

class SvPlaneAttractorVectorField(SvVectorField):
    
    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff
        self.__description__ = "Plane Attractor"

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        dv = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        if self.falloff is not None:
            norm = np.linalg.norm(dv)
            dv = self.falloff(norm) * dv / norm
        return dv

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            return projection

        points = np.stack((xs, ys, zs)).T
        vectors = np.vectorize(func, signature='(3)->(3)')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            lens = self.falloff(norms)
            nonzero = (norms > 0)[:,0]
            vectors[nonzero] = vectors[nonzero] / norms[nonzero][:,0][np.newaxis].T
            R = (lens * vectors).T
            return R[0], R[1], R[2]
        else:
            R = vectors.T
            return R[0], R[1], R[2]

class SvCircleAttractorVectorField(SvVectorField):
    __description__ = "Circle Attractor"

    def __init__(self, center, radius, normal, falloff=None):
        self.circle = CircleEquation3D.from_center_radius_normal(center, radius, normal)
        self.falloff = falloff

    def evaluate(self, x, y, z):
        v = np.array([x,y,z])
        projection = self.circle.get_projections([v])[0]
        vector = projection - v
        if self.fallof is not None:
            new_len = self.falloff(np.array([distance]))[0]
            norm = np.linalg.norm(vector)
            return new_len * vector / norm
        else:
            return vector

    def evaluate_grid(self, xs, ys, zs):
        vs = np.stack((xs, ys, zs)).T
        projections = self.circle.get_projections(vs)
        vectors = projections - vs
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            lens = self.falloff(norms)
            nonzero = (norms > 0)[:,0]
            vectors[nonzero] = vectors[nonzero] / norms[nonzero][:,0][np.newaxis].T
            R = (lens * vectors).T
            return R[0], R[1], R[2]
        else:
            R = vectors.T
            return R[0], R[1], R[2]

class SvEdgeAttractorVectorField(SvVectorField):
    __description__ = "Edge attractor"

    def __init__(self, v1, v2, falloff=None):
        self.falloff = falloff
        self.v1 = Vector(v1)
        self.v2 = Vector(v2)
    
    def evaluate(self, x, y, z):
        v = Vector([x,y,z])
        dv1 = (v - self.v1).length
        dv2 = (v - self.v2).length
        if dv1 > dv2:
            distance_to_nearest = dv2
            nearest_vert = self.v2
            another_vert = self.v1
        else:
            distance_to_nearest = dv1
            nearest_vert = self.v1
            another_vert = self.v2
        edge = another_vert - nearest_vert
        to_nearest = v - nearest_vert
        if to_nearest.length == 0:
            return 0
        angle = edge.angle(to_nearest)
        if angle > pi/2:
            distance = distance_to_nearest
            vector = - to_nearest
        else:
            vector = LineEquation.from_two_points(self.v1, self.v2).projection_of_points(v)
            distance = vector.length
            vector = np.array(vector)
        if self.falloff is not None:
            return self.falloff(distance) * vector / distance
        else:
            return vector
    
    def evaluate_grid(self, xs, ys, zs):
        n = len(xs)
        vs = np.stack((xs, ys, zs)).T
        v1 = np.array(self.v1)
        v2 = np.array(self.v2)    
        dv1s = np.linalg.norm(vs - v1, axis=1)
        dv2s = np.linalg.norm(vs - v2, axis=1)
        v1_is_nearest = (dv1s < dv2s)
        v2_is_nearest = np.logical_not(v1_is_nearest)
        nearest_verts = np.empty_like(vs)
        other_verts = np.empty_like(vs)
        nearest_verts[v1_is_nearest] = v1
        nearest_verts[v2_is_nearest] = v2
        other_verts[v1_is_nearest] = v2
        other_verts[v2_is_nearest] = v1
        
        to_nearest = vs - nearest_verts
        
        edges = other_verts - nearest_verts
        dot = (to_nearest * edges).sum(axis=1)
        at_edge = (dot > 0)
        at_vertex = np.logical_not(at_edge)
        at_v1 = np.logical_and(at_vertex, v1_is_nearest)
        at_v2 = np.logical_and(at_vertex, v2_is_nearest)

        line = LineEquation.from_two_points(self.v1, self.v2)
        
        vectors = np.empty((n,3))
        vectors[at_edge] = line.projection_of_points(vs[at_edge]) - vs[at_edge]
        vectors[at_v1] = v1 - vs[at_v1]
        vectors[at_v2] = v2 - vs[at_v2]

        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            lens = self.falloff(norms)
            nonzero = (norms > 0)[:,0]
            vectors[nonzero] = vectors[nonzero] / norms[nonzero][:,0][np.newaxis].T
            R = (lens * vectors).T
            return R[0], R[1], R[2]
        else:
            R = vectors.T
            return R[0], R[1], R[2]
        
class SvBvhAttractorVectorField(SvVectorField):

    def __init__(self, bvh=None, verts=None, faces=None, falloff=None, use_normal=False, signed_normal=False):
        self.falloff = falloff
        self.use_normal = use_normal
        self.signed_normal = signed_normal
        if bvh is not None:
            self.bvh = bvh
        elif verts is not None and faces is not None:
            self.bvh = bvhtree.BVHTree.FromPolygons(verts, faces)
        else:
            raise Exception("Either bvh or verts and faces must be provided!")
        self.__description__ = "BVH Attractor"

    def evaluate(self, x, y, z):
        vertex = Vector((x,y,z))
        nearest, normal, idx, distance = self.bvh.find_nearest(vertex)
        if self.use_normal:
            if self.signed_normal:
                sign = (v - nearest).dot(normal)
                sign = copysign(1, sign)
            else:
                sign = 1
            return sign * np.array(normal)
        else:
            dv = np.array(nearest - vertex)
            if self.falloff is not None:
                norm = np.linalg.norm(dv)
                len = self.falloff(norm)
                dv = len * dv
                return dv
            else:
                return dv

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, normal, idx, distance = self.bvh.find_nearest(v)
            if nearest is None:
                raise Exception("No nearest point on mesh found for vertex %s" % v)
            if self.use_normal:
                if self.signed_normal:
                    sign = (v - nearest).dot(normal)
                    sign = copysign(1, sign)
                else:
                    sign = 1
                return sign * np.array(normal)
            else:
                return np.array(nearest) - v

        points = np.stack((xs, ys, zs)).T
        vectors = np.vectorize(find, signature='(3)->(3)')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            lens = self.falloff(norms)
            vectors[nonzero] = vectors[nonzero] / norms[nonzero]
            R = (lens * vectors).T
            return R[0], R[1], R[2]
        else:
            R = vectors.T
            return R[0], R[1], R[2]

class SvSelectVectorField(SvVectorField):
    def __init__(self, fields, mode):
        self.fields = fields
        self.mode = mode
        self.__description__ = "{}({})".format(mode, fields)

    def evaluate(self, x, y, z):
        vectors = [field.evaluate(x, y, z) for field in self.fields]
        vectors = np.array(vectors)
        norms = np.linalg.norm(vectors, axis=1)
        if self.mode == 'MIN':
            selected = np.argmin(norms)
        else: # MAX
            selected = np.argmax(norms)
        return vectors[selected]

    def evaluate_grid(self, xs, ys, zs):
        n = len(xs)
        vectors = [field.evaluate_grid(xs, ys, zs) for field in self.fields]
        vectors = np.stack(vectors)
        vectors = np.transpose(vectors, axes=(2,0,1))
        norms = np.linalg.norm(vectors, axis=2)
        if self.mode == 'MIN':
            selected = np.argmin(norms, axis=1)
        else: # MAX
            selected = np.argmax(norms, axis=1)
        all_points = list(range(n))
        vectors = vectors[all_points, selected, :]
        return vectors

class SvVectorFieldTangent(SvVectorField):

    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "Tangent"

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x,y,z)
        projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
        return projection
    
    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1)).T
        vectors2 = np.stack((vx2, vy2, vz2)).T

        def project(v1, v2):
            projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
            vx, vy, vz = projection
            return vx, vy, vz

        return np.vectorize(project, signature="(3),(3)->(),(),()")(vectors1, vectors2)

class SvVectorFieldCotangent(SvVectorField):

    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "Cotangent"

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x,y,z)
        projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
        return v1 - projection
    
    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1)).T
        vectors2 = np.stack((vx2, vy2, vz2)).T

        def project(v1, v2):
            projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
            coprojection = v1 - projection
            vx, vy, vz = coprojection
            return vx, vy, vz

        return np.vectorize(project, signature="(3),(3)->(),(),()")(vectors1, vectors2)

class SvVectorFieldComposition(SvVectorField):

    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "Composition"

    def evaluate(self, x, y, z):
        x1, y1, z1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x1,y1,z1)
        return v2
    
    def evaluate_grid(self, xs, ys, zs):
        r = self.field1.evaluate_grid(xs, ys, zs)
        vx1, vy1, vz1 = r
        return self.field2.evaluate_grid(vx1, vy1, vz1)

class SvScalarFieldGradient(SvVectorField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Grad({})".format(field)

    def evaluate(self, x, y, z):
        return self.field.gradient([x, y, z], step=self.step)
    
    def evaluate_grid(self, xs, ys, zs):
        return self.field.gradient_grid(xs, ys, zs, step=self.step)

class SvVectorFieldRotor(SvVectorField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Rot({})".format(field)

    def evaluate(self, x, y, z):
        step = self.step
        _, y_dx_plus, z_dx_plus = self.field.evaluate(x+step,y,z)
        _, y_dx_minus, z_dx_minus = self.field.evaluate(x-step,y,z)
        x_dy_plus, _, z_dy_plus = self.field.evaluate(x, y+step, z)
        x_dy_minus, _, z_dy_minus = self.field.evaluate(x, y-step, z)
        x_dz_plus, y_dz_plus, _ = self.field.evaluate(x, y, z+step)
        x_dz_minus, y_dz_minus, _ = self.field.evaluate(x, y, z-step)

        dy_dx = (y_dx_plus - y_dx_minus) / (2*step)
        dz_dx = (z_dx_plus - z_dx_minus) / (2*step)
        dx_dy = (x_dy_plus - x_dy_minus) / (2*step)
        dz_dy = (z_dy_plus - z_dy_minus) / (2*step)
        dx_dz = (x_dz_plus - x_dz_minus) / (2*step)
        dy_dz = (y_dz_plus - y_dz_minus) / (2*step)

        rx = dz_dy - dy_dz
        ry = - (dz_dx - dx_dz)
        rz = dy_dx - dx_dy

        return np.array([rx, ry, rz])

    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        _, y_dx_plus, z_dx_plus = self.field.evaluate_grid(xs+step,ys,zs)
        _, y_dx_minus, z_dx_minus = self.field.evaluate_grid(xs-step,ys,zs)
        x_dy_plus, _, z_dy_plus = self.field.evaluate_grid(xs, ys+step, zs)
        x_dy_minus, _, z_dy_minus = self.field.evaluate_grid(xs, ys-step, zs)
        x_dz_plus, y_dz_plus, _ = self.field.evaluate_grid(xs, ys, zs+step)
        x_dz_minus, y_dz_minus, _ = self.field.evaluate_grid(xs, ys, zs-step)

        dy_dx = (y_dx_plus - y_dx_minus) / (2*step)
        dz_dx = (z_dx_plus - z_dx_minus) / (2*step)
        dx_dy = (x_dy_plus - x_dy_minus) / (2*step)
        dz_dy = (z_dy_plus - z_dy_minus) / (2*step)
        dx_dz = (x_dz_plus - x_dz_minus) / (2*step)
        dy_dz = (y_dz_plus - y_dz_minus) / (2*step)

        rx = dz_dy - dy_dz
        ry = - (dz_dx - dx_dz)
        rz = dy_dx - dx_dy
        R = np.stack((rx, ry, rz))
        return R[0], R[1], R[2]

class SvBendAlongCurveField(SvVectorField):

    ZERO = 'ZERO'
    FRENET = 'FRENET'
    HOUSEHOLDER = 'householder'
    TRACK = 'track'
    DIFF = 'diff'
    TRACK_NORMAL = 'track_normal'

    def __init__(self, curve, algorithm, scale_all, axis, t_min, t_max, up_axis=None, resolution=50, length_mode='T'):
        self.curve = curve
        self.axis = axis
        self.t_min = t_min
        self.t_max = t_max
        self.algorithm = algorithm
        self.scale_all = scale_all
        self.up_axis = up_axis
        self.length_mode = length_mode
        if algorithm == SvBendAlongCurveField.ZERO:
            self.curve.pre_calc_torsion_integral(resolution)
        elif algorithm == SvBendAlongCurveField.TRACK_NORMAL:
            self.normal_tracker = SvNormalTrack(curve, resolution)
        if length_mode == 'L':
            self.length_solver = SvCurveLengthSolver(curve)
            self.length_solver.prepare('SPL', resolution)
        self.__description__ = "Bend along {}".format(curve)

    def get_matrix(self, tangent, scale):
        x = Vector((1.0, 0.0, 0.0))
        y = Vector((0.0, 1.0, 0.0))
        z = Vector((0.0, 0.0, 1.0))

        if self.axis == 0:
            ax1, ax2, ax3 = x, y, z
        elif self.axis == 1:
            ax1, ax2, ax3 = y, x, z
        else:
            ax1, ax2, ax3 = z, x, y

        if self.scale_all:
            scale_matrix = Matrix.Scale(1/scale, 4, ax1) @ Matrix.Scale(scale, 4, ax2) @ Matrix.Scale(scale, 4, ax3)
        else:
            scale_matrix = Matrix.Scale(1/scale, 4, ax1)
        scale_matrix = np.array(scale_matrix.to_3x3())

        tangent = Vector(tangent)
        if self.algorithm == SvBendAlongCurveField.HOUSEHOLDER:
            rot = autorotate_householder(ax1, tangent).inverted()
        elif self.algorithm == SvBendAlongCurveField.TRACK:
            axis = "XYZ"[self.axis]
            rot = autorotate_track(axis, tangent, self.up_axis)
        elif self.algorithm == SvBendAlongCurveField.DIFF:
            rot = autorotate_diff(tangent, ax1)
        else:
            raise Exception("Unsupported algorithm")
        rot = np.array(rot.to_3x3())

        return np.matmul(rot, scale_matrix)

    def get_matrices(self, ts, scale):
        n = len(ts)
        if self.scale_all:
            scale_matrix = np.array([
                [scale, 0, 0],
                [0, scale, 0],
                [0, 0, 1/scale]
            ])
        else:
            scale_matrix = np.array([
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1/scale]
            ])
        if self.algorithm == SvBendAlongCurveField.FRENET:
            frenet, _ , _ = self.curve.frame_array(ts)
            return frenet @ scale_matrix
        elif self.algorithm == SvBendAlongCurveField.ZERO:
            frenet, _ , _ = self.curve.frame_array(ts)
            angles = - self.curve.torsion_integral(ts)
            zeros = np.zeros((n,))
            ones = np.ones((n,))
            row1 = np.stack((np.cos(angles), np.sin(angles), zeros)).T # (n, 3)
            row2 = np.stack((-np.sin(angles), np.cos(angles), zeros)).T # (n, 3)
            row3 = np.stack((zeros, zeros, ones)).T # (n, 3)
            rotation_matrices = np.dstack((row1, row2, row3))
            return frenet @ rotation_matrices @ scale_matrix
        elif self.algorithm == SvBendAlongCurveField.TRACK_NORMAL:
            matrices = self.normal_tracker.evaluate_array(ts)
            return matrices @ scale_matrix
        else:
            raise Exception("Unsupported algorithm")

    def get_t_value(self, x, y, z):
        curve_t_min, curve_t_max = self.curve.get_u_bounds()
        t = [x, y, z][self.axis]
        if self.length_mode == 'T':
            t = (curve_t_max - curve_t_min) * (t - self.t_min) / (self.t_max - self.t_min) + curve_t_min
        else:
            t = (t - self.t_min) / (self.t_max - self.t_min) # 0 .. 1
            t = t * self.length_solver.get_total_length()
            t = self.length_solver.solve(np.array([t]))[0]
        return t

    def get_t_values(self, xs, ys, zs):
        curve_t_min, curve_t_max = self.curve.get_u_bounds()
        ts = [xs, ys, zs][self.axis]
        if self.length_mode == 'T':
            ts = (curve_t_max - curve_t_min) * (ts - self.t_min) / (self.t_max - self.t_min) + curve_t_min
        else:
            ts = (ts - self.t_min) / (self.t_max - self.t_min) # 0 .. 1
            ts = ts * self.length_solver.get_total_length()
            ts = self.length_solver.solve(ts)
        return ts

    def get_scale(self):
        if self.length_mode == 'T':
            curve_t_min, curve_t_max = self.curve.get_u_bounds()
            t_range = curve_t_max - curve_t_min
        else:
            t_range = self.length_solver.get_total_length()
        return (self.t_max - self.t_min) / t_range

    def evaluate(self, x, y, z):
        t = self.get_t_value(x, y, z)
        spline_tangent = self.curve.tangent(t)
        spline_vertex = self.curve.evaluate(t)
        scale = self.get_scale()
        if self.algorithm in {SvBendAlongCurveField.ZERO, SvBendAlongCurveField.FRENET, SvBendAlongCurveField.TRACK_NORMAL}:
            matrix = self.get_matrices(np.array([t]), scale)
        else:
            matrix = self.get_matrix(spline_tangent, scale)
        src_vector_projection = np.array([x, y, z])
        src_vector_projection[self.axis] = 0
        new_vertex = np.matmul(matrix, src_vector_projection) + spline_vertex
        vector = new_vertex - np.array([x, y, z])
        return vector

    def evaluate_grid(self, xs, ys, zs):
        def multiply(matrices, vectors):
            vectors = vectors[np.newaxis]
            vectors = np.transpose(vectors, axes=(1,2,0))
            r = matrices @ vectors
            return r[:,:,0]

        ts = self.get_t_values(xs, ys, zs).flatten()
        spline_tangents = self.curve.tangent_array(ts)
        spline_vertices = self.curve.evaluate_array(ts)
        scale = self.get_scale()
        if self.algorithm in {SvBendAlongCurveField.ZERO, SvBendAlongCurveField.FRENET, SvBendAlongCurveField.TRACK_NORMAL}:
            matrices = self.get_matrices(ts, scale)
        else:
            matrices = np.vectorize(lambda t : self.get_matrix(t, scale), signature='(3)->(3,3)')(spline_tangents)
        src_vectors = np.stack((xs, ys, zs)).T
        src_vector_projections = src_vectors.copy()
        src_vector_projections[:,self.axis] = 0
        #multiply = np.vectorize(lambda m, v: m @ v, signature='(3,3),(3)->(3)')
        new_vertices = multiply(matrices, src_vector_projections) + spline_vertices
        R = (new_vertices - src_vectors).T
        return R[0], R[1], R[2]

class SvBendAlongSurfaceField(SvVectorField):
    def __init__(self, surface, axis, autoscale=False, flip=False):
        self.surface = surface
        self.orient_axis = axis
        self.autoscale = autoscale
        self.flip = flip
        self.u_bounds = (0, 1)
        self.v_bounds = (0, 1)
        self.__description__ = "Bend along {}".format(surface)

    def get_other_axes(self):
        # Select U and V to be two axes except orient_axis
        if self.orient_axis == 0:
            u_index, v_index = 1,2
        elif self.orient_axis == 1:
            u_index, v_index = 2,0
        else:
            u_index, v_index = 1,0
        return u_index, v_index
        
    def get_uv(self, vertices):
        """
        Translate source vertices to UV space of future spline.
        vertices must be np.array of shape (n, 3).
        """
        u_index, v_index = self.get_other_axes()

        # Rescale U and V coordinates to [0, 1], drop third coordinate
        us = vertices[:,u_index].flatten()
        vs = vertices[:,v_index].flatten()
        min_u, max_u = self.u_bounds
        min_v, max_v = self.v_bounds
        size_u = max_u - min_u
        size_v = max_v - min_v

        if size_u < 0.00001:
            raise Exception("Object has too small size in U direction")
        if size_v < 0.00001:
            raise Exception("Object has too small size in V direction")

        us = self.surface.u_size * (us - min_u) / size_u + self.surface.get_u_min()
        vs = self.surface.v_size * (vs - min_v) / size_v + self.surface.get_v_min()

        return size_u, size_v, us, vs

    def _evaluate(self, vertices):
        src_size_u, src_size_v, us, vs = self.get_uv(vertices)
        if self.autoscale:
            u_index, v_index = self.get_other_axes()
            scale_u = src_size_u / self.surface.u_size
            scale_v = src_size_v / self.surface.v_size
            scale_z = sqrt(scale_u * scale_v)
        else:
            if self.orient_axis == 2:
                scale_z = -1.0
            else:
                scale_z = 1.0
        if self.flip:
            scale_z = - scale_z

        surf_vertices = self.surface.evaluate_array(us, vs)
        spline_normals = self.surface.normal_array(us, vs)
        zs = vertices[:,self.orient_axis].flatten()
        zs = zs[np.newaxis].T
        v1 = zs * spline_normals
        v2 = scale_z * v1
        new_vertices = surf_vertices + v2
        return new_vertices

    def evaluate_grid(self, xs, ys, zs):
        vertices = np.stack((xs, ys, zs)).T
        new_vertices = self._evaluate(vertices)
        R = (new_vertices - vertices).T
        return R[0], R[1], R[2]

    def evaluate(self, x, y, z):
        xs, ys, zs = self.evaluate_grid(np.array([[[x]]]), np.array([[[y]]]), np.array([[[z]]]))
        return np.array([xs, ys, zs])

class SvVoronoiVectorField(SvVectorField):

    def __init__(self, vertices):
        self.kdt = kdtree.KDTree(len(vertices))
        for i, v in enumerate(vertices):
            self.kdt.insert(v, i)
        self.kdt.balance()
        self.__description__ = "Voronoi"

    def evaluate(self, x, y, z):
        v = Vector((x,y,z))
        vs = self.kdt.find_n(v, 2)
        if len(vs) != 2:
            raise Exception("Unexpected kdt result at (%s,%s,%s): %s" % (x, y, z, vs))
        t1, t2 = vs
        d1 = t1[2]
        d2 = t2[2]
        delta = abs(d1 - d2)
        v1 = (t1[0] - v).normalized()
        return delta * np.array(v1)

    def evaluate_grid(self, xs, ys, zs):
        points = np.vectorize(self.evaluate, signature='(),(),()->(3)')(xs,ys,zs).T
        return points[0], points[1], points[2]

