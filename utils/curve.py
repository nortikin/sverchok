# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sin, cos, pi, radians, sqrt

from mathutils import Vector, Matrix

from sverchok.utils.geom import PlaneEquation, LineEquation, LinearSpline, CubicSpline, CircleEquation2D, CircleEquation3D, Ellipse3D
from sverchok.utils.integrate import TrapezoidIntegral
from sverchok.utils.logging import error, exception
from sverchok.utils.math import (
        binomial,
        ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL
    )
from sverchok.utils.geom import autorotate_householder, autorotate_track, autorotate_diff

##################
#                #
#  Curves        #
#                #
##################

def make_euclidian_ts(pts):
    tmp = np.linalg.norm(pts[:-1] - pts[1:], axis=1)
    tknots = np.insert(tmp, 0, 0).cumsum()
    tknots = tknots / tknots[-1]
    return tknots

class ZeroCurvatureException(Exception):
    def __init__(self, ts, mask=None):
        self.ts = ts
        self.mask = mask
        super(Exception, self).__init__(self.get_message())

    def get_message(self):
        return f"Curve has zero curvature at some points: {self.ts}"

class SvCurve(object):
    def __repr__(self):
        if hasattr(self, '__description__'):
            description = self.__description__
        else:
            description = self.__class__.__name__
        return "<{} curve>".format(description)

    def evaluate(self, t):
        raise Exception("not implemented!")

    def evaluate_array(self, ts):
        raise Exception("not implemented!")

    def calc_length(self, t_min, t_max, resolution = 50):
        ts = np.linspace(t_min, t_max, num=resolution)
        vectors = self.evaluate_array(ts)
        dvs = vectors[1:] - vectors[:-1]
        lengths = np.linalg.norm(dvs, axis=1)
        return np.sum(lengths)

    def tangent(self, t):
        v = self.evaluate(t)
        h = self.tangent_delta
        v_h = self.evaluate(t+h)
        return (v_h - v) / h

    def tangent_array(self, ts):
        vs = self.evaluate_array(ts)
        h = self.tangent_delta
        u_max = self.get_u_bounds()[1]
        bad_idxs = (ts+h) > u_max
        good_idxs = (ts+h) <= u_max
        ts_h = ts + h
        ts_h[bad_idxs] = (ts - h)[bad_idxs]

        vs_h = self.evaluate_array(ts_h)
        tangents_plus = (vs_h - vs) / h
        tangents_minus = (vs - vs_h) / h
        tangents_x = np.where(good_idxs, tangents_plus[:,0], tangents_minus[:,0])
        tangents_y = np.where(good_idxs, tangents_plus[:,1], tangents_minus[:,1])
        tangents_z = np.where(good_idxs, tangents_plus[:,2], tangents_minus[:,2])
        tangents = np.stack((tangents_x, tangents_y, tangents_z)).T
        return tangents

    def second_derivative(self, t):
        if hasattr(self, 'tangent_delta'):
            h = self.tangent_delta
        else:
            h = 0.001
        v0 = self.evaluate(t-h)
        v1 = self.evaluate(t)
        v2 = self.evaluate(t+h)
        return (v2 - 2*v1 + v0) / (h * h)

    def second_derivative_array(self, ts):
        h = 0.001
        v0s = self.evaluate_array(ts-h)
        v1s = self.evaluate_array(ts)
        v2s = self.evaluate_array(ts+h)
        return (v2s - 2*v1s + v0s) / (h * h)

    def third_derivative_array(self, ts):
        h = 0.001
        v0s = self.evaluate_array(ts)
        v1s = self.evaluate_array(ts+h)
        v2s = self.evaluate_array(ts+2*h)
        v3s = self.evaluate_array(ts+3*h)
        return (- v0s + 3*v1s - 3*v2s + v3s) / (h * h * h)

    def derivatives_array(self, n, ts):
        result = []
        N = len(ts)
        t_min, t_max = self.get_u_bounds()
        if n >= 1:
            first = self.tangent_array(ts)
            result.append(first)

        h = 0.001
        if n >= 2:
            low = ts < t_min + h
            high = ts > t_max - h
            good = np.logical_and(np.logical_not(low), np.logical_not(high))

            points = np.empty((N, 3))
            minus_h = np.empty((N, 3))
            plus_h = np.empty((N, 3))

            if good.any():
                minus_h[good] = self.evaluate_array(ts[good]-h)
                points[good] = self.evaluate_array(ts[good])
                plus_h[good] = self.evaluate_array(ts[good]+h)

            if low.any():
                minus_h[low] = self.evaluate_array(ts[low])
                points[low] = self.evaluate_array(ts[low]+h)
                plus_h[low] = self.evaluate_array(ts[low]+2*h)

            if high.any():
                minus_h[high] = self.evaluate_array(ts[high]-2*h)
                points[high] = self.evaluate_array(ts[high]-h)
                plus_h[high] = self.evaluate_array(ts[high])

            second = (plus_h - 2*points + minus_h) / (h * h)
            result.append(second)

        if n >= 3:
            v0s = points
            v1s = plus_h
            v2s = self.evaluate_array(ts+2*h)
            v3s = self.evaluate_array(ts+3*h)
            third = (- v0s + 3*v1s - 3*v2s + v3s) / (h * h * h)
            result.append(third)

        return result

    def main_normal(self, t, normalize=True):
        tangent = self.tangent(t)
        binormal = self.binormal(t, normalize)
        v = np.cross(binormal, tangent)
        if normalize:
            v = v / np.linalg.norm(v)
        return v

    def binormal(self, t, normalize=True):
        tangent = self.tangent(t)
        second = self.second_derivative(t)
        v = np.cross(tangent, second)
        if normalize:
            v = v / np.linalg.norm(v)
        return v

    def main_normal_array(self, ts, normalize=True):
        tangents = self.tangent_array(ts)
        binormals = self.binormal_array(ts, normalize)
        v = np.cross(binormals, tangents)
        if normalize:
            norms = np.linalg.norm(v, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            v[nonzero] = v[nonzero] / norms[nonzero][:,0][np.newaxis].T
        return v

    def binormal_array(self, ts, normalize=True):
        tangents, seconds = self.derivatives_array(2, ts)
        v = np.cross(tangents, seconds)
        if normalize:
            norms = np.linalg.norm(v, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            v[nonzero] = v[nonzero] / norms[nonzero][:,0][np.newaxis].T
        return v

    def tangent_normal_binormal_array(self, ts, normalize=True):
        tangents, seconds = self.derivatives_array(2, ts)
        binormals = np.cross(tangents, seconds)
        if normalize:
            norms = np.linalg.norm(binormals, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            binormals[nonzero] = binormals[nonzero] / norms[nonzero][:,0][np.newaxis].T
        normals = np.cross(binormals, tangents)
        if normalize:
            norms = np.linalg.norm(normals, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            normals[nonzero] = normals[nonzero] / norms[nonzero][:,0][np.newaxis].T
        return tangents, normals, binormals

    def arbitrary_frame_array(self, ts):
        normals = []
        binormals = []

        points = self.evaluate_array(ts)
        tangents = self.tangent_array(ts)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)

        for i, t in enumerate(ts):
            tangent = tangents[i]
            normal = np.array(Vector(tangent).orthogonal())
            binormal = np.cross(tangent, normal)
            binormal /= np.linalg.norm(binormal)
            normals.append(normal)
            binormals.append(binormal)

        normals = np.array(normals)
        binormals = np.array(binormals)

        matrices_np = np.dstack((normals, binormals, tangents))
        matrices_np = np.transpose(matrices_np, axes=(0,2,1))
        matrices_np = np.linalg.inv(matrices_np)
        return matrices_np, normals, binormals

    FAIL = 'fail'
    ASIS = 'asis'
    RETURN_NONE = 'none'

    def frame_array(self, ts, on_zero_curvature=ASIS):
        """
        input:
            * ts - np.array of shape (n,)
            * on_zero_curvature - what to do if the curve has zero curvature at one of T values.
              The supported options are:
              * SvCurve.FAIL: raise ZeroCurvatureException
              * SvCurve.RETURN_NONE: return None
              * SvCurve.ASIS: do not perform special check for this case, the
                algorithm wil raise a general LinAlgError exception if it can't calculate the matrix.

        output: tuple:
            * matrices: np.array of shape (n, 3, 3)
            * normals: np.array of shape (n, 3)
            * binormals: np.array of shape (n, 3)
        """
        tangents, normals, binormals = self.tangent_normal_binormal_array(ts)

        if on_zero_curvature != SvCurve.ASIS:
            zero_normal = np.linalg.norm(normals, axis=1) < 1e-6
            if zero_normal.any():
                if on_zero_curvature == SvCurve.FAIL:
                    raise ZeroCurvatureException(np.unique(ts[zero_normal]), zero_normal)
                elif on_zero_curvature == SvCurve.RETURN_NONE:
                    return None

        tangents = tangents / np.linalg.norm(tangents, axis=1)[np.newaxis].T
        matrices_np = np.dstack((normals, binormals, tangents))
        matrices_np = np.transpose(matrices_np, axes=(0,2,1))
        try:
            matrices_np = np.linalg.inv(matrices_np)
            return matrices_np, normals, binormals
        except np.linalg.LinAlgError as e:
            error("Some of matrices are singular:")
            for i, m in enumerate(matrices_np):
                if abs(np.linalg.det(m) < 1e-5):
                    error("M[%s] (t = %s):\n%s", i, ts[i], m)
            raise e

    def zero_torsion_frame_array(self, ts):
        """
        input: ts - np.array of shape (n,)
        output: tuple:
            * cumulative torsion - np.array of shape (n,) (rotation angles in radians)
            * matrices - np.array of shape (n, 3, 3)
        """
        if not hasattr(self, '_torsion_integral'):
            raise Exception("pre_calc_torsion_integral() has to be called first")

        vectors = self.evaluate_array(ts)
        matrices_np, normals, binormals = self.frame_array(ts)
        integral = self.torsion_integral(ts)
        new_matrices = []
        for matrix_np, point, angle in zip(matrices_np, vectors, integral):
            frenet_matrix = Matrix(matrix_np.tolist()).to_4x4()
            rotation_matrix = Matrix.Rotation(-angle, 4, 'Z')
            matrix = frenet_matrix @ rotation_matrix
            matrix.translation = Vector(point)
            new_matrices.append(matrix)

        return integral, new_matrices

    def curvature_array(self, ts):
        tangents, seconds = self.derivatives_array(2, ts)
        numerator = np.linalg.norm(np.cross(tangents, seconds), axis=1)
        tangents_norm = np.linalg.norm(tangents, axis=1)
        denominator = tangents_norm * tangents_norm * tangents_norm
        return numerator / denominator

    def torsion_array(self, ts):
        tangents, seconds, thirds = self.derivatives_array(3, ts)
        seconds_thirds = np.cross(seconds, thirds)
        numerator = (tangents * seconds_thirds).sum(axis=1)
        #numerator = np.apply_along_axis(lambda tangent: tangent.dot(seconds_thirds), 1, tangents)
        first_second = np.cross(tangents, seconds)
        denominator = np.linalg.norm(first_second, axis=1)
        return numerator / (denominator * denominator)

    def pre_calc_torsion_integral(self, resolution):
        t_min, t_max = self.get_u_bounds()
        ts = np.linspace(t_min, t_max, resolution)
        vectors = self.evaluate_array(ts)
        dvs = vectors[1:] - vectors[:-1]
        lengths = np.linalg.norm(dvs, axis=1)
        xs = np.insert(np.cumsum(lengths), 0, 0)
        ys = self.torsion_array(ts)
        self._torsion_integral = TrapezoidIntegral(ts, xs, ys)
        self._torsion_integral.calc()

    def torsion_integral(self, ts):
        return self._torsion_integral.evaluate_cubic(ts)

    def get_u_bounds(self):
        raise Exception("not implemented!")

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

class SvScalarFunctionCurve(SvCurve):
    __description__ = "Function"

    def __init__(self, function):
        self.function = function
        self.u_bounds = (0.0, 1.0)
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        y = self.function(t)
        return np.array([t, y, 0.0])

    def evaluate_array(self, ts):
        return np.vectorize(self.evaluate, signature='()->(3)')(ts)

class SvConcatCurve(SvCurve):
    def __init__(self, curves, scale_to_unit = False):
        self.curves = curves
        self.scale_to_unit = scale_to_unit
        bounds = [curve.get_u_bounds() for curve in curves]
        self.src_min_bounds = np.array([bound[0] for bound in bounds])
        self.ranges = np.array([bound[1] - bound[0] for bound in bounds])
        if scale_to_unit:
            self.u_max = float(len(curves))
            self.min_bounds = np.array(range(len(curves)), dtype=np.float64)
        else:
            self.u_max = self.ranges.sum()
            self.min_bounds = np.insert(np.cumsum(self.ranges), 0, 0)
        self.tangent_delta = 0.001
        self.__description__ = "Concat{}".format(curves)

    def get_u_bounds(self):
        return (0.0, self.u_max)

    def _get_ts_grouped(self, ts):
        index = self.min_bounds.searchsorted(ts, side='left') - 1
        index = index.clip(0, len(self.curves) - 1)
        left_bounds = self.min_bounds[index]
        curve_left_bounds = self.src_min_bounds[index]
        dts = ts - left_bounds + curve_left_bounds
        if self.scale_to_unit:
            dts = dts * self.ranges[index]
        #dts_grouped = np.split(dts, np.cumsum(np.unique(index, return_counts=True)[1])[:-1])
        # TODO: this should be vectorized somehow
        dts_grouped = []
        prev_i = None
        prev_dts = []

        for i, dt in zip(index, dts):
            if i == prev_i:
                prev_dts.append(dt)
            else:
                if prev_dts:
                    dts_grouped.append((prev_i, prev_dts[:]))
                    prev_dts = [dt]
                else:
                    prev_dts = [dt]
                    if prev_i is not None:
                        dts_grouped.append((prev_i, prev_dts[:]))
            prev_i = i

        if prev_dts:
            dts_grouped.append((i, prev_dts))

        return dts_grouped

    def evaluate(self, t):
        index = self.min_bounds.searchsorted(t, side='left') - 1
        index = index.clip(0, len(self.curves) - 1)
        left_bound = self.min_bounds[index]
        curve_left_bound = self.src_min_bounds[index]
        dt = t - left_bound + curve_left_bound
        return self.curves[index].evaluate(dt)

    def evaluate_array(self, ts):
        dts_grouped = self._get_ts_grouped(ts)
        points_grouped = [self.curves[i].evaluate_array(np.array(dts)) for i, dts in dts_grouped]
        return np.concatenate(points_grouped)

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        dts_grouped = self._get_ts_grouped(ts)
        tangents_grouped = [self.curves[i].tangent_array(np.array(dts)) for i, dts in dts_grouped]
        return np.concatenate(tangents_grouped)

    def second_derivative_array(self, ts):
        dts_grouped = self._get_ts_grouped(ts)
        vectors = [self.curves[i].second_derivative_array(np.array(dts)) for i, dts in dts_grouped]
        return np.concatenate(vectors)

    def third_derivative_array(self, ts):
        dts_grouped = self._get_ts_grouped(ts)
        vectors = [self.curves[i].third_derivative_array(np.array(dts)) for i, dts in dts_grouped]
        return np.concatenate(vectors)

    def derivatives_array(self, n, ts):
        dts_grouped = self._get_ts_grouped(ts)
        derivs = [self.curves[i].derivatives_array(n, np.array(dts)) for i, dts in dts_grouped]
        result = []
        for i in range(n):
            ith_derivs_grouped = [curve_derivs[i] for curve_derivs in derivs]
            ith_derivs = np.concatenate(ith_derivs_grouped)
            result.append(ith_derivs)
        return result

class SvFlipCurve(SvCurve):
    def __init__(self, curve):
        self.curve = curve
        if hasattr(curve, 'tangent_delta'):
            self.tangent_delta = curve.tangent_delta
        else:
            self.tangent_delta = 0.001
        self.__description__ = "Flip({})".format(curve)

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

    def evaluate(self, t):
        m, M = self.curve.get_u_bounds()
        t = M - t + m
        return self.curve.evaluate(t)

    def evaluate_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return self.curve.evaluate_array(ts)

    def tangent(self, t):
        m, M = self.curve.get_u_bounds()
        t = M - t + m
        return -self.curve.tangent(t)
        
    def tangent_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return - self.curve.tangent_array(ts)

    def second_derivative_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return self.curve.second_derivative_array(ts)

    def third_derivative_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return - self.curve.third_derivative_array(ts)

    def derivatives_array(self, n, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        derivs = self.curve.derivatives_array(n, ts)
        array = []
        sign = -1
        for deriv in derivs:
            array.append(sign * deriv)
            sign = -sign
        return array

class SvReparametrizedCurve(SvCurve):
    def __init__(self, curve, new_u_min, new_u_max):
        self.curve = curve
        self.new_u_min = new_u_min
        self.new_u_max = new_u_max
        if hasattr(curve, 'tangent_delta'):
            self.tangent_delta = curve.tangent_delta
        else:
            self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.new_u_min, self.new_u_max

    @property
    def scale(self):
        u_min, u_max = self.curve.get_u_bounds()
        return (u_max - u_min) / (self.new_u_max - self.new_u_min)

    def map_u(self, u):
        u_min, u_max = self.curve.get_u_bounds()
        return (u_max - u_min) * (u - self.new_u_min) / (self.new_u_max - self.new_u_min) + u_min

    def evaluate(self, t):
        return self.curve.evaluate(self.map_u(t))

    def evaluate_array(self, ts):
        return self.curve.evaluate_array(self.map_u(ts))

    def tangent(self, t):
        return self.scale * self.curve.tangent(self.map_u(t))

    def tangent_array(self, ts):
        return self.scale * self.curve.tangent_array(self.map_u(ts))

    def second_derivative_array(self, ts):
        return self.scale**2 * self.curve.second_derivative_array(self.map_u(ts))

    def third_derivative_array(self, ts):
        return self.scale**3 * self.curve.third_derivative_array(self.map_u(ts))

    def derivatives_array(self, n, ts):
        derivs = self.curve.derivatives_array(n, ts)
        k = self.scale
        array = []
        for deriv in derivs:
            array.append(k * deriv)
            k = k * self.scale
        return array

class SvCurveSegment(SvCurve):
    def __init__(self, curve, u_min, u_max, rescale=False):
        self.curve = curve
        if hasattr(curve, 'tangent_delta'):
            self.tangent_delta = curve.tangent_delta
        else:
            self.tangent_delta = 0.001
        self.rescale = rescale
        if self.rescale:
            self.u_bounds = (0.0, 1.0)
            self.target_u_bounds = (u_min, u_max)
        else:
            self.u_bounds = (u_min, u_max)
            self.target_u_bounds = (u_min, u_max)
        if hasattr(curve, '__description__'):
            curve_description = curve.__description__
        else:
            curve_description = repr(curve)
        self.__description__ = "{}[{} .. {}]".format(curve_description, u_min, u_max)

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        if self.rescale:
            m,M = self.target_u_bounds
            t = (M - m)*t + m
        return self.curve.evaluate(t)

    def evaluate_array(self, ts):
        if self.rescale:
            m,M = self.target_u_bounds
            ts = (M - m)*ts + m
        return self.curve.evaluate_array(ts)

    def tangent(self, t):
        if self.rescale:
            m,M = self.target_u_bounds
            t = (M - m)*t + m
        return self.curve.tangent(t)
        
    def tangent_array(self, ts):
        if self.rescale:
            m,M = self.target_u_bounds
            ts = (M - m)*ts + m
        return self.curve.tangent_array(ts)

    def second_derivative_array(self, ts):
        if self.rescale:
            m,M = self.target_u_bounds
            ts = (M - m)*ts + m
        return self.curve.second_derivative_array(ts)

    def third_derivative_array(self, ts):
        if self.rescale:
            m,M = self.target_u_bounds
            ts = (M - m)*ts + m
        return self.curve.third_derivative_array(ts)

    def derivatives_array(self, ts):
        if self.rescale:
            m,M = self.target_u_bounds
            ts = (M - m)*ts + m
        return self.curve.derivatives_array(ts)

class SvLine(SvCurve):
    __description__ = "Line"

    def __init__(self, point, direction):
        self.point = np.array(point)
        self.direction = np.array(direction)
        self.u_bounds = (0.0, 1.0)

    @classmethod
    def from_two_points(cls, point1, point2):
        direction = np.array(point2) - np.array(point1)
        return SvLine(point1, direction)

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.point + t * self.direction

    def evaluate_array(self, ts):
        ts = ts[np.newaxis].T
        return self.point + ts * self.direction

    def tangent(self, t):
        tg = self.direction
        n = np.linalg.norm(tg)
        return tg / n

    def tangent_array(self, ts):
        tg = self.direction
        n = np.linalg.norm(tg)
        tangent = tg / n
        result = np.tile(tangent[np.newaxis].T, len(ts)).T
        return result

class SvCircle(SvCurve):
    __description__ = "Circle"

    def __init__(self, matrix, radius):
        self.matrix = np.array(matrix.to_3x3())
        self.center = np.array(matrix.translation)
        self.radius = radius
        self.u_bounds = (0.0, 2*pi)

    @classmethod
    def from_equation(cls, eq):
        """
        Make an instance of SvCircle from an instance of CircleEquation2D/3D.
        """
        if isinstance(eq, CircleEquation2D):
            matrix = Matrix.Translation(eq.center)
            circle = SvCircle(matrix, eq.radius)
            return circle
        elif isinstance(eq, CircleEquation3D):
            circle = SvCircle(eq.get_matrix(), eq.radius)
            if eq.arc_angle:
                circle.u_bounds = (0, eq.arc_angle)
            return circle
        else:
            raise TypeError("Unsupported argument type:" + str(eq))

    @classmethod
    def from_arc(cls, arc):
        """
        Make an instance of SvCircle from an instance of sverchok.utils.sv_curve_utils.Arc
        """
        radius = abs(arc.radius)
        radius_dx = arc.radius.real / radius
        radius_dy = arc.radius.imag / radius
        matrix = Matrix.Translation(Vector((arc.center.real, arc.center.imag, 0)))
        scale_x = Matrix.Scale(radius_dx, 4, (1,0,0))
        scale_y = Matrix.Scale(radius_dy, 4, (0,1,0))
        rotation = radians(arc.theta)
        angle = radians(abs(arc.delta))
        rot_z = Matrix.Rotation(rotation, 4, 'Z')
        matrix = matrix @ scale_x @ scale_y @ rot_z
        if arc.delta < 0:
            matrix = matrix @ Matrix.Rotation(radians(180), 4, 'X')
        circle = SvCircle(matrix, radius)
        circle.u_bounds = (0, angle)
        return circle

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        r = self.radius
        x = r * cos(t)
        y = r * sin(t)
        return self.matrix @ np.array([x, y, 0]) + self.center

    def evaluate_array(self, ts):
        r = self.radius
        xs = r * np.cos(ts)
        ys = r * np.sin(ts)
        zs = np.zeros_like(xs)
        vertices = np.stack((xs, ys, zs)).T
        return np.apply_along_axis(lambda v: self.matrix @ v, 1, vertices) + self.center

    def tangent(self, t):
        x = - self.radius * sin(t)
        y = self.radius * cos(t)
        z = 0
        return self.matrix @ np.array([x, y, z])

    def tangent_array(self, ts):
        xs = - self.radius * np.sin(ts)
        ys = self.radius * np.cos(ts)
        zs = np.zeros_like(xs)
        vectors = np.stack((xs, ys, zs)).T
        result = np.apply_along_axis(lambda v: self.matrix @ v, 1, vectors)
        return result

#     def second_derivative_array(self, ts):
#         xs = - np.cos(ts)
#         ys = - np.sin(ts)
#         zs = np.zeros_like(xs)
#         vectors = np.stack((xs, ys, zs)).T
#         return np.apply_along_axis(lambda v: self.matrix @ v, 1, vectors)

class SvEllipse(SvCurve):
    __description__ = "Ellipse"
     
    CENTER = 'center'
    F1 = 'f1'
    F2 = 'f2'

    def __init__(self, matrix, a, b, center_type=CENTER):
        self.matrix = np.array(matrix.to_3x3())
        self.center = np.array(matrix.translation)
        self.center_type = center_type
        self.a = a
        self.b = b
        self.u_bounds = (0, 2*pi)
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.u_bounds

    @classmethod
    def from_equation(cls, eq):
        """
        input: an instance of sverchok.utils.geom.Ellipse3D
        output: an instance of SvEllipse
        """
        return SvEllipse(eq.get_matrix(), eq.a, eq.b)

    def to_equation(self):
        """
        output: an instance of sverchok.utils.geom.Ellipse3D
        """
        major_radius = self.matrix @ np.array([self.a, 0, 0])
        minor_radius = self.matrix @ np.array([0, self.b, 0])
        eq = Ellipse3D(Vector(self.center), Vector(major_radius), Vector(minor_radius))
        return eq

    @property
    def c(self):
        a, b = self.a, self.b
        return sqrt(a*a - b*b)

    def focal_points(self):
        df = self.matrix @ np.array([self.c, 0, 0])
        f1 = self.center + df
        f2 = self.center - df
        return [f1, f2]

    def get_center(self):
        if self.center_type == SvEllipse.CENTER:
            return self.center
        elif self.center_type == SvEllipse.F1:
            df = self.matrix @ np.array([self.c, 0, 0])
            return self.center + df
        else: # F2
            df = self.matrix @ np.array([self.c, 0, 0])
            return self.center - df

    def evaluate(self, t):
        v = np.array([self.a * cos(t), self.b * sin(t), 0])
        center = self.get_center()
        v = center + self.matrix @ v
        return v

    def evaluate_array(self, ts):
        xs = self.a * np.cos(ts)
        ys = self.b * np.sin(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        center = self.get_center()
        return center + vs

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        xs = - self.a * np.sin(ts)
        ys = self.b * np.cos(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        return vs

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        xs = - self.a * np.cos(ts)
        ys = - self.b * np.sin(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        return vs

class SvLambdaCurve(SvCurve):
    __description__ = "Formula"

    def __init__(self, function, function_numpy = None):
        self.function = function
        self.function_numpy = function_numpy
        self.u_bounds = (0.0, 1.0)
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.function(t)

    def evaluate_array(self, ts):
        if self.function_numpy is not None:
            return self.function_numpy(ts)
        else:
            return np.vectorize(self.function, signature='()->(3)')(ts)

    def tangent(self, t):
        point = self.function(t)
        point_h = self.function(t+self.tangent_delta)
        return (point_h - point) / self.tangent_delta

    def tangent_array(self, ts):
        points = np.vectorize(self.function, signature='()->(3)')(ts)
        points_h = np.vectorize(self.function, signature='()->(3)')(ts+self.tangent_delta)
        return (points_h - points) / self.tangent_delta

class SvSplineCurve(SvCurve):
    __description__ = "Spline"

    def __init__(self, spline):
        self.spline = spline
        self.u_bounds = (0.0, 1.0)

    @classmethod
    def from_points(cls, points, metric=None, is_cyclic=False):
        if not points or len(points) < 2:
            raise Exception("At least two points are required")
        if len(points) < 3:
            return SvLine.from_two_points(points[0], points[1])
        spline = CubicSpline(points, metric=metric, is_cyclic=is_cyclic)
        return SvSplineCurve(spline)

    def evaluate(self, t):
        v = self.spline.eval_at_point(t)
        return np.array(v)

    def evaluate_array(self, ts):
        vs = self.spline.eval(ts)
        return np.array(vs)

    def tangent(self, t):
        vs = self.spline.tangent(np.array([t]))
        return vs[0]

    def tangent_array(self, ts):
        return self.spline.tangent(ts)

    def get_u_bounds(self):
        return self.u_bounds

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
    def __init__(self, curve, offset_vector, algorithm, resolution=50):
        self.curve = curve
        self.offset_vector = offset_vector
        self.algorithm = algorithm
        if algorithm in {FRENET, ZERO, TRACK_NORMAL}:
            self.calculator = DifferentialRotationCalculator(curve, algorithm, resolution)
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

    def evaluate_array(self, ts):
        n = len(ts)
        t_min, t_max = self.curve.get_u_bounds()
        profile_vectors = np.tile(self.offset_vector[np.newaxis].T, n)
        #profile_vectors = np.transpose(profile_vectors[np.newaxis], axes=(1, 2, 0))
        extrusion_start = self.curve.evaluate(t_min)
        extrusion_points = self.curve.evaluate_array(ts)
        extrusion_vectors = extrusion_points - extrusion_start
        matrices = self.get_matrices(ts)
        profile_vectors = (matrices @ profile_vectors)[:,:,0]
        result = extrusion_vectors + profile_vectors
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
    def __init__(self, curve, surface, offset, uv_space=False):
        self.curve = curve
        self.surface = surface
        self.offset = offset
        self.uv_space = uv_space
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        uv_points = self.curve.evaluate_array(ts)
        us, vs = uv_points[:,0], uv_points[:,1]
        # Tangents of the curve in surface's UV space
        uv_tangents = self.curve.tangent_array(ts) # (n, 3), with Z == 0 (Z is ignored anyway)
        tangents_u, tangents_v = uv_tangents[:,0], uv_tangents[:,1] # (n,), (n,)
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
        k = self.offset / delta_s

        res_us = us + delta_u * k
        res_vs = vs + delta_v * k

        if self.uv_space:
            zs = np.zeros_like(us)
            result = np.stack((res_us, res_vs, zs)).T
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

class SvBezierCurve(SvCurve):
    """
    Bezier curve of arbitrary degree.
    """
    def __init__(self, points):
        self.points = points
        self.tangent_delta = 0.001
        n = self.degree = len(points) - 1
        self.__description__ = "Bezier[{}]".format(n)

    @classmethod
    def from_points_and_tangents(cls, p0, t0, t1, p1):
        """
        Build cubic Bezier curve, which goes from p0 to p1,
        and has tangent at 0 equal to t0 and tangent at 1 equal to t1.
        This is also called Hermite spline.

        inputs: p0, t0, t1, p1 - numpy arrays of shape (3,).
        """
        return SvCubicBezierCurve(
                p0,
                p0 + t0 / 3.0,
                p1 - t1 / 3.0,
                p1)

    @classmethod
    def blend_second_derivatives(cls, p0, v0, a0, p5, v5, a5):
        """
        Build Bezier curve of 5th order, which goes from p0 to p5, and has:
        * first derivative at 0 = v0, second derivative at 0 = a0;
        * first derivative at 1 = v5, second derivative at 1 = a1.

        inputs: numpy arrays of shape (3,).
        """
        p1 = p0 + v0 / 5.0
        p4 = p5 - v5 / 5.0
        p2 = a0/20.0 + 2*p1 - p0
        p3 = a5/20.0 + 2*p4 - p5
        return SvBezierCurve([p0, p1, p2, p3, p4, p5])

    @classmethod
    def blend_third_derivatives(cls, p0, v0, a0, k0, p7, v7, a7, k7):
        """
        Build Bezier curve of 7th order, which goes from p0 to p7, and has:
        * first derivative at 0 = v0, second derivative at 0 = a0, third derivative at 0 = k0;
        * first derivative at 1 = v7, second derivative at 1 = a7, third derivative at 1 = k7.

        inputs: numpy arrays of shape (3,).
        """
        p1 = p0 + v0 / 7.0
        p6 = p7 - v7 / 7.0
        p2 = a0/42.0 + 2*p1 - p0
        p5 = a7/42.0 + 2*p6 - p7
        p3 = k0/210.0 + 3*p2 - 3*p1 + p0
        p4 = -k7/210.0 + 3*p5 - 3*p6 + p7
        return SvBezierCurve([p0, p1, p2, p3, p4, p5, p6, p7])

    @classmethod
    def coefficient(cls, n, k, ts):
        C = binomial(n, k)
        return C * ts**k * (1 - ts)**(n-k)

    def coeff(self, k, ts):
        n = self.degree
        return SvBezierCurve.coefficient(n, k, ts)

    def coeff_deriv1(self, k, t):
        n = self.degree
        C = binomial(n, k)
        if k >= 1:
            s1 = k*(1-t)**(n-k)*t**(k-1) 
        else:
            s1 = np.zeros_like(t)
        if n-k-1 > 0:
            s2 = - (n-k)*(1-t)**(n-k-1)*t**k
        elif n-k == 1:
            s2 = - t**k
        else:
            s2 = np.zeros_like(t)
        coeff = s1 + s2
        return C*coeff

    def coeff_deriv2(self, k, t):
        n = self.degree
        C = binomial(n, k)
        if n-k-2 > 0:
            s1 = (n-k-1)*(n-k)*(1-t)**(n-k-2)*t**k
        elif n-k == 2:
            s1 = 2*t**k
        else:
            s1 = np.zeros_like(t)
        if k >= 1 and n-k-1 > 0:
            s2 = - 2*k*(n-k)*(1-t)**(n-k-1)*t**(k-1)
        elif k >= 1 and n-k == 1:
            s2 = - 2*k*t**(k-1)
        else:
            s2 = np.zeros_like(t)
        if k >= 2:
            s3 = (k-1)*k*(1-t)**(n-k)*t**(k-2)
        else:
            s3 = np.zeros_like(t)
        coeff = s1 + s2 + s3
        return C*coeff

    def coeff_deriv3(self, k, t):
        n = self.degree
        C = binomial(n, k)
        if n-k-2 > 0:
            s1 = -(n-k-2)*(n-k-1)*(n-k)*(1-t)**(n-k-3)*t**k
        else:
            s1 = np.zeros_like(t)
        if k >= 1 and n-k-2 > 0:
            s2 = 3*k*(n-k-1)*(n-k)*(1-t)**(n-k-2)*t**(k-1)
        elif k >= 1 and n-k == 2:
            s2 = 6*k*t**(k-1)
        else:
            s2 = np.zeros_like(t)
        if k >= 2 and n-k-1 > 0:
            s3 = - 3*(k-1)*k*(n-k)*(1-t)**(n-k-1)*t**(k-2)
        elif k >= 2 and n-k == 1:
            s3 = -3*(k-1)*k*t**(k-2)
        else:
            s3 = np.zeros_like(t)
        if k >= 3:
            s4 = (k-2)*(k-1)*k*(1-t)**(n-k)*t**(k-3)
        else:
            s4 = np.zeros_like(t)
        coeff = s1 + s2 + s3 + s4
        return C*coeff

    def get_u_bounds(self):
        return (0.0, 1.0)

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        coeffs = [SvBezierCurve.coefficient(self.degree, k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        return np.dot(coeffs.T, self.points)

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        coeffs = [self.coeff_deriv1(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C1", coeffs)
        return np.dot(coeffs.T, self.points)

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        coeffs = [self.coeff_deriv2(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C2", coeffs)
        return np.dot(coeffs.T, self.points)

    def third_derivative_array(self, ts):
        coeffs = [self.coeff_deriv3(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C3", coeffs)
        return np.dot(coeffs.T, self.points)

    def derivatives_array(self, n, ts):
        result = []
        if n >= 1:
            first = self.tangent_array(ts)
            result.append(first)
        if n >= 2:
            second = self.second_derivative_array(ts)
            result.append(second)
        if n >= 3:
            third = self.third_derivative_array(ts)
            result.append(third)
        return result

class SvCubicBezierCurve(SvCurve):
    __description__ = "Bezier[3*]"
    def __init__(self, p0, p1, p2, p3):
        self.p0 = np.array(p0)
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)
        self.p3 = np.array(p3)
        self.tangent_delta = 0.001

    @classmethod
    def from_four_points(cls, v0, v1, v2, v3):
        v0 = np.array(v0)
        v1 = np.array(v1)
        v2 = np.array(v2)
        v3 = np.array(v3)

        p1 = (-5*v0 + 18*v1 - 9*v2 + 2*v3)/6.0
        p2 = (2*v0 - 9*v1 + 18*v2 - 5*v3)/6.0

        return SvCubicBezierCurve(v0, p1, p2, v3)

    def get_u_bounds(self):
        return (0.0, 1.0)

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        c0 = (1 - ts)**3
        c1 = 3*ts*(1-ts)**2
        c2 = 3*ts**2*(1-ts)
        c3 = ts**3
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        c0 = -3*(1 - ts)**2
        c1 = 3*(1-ts)**2 - 6*(1-ts)*ts
        c2 = 6*(1-ts)*ts - 3*ts**2
        c3 = 3*ts**2
        #print("C/C1", np.array([c0, c1, c2, c3]))
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        c0 = 6*(1-ts)
        c1 = 6*ts - 12*(1-ts)
        c2 = 6*(1-ts) - 12*ts
        c3 = 6*ts
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def third_derivative_array(self, ts):
        c0 = np.full_like(ts, -6)[:,np.newaxis]
        c1 = np.full_like(ts, 18)[:,np.newaxis]
        c2 = np.full_like(ts, -18)[:,np.newaxis]
        c3 = np.full_like(ts, 6)[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3
        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def derivatives_array(self, n, ts):
        result = []
        if n >= 1:
            first = self.tangent_array(ts)
            result.append(first)
        if n >= 2:
            second = self.second_derivative_array(ts)
            result.append(second)
        if n >= 3:
            third = self.third_derivative_array(ts)
            result.append(third)
        return result

class SvTaylorCurve(SvCurve):
    __description__ = "Taylor"

    def __init__(self, start, derivatives):
        self.start = start
        self.derivatives = np.array(derivatives)
        self.u_bounds = (0, 1.0)

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        result = self.start
        denom = 1
        for i, vec in enumerate(self.derivatives):
            result = result + t**(i+1) * vec / denom
            denom *= (i+1)
        return result
    
    def evaluate_array(self, ts):
        n = len(ts)
        result = np.broadcast_to(self.start, (n, 3))
        denom = 1
        ts = ts[np.newaxis].T
        for i, vec in enumerate(self.derivatives):
            result = result + ts**(i+1) * vec / denom
            denom *= (i+1)
        return result

    def tangent(self, t):
        result = np.array([0, 0, 0])
        denom = 1
        for i, vec in enumerate(self.derivatives):
            result = result + (i+1)*t**i * vec / denom
            denom *= (i+1)
        return result

    def tangent_array(self, ts):
        n = len(ts)
        result = np.zeros((n, 3))
        denom = 1
        ts = ts[np.newaxis].T
        for i, vec in enumerate(self.derivatives):
            result = result + (i+1)*ts**i * vec / denom
            denom *= (i+1)
        return result

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        n = len(ts)
        result = np.zeros((n, 3))
        denom = 1
        ts = ts[np.newaxis].T
        for k, vec in enumerate(self.derivatives[1:]):
            i = k+1
            result = result + (i+1)*i*ts**(i-1) * vec / denom
            denom *= (i+1)
        return result

    def third_derivative_array(self, ts):
        n = len(ts)
        result = np.zeros((n, 3))
        denom = 1
        ts = ts[np.newaxis].T
        for k, vec in enumerate(self.derivatives[2:]):
            i = k+2
            result = result + (i+1)*i*(i-1)*ts**(i-2) * vec / denom
            denom *= (i+1)
        return result

