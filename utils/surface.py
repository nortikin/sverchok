# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi, cos, sin, atan, sqrt
from collections import defaultdict

from mathutils import Matrix, Vector

from sverchok.utils.logging import info, exception
from sverchok.utils.math import from_spherical
from sverchok.utils.geom import LineEquation

def rotate_vector_around_vector_np(v, k, theta):
    """
    Rotate vector v around vector k by theta angle.
    input: v, k - np.array of shape (3,); theta - float, in radians.
    output: np.array.

    This implements Rodrigues' formula: https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
    """
    if not isinstance(v, np.ndarray):
        v = np.array(v)
    if not isinstance(k, np.ndarray):
        k = np.array(k)
    if k.ndim == 1:
        k = k[np.newaxis]
    k = k / np.linalg.norm(k, axis=1)

    if isinstance(theta, np.ndarray):
        ct, st = np.cos(theta)[np.newaxis].T, np.sin(theta)[np.newaxis].T
    else:
        ct, st = cos(theta), sin(theta)

    s1 = ct * v
    s2 = st * np.cross(k, v)
    p1 = 1.0 - ct
    p2 = np.apply_along_axis(lambda v : k.dot(v), 1, v)
    s3 = p1 * p2 * k
    return s1 + s2 + s3

class SvExSurface(object):
    def __repr__(self):
        if hasattr(self, '__description__'):
            description = self.__description__
        else:
            description = self.__class__.__name__
        return "<{} surface>".format(description)

    def evaluate(self, u, v):
        raise Exception("not implemented!")

    def evaluate_array(self, us, vs):
        raise Exception("not implemented!")

    def normal(self, u, v):
        h = self.normal_delta
        p = self.evaluate(u, v)
        p_u = self.evaluate(u+h, v)
        p_v = self.evaluate(u, v+h)
        du = (p_u - p) / h
        dv = (p_v - p) / h
        normal = np.cross(du, dv)
        n = np.linalg.norm(normal)
        normal = normal / n
        return normal

    def normal_array(self, us, vs):
        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + self.normal_delta, vs)
        v_plus = self.evaluate_array(us, vs + self.normal_delta)
        du = u_plus - surf_vertices
        dv = v_plus - surf_vertices
        #self.info("Du: %s", du)
        #self.info("Dv: %s", dv)
        normal = np.cross(du, dv)
        norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
        #if norm != 0:
        normal = normal / norm
        #self.info("Normals: %s", normal)
        return normal

    def get_coord_mode(self):
        return 'UV'

    @property
    def has_input_matrix(self):
        return False

    def get_input_matrix(self):
        return None

    def get_input_orientation(self):
        return None

    def get_u_min(self):
        return 0.0

    def get_u_max(self):
        return 1.0

    def get_v_min(self):
        return 0.0

    def get_v_max(self):
        return 1.0

    @property
    def u_size(self):
        m,M = self.get_u_min(), self.get_u_max()
        return M - m

    @property
    def v_size(self):
        m,M = self.get_v_min(), self.get_v_max()
        return M - m

class SvExSurfaceSubdomain(SvExSurface):
    def __init__(self, surface, u_bounds, v_bounds):
        self.surface = surface
        self.u_bounds = u_bounds
        self.v_bounds = v_bounds
        if hasattr(surface, "normal_delta"):
            self.normal_delta = surface.normal_delta
        else:
            self.normal_delta = 0.001
        self.__description__ = "{}[{} .. {}][{} .. {}]".format(surface, u_bounds[0], u_bounds[1], v_bounds[0], v_bounds[1])

    def evaluate(self, u, v):
        return self.surface.evaluate(u, v)

    def evaluate_array(self, us, vs):
        return self.surface.evaluate_array(us, vs)

    def normal(self, u, v):
        return self.surface.normal(u, v)

    def normal_array(self, us, vs):
        return self.surface.normal_array(us, vs)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

class SvExPlane(SvExSurface):
    __description__ = "Plane"
    
    def __init__(self, point, vector1, vector2):
        self.point = point
        self.vector1 = vector1
        self.vector2 = vector2
        self._normal = np.cross(vector1, vector2)
        n = np.linalg.norm(self._normal)
        self._normal = self._normal / n
        self.u_bounds = (0.0, 1.0)
        self.v_bounds = (0.0, 1.0)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        return self.point + u*self.vector1 + v*self.vector2

    def evaluate_array(self, us, vs):
        us = us[np.newaxis].T
        vs = vs[np.newaxis].T
        return self.point + us*self.vector1 + vs*self.vector2

    def normal(self, u, v):
        return self._normal

    def normal_array(self, us, vs):
        normal = self.normal
        n = np.linalg.norm(normal)
        normal = normal / n
        return np.tile(normal, len(us))

class SvExEquirectSphere(SvExSurface):
    __description__ = "Equirectangular Sphere"

    def __init__(self, center, radius, theta1):
        self.center = center
        self.radius = radius
        self.theta1 = theta1
        self.u_bounds = (0, radius * 2*pi * cos(theta1))
        self.v_bounds = (-radius * theta1, radius * (pi - theta1))

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u / (rho * cos(self.theta1))
        theta = v / rho + self.theta1
        x, y, z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z]) + self.center

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us / (rho * cos(self.theta1))
        thetas = vs / rho + self.theta1
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def normal(self, u, v):
        rho = self.radius
        phi = u / (rho * np.cos(self.theta1))
        theta = v / rho + self.theta1
        x, y, z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us / (rho * cos(self.theta1))
        thetas = vs / rho + self.theta1
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

class SvExLambertSphere(SvExSurface):
    __description__ = "Lambert Sphere"

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.u_bounds = (0, 2*pi)
        self.v_bounds = (-1.0, 1.0)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u
        theta = np.arcsin(v)
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z]) + self.center

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = np.arcsin(vs) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def normal(self, u, v):
        rho = self.radius
        phi = u
        theta = np.arcsin(v) + pi/2
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = np.arcsin(vs) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

class SvExGallSphere(SvExSurface):
    __description__ = "Gall Sphere"

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.u_bounds = (0, radius * 2*pi / sqrt(2))
        self.v_bounds = (- radius * (1 + sqrt(2)/2), radius * (1 + sqrt(2)/2))

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u * sqrt(2) / rho
        theta = 2 * atan(v / (rho * (1 + sqrt(2)/2))) + pi/2
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z]) + self.center

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us * sqrt(2) / rho
        thetas = 2 * np.arctan(vs / (rho * (1 + sqrt(2)/2))) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def normal(self, u, v):
        rho = self.radius
        phi = u * sqrt(2) / rho
        theta = 2 * atan(v / (rho * (1 + sqrt(2)/2))) + pi/2
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us * sqrt(2) / rho
        thetas = 2 * np.arctan(vs / (rho * (1 + sqrt(2)/2))) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

class SvExDefaultSphere(SvExSurface):
    __description__ = "Default Sphere"

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.u_bounds = (0, 2*pi)
        self.v_bounds = (0, pi)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u
        theta = v
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z]) + self.center

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = vs
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def normal(self, u, v):
        rho = self.radius
        phi = u
        theta = v
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = vs
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

class SvExLambdaSurface(SvExSurface):
    __description__ = "Formula"

    def __init__(self, function):
        self.function = function
        self.u_bounds = (0.0, 1.0)
        self.v_bounds = (0.0, 1.0)
        self.normal_delta = 0.001

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        return self.function(u, v)

    def evaluate_array(self, us, vs):
        return np.vectorize(self.function, signature='(),()->(3)')(us, vs)

    def normal(self, u, v):
        return self.normal_array(np.array([u]), np.array([v]))[0]

    def normal_array(self, us, vs):
        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + self.normal_delta, vs)
        v_plus = self.evaluate_array(us, vs + self.normal_delta)
        du = u_plus - surf_vertices
        dv = v_plus - surf_vertices
        #self.info("Du: %s", du)
        #self.info("Dv: %s", dv)
        normal = np.cross(du, dv)
        norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
        #if norm != 0:
        normal = normal / norm
        #self.info("Normals: %s", normal)
        return normal

class SvExInterpolatingSurface(SvExSurface):
    __description__ = "Interpolating"

    def __init__(self, u_bounds, v_bounds, u_spline_constructor, v_splines):
        self.v_splines = v_splines
        self.u_spline_constructor = u_spline_constructor
        self.u_bounds = u_bounds
        self.v_bounds = v_bounds

        # Caches
        # v -> Spline
        self._u_splines = {}
        # (u,v) -> vertex
        self._eval_cache = {}
        # (u,v) -> normal
        self._normal_cache = {}

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]
        #v = 0.0
        #verts = [spline.evaluate(v) for spline in self.v_splines]
        #return self.get_u_spline(v, verts).u_size

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]
        #return self.v_splines[0].v_size

    def get_u_spline(self, v, vertices):
        """Get a spline along U direction for specified value of V coordinate"""
        spline = self._u_splines.get(v, None)
        if spline is not None:
            return spline
        else:
            spline = self.u_spline_constructor(vertices)
            self._u_splines[v] = spline
            return spline

    def _evaluate(self, u, v):
        spline_vertices = []
        for spline in self.v_splines:
            v_min, v_max = spline.get_u_bounds()
            vx = (v_max - v_min) * v + v_min
            point = spline.evaluate(vx)
            spline_vertices.append(point)
        #spline_vertices = [spline.evaluate(v) for spline in self.v_splines]
        u_spline = self.get_u_spline(v, spline_vertices)
        result = u_spline.evaluate(u)
        return result

    def evaluate(self, u, v):
        result = self._eval_cache.get((u,v), None)
        if result is not None:
            return result
        else:
            result = self._evaluate(u, v)
            self._eval_cache[(u,v)] = result
            return result

    def evaluate_array(self, us, vs):
        # FIXME: To be optimized!
        normals = [self._evaluate(u, v) for u,v in zip(us, vs)]
        return np.array(normals)

#     def evaluate_array(self, us, vs):
#         result = np.empty((len(us), 3))
#         v_to_u = defaultdict(list)
#         v_to_i = defaultdict(list)
#         for i, (u, v) in enumerate(zip(us, vs)):
#             v_to_u[v].append(u)
#             v_to_i[v].append(i)
#         for v, us_by_v in v_to_u.items():
#             is_by_v = v_to_i[v]
#             spline_vertices = [spline.evaluate(v) for spline in self.v_splines]
#             u_spline = self.get_u_spline(v, spline_vertices)
#             points = u_spline.evaluate_array(np.array(us_by_v))
#             np.put(result, is_by_v, points)
#         return result

    def _normal(self, u, v):
        h = 0.001
        point = self.evaluate(u, v)
        # we know this exists because it was filled in evaluate()
        u_spline = self._u_splines[v]
        u_tangent = u_spline.tangent(u)
        point_v = self.evaluate(u, v+h)
        dv = (point_v - point)/h
        n = np.cross(u_tangent, dv)
        norm = np.linalg.norm(n)
        if norm != 0:
            n = n / norm
        return n

    def normal(self, u, v):
        result = self._normal_cache.get((u,v), None)
        if result is not None:
            return result
        else:
            result = self._normal(u, v)
            self._normal_cache[(u,v)] = result
            return result

    def normal_array(self, us, vs):
        # FIXME: To be optimized!
        normals = [self._normal(u, v) for u,v in zip(us, vs)]
        return np.array(normals)

class SvExDeformedByFieldSurface(SvExSurface):
    def __init__(self, surface, field, coefficient=1.0):
        self.surface = surface
        self.field = field
        self.coefficient = coefficient
        self.normal_delta = 0.001
        self.__description__ = "{}({})".format(field, surface)

    def get_coord_mode(self):
        return self.surface.get_coord_mode()

    def get_u_min(self):
        return self.surface.get_u_min()

    def get_u_max(self):
        return self.surface.get_u_max()

    def get_v_min(self):
        return self.surface.get_v_min()

    def get_v_max(self):
        return self.surface.get_v_max()

    @property
    def u_size(self):
        return self.surface.u_size

    @property
    def v_size(self):
        return self.surface.v_size

    @property
    def has_input_matrix(self):
        return self.surface.has_input_matrix

    def get_input_matrix(self):
        return self.surface.get_input_matrix()

    def evaluate(self, u, v):
        p = self.surface.evaluate(u, v)
        vec = self.field.evaluate(p)
        return p + self.coefficient * vec

    def evaluate_array(self, us, vs):
        ps = self.surface.evaluate_array(us, vs)
        xs, ys, zs = ps[:,0], ps[:,1], ps[:,2]
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        vecs = np.stack((vxs, vys, vzs)).T
        return ps + self.coefficient * vecs

    def normal(self, u, v):
        h = self.normal_delta
        p = self.evaluate(u, v)
        p_u = self.evaluate(u+h, v)
        p_v = self.evaluate(u, v+h)
        du = (p_u - p) / h
        dv = (p_v - p) / h
        normal = np.cross(du, dv)
        n = np.linalg.norm(normal)
        normal = normal / n
        return normal

    def normal_array(self, us, vs):
        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + self.normal_delta, vs)
        v_plus = self.evaluate_array(us, vs + self.normal_delta)
        du = u_plus - surf_vertices
        dv = v_plus - surf_vertices
        #self.info("Du: %s", du)
        #self.info("Dv: %s", dv)
        normal = np.cross(du, dv)
        norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
        #if norm != 0:
        normal = normal / norm
        #self.info("Normals: %s", normal)
        return normal

class SvExRevolutionSurface(SvExSurface):
    __description__ = "Revolution"

    def __init__(self, curve, point, direction):
        self.curve = curve
        self.point = point
        self.direction = direction
        self.normal_delta = 0.001
        self.v_bounds = (0.0, 2*pi)

    def evaluate(self, u, v):
        point_on_curve = self.curve.evaluate(u)
        dv = point_on_curve - self.point
        return rotate_vector_around_vector_np(dv, self.direction, v)

    def evaluate_array(self, us, vs):
        points_on_curve = self.curve.evaluate_array(us)
        dvs = points_on_curve - self.point
        return rotate_vector_around_vector_np(dvs, self.direction, vs)

    def get_u_min(self):
        return self.curve.get_u_bounds()[0]

    def get_u_max(self):
        return self.curve.get_u_bounds()[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

class SvExExtrudeCurveVectorSurface(SvExSurface):
    def __init__(self, curve, vector):
        self.curve = curve
        self.vector = vector
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(curve)

    def evaluate(self, u, v):
        point_on_curve = self.curve.evaluate(u)
        return point_on_curve + v * self.vector

    def evaluate_array(self, us, vs):
        points_on_curve = self.curve.evaluate_array(us)
        return points_on_curve + vs[np.newaxis].T * self.vector

    def get_u_min(self):
        return self.curve.get_u_bounds()[0]

    def get_u_max(self):
        return self.curve.get_u_bounds()[1]

    def get_v_min(self):
        return 0.0

    def get_v_max(self):
        return 1.0

    @property
    def u_size(self):
        m,M = self.curve.get_u_bounds()
        return M - m

    @property
    def v_size(self):
        return 1.0

class SvExExtrudeCurvePointSurface(SvExSurface):
    def __init__(self, curve, point):
        self.curve = curve
        self.point = point
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(curve)

    def evaluate(self, u, v):
        point_on_curve = self.curve.evaluate(u)
        return (1.0 - v) * point_on_curve + v * self.point

    def evaluate_array(self, us, vs):
        points_on_curve = self.curve.evaluate_array(us)
        vs = vs[np.newaxis].T
        return (1.0 - vs) * points_on_curve + vs * self.point

    def get_u_min(self):
        return self.curve.get_u_bounds()[0]

    def get_u_max(self):
        return self.curve.get_u_bounds()[1]

    def get_v_min(self):
        return 0.0

    def get_v_max(self):
        return 1.0

    @property
    def u_size(self):
        m,M = self.curve.get_u_bounds()
        return M - m

    @property
    def v_size(self):
        return 1.0

class SvExExtrudeCurveCurveSurface(SvExSurface):
    def __init__(self, u_curve, v_curve):
        self.u_curve = u_curve
        self.v_curve = v_curve
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(u_curve)

    def evaluate(self, u, v):
        u_point = self.u_curve.evaluate(u)
        v_min, v_max = self.v_curve.get_u_bounds()
        v0 = self.v_curve.evaluate(v_min)
        v_point = self.v_curve.evaluate(v)
        return u_point + (v_point - v0)

    def evaluate_array(self, us, vs):
        u_points = self.u_curve.evaluate_array(us)
        v_min, v_max = self.v_curve.get_u_bounds()
        v0 = self.v_curve.evaluate(v_min)
        v_points = self.v_curve.evaluate_array(vs)
        return u_points + (v_points - v0)

    def get_u_min(self):
        return self.u_curve.get_u_bounds()[0]

    def get_u_max(self):
        return self.u_curve.get_u_bounds()[1]

    def get_v_min(self):
        return self.v_curve.get_u_bounds()[0]

    def get_v_max(self):
        return self.v_curve.get_u_bounds()[1]

    @property
    def u_size(self):
        m,M = self.u_curve.get_u_bounds()
        return M - m

    @property
    def v_size(self):
        m,M = self.v_curve.get_u_bounds()
        return M - m

class SvExExtrudeCurveFrenetSurface(SvExSurface):
    def __init__(self, profile, extrusion):
        self.profile = profile
        self.extrusion = extrusion
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(profile)

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        profile_points = self.profile.evaluate_array(us)
        u_min, u_max = self.profile.get_u_bounds()
        v_min, v_max = self.extrusion.get_u_bounds()
        profile_start = self.extrusion.evaluate(u_min)
        profile_vectors = profile_points # - profile_start
        profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.extrusion.evaluate(v_min)
        extrusion_points = self.extrusion.evaluate_array(vs)
        extrusion_vectors = extrusion_points - extrusion_start
        frenet, _ , _ = self.extrusion.frame_array(vs)
        profile_vectors = (frenet @ profile_vectors)[:,:,0]
        return extrusion_vectors + profile_vectors

    def get_u_min(self):
        return self.profile.get_u_bounds()[0]

    def get_u_max(self):
        return self.profile.get_u_bounds()[1]

    def get_v_min(self):
        return self.extrusion.get_u_bounds()[0]

    def get_v_max(self):
        return self.extrusion.get_u_bounds()[1]

    @property
    def u_size(self):
        m,M = self.profile.get_u_bounds()
        return M - m

    @property
    def v_size(self):
        m,M = self.extrusion.get_u_bounds()
        return M - m

class SvExExtrudeCurveZeroTwistSurface(SvExSurface):
    def __init__(self, profile, extrusion, resolution):
        self.profile = profile
        self.extrusion = extrusion
        self.normal_delta = 0.001
        self.extrusion.pre_calc_torsion_integral(resolution)
        self.__description__ = "Extrusion of {}".format(profile)

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        profile_points = self.profile.evaluate_array(us)
        u_min, u_max = self.profile.get_u_bounds()
        v_min, v_max = self.extrusion.get_u_bounds()
        profile_start = self.extrusion.evaluate(u_min)
        profile_vectors = profile_points # - profile_start
        profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.extrusion.evaluate(v_min)
        extrusion_points = self.extrusion.evaluate_array(vs)
        extrusion_vectors = extrusion_points - extrusion_start

        frenet, _ , _ = self.extrusion.frame_array(vs)

        angles = - self.extrusion.torsion_integral(vs)
        n = len(us)
        zeros = np.zeros((n,))
        ones = np.ones((n,))
        row1 = np.stack((np.cos(angles), np.sin(angles), zeros)).T # (n, 3)
        row2 = np.stack((-np.sin(angles), np.cos(angles), zeros)).T # (n, 3)
        row3 = np.stack((zeros, zeros, ones)).T # (n, 3)
        rotation_matrices = np.dstack((row1, row2, row3))

        profile_vectors = (frenet @ rotation_matrices @ profile_vectors)[:,:,0]
        return extrusion_vectors + profile_vectors

    def get_u_min(self):
        return self.profile.get_u_bounds()[0]

    def get_u_max(self):
        return self.profile.get_u_bounds()[1]

    def get_v_min(self):
        return self.extrusion.get_u_bounds()[0]

    def get_v_max(self):
        return self.extrusion.get_u_bounds()[1]

class SvExCurveLerpSurface(SvExSurface):
    __description__ = "Lerp"

    def __init__(self, curve1, curve2):
        self.curve1 = curve1
        self.curve2 = curve2
        self.normal_delta = 0.001
        self.v_bounds = (0.0, 1.0)
        self.u_bounds = (0.0, 1.0)
        self.c1_min, self.c1_max = curve1.get_u_bounds()
        self.c2_min, self.c2_max = curve2.get_u_bounds()

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        us1 = (self.c1_max - self.c1_min) * us + self.c1_min
        us2 = (self.c2_max - self.c2_min) * us + self.c2_min
        c1_points = self.curve1.evaluate_array(us1)
        c2_points = self.curve2.evaluate_array(us2)
        vs = vs[np.newaxis].T
        points = (1.0 - vs)*c1_points + vs*c2_points
        return points

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

class SvExSurfaceLerpSurface(SvExSurface):
    __description__ = "Lerp"

    def __init__(self, surface1, surface2, coefficient):
        self.surface1 = surface1
        self.surface2 = surface2
        self.coefficient = coefficient
        self.normal_delta = 0.001
        self.v_bounds = (0.0, 1.0)
        self.u_bounds = (0.0, 1.0)
        self.s1_u_min, self.s1_u_max = surface1.get_u_min(), surface1.get_u_max()
        self.s1_v_min, self.s1_v_max = surface1.get_v_min(), surface1.get_v_max()
        self.s2_u_min, self.s2_u_max = surface2.get_u_min(), surface2.get_u_max()
        self.s2_v_min, self.s2_v_max = surface2.get_v_min(), surface2.get_v_max()

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]
    
    def evaluate_array(self, us, vs):
        us1 = (self.s1_u_max - self.s1_u_min) * us + self.s1_u_min
        us2 = (self.s2_u_max - self.s2_u_min) * us + self.s2_u_min
        vs1 = (self.s1_v_max - self.s1_v_min) * vs + self.s1_v_min
        vs2 = (self.s2_v_max - self.s2_v_min) * vs + self.s2_v_min
        s1_points = self.surface1.evaluate_array(us1, vs1)
        s2_points = self.surface2.evaluate_array(us2, vs2)
        k = self.coefficient
        points = (1.0 - k) * s1_points + k * s2_points
        return points

class SvExTaperSweepSurface(SvExSurface):
    __description__ = "Taper & Sweep"

    def __init__(self, profile, taper, point, direction):
        self.profile = profile
        self.taper = taper
        self.direction = direction
        self.point = point
        self.line = LineEquation.from_direction_and_point(direction, point)
        self.normal_delta = 0.001

    def get_u_min(self):
        return self.profile.get_u_bounds()[0]

    def get_u_max(self):
        return self.profile.get_u_bounds()[1]

    def get_v_min(self):
        return self.taper.get_u_bounds()[0]

    def get_v_max(self):
        return self.taper.get_u_bounds()[1]

    def evaluate(self, u, v):
        taper_point = self.taper.evaluate(v)
        taper_projection = np.array( self.line.projection_of_point(taper_point) )
        scale = np.linalg.norm(taper_projection - taper_point)
        profile_point = self.profile.evaluate(u)
        return profile_point * scale + taper_projection

    def evaluate_array(self, us, vs):
        taper_points = self.taper.evaluate_array(vs)
        taper_projections = self.line.projection_of_points(taper_points)
        scale = np.linalg.norm(taper_projections - taper_points, axis=1, keepdims=True)
        profile_points = self.profile.evaluate_array(us)
        return profile_points * scale + taper_projections

