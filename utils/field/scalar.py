# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import copysign

from mathutils import Matrix, Vector
from mathutils import kdtree
from mathutils import bvhtree

from sverchok.utils.math import from_cylindrical, from_spherical, to_cylindrical, to_spherical

##################
#                #
#  Scalar Fields #
#                #
##################

class SvScalarField(object):

    def __repr__(self):
        if hasattr(self, '__description__'):
            description = self.__description__
        else:
            description = self.__class__.__name__
        return "<{} scalar field>".format(description)

    def evaluate(self, point):
        raise Exception("not implemented")

    def evaluate_grid(self, xs, ys, zs):
        raise Exception("not implemented")

class SvConstantScalarField(SvScalarField):
    def __init__(self, value):
        self.value = value
        self.__description__ = "Constant = {}".format(value)

    def evaluate(self, x, y, z):
        return self.value

    def evaluate_grid(self, xs, ys, zs):
        result = np.full_like(xs, self.value, dtype=np.float64)
        return result

class SvVectorFieldDecomposed(SvScalarField):
    def __init__(self, vfield, coords, axis):
        self.vfield = vfield
        self.coords = coords
        self.axis = axis
        self.__description__ = "{}.{}[{}]".format(vfield, coords, axis)

    def evaluate(self, x, y, z):
        result = self.vfield.evaluate(x, y, z)
        if self.coords == 'XYZ':
            return result[self.axis]
        elif self.coords == 'CYL':
            rho, phi, z = to_cylindrical(tuple(result), mode='radians')
            return [rho, phi, z][self.axis]
        else: # SPH
            rho, phi, theta = to_spherical(tuple(result), mode='radians')
            return [rho, phi, theta][self.axis]

    def evaluate_grid(self, xs, ys, zs):
        results = self.vfield.evaluate_grid(xs, ys, zs)
        if self.coords == 'XYZ':
            return results[self.axis]
        elif self.coords == 'CYL':
            vectors = np.stack(results).T
            vectors = np.apply_along_axis(lambda v: np.array(to_cylindrical(tuple(v), mode='radians')), 1, vectors)
            return vectors[:, self.axis]
        else: # SPH
            vectors = np.stack(results).T
            vectors = np.apply_along_axis(lambda v: np.array(to_spherical(tuple(v), mode='radians')), 1, vectors)
            return vectors[:, self.axis]

class SvScalarFieldLambda(SvScalarField):
    __description__ = "Formula"

    def __init__(self, function, variables, in_field):
        self.function = function
        self.variables = variables
        self.in_field = in_field

    def evaluate_grid(self, xs, ys, zs):
        if self.in_field is None:
            Vs = np.zeros(xs.shape[0])
        else:
            Vs = self.in_field.evaluate_grid(xs, ys, zs)
        return np.vectorize(self.function)(xs, ys, zs, Vs)

    def evaluate(self, x, y, z):
        if self.in_field is None:
            V = None
        else:
            V = self.in_field.evaluate(x, y, z)
        return self.function(x, y, z, V)

class SvScalarFieldPointDistance(SvScalarField):
    def __init__(self, center, metric='EUCLIDEAN', falloff=None):
        self.center = center
        self.falloff = falloff
        self.metric = metric
        self.__description__ = "Distance from {}".format(tuple(center))

    def evaluate_grid(self, xs, ys, zs):
        x0, y0, z0 = tuple(self.center)
        xs = xs - x0
        ys = ys - y0
        zs = zs - z0
        points = np.stack((xs, ys, zs))
        if self.metric == 'EUCLIDEAN':
            norms = np.linalg.norm(points, axis=0)
        elif self.metric == 'CHEBYSHEV':
            norms = np.max(np.abs(points), axis=0)
        elif self.metric == 'MANHATTAN':
            norms = np.sum(np.abs(points), axis=0)
        else:
            raise Exception('Unknown metric')
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

    def evaluate(self, x, y, z):
        point = np.array([x, y, z]) - self.center
        if self.metric == 'EUCLIDEAN':
            norm = np.linalg.norm(point)
        elif self.metric == 'CHEBYSHEV':
            norm = np.max(np.abs(point))
        elif self.metric == 'MANHATTAN':
            norm = np.sum(np.abs(point))
        else:
            raise Exception('Unknown metric')
        if self.falloff is not None:
            return self.falloff(np.array([norm]))[0]
        else:
            return norm

class SvScalarFieldBinOp(SvScalarField):
    def __init__(self, field1, field2, function):
        self.function = function
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        return self.function(self.field1.evaluate(x, y, z), self.field2.evaluate(x, y, z))

    def evaluate_grid(self, xs, ys, zs):
        func = lambda xs, ys, zs : self.function(self.field1.evaluate_grid(xs, ys, zs), self.field2.evaluate_grid(xs, ys, zs))
        return np.vectorize(func, signature="(m),(m),(m)->(m)")(xs, ys, zs)

class SvNegatedScalarField(SvScalarField):
    def __init__(self, field):
        self.field = field
        self.__description__ = "Negate({})".format(field)

    def evaluate(self, x, y, z):
        v = self.field.evaluate(x, y, z)
        return -x

    def evaluate_grid(self, xs, ys, zs):
        return (- self.field.evaluate_grid(xs, ys, zs))

class SvVectorFieldsScalarProduct(SvScalarField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "{} . {}".format(field1, field2)

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x, y, z)
        v2 = self.field2.evaluate(x, y, z)
        return np.dot(v1, v2)

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1)).T
        vectors2 = np.stack((vx2, vy2, vz2)).T
        result = np.vectorize(np.dot, signature="(3),(3)->()")(vectors1, vectors2)
        return result

class SvVectorFieldNorm(SvScalarField):
    def __init__(self, field):
        self.field = field
        self.__description__ = "Norm({})".format(field)

    def evaluate(self, x, y, z):
        v = self.field.evaluate(x, y, z)
        return np.linalg.norm(v)

    def evaluate_grid(self, xs, ys, zs):
        vx, vy, vz = self.field.evaluate_grid(xs, ys, zs)
        vectors = np.stack((vx, vy, vz)).T
        result = np.linalg.norm(vectors, axis=1)
        return result

class SvMergedScalarField(SvScalarField):
    def __init__(self, mode, fields):
        self.mode = mode
        self.fields = fields
        self.__description__ = "{}{}".format(mode, fields)

    def _minimal_diff(self, array, **kwargs):
        v1,v2 = np.partition(array, 1, **kwargs)[0:2]
        return abs(v1 - v2)

    def evaluate(self, x, y, z):
        values = np.array([field.evaluate(x, y, z) for field in self.fields])
        if self.mode == 'MIN':
            value = np.min(values)
        elif self.mode == 'MAX':
            value = np.max(values)
        elif self.mode == 'SUM':
            value = np.sum(values)
        elif self.mode == 'AVG':
            value = np.mean(values)
        elif self.mode == 'MINDIFF':
            value = self._minimal_diff(values)
        else:
            raise Exception("unsupported operation")
        return value

    def evaluate_grid(self, xs, ys, zs):
        values = np.array([field.evaluate_grid(xs, ys, zs) for field in self.fields])
        if self.mode == 'MIN':
            value = np.min(values, axis=0)
        elif self.mode == 'MAX':
            value = np.max(values, axis=0)
        elif self.mode == 'SUM':
            value = np.sum(values, axis=0)
        elif self.mode == 'AVG':
            value = np.mean(values, axis=0)
        elif self.mode == 'MINDIFF':
            value = self._minimal_diff(values, axis=0)
        else:
            raise Exception("unsupported operation")
        return value

class SvKdtScalarField(SvScalarField):
    __description__ = "KDT"

    def __init__(self, vertices=None, kdt=None, falloff=None):
        self.falloff = falloff
        if kdt is not None:
            self.kdt = kdt
        elif vertices is not None:
            self.kdt = kdtree.KDTree(len(vertices))
            for i, v in enumerate(vertices):
                self.kdt.insert(v, i)
            self.kdt.balance()
        else:
            raise Exception("Either kdt or vertices must be provided")

    def evaluate(self, x, y, z):
        nearest, i, distance = self.kdt.find((x, y, z))
        if self.falloff is not None:
            value = self.falloff(np.array([distance]))[0]
            return value
        else:
            return distance

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, i, distance = self.kdt.find(v)
            return distance

        points = np.stack((xs, ys, zs)).T
        norms = np.vectorize(find, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvLineAttractorScalarField(SvScalarField):
    __description__ = "Line Attractor"

    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        dv = to_center - projection
        return np.linalg.norm(dv)

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            dv = to_center - projection
            return np.linalg.norm(dv)

        points = np.stack((xs, ys, zs)).T
        norms = np.vectorize(func, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvPlaneAttractorScalarField(SvScalarField):
    __description__ = "Plane Attractor"

    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        return np.linalg.norm(projection)

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            return np.linalg.norm(projection)

        points = np.stack((xs, ys, zs)).T
        norms = np.vectorize(func, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvBvhAttractorScalarField(SvScalarField):
    __description__ = "BVH Attractor"

    def __init__(self, bvh=None, verts=None, faces=None, falloff=None, signed=False):
        self.falloff = falloff
        self.signed = signed
        if bvh is not None:
            self.bvh = bvh
        elif verts is not None and faces is not None:
            self.bvh = bvhtree.BVHTree.FromPolygons(verts, faces)
        else:
            raise Exception("Either bvh or verts and faces must be provided!")

    def evaluate(self, x, y, z):
        nearest, normal, idx, distance = self.bvh.find_nearest((x,y,z))
        if self.signed:
            sign = (Vector((x,y,z)) - nearest).dot(normal)
            sign = copysign(1, sign)
        else:
            sign = 1
        return sign * distance

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, normal, idx, distance = self.bvh.find_nearest(v)
            if nearest is None:
                raise Exception("No nearest point on mesh found for vertex %s" % v)
            if self.signed:
                sign = (v - nearest).dot(normal)
                sign = copysign(1, sign)
            else:
                sign = 1
            return sign * distance

        points = np.stack((xs, ys, zs)).T
        norms = np.vectorize(find, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvVectorScalarFieldComposition(SvScalarField):
    __description__ = "Composition"

    def __init__(self, vfield, sfield):
        self.sfield = sfield
        self.vfield = vfield

    def evaluate(self, x, y, z):
        x1, y1, z1 = self.vfield.evaluate(x,y,z)
        v2 = self.sfield.evaluate(x1,y1,z1)
        return v2
    
    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.vfield.evaluate_grid(xs, ys, zs)
        return self.sfield.evaluate_grid(vx1, vy1, vz1)

class SvVectorFieldDivergence(SvScalarField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Div({})".format(field)

    def evaluate(self, x, y, z):
        step = self.step
        xs_dx_plus, _, _ = self.field.evaluate(x+step,y,z)
        xs_dx_minus, _, _ = self.field.evaluate(x-step,y,z)
        _, ys_dy_plus, _ = self.field.evaluate(x, y+step, z)
        _, ys_dy_minus, _ = self.field.evaluate(x, y-step, z)
        _, _, zs_dz_plus = self.field.evaluate(x, y, z+step)
        _, _, zs_dz_minus = self.field.evaluate(x, y, z-step)

        dx_dx = (xs_dx_plus - xs_dx_minus) / (2*step)
        dy_dy = (ys_dy_plus - ys_dy_minus) / (2*step)
        dz_dz = (zs_dz_plus - zs_dz_minus) / (2*step)

        return dx_dx + dy_dy + dz_dz
    
    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        xs_dx_plus, _, _ = self.field.evaluate_grid(xs+step, ys,zs)
        xs_dx_minus, _, _ = self.field.evaluate_grid(xs-step,ys,zs)
        _, ys_dy_plus, _ = self.field.evaluate_grid(xs, ys+step, zs)
        _, ys_dy_minus, _ = self.field.evaluate_grid(xs, ys-step, zs)
        _, _, zs_dz_plus = self.field.evaluate_grid(xs, ys, zs+step)
        _, _, zs_dz_minus = self.field.evaluate_grid(xs, ys, zs-step)

        dx_dx = (xs_dx_plus - xs_dx_minus) / (2*step)
        dy_dy = (ys_dy_plus - ys_dy_minus) / (2*step)
        dz_dz = (zs_dz_plus - zs_dz_minus) / (2*step)

        return dx_dx + dy_dy + dz_dz

class SvScalarFieldLaplacian(SvScalarField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Laplace({})".format(field)

    def evaluate(self, x, y, z):
        step = self.step
        v_dx_plus = self.field.evaluate(x+step,y,z)
        v_dx_minus = self.field.evaluate(x-step,y,z)
        v_dy_plus = self.field.evaluate(x, y+step, z)
        v_dy_minus = self.field.evaluate(x, y-step, z)
        v_dz_plus = self.field.evaluate(x, y, z+step)
        v_dz_minus = self.field.evaluate(x, y, z-step)
        v0 = self.field.evaluate(x, y, z)

        sides = v_dx_plus + v_dx_minus + v_dy_plus + v_dy_minus + v_dz_plus + v_dz_minus
        result = (sides - 6*v0) / (8 * step * step * step)
        return result
    
    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        v_dx_plus = self.field.evaluate_grid(xs+step, ys,zs)
        v_dx_minus = self.field.evaluate_grid(xs-step,ys,zs)
        v_dy_plus = self.field.evaluate_grid(xs, ys+step, zs)
        v_dy_minus = self.field.evaluate_grid(xs, ys-step, zs)
        v_dz_plus = self.field.evaluate_grid(xs, ys, zs+step)
        v_dz_minus = self.field.evaluate_grid(xs, ys, zs-step)
        v0 = self.field.evaluate_grid(xs, ys, zs)

        sides = v_dx_plus + v_dx_minus + v_dy_plus + v_dy_minus + v_dz_plus + v_dz_minus
        result = (sides - 6*v0) / (8 * step * step * step)
        return result

class SvVoronoiScalarField(SvScalarField):
    __description__ = "Voronoi"

    def __init__(self, vertices):
        self.kdt = kdtree.KDTree(len(vertices))
        for i, v in enumerate(vertices):
            self.kdt.insert(v, i)
        self.kdt.balance()

    def evaluate(self, x, y, z):
        vs = self.kdt.find_n((x,y,z), 2)
        if len(vs) != 2:
            raise Exception("Unexpected kdt result at (%s,%s,%s): %s" % (x, y, z, vs))
        t1, t2 = vs
        distance1 = t1[2]
        distance2 = t2[2]
        return abs(distance1 - distance2)

    def evaluate_grid(self, xs, ys, zs):
        return np.vectorize(self.evaluate, signature='(),(),()->()')(xs,ys,zs)

