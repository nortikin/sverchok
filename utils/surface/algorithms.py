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
        ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL
    )
from sverchok.utils.geom import (
        LineEquation, CircleEquation3D,
        rotate_vector_around_vector, rotate_vector_around_vector_np,
        autorotate_householder, autorotate_track, autorotate_diff
    )
from sverchok.utils.curve.core import SvFlipCurve, UnsupportedCurveTypeException
from sverchok.utils.curve.primitives import SvCircle, SvLine
from sverchok.utils.curve.algorithms import (
            SvNormalTrack, curve_frame_on_surface_array,
            MathutilsRotationCalculator, DifferentialRotationCalculator,
            reparametrize_curve
        )
from sverchok.utils.surface.core import SvSurface, UnsupportedSurfaceTypeException
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface.data import *
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
            except UnsupportedCurveTypeException:
                pass
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

class SvBlendSurface(SvSurface):
    def __init__(self, surface1, surface2, curve1, curve2, bulge1, bulge2):
        self.surface1 = surface1
        self.surface2 = surface2
        self.curve1 = curve1
        self.curve2 = curve2
        self.bulge1 = bulge1
        self.bulge2 = bulge2
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

    def evaluate_array(self, us, vs):
        c1_min, c1_max = self.curve1.get_u_bounds()
        c2_min, c2_max = self.curve2.get_u_bounds()
        c1_us = (c1_max - c1_min) * us + c1_min
        c2_us = (c2_max - c2_min) * us + c2_min

        _, c1_points, _, _, c1_binormals = curve_frame_on_surface_array(self.surface1, self.curve1, c1_us)
        _, c2_points, _, _, c2_binormals = curve_frame_on_surface_array(self.surface2, self.curve2, c2_us)
        c1_binormals = self.bulge1 * c1_binormals
        c2_binormals = self.bulge2 * c2_binormals

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

        # (n,1)
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]

        return c0*p0s + c1*p1s + c2*p2s + c3*p3s

blend_surface_adapters = []

def blend_nurbs_surfaces(surface1, surface2, curve1, curve2, bulge1, bulge2):
    surface1 = SvNurbsSurface.get(surface1)
    surface2 = SvNurbsSurface.get(surface2)
    if surface1 is None or surface2 is None:
        raise UnsupportedSurfaceTypeException("surfaces are not nurbs")
    if not isinstance(curve1, SvLine) or not isinstance(curve2, SvLine):
        raise UnsupportedSurfaceTypeException("only lines are supported")

    bounds_1 = surface1.get_bounds()
    bounds_2 = surface2.get_bounds()

    def get_iso_values(line, bounds):
        p1 = line.point
        p2 = line.point + line.direction
        if p1[0] == p2[0] and p1[0] in bounds[0]:
            if p1[1] == bounds[1][0] and p2[1] == bounds[1][1]:
                return 0, p1[0]

        if p1[1] == p2[1] and p1[1] in bounds[1]:
            if p1[0] == bounds[0][0] and p2[0] == bounds[0][1]:
                return 1, p1[1]
        raise UnsupportedSurfaceTypeException("only iso-lines are supported")

    fixed_axis_1, fixed_value_1 = get_iso_values(curve1, bounds_1)
    fixed_axis_2, fixed_value_2 = get_iso_values(curve2, bounds_2)

    degrees_1 = surface1.get_degree_u(), surface1.get_degree_v()
    degrees_2 = surface2.get_degree_u(), surface2.get_degree_v()

    degree_1 = degrees_1[1-fixed_axis_1]
    degree_2 = degrees_2[1-fixed_axis_2]
    if degree_1 != degree_2:
        raise UnsupportedSurfaceTypeException("degrees are different")

    knotvectors_1 = surface1.get_knotvector_u(), surface1.get_knotvector_v()
    knotvectors_2 = surface2.get_knotvector_u(), surface2.get_knotvector_v()
    knotvector_1 = knotvectors_1[1-fixed_axis_1]
    knotvector_2 = knotvectors_2[1-fixed_axis_2]
    if not sv_knotvector.equal(knotvector_1, knotvector_2):
        raise UnsupportedSurfaceTypeException("knotvectors are different")

    if fixed_value_1 == bounds_1[fixed_axis_1][0]:
        sign_1 = -1
    elif fixed_value_1 == bounds_1[fixed_axis_1][1]:
        sign_1 = 1
    else:
        raise UnsupportedSurfaceTypeException("not a boundary curve")

    if fixed_value_2 == bounds_2[fixed_axis_2][0]:
        sign_2 = -1
    elif fixed_value_2 == bounds_2[fixed_axis_2][1]:
        sign_2 = 1
    else:
        raise UnsupportedSurfaceTypeException("not a boundary curve")

    controls_1 = surface1.get_control_points()
    if fixed_axis_1 == 1:
        controls_1 = np.transpose(controls_1, axes=(1,0,2))
    controls_2 = surface2.get_control_points()
    if fixed_axis_2 == 1:
        controls_2 = np.transpose(controls_2, axes=(1,0,2))
        print(f"C2S: {controls_2.shape}")

    if sign_1 == -1:
        boundary_1 = controls_1[0,:]
        next_1 = controls_1[1,:]
    else:
        boundary_1 = controls_1[-1,:]
        next_1 = controls_1[-2,:]
    if sign_2 == -1:
        boundary_2 = controls_2[0,:]
        next_2 = controls_2[1,:]
    else:
        boundary_2 = controls_2[-1,:]
        next_2 = controls_2[-2,:]
    print(f"1: sign {sign_1}, b {boundary_1}, next {next_1}")
    print(f"2: sign {sign_2}, b {boundary_2}, next {next_2}")

    vectors_1 = (boundary_1 - next_1)
    vectors_2 = (boundary_2 - next_2)

    midpoints_1 = boundary_1 + bulge1*vectors_1
    midpoints_2 = boundary_2 + bulge2*vectors_2

    controls = np.stack((boundary_1, midpoints_1, midpoints_2, boundary_2))

    degree_u = 3

    knotvector_u = sv_knotvector.generate(degree_u, 4)

    return SvNurbsSurface.build(surface1.get_nurbs_implementation(),
            degree_u, degree_1,
            knotvector_u, knotvector_1,
            controls)

blend_surface_adapters.append(blend_nurbs_surfaces)

def blend_surfaces(surface1, surface2, curve1, curve2, bulge1, bulge2):
    for adapter in blend_surface_adapters:
        try:
            return adapter(surface1, surface2, curve1, curve2, bulge1, bulge2)
        except UnsupportedSurfaceTypeException as e:
            print(e)
            pass
    return SvBlendSurface(surface1, surface2, curve1, curve2, bulge1, bulge2)

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

