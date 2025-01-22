# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import copysign, pi
import numpy as np

from mathutils import Vector
from mathutils import bvhtree
from sverchok.utils.geom import LineEquation, CircleEquation3D
from sverchok.utils.kdtree import SvKdTree
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.vector import SvVectorField

class SvKdtVectorField(SvVectorField):

    def __init__(self, vertices=None, kdt=None, falloff=None, negate=False, power=2):
        self.falloff = falloff
        self.negate = negate
        if kdt is not None:
            self.kdt = kdt
        elif vertices is not None:
            self.kdt = SvKdTree.new(SvKdTree.best_available_implementation(), vertices, power=power)
        else:
            raise Exception("Either kdt or vertices must be provided")
        self.__description__ = "KDT Attractor"

    def evaluate(self, x, y, z):
        nearest, i, distance = self.kdt.query(np.array([x, y, z]))
        vector = nearest - np.array([x, y, z])
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
        points = np.stack((xs, ys, zs)).T
        locs, idxs, distances = self.kdt.query_array(points)
        vectors = locs - points
        if self.negate:
            vectors = - vectors
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
    def __init__(self, center, metric='EUCLIDEAN', falloff=None, power=2):
        self.center = center
        self.falloff = falloff
        self.metric = metric
        self.power = power
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
        elif self.metric == 'CUSTOM':
            norms = np.linalg.norm(vectors, axis=0, ord=self.power)
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
        elif self.metric == 'CUSTOM':
            norm = np.linalg.norm(point, ord=self.power)
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

class SvScalarFieldPointDistance(SvScalarField):
    def __init__(self, center, metric='EUCLIDEAN', falloff=None, power=2):
        self.center = center
        self.falloff = falloff
        self.metric = metric
        self.power = power
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
        elif self.metric == 'CUSTOM':
            norms = np.linalg.norm(points, axis=0, ord=self.power)
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
        elif self.metric == 'CUSTOM':
            norm = np.linalg.norm(point, ord=self.power)
        else:
            raise Exception('Unknown metric')
        if self.falloff is not None:
            return self.falloff(np.array([norm]))[0]
        else:
            return norm

class SvKdtScalarField(SvScalarField):
    __description__ = "KDT"

    def __init__(self, vertices=None, kdt=None, falloff=None, power=2):
        self.falloff = falloff
        if kdt is not None:
            self.kdt = kdt
        elif vertices is not None:
            self.kdt = SvKdTree.new(SvKdTree.best_available_implementation(), vertices, power=power)
        else:
            raise Exception("Either kdt or vertices must be provided")

    def evaluate(self, x, y, z):
        nearest, i, distance = self.kdt.query(np.array([x,y,z]))
        if self.falloff is not None:
            value = self.falloff(np.array([distance]))[0]
            return value
        else:
            return distance

    def evaluate_grid(self, xs, ys, zs):
        points = np.stack((xs, ys, zs)).T
        locs, idxs, distances = self.kdt.query_array(points)
        if self.falloff is not None:
            result = self.falloff(distances)
            return result
        else:
            return distances

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
        points = np.stack((xs, ys, zs)).T
        to_center = self.center - points
        dot = (to_center * direction).sum(axis=1)
        projections = (dot * direction[np.newaxis].T / direction2).T
        vectors = to_center - projections
        norms = np.linalg.norm(vectors, axis=1)

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

class SvCircleAttractorScalarField(SvScalarField):
    __description__ = "Circle Attractor"

    def __init__(self, center, radius, normal, falloff=None):
        self.circle = CircleEquation3D.from_center_radius_normal(center, radius, normal)
        self.falloff = falloff

    def evaluate(self, x, y, z):
        v = np.array([x,y,z])
        projection = self.circle.get_projections([v])[0]
        distance = np.linalg.norm(v - projection)
        if self.fallof is not None:
            return self.falloff(np.array([distance]))[0]
        else:
            return distance

    def evaluate_grid(self, xs, ys, zs):
        vs = np.stack((xs, ys, zs)).T
        projections = self.circle.get_projections(vs)
        distances = np.linalg.norm(vs - projections, axis=1)
        if self.falloff is not None:
            return self.falloff(distances)
        else:
            return distances

class SvBvhAttractorScalarField(SvScalarField):
    __description__ = "BVH Attractor (faces)"

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
        value = sign * distance
        if self.falloff is None:
            return value
        else:
            return self.falloff(np.array([value]))[0]

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

class SvBvhEdgesAttractorScalarField(SvScalarField):
    __description__ = "BVH Attractor (edges)"

    def __init__(self, verts, edges, falloff=None):
        self.verts = verts
        self.edges = edges
        self.falloff = falloff
        self.bvh = self._make_bvh(verts, edges)

    def _make_bvh(self, verts, edges):
        faces = [(i1, i2, i1) for i1, i2 in edges]
        return bvhtree.BVHTree.FromPolygons(verts, faces)

    def evaluate(self, x, y, z):
        nearest, normal, idx, distance = self.bvh.find_nearest((x,y,z))
        if self.falloff is None:
            return distance
        else:
            return self.falloff(np.array([distance]))[0]

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, normal, idx, distance = self.bvh.find_nearest(v)
            return distance

        points = np.stack((xs, ys, zs)).T
        norms = np.vectorize(find, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvEdgeAttractorScalarField(SvScalarField):
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
        else:
            distance = LineEquation.from_two_points(self.v1, self.v2).distance_to_point(v)
        if self.falloff is not None:
            value = self.falloff(np.array([distance]))[0]
            return value
        else:
            return distance
    
    def evaluate_grid(self, xs, ys, zs):
        n = len(xs)
        vs = np.stack((xs, ys, zs)).T
        v1 = np.array(self.v1)
        v2 = np.array(self.v2)    
        dv1 = vs - v1
        dv2 = vs - v2
        edge = v2 - v1
        dot1 = (dv1 * edge).sum(axis=1)
        dot2 = -(dv2 * edge).sum(axis=1)
        v1_is_nearest = (dot1 < 0)
        v2_is_nearest = (dot2 < 0)
        at_edge = np.logical_not(np.logical_or(v1_is_nearest, v2_is_nearest))

        distances = np.empty((n,))
        distances[v1_is_nearest] = np.linalg.norm(dv1[v1_is_nearest], axis=1)
        distances[v2_is_nearest] = np.linalg.norm(dv2[v2_is_nearest], axis=1)
        distances[at_edge] = LineEquation.from_two_points(self.v1, self.v2).distance_to_points(vs[at_edge])

        if self.falloff is not None:
            distances = self.falloff(distances)
            return distances
        else:
            return distances

