# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from mathutils import Vector, Matrix
from sverchok.utils.curve.core import (
        SvCurve, ZeroCurvatureException,
        SvCurveSegment, SvReparametrizedCurve,
        SvFlipCurve, SvConcatCurve,
        UnsupportedCurveTypeException
    )
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.geom import PlaneEquation, LineEquation, Spline, LinearSpline, CubicSpline
from sverchok.utils.geom import autorotate_householder, autorotate_track, autorotate_diff
from sverchok.utils.math import (
    ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL,
    NORMAL_DIR
)
from sverchok.utils.logging import info

def make_euclidian_ts(pts):
    tmp = np.linalg.norm(pts[:-1] - pts[1:], axis=1)
    tknots = np.insert(tmp, 0, 0).cumsum()
    tknots = tknots / tknots[-1]
    return tknots

class SvCurveLengthSolver(object):
    def __init__(self, curve):
        self.curve = curve
        self._spline = None

    def calc_length_segments(self, tknots):
        vectors = self.curve.evaluate_array(tknots)
        dvs = vectors[1:] - vectors[:-1]
        lengths = np.linalg.norm(dvs, axis=1)
        return lengths

    def get_total_length(self):
        if self._spline is None:
            raise Exception("You have to call solver.prepare() first")
        return self._length_params[-1]

    def prepare(self, mode, resolution=50):
        t_min, t_max = self.curve.get_u_bounds()
        tknots = np.linspace(t_min, t_max, num=resolution)
        lengths = self.calc_length_segments(tknots)
        self._length_params = np.cumsum(np.insert(lengths, 0, 0))
        self._spline = self._make_spline(mode, tknots)

    def _make_spline(self, mode, tknots):
        zeros = np.zeros(len(tknots))
        control_points = np.vstack((self._length_params, tknots, zeros)).T
        if mode == 'LIN':
            spline = LinearSpline(control_points, tknots = self._length_params, is_cyclic = False)
        elif mode == 'SPL':
            spline = CubicSpline(control_points, tknots = self._length_params, is_cyclic = False)
        else:
            raise Exception("Unsupported mode; supported are LIN and SPL.")
        return spline

    def solve(self, input_lengths):
        if self._spline is None:
            raise Exception("You have to call solver.prepare() first")
        spline_verts = self._spline.eval(input_lengths)
        return spline_verts[:,1]

class SvNormalTrack(object):
    def __init__(self, curve, resolution):
        self.curve = curve
        self.resolution = resolution
        self._pre_calc()

    def _make_quats(self, points, tangents, normals, binormals):
        matrices = np.dstack((normals, binormals, tangents))
        matrices = np.transpose(matrices, axes=(0,2,1))
        matrices = np.linalg.inv(matrices)
        return [Matrix(m).to_quaternion() for m in matrices]

    def _pre_calc(self):
        curve = self.curve
        t_min, t_max = curve.get_u_bounds()
        ts = np.linspace(t_min, t_max, num=self.resolution)

        points = curve.evaluate_array(ts)
        tangents, normals, binormals = curve.tangent_normal_binormal_array(ts)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)

        normal = normals[0]
        if np.linalg.norm(normal) > 1e-4:
            binormal = binormals[0]
            binormal /= np.linalg.norm(binormal)
        else:
            tangent = tangents[0]
            normal = Vector(tangent).orthogonal()
            normal = np.array(normal)
            binormal = np.cross(tangent, normal)
            binormal /= np.linalg.norm(binormal)

        out_normals = [normal]
        out_binormals = [binormal]

        for point, tangent in zip(points[1:], tangents[1:]):
            plane = PlaneEquation.from_normal_and_point(Vector(tangent), Vector(point))
            normal = plane.projection_of_vector(Vector(point), Vector(point + normal))
            normal = np.array(normal.normalized())
            binormal = np.cross(tangent, normal)
            binormal /= np.linalg.norm(binormal)
            out_normals.append(normal)
            out_binormals.append(binormal)

        self.quats = self._make_quats(points, tangents, np.array(out_normals), np.array(out_binormals))
        self.tknots = ts

    def evaluate_array(self, ts):
        """
        input: ts - np.array of snape (n,) or list of floats
        output: np.array of shape (n, 3, 3)
        """
        ts = np.array(ts)
        tknots, quats = self.tknots, self.quats
        base_indexes = tknots.searchsorted(ts, side='left')-1
        t1s, t2s = tknots[base_indexes], tknots[base_indexes+1]
        dts = (ts - t1s) / (t2s - t1s)
        #dts = np.clip(dts, 0.0, 1.0) # Just in case...
        matrix_out = []
        # TODO: ideally this shoulld be vectorized with numpy;
        # but that would require implementation of quaternion
        # interpolation in numpy.
        for dt, base_index in zip(dts, base_indexes):
            q1, q2 = quats[base_index], quats[base_index+1]
            # spherical linear interpolation.
            # TODO: implement `squad`.
            if dt < 0:
                q = q1
            elif dt > 1.0:
                q = q2
            else:
                q = q1.slerp(q2, dt)
            matrix = np.array(q.to_matrix())
            matrix_out.append(matrix)
        return np.array(matrix_out)

class MathutilsRotationCalculator(object):

    @classmethod
    def get_matrix(cls, tangent, scale, axis, algorithm, scale_all=True, up_axis='X'):
        """
        Calculate matrix required to rotate object according to `tangent` vector.
        inputs:
            * tangent - np.array of shape (3,)
            * scale - float
            * axis - int, 0 - X, 1 - Y, 2 - Z
            * algorithm - one of HOUSEHOLDER, TRACK, DIFF
            * scale_all - True to scale along all axes, False to scale along tangent only
            * up_axis - string, "X", "Y" or "Z", for algorithm == TRACK only.
        output:
            np.array of shape (3,3).
        """
        x = Vector((1.0, 0.0, 0.0))
        y = Vector((0.0, 1.0, 0.0))
        z = Vector((0.0, 0.0, 1.0))

        if axis == 0:
            ax1, ax2, ax3 = x, y, z
        elif axis == 1:
            ax1, ax2, ax3 = y, x, z
        else:
            ax1, ax2, ax3 = z, x, y

        if scale_all:
            scale_matrix = Matrix.Scale(1/scale, 4, ax1) @ Matrix.Scale(scale, 4, ax2) @ Matrix.Scale(scale, 4, ax3)
        else:
            scale_matrix = Matrix.Scale(1/scale, 4, ax1)
        scale_matrix = np.array(scale_matrix.to_3x3())

        tangent = Vector(tangent)
        if algorithm == HOUSEHOLDER:
            rot = autorotate_householder(ax1, tangent).inverted()
        elif algorithm == TRACK:
            axis = "XYZ"[axis]
            rot = autorotate_track(axis, tangent, up_axis)
        elif algorithm == DIFF:
            rot = autorotate_diff(tangent, ax1)
        else:
            raise Exception("Unsupported algorithm")
        rot = np.array(rot.to_3x3())

        return np.matmul(rot, scale_matrix)

class DifferentialRotationCalculator(object):

    def __init__(self, curve, algorithm, resolution=50):
        self.curve = curve
        self.algorithm = algorithm
        if algorithm == TRACK_NORMAL:
            self.normal_tracker = SvNormalTrack(curve, resolution)
        elif algorithm == ZERO:
            self.curve.pre_calc_torsion_integral(resolution)

    def get_matrices(self, ts):
        n = len(ts)
        if self.algorithm == FRENET:
            frenet, _ , _ = self.curve.frame_array(ts)
            return frenet
        elif self.algorithm == ZERO:
            frenet, _ , _ = self.curve.frame_array(ts)
            angles = - self.curve.torsion_integral(ts)
            zeros = np.zeros((n,))
            ones = np.ones((n,))
            row1 = np.stack((np.cos(angles), np.sin(angles), zeros)).T # (n, 3)
            row2 = np.stack((-np.sin(angles), np.cos(angles), zeros)).T # (n, 3)
            row3 = np.stack((zeros, zeros, ones)).T # (n, 3)
            rotation_matrices = np.dstack((row1, row2, row3))
            return frenet @ rotation_matrices
        elif self.algorithm == TRACK_NORMAL:
            matrices = self.normal_tracker.evaluate_array(ts)
            return matrices
        else:
            raise Exception("Unsupported algorithm")

class SvDeformedByFieldCurve(SvCurve):
    def __init__(self, curve, field, coefficient=1.0):
        self.curve = curve
        self.field = field
        self.coefficient = coefficient
        self.tangent_delta = 0.001
        self.__description__ = "{}({})".format(field, curve)

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

    def evaluate(self, t):
        v = self.curve.evaluate(t)
        vec = self.field.evaluate(*tuple(v))
        return v + self.coefficient * vec

    def evaluate_array(self, ts):
        vs = self.curve.evaluate_array(ts)
        xs, ys, zs = vs[:,0], vs[:,1], vs[:,2]
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        vecs = np.stack((vxs, vys, vzs)).T
        return vs + self.coefficient * vecs

class SvCastCurveToPlane(SvCurve):
    def __init__(self, curve, point, normal, coefficient):
        self.curve = curve
        self.point = point
        self.normal = normal
        self.coefficient = coefficient
        self.plane = PlaneEquation.from_normal_and_point(normal, point)
        self.tangent_delta = 0.001
        self.__description__ = "{} casted to Plane".format(curve)

    def evaluate(self, t):
        point = self.curve.evaluate(t)
        target = np.array(self.plane.projection_of_point(point))
        k = self.coefficient
        return (1 - k) * point + k * target

    def evaluate_array(self, ts):
        points = self.curve.evaluate_array(ts)
        targets = self.plane.projection_of_points(points)
        k = self.coefficient
        return (1 - k) * points + k * targets

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

class SvCastCurveToSphere(SvCurve):
    def __init__(self, curve, center, radius, coefficient):
        self.curve = curve
        self.center = center
        self.radius = radius
        self.coefficient = coefficient
        self.tangent_delta = 0.001
        self.__description__ = "{} casted to Sphere".format(curve)

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        points = self.curve.evaluate_array(ts)
        centered_points = points - self.center
        norms = np.linalg.norm(centered_points, axis=1)[np.newaxis].T
        normalized = centered_points / norms
        targets = self.radius * normalized + self.center
        k = self.coefficient
        return (1 - k) * points + k * targets

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

class SvCastCurveToCylinder(SvCurve):
    def __init__(self, curve, center, direction, radius, coefficient):
        self.curve = curve
        self.center = center
        self.direction = direction
        self.radius = radius
        self.coefficient = coefficient
        self.line = LineEquation.from_direction_and_point(direction, center)
        self.tangent_delta = 0.001
        self.__description__ = "{} casted to Cylinder".format(curve)

    def evaluate(self, t):
        point = self.curve.evaluate(t)
        projection_to_line = self.line.projection_of_point(point)
        projection_to_line = np.array(projection_to_line)
        radial = point - projection_to_line
        radius = self.radius * radial / np.linalg.norm(radial)
        projection = projection_to_line + radius
        k = self.coefficient
        return (1 - k) * point + k * projection

    def evaluate_array(self, ts):
        points = self.curve.evaluate_array(ts)
        projection_to_line = self.line.projection_of_points(points)
        radial = points - projection_to_line
        radius = self.radius * radial / np.linalg.norm(radial, axis=1, keepdims=True)
        projections = projection_to_line + radius
        k = self.coefficient
        return (1 - k) * points + k * projections

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

class SvCurveLerpCurve(SvCurve):
    __description__ = "Lerp"

    def __init__(self, curve1, curve2, coefficient):
        self.curve1 = curve1
        self.curve2 = curve2
        self.coefficient = coefficient
        self.u_bounds = (0.0, 1.0)
        self.c1_min, self.c1_max = curve1.get_u_bounds()
        self.c2_min, self.c2_max = curve2.get_u_bounds()
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        us1 = (self.c1_max - self.c1_min) * ts + self.c1_min
        us2 = (self.c2_max - self.c2_min) * ts + self.c2_min
        c1_points = self.curve1.evaluate_array(us1)
        c2_points = self.curve2.evaluate_array(us2)
        k = self.coefficient
        return (1.0 - k) * c1_points + k * c2_points

class SvOffsetCurve(SvCurve):

    BY_PARAMETER = 'T'
    BY_LENGTH = 'L'

    def __init__(self, curve, offset_vector,
                    offset_amount=None,
                    offset_curve = None, offset_curve_type = BY_PARAMETER,
                    algorithm=FRENET, resolution=50):
        self.curve = curve
        if algorithm == NORMAL_DIR and (offset_amount is None and offset_curve is None):
            raise Exception("offset_amount or offset_curve is mandatory if algorithm is NORMAL_DIR")
        self.offset_amount = offset_amount
        self.offset_vector = offset_vector
        self.offset_curve = offset_curve
        self.offset_curve_type = offset_curve_type
        self.algorithm = algorithm
        if algorithm in {FRENET, ZERO, TRACK_NORMAL}:
            self.calculator = DifferentialRotationCalculator(curve, algorithm, resolution)
        if offset_curve_type == SvOffsetCurve.BY_LENGTH:
            self.len_solver = SvCurveLengthSolver(curve)
            self.len_solver.prepare('SPL', resolution)
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

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

    def get_offset(self, ts):
        u_min, u_max = self.curve.get_u_bounds()
        if self.offset_curve is None:
            if self.offset_amount is not None:
                return self.offset_amount
            else:
                return np.linalg.norm(self.offset_vector)
        elif self.offset_curve_type == SvOffsetCurve.BY_PARAMETER:
            off_u_min, off_u_max = self.offset_curve.get_u_bounds()
            ts = (off_u_max - off_u_min) * (ts - u_min) / (u_max - u_min) + off_u_min
            ps = self.offset_curve.evaluate_array(ts)
            return ps[:,1][np.newaxis].T
        else:
            off_u_max = self.len_solver.get_total_length()
            ts = off_u_max * (ts - u_min) / (u_max - u_min)
            ts = self.len_solver.solve(ts)
            ps = self.offset_curve.evaluate_array(ts)
            return ps[:,1][np.newaxis].T

    def evaluate_array(self, ts):
        n = len(ts)
        t_min, t_max = self.curve.get_u_bounds()
        extrusion_start = self.curve.evaluate(t_min)
        extrusion_points = self.curve.evaluate_array(ts)
        extrusion_vectors = extrusion_points - extrusion_start
        offset_vector = self.offset_vector / np.linalg.norm(self.offset_vector)
        if self.algorithm == NORMAL_DIR:
            offset_vectors = np.tile(offset_vector[np.newaxis].T, n).T
            tangents = self.curve.tangent_array(ts)
            offset_vectors = np.cross(tangents, offset_vectors)
            offset_norm = np.linalg.norm(offset_vectors, axis=1, keepdims=True)
            offset_amounts = self.get_offset(ts)
            offset_vectors = offset_amounts * offset_vectors / offset_norm
        else:
            offset_vectors = np.tile(offset_vector[np.newaxis].T, n)
            matrices = self.get_matrices(ts)
            offset_amounts = self.get_offset(ts)
            offset_vectors = offset_amounts * (matrices @ offset_vectors)[:,:,0]
        result = extrusion_vectors + offset_vectors
        result = result + extrusion_start
        return result

class SvCurveOnSurface(SvCurve):
    def __init__(self, curve, surface, axis=0):
        self.curve = curve
        self.surface = surface
        self.axis = axis
        self.tangent_delta = 0.001
        self.__description__ = "{} on {}".format(curve, surface)

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        points = self.curve.evaluate_array(ts)
        xs = points[:,0]
        ys = points[:,1]
        zs = points[:,2]
        if self.axis == 0:
            us = ys
            vs = zs
        elif self.axis == 1:
            us = xs
            vs = zs
        elif self.axis == 2:
            us = xs
            vs = ys
        else:
            raise Exception("Unsupported orientation axis")
        return self.surface.evaluate_array(us, vs)

class SvCurveOffsetOnSurface(SvCurve):

    BY_PARAMETER = 'T'
    BY_LENGTH = 'L'

    def __init__(self, curve, surface, offset = None, offset_curve = None,
                    offset_curve_type = BY_PARAMETER, len_resolution = 50,
                    uv_space=False, axis=0):
        self.curve = curve
        self.surface = surface
        self.offset = offset
        self.offset_curve = offset_curve
        self.offset_curve_type = offset_curve_type
        self.uv_space = uv_space
        self.z_axis = axis
        self.tangent_delta = 0.001
        if offset_curve_type == SvCurveOffsetOnSurface.BY_LENGTH:
            self.len_solver = SvCurveLengthSolver(curve)
            self.len_solver.prepare('SPL', len_resolution)

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def get_offset(self, ts):
        u_min, u_max = self.curve.get_u_bounds()
        if self.offset_curve_type == SvCurveOffsetOnSurface.BY_PARAMETER:
            off_u_min, off_u_max = self.offset_curve.get_u_bounds()
            ts = (off_u_max - off_u_min) * (ts - u_min) / (u_max - u_min) + off_u_min
            ps = self.offset_curve.evaluate_array(ts)
            return ps[:,1]
        else:
            off_u_max = self.len_solver.get_total_length()
            ts = off_u_max * (ts - u_min) / (u_max - u_min)
            ts = self.len_solver.solve(ts)
            ps = self.offset_curve.evaluate_array(ts)
            return ps[:,1]

    def evaluate_array(self, ts):
        if self.z_axis == 2:
            U, V = 0, 1
        elif self.z_axis == 1:
            U, V = 0, 2
        else:
            U, V = 1, 2

        uv_points = self.curve.evaluate_array(ts)
        us, vs = uv_points[:,U], uv_points[:,V]
        # Tangents of the curve in surface's UV space
        uv_tangents = self.curve.tangent_array(ts) # (n, 3), with Z == 0 (Z is ignored anyway)
        tangents_u, tangents_v = uv_tangents[:,U], uv_tangents[:,V] # (n,), (n,)
        derivs = self.surface.derivatives_data_array(us, vs)
        su, sv = derivs.du, derivs.dv

        # Take surface's normals as N = [su, sv];
        # Take curve's tangent in 3D space as T = (tangents_u * su + tangents_v * sv);
        # Take a vector in surface's tangent plane, which is perpendicular to curve's
        # tangent, as Nc = [N, T] (call it "curve's normal on a surface");
        # Calculate Nc's decomposition in su, sv vectors as Ncu = (Nc, su) and Ncv = (Nc, sv);
        # Interpret Ncu and Ncv as coordinates of Nc in surface's UV space.

        # If you write down all above in formulas, you will have
        #
        # Nc = (Tu (Su, Sv) + Tv Sv^2) Su - (Tu Su^2 + Tv (Su, Sv)) Sv

        # We could've calculate the offset as (Curve on a surface) + (offset*Nc),
        # but there is no guarantee that these points will lie on the surface again
        # (especially with not-so-small values of offset).
        # So instead we calculate Curve + offset*(Ncu; Ncv) in UV space, and then
        # map all that into 3D space.

        su2 = (su*su).sum(axis=1) # (n,)
        sv2 = (sv*sv).sum(axis=1) # (n,)
        suv = (su*sv).sum(axis=1) # (n,)

        su_norm, sv_norm = derivs.tangent_lens()
        su_norm, sv_norm = su_norm.flatten(), sv_norm.flatten()

        delta_u =   (tangents_u*suv + tangents_v*sv2) # (n,)
        delta_v = - (tangents_u*su2 + tangents_v*suv) # (n,)

        delta_s = delta_u[np.newaxis].T * su + delta_v[np.newaxis].T * sv
        delta_s = np.linalg.norm(delta_s, axis=1)

        if self.offset_curve is None:
            offset = self.offset
        else:
            offset = self.get_offset(ts)

        res_us = us + delta_u * offset / delta_s
        res_vs = vs + delta_v * offset / delta_s

        if self.uv_space:
            zs = np.zeros_like(us)
            if self.z_axis == 2:
                result = np.stack((res_us, res_vs, zs)).T
            elif self.z_axis == 1:
                result = np.stack((res_us, zs, res_vs)).T
            else:
                result = np.stack((zs, res_us, res_vs)).T
            return result
        else:
            result = self.surface.evaluate_array(res_us, res_vs)
            # Just for testing
            # on_curve = self.surface.evaluate_array(us, vs)
            # dvs = result - on_curve
            # print(np.linalg.norm(dvs, axis=1))
            return result

class SvIsoUvCurve(SvCurve):
    def __init__(self, surface, fixed_axis, value, flip=False):
        self.surface = surface
        self.fixed_axis = fixed_axis
        self.value = value
        self.flip = flip
        self.tangent_delta = 0.001
        self.__description__ = "{} at {} = {}".format(surface, fixed_axis, value)

    def get_u_bounds(self):
        if self.fixed_axis == 'U':
            return self.surface.get_v_min(), self.surface.get_v_max()
        else:
            return self.surface.get_u_min(), self.surface.get_u_max()

    def evaluate(self, t):
        if self.fixed_axis == 'U':
            if self.flip:
                t = self.surface.get_v_max() - t + self.surface.get_v_min()
            return self.surface.evaluate(self.value, t)
        else:
            if self.flip:
                t = self.surface.get_u_max() - t + self.surface.get_u_min()
            return self.surface.evaluate(t, self.value)

    def evaluate_array(self, ts):
        if self.fixed_axis == 'U':
            if self.flip:
                ts = self.surface.get_v_max() - ts + self.surface.get_v_min()
            return self.surface.evaluate_array(np.repeat(self.value, len(ts)), ts)
        else:
            if self.flip:
                ts = self.surface.get_u_max() - ts + self.surface.get_u_min()
            return self.surface.evaluate_array(ts, np.repeat(self.value, len(ts)))

class SvLengthRebuiltCurve(SvCurve):
    def __init__(self, curve, resolution, mode='SPL'):
        self.curve = curve
        self.resolution = resolution
        if hasattr(curve, 'tangent_delta'):
            self.tangent_delta = curve.tangent_delta
        else:
            self.tangent_delta = 0.001
        self.mode = mode
        self.solver = SvCurveLengthSolver(curve)
        self.solver.prepare(self.mode, resolution)
        self.u_bounds = (0.0, self.solver.get_total_length())
        self.__description__ = "{} rebuilt".format(curve)

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        c_ts = self.solver.solve(np.array([t]))
        return self.curve.evaluate(c_ts[0])

    def evaluate_array(self, ts):
        c_ts = self.solver.solve(ts)
        return self.curve.evaluate_array(c_ts)

def curve_frame_on_surface_array(surface, uv_curve, us, w_axis=2, on_zero_curvature=SvCurve.ASIS):
    """
    Curve frame which is lying in the surface.

    Frame is oriented as follows:
        * X is pointing along surface normal
        * Z is pointing along curve tangent
        * Y is perpendicular to both X and Z.

    input:
        * surface
        * uv_curve - uv_curve in the surface's UV space
        * us - values of curve's T parameter; type: np.array of shape (n,)
        * w_axis - defines which axis of the curve is surface's normal (two
          other axes are surface's U and V). Default of 2 means X is U and Y is V.

    output: tuple:
        * matrices: np.array of shape (n, 3, 3)
        * points: np.array of shape (n, 3) - points on the surface
        * tangents: np.array of shape (n, 3)
        * normals: np.array of shape (n, 3)
        * binormals: np.array of shape (n, 3)
    """

    if w_axis == 2:
        U, V = 0, 1
    elif w_axis == 1:
        U, V = 0, 2
    else:
        U, V = 1, 2

    uv_points = uv_curve.evaluate_array(us)
    curve = SvCurveOnSurface(uv_curve, surface, axis=w_axis)
    surf_points = curve.evaluate_array(us)
    tangents = curve.tangent_array(us)
    tangents = tangents / np.linalg.norm(tangents, axis=1, keepdims=True)

    us, vs = uv_points[:,U], uv_points[:,V]
    normals = surface.normal_array(us, vs)
    normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)

    if on_zero_curvature != SvCurve.ASIS:
        zero_normal = np.linalg.norm(normals, axis=1) < 1e-6
        if zero_normal.any():
            if on_zero_curvature == SvCurve.FAIL:
                raise ZeroCurvatureException(np.unique(ts[zero_normal]), zero_normal)
            elif on_zero_curvature == SvCurve.RETURN_NONE:
                return None

    binormals = - np.cross(normals, tangents)
    matrices_np = np.dstack((normals, binormals, tangents))
    matrices_np = np.transpose(matrices_np, axes=(0,2,1))
    matrices_np = np.linalg.inv(matrices_np)
    return matrices_np, surf_points, tangents, normals, binormals

def concatenate_curves(curves, scale_to_unit=False):
    if not curves:
        raise Exception("List of curves must be not empty")
    result = [curves[0]]
    some_native = False
    for idx, curve in enumerate(curves[1:]):
        new_curve = None
        ok = False
        if hasattr(result[-1], 'concatenate'):
            try:
                if scale_to_unit:
                    # P.1: try to join with rescaled curve
                    new_curve = result[-1].concatenate(reparametrize_curve(curve))
                else:
                    new_curve = result[-1].concatenate(curve)
                some_native = True
                ok = True
            except UnsupportedCurveTypeException as e:
                # "concatenate" method can't work with this type of curve
                info("Can't natively join curve #%s (%s), will use generic method: %s", idx+1, curve, e)
                # P.2: if some curves were already joined natively,
                # then we have to rescale each of other curves separately
                if some_native and scale_to_unit:
                    curve = reparametrize_curve(curve)

        #print(f"C: {curve}, prev: {result[-1]}, ok: {ok}, new: {new_curve}")

        if ok:
            result[-1] = new_curve
        else:
            result.append(curve)

    if len(result) == 1:
        return result[0]
    else:
        # if any of curves were scaled while joining natively (at P.1),
        # then all other were scaled at P.2;
        # if no successfull joins were made, then we can rescale all curves
        # at once.
        return SvConcatCurve(result, scale_to_unit and not some_native)

def reparametrize_curve(curve, new_t_min=0.0, new_t_max=1.0):
    t_min, t_max = curve.get_u_bounds()
    if t_min == new_t_min and t_max == new_t_max:
        return curve
    if hasattr(curve, 'reparametrize'):
        return curve.reparametrize(new_t_min, new_t_max)
    else:
        return SvReparametrizedCurve(curve, new_t_min, new_t_max)

def reverse_curve(curve):
    if hasattr(curve, 'reverse'):
        return curve.reverse()
    else:
        return SvFlipCurve(curve)

def split_curve(curve, splits, rescale=False):
    if hasattr(curve, 'split_at'):
        result = []
        for split in splits:
            head, tail = curve.split_at(split)
            if rescale:
                head = reparametrize_curve(head, 0, 1)
            result.append(head)
            curve = tail
        if rescale:
            tail = reparametrize_curve(tail, 0, 1)
        result.append(tail)
        return result
    else:
        t_min, t_max = curve.get_u_bounds()
        if splits[0] != t_min:
            splits.insert(0, t_min)
        if splits[-1] != t_max:
            splits.append(t_max)
        pairs = zip(splits, splits[1:])
        result = []
        for start, end in pairs:
            segment = SvCurveSegment(curve, start, end, rescale)
            result.append(segment)
        return result

def curve_segment(curve, new_t_min, new_t_max, rescale=False):
    t_min, t_max = curve.get_u_bounds()
    if hasattr(curve, 'split_at') and (new_t_min > t_min or new_t_max < t_max):
        if new_t_min > t_min:
            start, curve = curve.split_at(new_t_min)
        if new_t_max < t_max:
            curve, end = curve.split_at(new_t_max)
        if rescale:
            curve = reparametrize_curve(curve, 0, 1)
        return curve
    else:
        return SvCurveSegment(curve, new_t_min, new_t_max, rescale)

def interpolate_nurbs_curve(cls, degree, points, metric='DISTANCE'):
    n = len(points)
    tknots = Spline.create_knots(points, metric=metric)
    knotvector = sv_knotvector.from_tknots(degree, tknots)
    functions = SvNurbsBasisFunctions(knotvector)
    coeffs_by_row = [functions.function(idx, degree)(tknots) for idx in range(n)]
    A = np.zeros((3*n, 3*n))
    for equation_idx, t in enumerate(tknots):
        for unknown_idx in range(n):
            coeff = coeffs_by_row[unknown_idx][equation_idx]
            row = 3*equation_idx
            col = 3*unknown_idx
            A[row,col] = A[row+1,col+1] = A[row+2,col+2] = coeff
    B = np.zeros((3*n,1))
    for point_idx, point in enumerate(points):
        row = 3*point_idx
        B[row:row+3] = point[:,np.newaxis]

    x = np.linalg.solve(A, B)

    control_points = []
    for i in range(n):
        row = i*3
        control = x[row:row+3,0].T
        control_points.append(control)
    control_points = np.array(control_points)
    weights = np.ones((n,))

    return cls.build(cls.get_nurbs_implementation(),
                degree, knotvector,
                control_points, weights)

