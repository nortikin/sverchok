# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from math import sin, cos, pi

from sverchok.utils.geom import PlaneEquation, LineEquation, LinearSpline, CubicSpline
from sverchok.utils.integrate import TrapezoidIntegral
from sverchok.utils.logging import error, exception

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
        if n >= 1:
            first = self.tangent_array(ts)
            result.append(first)

        h = 0.001
        if n >= 2:
            minus_h = self.evaluate_array(ts-h)
            points = self.evaluate_array(ts)
            plus_h = self.evaluate_array(ts+h)
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

    def frame_array(self, ts):
        tangents, normals, binormals = self.tangent_normal_binormal_array(ts)
        tangents = tangents / np.linalg.norm(tangents, axis=1)[np.newaxis].T
        matrices_np = np.dstack((normals, binormals, tangents))
        matrices_np = np.transpose(matrices_np, axes=(0,2,1))
        try:
            matrices_np = np.linalg.inv(matrices_np)
            return matrices_np, normals, binormals
        except np.linalg.LinAlgError as e:
            error("Some of matrices are singular:")
            for m in matrices_np:
                error("M:\n%s", m)
            raise e

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
        return self.curve.tangent(t)
        
    def tangent_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return self.curve.tangent_array(ts)

    def second_derivative_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return self.curve.second_derivative_array(ts)

    def third_derivative_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return self.curve.third_derivative_array(ts)

    def derivatives_array(self, ts):
        m, M = self.curve.get_u_bounds()
        ts = M - ts + m
        return self.curve.derivatives_array(ts)

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
        self.__description__ = "{}[{} .. {}]".format(curve, u_min, u_max)

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

class SvLambdaCurve(SvCurve):
    __description__ = "Formula"

    def __init__(self, function):
        self.function = function
        self.u_bounds = (0.0, 1.0)
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.function(t)

    def evaluate_array(self, ts):
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
        return (0.0, 1.0)

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

