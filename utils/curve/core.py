# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sin, cos, pi, radians, sqrt

from mathutils import Vector, Matrix

from sverchok.utils.geom import LineEquation, CubicSpline
from sverchok.utils.integrate import TrapezoidIntegral
from sverchok.utils.logging import info, error

class ZeroCurvatureException(Exception):
    def __init__(self, ts, mask=None):
        self.ts = ts
        self.mask = mask
        super(Exception, self).__init__(self.get_message())

    def get_message(self):
        return f"Curve has zero curvature at some points: {self.ts}"

class UnsupportedCurveTypeException(TypeError):
    pass

##################
#                #
#  Curves        #
#                #
##################

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

    def third_derivative(self, t):
        return self.third_derivative_array(np.array([t]))[0]

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

    def frame_by_plane_array(self, ts, plane_normal):
        n = len(ts)
        tangents = self.tangent_array(ts)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
        plane_normals = np.tile(plane_normal[np.newaxis].T, n).T
        normals = np.cross(tangents, plane_normals)
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        binormals = np.cross(tangents, normals)

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

    def get_degree(self):
        raise Exception("`Get Degree' method is not applicable to curve of type `{}'".format(type(self)))

    def get_control_points(self):
        """
        Returns: np.array of shape (n, 3)
        """
        return np.array([])
        #raise Exception("Curve of type type `{}' does not have control points".format(type(self)))

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
    
    def __repr__(self):
        return "+".join([str(curve) for curve in self.curves])

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

    def __repr__(self):
        return f"Flip {self.curve}"

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

    def __repr__(self):
        return f"{self.curve}::[{self.new_u_min}..{self.new_u_max}]"

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

    def __repr__(self):
        if hasattr(self.curve, '__description__'):
            curve_description = self.curve.__description__
        else:
            curve_description = repr(self.curve)
        u_min, u_max = self.u_bounds
        return "{}[{} .. {}]".format(curve_description, u_min, u_max)

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

