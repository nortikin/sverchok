# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi, cos, sin
from collections import defaultdict

from mathutils import Matrix, Vector

from sverchok.utils.math import (
        ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL,
        np_dot
    )
from sverchok.utils.geom import (
        LineEquation, CircleEquation3D, PlaneEquation,
        rotate_vector_around_vector, rotate_vector_around_vector_np,
        autorotate_householder, autorotate_track, autorotate_diff,
        center, linear_approximation
    )
from sverchok.utils.curve.core import SvFlipCurve, UnsupportedCurveTypeException
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import (
            SvNormalTrack, SvCurveOnSurfaceCurvaturesCalculator,
            MathutilsRotationCalculator, DifferentialRotationCalculator,
            reparametrize_curve,
            SvCurveOnSurface
        )
from sverchok.utils.surface.core import SvSurface, UnsupportedSurfaceTypeException
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.data import *
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions, SvNurbsMaths
from sverchok.utils.logging import info, debug

class SvInterpolatingSurface(SvSurface):
    __description__ = "Interpolating"

    def __init__(self, u_bounds, v_bounds, u_spline_constructor, v_splines, reparametrize_v_splines=True):
        if reparametrize_v_splines:
            self.v_splines = [reparametrize_curve(spline) for spline in v_splines]
        else:
            for spline in v_splines:
                m,M = spline.get_u_bounds()
                if m != 0.0 or M != 1.0:
                    raise Exception("one of splines has to be reparametrized")
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
            point = spline.evaluate(v)
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

#     def evaluate_array(self, us, vs):
#         # FIXME: To be optimized!
#         normals = [self._evaluate(u, v) for u,v in zip(us, vs)]
#         return np.array(normals)

    def evaluate_array(self, us, vs):
        result = np.empty((len(us), 3))
        v_to_u = defaultdict(list)
        v_to_i = defaultdict(list)
        for i, (u, v) in enumerate(zip(us, vs)):
            v_to_u[v].append(u)
            v_to_i[v].append(i)

        # here we rely on fact that in Python 3.7+ dicts are ordered.
        all_vs = np.array(list(v_to_u.keys()))
        v_spline_points = np.array([spline.evaluate_array(all_vs) for spline in self.v_splines])

        for v_idx, (v, us_by_v) in enumerate(v_to_u.items()):
            is_by_v = v_to_i[v]
            spline_vertices = []
            for spline_idx, spline in enumerate(self.v_splines):
                point = v_spline_points[spline_idx,v_idx]
                #point = spline.evaluate(v)
                spline_vertices.append(point)
            u_spline = self.get_u_spline(v, spline_vertices)
            points = u_spline.evaluate_array(np.array(us_by_v))
            idxs = np.array(is_by_v)[np.newaxis].T
            np.put_along_axis(result, idxs, points, axis=0)
        return result

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

#     def normal_array(self, us, vs):
#         # FIXME: To be optimized!
#         normals = [self._normal(u, v) for u,v in zip(us, vs)]
#         return np.array(normals)

    def normal_array(self, us, vs):
        h = 0.001
        result = np.empty((len(us), 3))
        v_to_u = defaultdict(list)
        v_to_i = defaultdict(list)
        for i, (u, v) in enumerate(zip(us, vs)):
            v_to_u[v].append(u)
            v_to_i[v].append(i)
        for v, us_by_v in v_to_u.items():
            us_by_v = np.array(us_by_v)
            is_by_v = v_to_i[v]
            spline_vertices = []
            spline_vertices_h = []
            for v_spline in self.v_splines:
                v_min, v_max = v_spline.get_u_bounds()
                vx = (v_max - v_min) * v + v_min
                if vx +h <= v_max:
                    point = v_spline.evaluate(vx)
                    point_h = v_spline.evaluate(vx + h)
                else:
                    point = v_spline.evaluate(vx - h)
                    point_h = v_spline.evaluate(vx)
                spline_vertices.append(point)
                spline_vertices_h.append(point_h)
            if v+h <= v_max:
                u_spline = self.get_u_spline(v, spline_vertices)
                u_spline_h = self.get_u_spline(v+h, spline_vertices_h)
            else:
                u_spline = self.get_u_spline(v-h, spline_vertices)
                u_spline_h = self.get_u_spline(v, spline_vertices_h)
            u_min, u_max = 0.0, 1.0

            good_us = us_by_v + h < u_max
            bad_us = np.logical_not(good_us)

            good_points = np.broadcast_to(good_us[np.newaxis].T, (len(us_by_v), 3)).flatten()
            bad_points = np.logical_not(good_points)
            points = np.empty((len(us_by_v), 3))
            points[good_us] = u_spline.evaluate_array(us_by_v[good_us])
            points[bad_us] = u_spline.evaluate_array(us_by_v[bad_us] - h)
            points_u_h = np.empty((len(us_by_v), 3))
            points_u_h[good_us] = u_spline.evaluate_array(us_by_v[good_us] + h)
            points_u_h[bad_us] = u_spline.evaluate_array(us_by_v[bad_us])
            points_v_h = u_spline_h.evaluate_array(us_by_v)

            dvs = (points_v_h - points) / h
            dus = (points_u_h - points) / h
            normals = np.cross(dus, dvs)
            norms = np.linalg.norm(normals, axis=1, keepdims=True)
            normals = normals / norms

            idxs = np.array(is_by_v)[np.newaxis].T
            np.put_along_axis(result, idxs, normals, axis=0)
        return result

PROJECT = 'project'
COPROJECT = 'coproject'

def _dot(vs1, vs2):
    return (vs1 * vs2).sum(axis=1)[np.newaxis].T

class SvDeformedByFieldSurface(SvSurface):
    def __init__(self, surface, field, coefficient=1.0, by_normal=None):
        self.surface = surface
        self.field = field
        self.coefficient = coefficient
        self.by_normal = by_normal
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
        vec = self.field.evaluate(p[0], p[1], p[2])
        if self.by_normal == PROJECT:
            normal = self.surface.normal(u, v)
            vec = np.dot(vec, normal) * normal / np.dot(normal, normal)
        elif self.by_normal == COPROJECT:
            normal = self.surface.normal(u, v)
            projection = np.dot(vec, normal) * normal / np.dot(normal, normal)
            vec = vec - projection
        return p + self.coefficient * vec

    def evaluate_array(self, us, vs):
        ps = self.surface.evaluate_array(us, vs)
        xs, ys, zs = ps[:,0], ps[:,1], ps[:,2]
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        vecs = np.stack((vxs, vys, vzs)).T
        if self.by_normal == PROJECT:
            normals = self.surface.normal_array(us, vs)
            vecs = _dot(vecs, normals) * normals / _dot(normals, normals)
        elif self.by_normal == COPROJECT:
            normals = self.surface.normal_array(us, vs)
            projections = _dot(vecs, normals) * normals / _dot(normals, normals)
            vecs = vecs - projections
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

class SvRevolutionSurface(SvSurface):
    __description__ = "Revolution"

    def __init__(self, curve, point, direction, global_origin=True):
        self.curve = curve
        self.point = point
        self.direction = direction
        self.global_origin = global_origin
        self.normal_delta = 0.001
        self.v_bounds = (0.0, 2*pi)

    @classmethod
    def build(cls, curve, point, direction, v_min=0, v_max=2*pi, global_origin=True):
        if hasattr(curve, 'make_revolution_surface'):
            try:
                return curve.make_revolution_surface(point, direction, v_min, v_max, global_origin)
            except UnsupportedCurveTypeException as e:
                debug(f"Can't build revolution surface from {curve} natively: {e}")
        surface = SvRevolutionSurface(curve, point, direction, global_origin)
        surface.v_bounds = (v_min, v_max)
        return surface

    def evaluate(self, u, v):
        point_on_curve = self.curve.evaluate(u)
        dv = point_on_curve - self.point
        result = np.array(rotate_vector_around_vector(dv, self.direction, v))
        if not self.global_origin:
            result = result + self.point
        return result

    def evaluate_array(self, us, vs):
        points_on_curve = self.curve.evaluate_array(us)
        dvs = points_on_curve - self.point
        result = rotate_vector_around_vector_np(dvs, self.direction, vs)
        if not self.global_origin:
            result = result + self.point
        return result

    def get_u_min(self):
        return self.curve.get_u_bounds()[0]

    def get_u_max(self):
        return self.curve.get_u_bounds()[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

class SvExtrudeCurveVectorSurface(SvSurface):
    def __init__(self, curve, vector):
        self.curve = curve
        self.vector = np.array(vector)
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(curve)

    @classmethod
    def build(cls, curve, vector):
        if hasattr(curve, 'extrude_along_vector'):
            try:
                return curve.extrude_along_vector(vector)
            except UnsupportedCurveTypeException:
                pass
        return SvExtrudeCurveVectorSurface(curve, vector)

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

class SvExtrudeCurvePointSurface(SvSurface):
    def __init__(self, curve, point):
        self.curve = curve
        self.point = point
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(curve)

    @staticmethod
    def build(curve, point):
        if hasattr(curve, 'extrude_to_point'):
            try:
                return curve.extrude_to_point(point)
            except UnsupportedCurveTypeException:
                pass
        return SvExtrudeCurvePointSurface(curve, point)

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

PROFILE = 'profile'
EXTRUSION = 'extrusion'

class SvExtrudeCurveCurveSurface(SvSurface):
    def __init__(self, u_curve, v_curve, origin = PROFILE):
        self.u_curve = u_curve
        self.v_curve = v_curve
        self.origin = origin
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(u_curve)

    def evaluate(self, u, v):
        u_point = self.u_curve.evaluate(u)
        u_min, u_max = self.u_curve.get_u_bounds()
        v_min, v_max = self.v_curve.get_u_bounds()
        v0 = self.v_curve.evaluate(v_min)
        v_point = self.v_curve.evaluate(v)
        if self.origin == EXTRUSION:
            result = u_point + v_point
        else:
            result = u_point + (v_point - v0)
        return result

    def evaluate_array(self, us, vs):
        u_points = self.u_curve.evaluate_array(us)
        u_min, u_max = self.u_curve.get_u_bounds()
        v_min, v_max = self.v_curve.get_u_bounds()
        v0 = self.v_curve.evaluate(v_min)
        v_points = self.v_curve.evaluate_array(vs)
        if self.origin == EXTRUSION:
            result = u_points + v_points
        else:
            result = u_points + (v_points - v0)
        return result

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

class SvExtrudeCurveFrenetSurface(SvSurface):
    def __init__(self, profile, extrusion, origin = PROFILE):
        self.profile = profile
        self.extrusion = extrusion
        self.origin = origin
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(profile)

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        profile_points = self.profile.evaluate_array(us)
        u_min, u_max = self.profile.get_u_bounds()
        v_min, v_max = self.extrusion.get_u_bounds()
        profile_vectors = profile_points
        profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.extrusion.evaluate(v_min)
        extrusion_points = self.extrusion.evaluate_array(vs)
        extrusion_vectors = extrusion_points - extrusion_start
        frenet, _ , _ = self.extrusion.frame_array(vs)
        profile_vectors = (frenet @ profile_vectors)[:,:,0]
        result = extrusion_vectors + profile_vectors
        if self.origin == EXTRUSION:
            result = result + self.extrusion.evaluate(v_min)
        return result

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

class SvExtrudeCurveZeroTwistSurface(SvSurface):
    def __init__(self, profile, extrusion, resolution, origin = PROFILE):
        self.profile = profile
        self.extrusion = extrusion
        self.origin = origin
        self.normal_delta = 0.001
        self.extrusion.pre_calc_torsion_integral(resolution)
        self.__description__ = "Extrusion of {}".format(profile)

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        profile_points = self.profile.evaluate_array(us)
        u_min, u_max = self.profile.get_u_bounds()
        v_min, v_max = self.extrusion.get_u_bounds()
        profile_vectors = profile_points
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
        result = extrusion_vectors + profile_vectors
        if self.origin == EXTRUSION:
            result = result + self.extrusion.evaluate(v_min)
        return result

    def get_u_min(self):
        return self.profile.get_u_bounds()[0]

    def get_u_max(self):
        return self.profile.get_u_bounds()[1]

    def get_v_min(self):
        return self.extrusion.get_u_bounds()[0]

    def get_v_max(self):
        return self.extrusion.get_u_bounds()[1]

class SvExtrudeCurveTrackNormalSurface(SvSurface):
    def __init__(self, profile, extrusion, resolution, origin = PROFILE):
        self.profile = profile
        self.extrusion = extrusion
        self.origin = origin
        self.normal_delta = 0.001
        self.tracker = SvNormalTrack(extrusion, resolution)
        self.__description__ = "Extrusion of {}".format(profile)

    def get_u_min(self):
        return self.profile.get_u_bounds()[0]

    def get_u_max(self):
        return self.profile.get_u_bounds()[1]

    def get_v_min(self):
        return self.extrusion.get_u_bounds()[0]

    def get_v_max(self):
        return self.extrusion.get_u_bounds()[1]

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        profile_vectors = self.profile.evaluate_array(us)
        u_min, u_max = self.profile.get_u_bounds()
        v_min, v_max = self.extrusion.get_u_bounds()
        profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.extrusion.evaluate(v_min)
        extrusion_points = self.extrusion.evaluate_array(vs)
        extrusion_vectors = extrusion_points - extrusion_start

        matrices = self.tracker.evaluate_array(vs)
        profile_vectors = (matrices @ profile_vectors)[:,:,0]
        result = extrusion_vectors + profile_vectors
        if self.origin == EXTRUSION:
            result = result + extrusion_start
        return result

class SvExtrudeCurveMathutilsSurface(SvSurface):
    def __init__(self, profile, extrusion, algorithm, orient_axis='Z', up_axis='X', origin = PROFILE):
        self.profile = profile
        self.extrusion = extrusion
        self.algorithm = algorithm
        self.orient_axis = orient_axis
        self.up_axis = up_axis
        self.origin = origin
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(profile)

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def get_matrix(self, tangent):
        x = Vector((1.0, 0.0, 0.0))
        y = Vector((0.0, 1.0, 0.0))
        z = Vector((0.0, 0.0, 1.0))

        if self.orient_axis == 'X':
            ax1, ax2, ax3 = x, y, z
        elif self.orient_axis == 'Y':
            ax1, ax2, ax3 = y, x, z
        else:
            ax1, ax2, ax3 = z, x, y

        if self.algorithm == 'householder':
            rot = autorotate_householder(ax1, tangent).inverted()
        elif self.algorithm == 'track':
            rot = autorotate_track(self.orient_axis, tangent, self.up_axis)
        elif self.algorithm == 'diff':
            rot = autorotate_diff(tangent, ax1)
        else:
            raise Exception("Unsupported algorithm")

        return rot

    def get_matrices(self, vs):
        tangents = self.extrusion.tangent_array(vs)
        matrices = []
        for tangent in tangents:
            matrix = self.get_matrix(Vector(tangent)).to_3x3()
            matrices.append(matrix)
        return np.array(matrices)

    def evaluate_array(self, us, vs):
        profile_points = self.profile.evaluate_array(us)
        u_min, u_max = self.profile.get_u_bounds()
        v_min, v_max = self.extrusion.get_u_bounds()
        profile_vectors = profile_points
        profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.extrusion.evaluate(v_min)
        extrusion_points = self.extrusion.evaluate_array(vs)
        extrusion_vectors = extrusion_points - extrusion_start

        matrices = self.get_matrices(vs)

        profile_vectors = (matrices @ profile_vectors)[:,:,0]
        result = extrusion_vectors + profile_vectors
        if self.origin == EXTRUSION:
            result = result + self.extrusion.evaluate(v_min)
        return result

    def get_u_min(self):
        return self.profile.get_u_bounds()[0]

    def get_u_max(self):
        return self.profile.get_u_bounds()[1]

    def get_v_min(self):
        return self.extrusion.get_u_bounds()[0]

    def get_v_max(self):
        return self.extrusion.get_u_bounds()[1]

class SvExtrudeCurveNormalDirSurface(SvSurface):
    def __init__(self, profile, extrusion, plane_normal, origin = PROFILE):
        self.profile = profile
        self.extrusion = extrusion
        self.origin = origin
        self.plane_normal = np.array(plane_normal)
        self.normal_delta = 0.001
        self.__description__ = "Extrusion of {}".format(profile)

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        profile_points = self.profile.evaluate_array(us)
        u_min, u_max = self.profile.get_u_bounds()
        v_min, v_max = self.extrusion.get_u_bounds()
        profile_vectors = profile_points
        profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.extrusion.evaluate(v_min)
        extrusion_points = self.extrusion.evaluate_array(vs)
        extrusion_vectors = extrusion_points - extrusion_start
        matrices, _ , _ = self.extrusion.frame_by_plane_array(vs, self.plane_normal)
        profile_vectors = (matrices @ profile_vectors)[:,:,0]
        result = extrusion_vectors + profile_vectors
        if self.origin == EXTRUSION:
            result = result + self.extrusion.evaluate(v_min)
        return result

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

class SvConstPipeSurface(SvSurface):
    __description__ = "Pipe"

    def __init__(self, curve, radius, algorithm = FRENET, resolution=50):
        self.curve = curve
        self.radius = radius
        self.circle = SvCircle(Matrix(), radius)
        self.algorithm = algorithm
        self.normal_delta = 0.001
        self.u_bounds = self.circle.get_u_bounds()
        if algorithm in {FRENET, ZERO, TRACK_NORMAL}:
            self.calculator = DifferentialRotationCalculator(curve, algorithm, resolution)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.curve.get_u_bounds()[0]

    def get_v_max(self):
        return self.curve.get_u_bounds()[1]

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def get_matrix(self, tangent):
        return MathutilsRotationCalculator.get_matrix(tangent, scale=1.0,
                axis=2,
                algorithm = self.algorithm,
                scale_all=False)

    def get_matrices(self, ts):
        if self.algorithm in {FRENET, ZERO, TRACK_NORMAL}:
            return self.calculator.get_matrices(ts)
        elif self.algorithm in {HOUSEHOLDER, TRACK, DIFF}:
            tangents = self.curve.tangent_array(ts)
            matrices = np.vectorize(lambda t : self.get_matrix(t), signature='(3)->(3,3)')(tangents)
            return matrices
        else:
            raise Exception("Unsupported algorithm")

    def evaluate_array(self, us, vs):
        profile_vectors = self.circle.evaluate_array(us)
        u_min, u_max = self.circle.get_u_bounds()
        v_min, v_max = self.curve.get_u_bounds()
        profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.curve.evaluate(v_min)
        extrusion_points = self.curve.evaluate_array(vs)
        extrusion_vectors = extrusion_points - extrusion_start

        matrices = self.get_matrices(vs)

        profile_vectors = (matrices @ profile_vectors)[:,:,0]
        result = extrusion_vectors + profile_vectors
        result = result + extrusion_start
        return result

class SvCurveLerpSurface(SvSurface):
    __description__ = "Ruled"

    def __init__(self, curve1, curve2):
        self.curve1 = curve1
        self.curve2 = curve2
        self.normal_delta = 0.001
        self.v_bounds = (0.0, 1.0)
        self.u_bounds = (0.0, 1.0)
        self.c1_min, self.c1_max = curve1.get_u_bounds()
        self.c2_min, self.c2_max = curve2.get_u_bounds()

    @classmethod
    def build(cls, curve1, curve2, vmin=0.0, vmax=1.0):
        if hasattr(curve1, 'make_ruled_surface'):
            try:
                return curve1.make_ruled_surface(curve2, vmin, vmax)
            except TypeError as e:
                # make_ruled_surface method can raise TypeError in case
                # it can't work with given curve2.
                # In this case we must use generic method.
                debug("Can't make a native ruled surface: %s", e)
                pass

        # generic method
        surface = SvCurveLerpSurface(curve1, curve2)
        surface.v_bounds = (vmin, vmax)
        return surface

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

class SvSurfaceLerpSurface(SvSurface):
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

class SvTaperSweepSurface(SvSurface):
    __description__ = "Taper & Sweep"

    UNIT = 'UNIT'
    PROFILE = 'PROFILE'
    TAPER = 'TAPER'

    def __init__(self, profile, taper, point, direction, scale_base=UNIT):
        self.profile = profile
        self.taper = taper
        self.direction = direction
        self.point = point
        self.line = LineEquation.from_direction_and_point(direction, point)
        self.scale_base = scale_base
        self.normal_delta = 0.001

    def get_u_min(self):
        return self.profile.get_u_bounds()[0]

    def get_u_max(self):
        return self.profile.get_u_bounds()[1]

    def get_v_min(self):
        return self.taper.get_u_bounds()[0]

    def get_v_max(self):
        return self.taper.get_u_bounds()[1]

    def _get_profile_scale(self):
        profile_u_min = self.profile.get_u_bounds()[0]
        profile_start = self.profile.evaluate(profile_u_min)
        profile_start_projection = self.line.projection_of_point(profile_start)
        dp = np.linalg.norm(profile_start - profile_start_projection)
        return dp

    def evaluate(self, u, v):
        taper_point = self.taper.evaluate(v)
        taper_projection = np.array( self.line.projection_of_point(taper_point) )
        scale = np.linalg.norm(taper_projection - taper_point)
        if self.scale_base == SvTaperSweepSurface.TAPER:
            dp = self._get_profile_scale()
            scale /= dp
        elif self.scale_base == SvTaperSweepSurface.PROFILE:
            taper_t_min = self.taper.get_u_bounds()[0]
            taper_start = self.taper.evaluate(taper_t_min)
            taper_start_projection = np.array(self.line.projection_of_point(taper_start))
            scale0 = np.linalg.norm(taper_start - taper_start_projection)
            scale /= scale0

        profile_point = self.profile.evaluate(u)
        return profile_point * scale + taper_projection

    def evaluate_array(self, us, vs):
        taper_points = self.taper.evaluate_array(vs)
        taper_projections = self.line.projection_of_points(taper_points)
        scale = np.linalg.norm(taper_projections - taper_points, axis=1, keepdims=True)

        if self.scale_base == SvTaperSweepSurface.TAPER:
            dp = self._get_profile_scale()
            scale /= dp
        elif self.scale_base == SvTaperSweepSurface.PROFILE:
            scale0 = scale[0]
            scale /= scale0

        profile_points = self.profile.evaluate_array(us)
        return profile_points * scale + taper_projections

class SvBlendSurface(SvSurface):
    G1 = 'G1'
    G2 = 'G2'

    ORTHO_3D = '3D'
    ORTHO_UV = 'UV'

    def __init__(self, surface1, surface2, curve1, curve2, bulge1, bulge2, absolute_bulge = True, tangency = G1, ortho_mode = ORTHO_3D):
        self.surface1 = surface1
        self.surface2 = surface2
        self.curve1 = curve1
        self.curve2 = curve2
        self.bulge1 = bulge1
        self.bulge2 = bulge2
        self.absolute_bulge = absolute_bulge
        self.tangency = tangency
        self.ortho_mode = ortho_mode
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

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def evaluate_array(self, us, vs):
        c1_min, c1_max = self.curve1.get_u_bounds()
        c2_min, c2_max = self.curve2.get_u_bounds()
        c1_us = (c1_max - c1_min) * us + c1_min
        c2_us = (c2_max - c2_min) * us + c2_min

        calc1 = SvCurveOnSurfaceCurvaturesCalculator(self.curve1, self.surface1, c1_us)
        calc2 = SvCurveOnSurfaceCurvaturesCalculator(self.curve2, self.surface2, c2_us)
        _, c1_points, c1_tangents, c1_normals, c1_binormals = calc1.curve_frame_on_surface_array(normalize=False)
        _, c2_points, c2_tangents, c2_normals, c2_binormals = calc2.curve_frame_on_surface_array(normalize=False)
        t1dir = c1_binormals / np.linalg.norm(c1_binormals, axis=1, keepdims=True)
        t2dir = c2_binormals / np.linalg.norm(c2_binormals, axis=1, keepdims=True)

        if self.ortho_mode == SvBlendSurface.ORTHO_UV:
            c1_binormals = calc1.uv_normals_in_3d
            c2_binormals = calc2.uv_normals_in_3d

        if self.absolute_bulge:
            c1_binormals = self.bulge1 * t1dir
            c2_binormals = self.bulge2 * t2dir
        else:
            c1_binormals = self.bulge1 * c1_binormals
            c2_binormals = self.bulge2 * c2_binormals

        if self.tangency == SvBlendSurface.G2:
            c1_across = calc1.calc_curvatures_across_curve()
            c2_across = calc2.calc_curvatures_across_curve()

            A1 = c1_points
            A2 = c2_points
            B1 = A1 + c1_binormals / 5
            B2 = A2 + c2_binormals / 5

            n1dir = c1_normals / np.linalg.norm(c1_normals, axis=1, keepdims=True)
            n2dir = c2_normals / np.linalg.norm(c2_normals, axis=1, keepdims=True)

            r1 = c1_across * np.linalg.norm(c1_binormals, axis=1)**2 / 20
            r2 = c2_across * np.linalg.norm(c2_binormals, axis=1)**2 / 20
            r1 = r1[np.newaxis].T
            r2 = r2[np.newaxis].T

            bs = (B2 - B1) / np.linalg.norm(B2 - B1, axis=1, keepdims=True)

#             cos_alpha1 = np_dot(t1dir, bs)[np.newaxis].T
#             cos_beta1 = np_dot(n1dir, bs)[np.newaxis].T
#             t12 = (r1 * cos_beta1) / (1 - cos_alpha1**2)
#             t11 = cos_alpha1 * t12
#             C1 = B1 + r1 * n1dir + t11 * t1dir
            C1 = B1 + r1 * n1dir + (B1 - A1)

#             cos_alpha2 = np_dot(t2dir, -bs)[np.newaxis].T
#             cos_beta2 = np_dot(n2dir, -bs)[np.newaxis].T
#             t22 = (r2 * cos_beta2) / (1 - cos_alpha2**2)
#             t21 = cos_alpha2 * t22
#             C2 = B2 + r2 * n2dir + t21 * t2dir
            C2 = B2 + r2 * n2dir + (B2 - A2)

            # See also sverchok.utils.curve.bezier.SvBezierCurve.
            c0 = (1 - vs)**5      # (n,)
            c1 = 5*vs*(1-vs)**4
            c2 = 10*vs**2*(1-vs)**3
            c3 = 10*vs**3*(1-vs)**2
            c4 = 5*vs**4*(1-vs)
            c5 = vs**5

            # (n,1)
            c0, c1, c2, c3, c4, c5 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis], c4[:,np.newaxis], c5[:,np.newaxis]

            return c0*A1 + c1*B1 + c2*C1 + c3*C2 + c4*B2 + c5*A2
        else: # G1
            # See also sverchok.utils.curve.bezier.SvCubicBezierCurve.
            # Here we have re-implementation of the same algorithm
            # which works with arrays of control points
            p0s = c1_points                 # (n, 3)
            p1s = c1_points + c1_binormals
            p2s = c2_points + c2_binormals
            p3s = c2_points

            c0 = (1 - vs)**3      # (n,)
            c1 = 3*vs*(1-vs)**2
            c2 = 3*vs**2*(1-vs)
            c3 = vs**3

            c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
            return c0*p0s + c1*p1s + c2*p2s + c3*p3s


class SvConcatSurface(SvSurface):
    def __init__(self, direction, surfaces):
        self.direction = direction
        self.surfaces = self._unify(surfaces)

        p1 = self._get_p_min(surfaces[0])
        boundaries = [p1]
        boundaries.extend([self._get_p_delta(s) for s in surfaces])
        self.boundaries = np.array(boundaries).cumsum()

    def _unify(self, surfaces):
        if self.direction == 'U':
            min_vs = [s.get_v_min() for s in surfaces]
            max_vs = [s.get_v_max() for s in surfaces]

            if min(min_vs) != max(min_vs) or min(max_vs) != max(max_vs):
                surfaces = [SvReparametrizedSurface.build(s, s.get_u_min(), s.get_u_max(), 0.0, 1.0) for s in surfaces]
            return surfaces
        
        else:
            min_us = [s.get_u_min() for s in surfaces]
            max_us = [s.get_u_max() for s in surfaces]

            if min(min_us) != max(min_us) or min(max_us) != max(max_us):
                surfaces = [SvReparametrizedSurface.build(s, 0.0, 1.0, s.get_v_min(), s.get_v_max()) for s in surfaces]
            return surfaces

    def _get_p_max(self, surface):
        if self.direction == 'U':
            return surface.get_u_max()
        else:
            return surface.get_v_max()

    def _get_p_delta(self, surface):
        if self.direction == 'U':
            return surface.get_u_max() - surface.get_u_min()
        else:
            return surface.get_v_max() - surface.get_v_min()

    def _get_p_min(self, surface):
        if self.direction == 'U':
            return surface.get_u_min()
        else:
            return surface.get_v_min()

    def get_u_min(self):
        if self.direction == 'U':
            return self.boundaries[0]
        else:
            return self.surfaces[0].get_u_min()

    def get_u_max(self):
        if self.direction == 'U':
            return self.boundaries[-1]
        else:
            return self.surfaces[0].get_u_max()

    def get_v_min(self):
        if self.direction == 'U':
            return self.surfaces[0].get_v_min()
        else:
            return self.boundaries[0]

    def get_v_max(self):
        if self.direction == 'U':
            return self.surfaces[0].get_v_max()
        else:
            return self.boundaries[-1]

    def evaluate(self, u, v):
        if self.direction == 'U':
            u_idx = self.boundaries.searchsorted(u, side='right')-1
            if u_idx >= len(self.surfaces):
                v_idx = len(self.surfaces)-1
                du = self._get_p_delta(self.surfaces[-1])
            else:
                du = u - self.boundaries[u_idx]
            subsurf = self.surfaces[u_idx]
            return subsurf.evaluate(subsurf.get_u_min()+du, v)
        else:
            v_idx = self.boundaries.searchsorted(v, side='right')-1
            if v_idx >= len(self.surfaces):
                v_idx = len(self.surfaces)-1
                dv = self._get_p_delta(self.surfaces[-1])
            else:
                dv = v - self.boundaries[v_idx]
            subsurf = self.surfaces[v_idx]
            return subsurf.evaluate(u, subsurf.get_v_min()+dv)

    def evaluate_array(self, us, vs):
        # TODO: numpy implementation
        return np.vectorize(self.evaluate, signature='(),()->(3)')(us, vs)

def concatenate_surfaces(direction, surfaces):
    if all(hasattr(s, 'concatenate') for s in surfaces):
        try:
            result = surfaces[0]
            for s in surfaces[1:]:
                result = result.concatenate(direction, s)
            return result
        except UnsupportedSurfaceTypeException as e:
            debug("Can't concatenate surfaces natively: %s", e)
    
    return SvConcatSurface(direction, surfaces)

def nurbs_revolution_surface(curve, origin, axis, v_min=0, v_max=2*pi, global_origin=True):
    my_control_points = curve.get_control_points()
    my_weights = curve.get_weights()
    control_points = []
    weights = []

    any_circle = SvCircle(Matrix(), 1)
    any_circle.u_bounds = (v_min, v_max)
    any_circle = any_circle.to_nurbs()
    # all circles with given (v_min, v_max)
    # actually always have the same knotvector
    # and the same number of control points
    n = len(any_circle.get_control_points())
    circle_knotvector = any_circle.get_knotvector()
    circle_weights = any_circle.get_weights()

    # TODO: vectorize with numpy? Or better let it so for better readability?
    for my_control_point, my_weight in zip(my_control_points, my_weights):
        eq = CircleEquation3D.from_axis_point(origin, axis, my_control_point)
        if abs(eq.radius) < 1e-8:
            parallel_points = np.empty((n, 3))
            parallel_points[:] = np.array(eq.center) #[np.newaxis].T
        else:
            circle = SvCircle.from_equation(eq)
            circle.u_bounds = (v_min, v_max)
            nurbs_circle = circle.to_nurbs()
            parallel_points = nurbs_circle.get_control_points()
        parallel_weights = circle_weights * my_weight
        control_points.append(parallel_points)
        weights.append(parallel_weights)
    control_points = np.array(control_points)
    if global_origin:
        control_points = control_points - origin

    weights = np.array(weights)
    degree_u = curve.get_degree()
    degree_v = 2 # circle

    return SvNurbsSurface.build(curve.get_nurbs_implementation(),
            degree_u, degree_v,
            curve.get_knotvector(), circle_knotvector,
            control_points, weights)

def round_knotvectors(surface, accuracy):
    knotvector_u = surface.get_knotvector_u()
    knotvector_v = surface.get_knotvector_v()

    knotvector_u = np.round(knotvector_u, accuracy)
    knotvector_v = np.round(knotvector_v, accuracy)

    result = surface.copy(knotvector_u = knotvector_u, knotvector_v = knotvector_v)

    tolerance = 10**(-accuracy)

#     print(f"KV_U: {knotvector_u}")
#     print(f"KV_V: {knotvector_v}")
#     degree = surface.get_degree_u()
#     ms = sv_knotvector.to_multiplicity(knotvector_u, tolerance)
#     n = len(ms)
#     for idx, (u, count) in enumerate(ms):
#         if idx == 0 or idx == n-1:
#             max_allowed = degree+1
#         else:
#             max_allowed = degree
#         print(f"U={u}: max.allowed {max_allowed}, actual {count}")
#         diff = count - max_allowed
# 
#         if diff > 0:
#             print(f"Remove U={u} x {diff}")
#             result = result.remove_knot(SvNurbsSurface.U, u, diff)
# 
#     degree = surface.get_degree_v()
#     ms = sv_knotvector.to_multiplicity(knotvector_v, tolerance)
#     n = len(ms)
#     for idx, (v, count) in enumerate(ms):
#         if idx == 0 or idx == n-1:
#             max_allowed = degree+1
#         else:
#             max_allowed = degree
#         print(f"V={v}: max.allowed {max_allowed}, actual {count}")
#         diff = count - max_allowed
# 
#         if diff > 0:
#             print(f"Remove V={v} x {diff}")
#             result = result.remove_knot(SvNurbsSurface.V, v, diff)

    return result

def unify_nurbs_surfaces(surfaces, knots_method = 'UNIFY', knotvector_accuracy=6):
    # Unify surface degrees

    degrees_u = [surface.get_degree_u() for surface in surfaces]
    degrees_v = [surface.get_degree_v() for surface in surfaces]

    degree_u = max(degrees_u)
    degree_v = max(degrees_v)
    #print(f"Elevate everything to {degree_u}x{degree_v}")

    surfaces = [surface.elevate_degree(SvNurbsSurface.U, target=degree_u) for surface in surfaces]
    surfaces = [surface.elevate_degree(SvNurbsSurface.V, target=degree_v) for surface in surfaces]

    # Unify surface knotvectors

    knotvector_tolerance = 10**(-knotvector_accuracy)

    if knots_method == 'UNIFY':

        surfaces = [round_knotvectors(s, knotvector_accuracy) for s in surfaces]
        for i, surface in enumerate(surfaces):
            #print(f"S #{i} KV_U: {surface.get_knotvector_u()}")
            #print(f"S #{i} KV_V: {surface.get_knotvector_v()}")
            kv_err = sv_knotvector.check_multiplicity(surface.get_degree_u(), surface.get_knotvector_u(), tolerance=knotvector_tolerance)
            if kv_err is not None:
                raise Exception(f"Surface #{i}: invalid U knotvector: {kv_err}")

            kv_err = sv_knotvector.check_multiplicity(surface.get_degree_v(), surface.get_knotvector_v(), tolerance=knotvector_tolerance)
            if kv_err is not None:
                raise Exception(f"Surface #{i}: invalid V knotvector: {kv_err}")

        dst_knots_u = defaultdict(int)
        dst_knots_v = defaultdict(int)
        for surface in surfaces:
            m_u = sv_knotvector.to_multiplicity(surface.get_knotvector_u(), tolerance=knotvector_tolerance)
            m_v = sv_knotvector.to_multiplicity(surface.get_knotvector_v(), tolerance=knotvector_tolerance)

            for u, count in m_u:
                u = round(u, knotvector_accuracy)
                dst_knots_u[u] = max(dst_knots_u[u], count)

            for v, count in m_v:
                v = round(v, knotvector_accuracy)
                dst_knots_v[v] = max(dst_knots_v[v], count)

        result = []
        for surface in surfaces:
            diffs_u = []
            kv_u = np.round(surface.get_knotvector_u(), knotvector_accuracy)
            ms_u = dict(sv_knotvector.to_multiplicity(kv_u, tolerance=knotvector_tolerance))
            for dst_u, dst_multiplicity in dst_knots_u.items():
                src_multiplicity = ms_u.get(dst_u, 0)
                diff = dst_multiplicity - src_multiplicity
                diffs_u.append((dst_u, diff))

            for u, diff in diffs_u:
                if diff > 0:
                    #print(f"S: Insert U = {u} x {diff}")
                    surface = surface.insert_knot(SvNurbsSurface.U, u, diff)

            diffs_v = []
            kv_v = np.round(surface.get_knotvector_v(), knotvector_accuracy)
            ms_v = dict(sv_knotvector.to_multiplicity(kv_v, tolerance=knotvector_tolerance))
            for dst_v, dst_multiplicity in dst_knots_v.items():
                src_multiplicity = ms_v.get(dst_v, 0)
                diff = dst_multiplicity - src_multiplicity
                diffs_v.append((dst_v, diff))

            for v, diff in diffs_v:
                if diff > 0:
                    #print(f"S: Insert V = {v} x {diff}")
                    surface = surface.insert_knot(SvNurbsSurface.V, v, diff)

            result.append(surface)

        return result

    elif knots_method == 'AVERAGE':
        kvs = [len(surface.get_control_points()) for surface in surfaces]
        max_kv, min_kv = max(kvs), min(kvs)
        if max_kv != min_kv:
            raise Exception(f"U knotvector averaging is not applicable: Surfaces have different number of control points: {kvs}")

        kvs = [len(surface.get_control_points()[0]) for surface in surfaces]
        max_kv, min_kv = max(kvs), min(kvs)
        if max_kv != min_kv:
            raise Exception(f"V knotvector averaging is not applicable: Surfaces have different number of control points: {kvs}")


        knotvectors = np.array([surface.get_knotvector_u() for surface in surfaces])
        knotvector_u = knotvectors.mean(axis=0)

        knotvectors = np.array([surface.get_knotvector_v() for surface in surfaces])
        knotvector_u = knotvectors.mean(axis=0)

        result = []
        for surface in surfaces:
            surface = SvNurbsSurface.build(surface.get_nurbs_implementation(),
                    surface.get_degree_u(), surface.get_degree_v(),
                    knotvector_u, knotvector_v,
                    surface.get_control_points(),
                    surface.get_weights())
            result.append(surface)
        return result
    else:
        raise Exception('Unsupported knotvector unification method')

def remove_excessive_knots(surface, direction, tolerance=1e-6):
    if direction not in {'U', 'V', 'UV'}:
        raise Exception("Unsupported direction")

    if direction in {'U', 'UV'}:
        kv = surface.get_knotvector_u()
        for u in sv_knotvector.get_internal_knots(kv):
            surface = surface.remove_knot('U', u, count='ALL', tolerance=tolerance, if_possible=True)

    if direction in {'V', 'UV'}:
        kv = surface.get_knotvector_v()
        for v in sv_knotvector.get_internal_knots(kv):
            surface = surface.remove_knot('V', v, count='ALL', tolerance=tolerance, if_possible=True)

    return surface

def build_nurbs_sphere(center, radius):
    """
    Generate NURBS Surface representing a sphere.
    Sphere is defined here as a surface of revolution of
    half a circle.
    """
    vectorx = np.array([0.0, 0.0, radius])
    axis = np.array([0.0, 0.0, 1.0])
    normal = np.array([1.0, 0.0, 0.0])
    matrix = SvCircle.calc_matrix(normal, vectorx)
    matrix = Matrix.Translation(center) @ Matrix(matrix).to_4x4()
    arc = SvCircle(matrix=matrix, radius=radius, normal=normal, vectorx=vectorx)
    arc.u_bounds = (0.0, pi)
    return nurbs_revolution_surface(arc.to_nurbs(), center, axis, 0, 2*pi, global_origin=True)

def deform_nurbs_surface(src_surface, uknots, vknots, points):
    """
    Move some control points of a NURBS surface so that at
    given parameter values it passes through the given points.
    NB: rational surfaces are not supported yet.
    Parameters:
    * src_surface - SvNurbsSurface instance
    * uknots, vknots - np.array of shape (n,): U and V coordinates
        of points to be moved
    * points: np.array of shape (n,3): desired locations of surface points.
    Output:
    * SvNurbsSurface instance.
    """
    n = len(points)
    if len(uknots) != n or len(vknots) != n:
        raise Exception("Number of points, uknots and vknots must be equal")
    if src_surface.is_rational():
        raise UnsupportedSurfaceTypeException("Rational surfaces are not supported yet")

    ndim = 3
    knotvector_u = src_surface.get_knotvector_u()
    knotvector_v = src_surface.get_knotvector_v()
    basis_u = SvNurbsBasisFunctions(knotvector_u)
    basis_v = SvNurbsBasisFunctions(knotvector_v)
    degree_u = src_surface.get_degree_u()
    degree_v = src_surface.get_degree_v()
    ncpts_u, ncpts_v,_ = src_surface.get_control_points().shape
    nsu = np.array([basis_u.derivative(i, degree_u, 0)(uknots) for i in range(ncpts_u)])
    nsv = np.array([basis_v.derivative(i, degree_v, 0)(vknots) for i in range(ncpts_v)])
    
    nsu_t = np.transpose(nsu[np.newaxis], axes=(1,0,2)) # (ncpts_u, 1, n)
    nsv_t = nsv[np.newaxis] # (1, ncpts_v, n)
    ns_t = nsu_t * nsv_t # (ncpts_u, ncpts_v, n)
    denominator = ns_t.sum(axis=0).sum(axis=0)
    
    n_equations = n*ndim
    n_unknowns = ncpts_u * ncpts_v * ndim
    #print(f"Eqs: {n_equations}, Unk: {n_unknowns}")
    
    A = np.zeros((n_equations, n_unknowns))
    for u_idx in range(ncpts_u):
        for v_idx in range(ncpts_v):
            cpt_idx = ncpts_v * u_idx + v_idx
            for pt_idx in range(n):
                alpha = nsu[u_idx][pt_idx] * nsv[v_idx][pt_idx] / denominator[pt_idx]
                for dim_idx in range(ndim):
                    A[ndim*pt_idx + dim_idx, ndim*cpt_idx + dim_idx] = alpha
                    
    src_points = src_surface.evaluate_array(uknots, vknots)
    
    B = np.zeros((n_equations,1))
    for pt_idx, point in enumerate(points):
        B[pt_idx*3:pt_idx*3+3,0] = point[np.newaxis] - src_points[pt_idx][np.newaxis]

    if n_equations == n_unknowns:
        print("Well-determined", n_equations)
        A1 = np.linalg.inv(A)
        X = (A1 @ B).T
    elif n_equations < n_unknowns:
        print("Underdetermined", n_equations, n_unknowns)
        A1 = np.linalg.pinv(A)
        X = (A1 @ B).T
    else: # n_equations > n_unknowns
        print("Overdetermined", n_equations, n_unknowns)
        X, residues, rank, singval = np.linalg.lstsq(A, B)
    d_cpts = X.reshape((ncpts_u, ncpts_v, ndim))
    cpts = src_surface.get_control_points()
    
    surface = SvNurbsSurface.build(src_surface.get_nurbs_implementation(),
                degree_u, degree_v, knotvector_u, knotvector_v,
                cpts + d_cpts)
    return surface

def make_planar_surface(origin, u_axis, v_axis, degree_u, degree_v, ncpts_u, ncpts_v, size_u, size_v, implementation = SvNurbsSurface.NATIVE):
    """
    Generate squa planar NURBS surface.
    Parameters:
    * origin - point at the plane, which will have UV coordinates (0.5, 0.5). np.array of shape (3,).
    * u_axis, v_axis - vectors which will define directions of U and V parameter axes. np.array of shape (3,).
    * degree_u, degree_v - degrees of the surface along U and V parameters.
    * ncpts_u, ncpts_v - number of control points of the surface along U and V.
    * size_u, size_v - size of the surface along U and V, measured in lengths of u_axis and v_axis.
    Return value: an instance of SvNurbsSurface.
    """
    us = np.linspace(-size_u/2.0, size_u/2.0, num=ncpts_u)
    vs = np.linspace(-size_v/2.0, size_v/2.0, num=ncpts_v)
    cpts = [[origin + u*u_axis + v*v_axis for u in list(vs)] for v in list(us)]
    cpts = np.array(cpts)
    knotvector_u = sv_knotvector.generate(degree_u, ncpts_u)
    knotvector_v = sv_knotvector.generate(degree_v, ncpts_v)
    return SvNurbsSurface.build(implementation, 
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                cpts)

def nurbs_surface_from_points(points, degree_u, degree_v, num_cpts_u, num_cpts_v, normal = None, implementation = SvNurbsSurface.NATIVE):
    """
    Generate a NURBS surface which passes either through or near the specified points.
    Parameters:
    * points - points to draw a surface through. np.array of shape (n,3).
    * degree_u, degree_v - degrees of the surface along U and V directions.
    * num_cpts_u, num_cpts_v - number of surface's control points along U and V.

    If total number of control points (num_cpts_u * num_cpts_v) is equal to the
    number of points specified, then the system will be well-determined, so
    this will do interpolation (although depending on location of points, it
    may fail).
    If total number of control points is less than the number of points
    specified, then the system will be overdetermined, so this will do
    approximation.
    If total number of control points is more than the number of points
    specified, then the system will be underdetermined, i.e. there are many
    surfaces passing through these points. In this case, the method will select
    the surface which has all it's control points as close to origin (0.0, 0.0,
    0.0) as possible.

    Return values:
    * SvNurbsSurface instance
    * uv_points - coordinates of points provided in UV space of the surface.
        np.array of shape (n, 3).
    """

    def calc_y_axis(plane, x_axis):
        normal = np.array(plane.normal)
        y_axis = np.cross(x_axis, normal)
        y_axis /= np.linalg.norm(y_axis)
        return y_axis

    if normal is None:
        linear = linear_approximation(points)
        origin = linear.center
        plane = linear.most_similar_plane()
    else:
        origin = center(points)
        plane = PlaneEquation.from_normal_and_point(normal, origin)

    start = points[0]
    start_projection = np.asarray(plane.projection_of_point(start))
    x_axis = start_projection - origin
    x_axis /= np.linalg.norm(x_axis)
    y_axis = calc_y_axis(plane, x_axis)
    distances = np.linalg.norm(points - origin, axis=1)
    max_distance = distances.max()
    
    planar_surface = make_planar_surface(origin,
                    x_axis, y_axis,
                    degree_u, degree_v,
                    num_cpts_u, num_cpts_v,
                    max_distance*2, max_distance*2,
                    implementation = implementation)
    
    us = np_dot(points, x_axis)
    vs = np_dot(points, y_axis)
    us_min, us_max = us.min(), us.max()
    vs_min, vs_max = vs.min(), vs.max()
    us = (us - us_min) / (us_max - us_min)
    vs = (vs - vs_min) / (vs_max - vs_min)
    surface = deform_nurbs_surface(planar_surface, us, vs, points)
    uv_points = np.array([[u,v, 0.0] for u,v in zip(us,vs)])
    return surface, uv_points

def nurbs_surface_from_curve(curve, samples, degree_u, degree_v, num_cpts_u, num_cpts_v, implementation = None):
    """
    Generate a NURBS surface which passes through the points of specified curve.
    See also documentation of nurbs_surface_from_points method.
    Parameters:
    * curve - SvNurbsCurve instance.
    * samples - the number of points on the curve, through which the surface should be build.
    * degree_u, degree_v - degrees of the surface along U and V directions.
    * num_cpts_u, num_cpts_v - number of surface's control points along U and V.
    Return value:
    * SvNurbsSurface instance
    * SvNurbsCurve instance: a curve in surface's UV space, which passes
        through projections of specified points to the surface.
    """

    if implementation is None:
        implementation = curve.get_nurbs_implementation()

    t_min, t_max = curve.get_u_bounds()
    ts = np.linspace(t_min, t_max, num=samples)
    points = curve.evaluate_array(ts)
    surface = nurbs_surface_from_points(points, degree_u, degere_v, num_cpts_u, num_cpts_v, implementation = implementation)
    trim_curve = SvNurbsMaths.interpolate_curve(implementation, curve.get_degree(), uv_points)
    return surface, trim_curve

