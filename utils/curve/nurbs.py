# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.nurbs_common import nurbs_divide, SvNurbsBasisFunctions, elevate_bezier_degree, from_homogenous
from sverchok.utils.surface.nurbs import SvNativeNurbsSurface, SvGeomdlSurface
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS, BSpline, operations

##################
#                #
#  Curves        #
#                #
##################

class SvNurbsCurve(SvCurve):
    """
    Base abstract class for all supported implementations of NURBS curves.
    """
    NATIVE = 'NATIVE'
    GEOMDL = 'GEOMDL'

    @classmethod
    def build(cls, implementation, degree, knotvector, control_points, weights=None, normalize_knots=False):
        kv_error = sv_knotvector.check(degree, knotvector, len(control_points))
        if kv_error is not None:
            raise Exception(kv_error)
        if implementation == SvNurbsCurve.NATIVE:
            if normalize_knots:
                knotvector = sv_knotvector.normalize(knotvector)
            return SvNativeNurbsCurve(degree, knotvector, control_points, weights)
        elif implementation == SvNurbsCurve.GEOMDL and geomdl is not None:
            return SvGeomdlCurve.build(degree, knotvector, control_points, weights, normalize_knots)
        else:
            raise Exception(f"Unsupported NURBS Curve implementation: {implementation}")

    @classmethod
    def to_nurbs(cls, curve, implementation = NATIVE):
        if isinstance(curve, SvNurbsCurve):
            return curve
        if hasattr(curve, 'to_nurbs'):
            return curve.to_nurbs(implementation = implementation)
        return None

    def get_nurbs_implementation(self):
        raise Exception("Not defined")

    def get_control_points(self):
        """
        returns: np.array of shape (k, 3)
        """
        raise Exception("Not implemented!")

    def get_weights(self):
        """
        returns: np.array of shape (k,)
        """
        raise Exception("Not implemented!")

    def get_homogenous_control_points(self):
        """
        returns: np.array of shape (k, 4)
        """
        points = self.get_control_points()
        weights = self.get_weights()[np.newaxis].T
        weighted = weights * points
        return np.concatenate((weighted, weights), axis=1)

    def is_bezier(self):
        k = len(self.get_control_points())
        p = self.get_degree()
        return p+1 == k

    def get_knotvector(self):
        """
        returns: np.array of shape (X,)
        """
        raise Exception("Not implemented!")

    def get_degree(self):
        raise Exception("Not implemented!")

    def elevate_degree(self, delta=1):
        if self.is_bezier():
            control_points = self.get_homogenous_control_points()
            degree = self.get_degree()
            control_points = elevate_bezier_degree(degree, control_points, delta)
            control_points, weights = from_homogenous(control_points)
            knotvector = self.get_knotvector()
            knotvector = sv_knotvector.elevate_degree(knotvector, delta)
            return SvNurbsCurve.build(self.get_nurbs_implementation(),
                    degree+delta, knotvector, control_points, weights)
        else:
            raise Exception("Not implemented yet!")

    def insert_knot(self, u, count=1):
        raise Exception("Not implemented!")

class SvGeomdlCurve(SvNurbsCurve):
    """
    geomdl-based implementation of NURBS curves
    """
    def __init__(self, curve):
        self.curve = curve
        self.u_bounds = (0.0, 1.0)
        self.__description__ = f"Geomdl NURBS (degree={curve.degree}, pts={len(curve.ctrlpts)})"

    @classmethod
    def build(cls, degree, knotvector, control_points, weights=None, normalize_knots=False):
        if weights is not None:
            curve = NURBS.Curve(normalize_kv = normalize_knots)
        else:
            curve = BSpline.Curve(normalize_kv = normalize_knots)
        curve.degree = degree
        if isinstance(control_points, np.ndarray):
            control_points = control_points.tolist()
        curve.ctrlpts = control_points
        if weights is not None:
            if isinstance(weights, np.ndarray):
                weights = weights.tolist()
            curve.weights = weights
        if isinstance(knotvector, np.ndarray):
            knotvector = knotvector.tolist()
        curve.knotvector = knotvector
        return SvGeomdlCurve(curve)

    @classmethod
    def from_any_nurbs(cls, curve):
        if not isinstance(curve, SvNurbsCurve):
            raise TypeError("Invalid surface type")
        if isinstance(curve, SvGeomdlCurve):
            return curve
        return SvGeomdlCurve.build(curve.get_degree(), curve.get_knotvector(),
                    curve.get_control_points(), 
                    curve.get_weights())

    def get_nurbs_implementation(self):
        return SvNurbsCurve.GEOMDL

    def get_control_points(self):
        return np.array(self.curve.ctrlpts)

    def get_weights(self):
        if self.curve.weights is not None:
            return np.array(self.curve.weights)
        else:
            k = len(self.curve.ctrlpts)
            return np.ones((k,))

    def get_knotvector(self):
        return np.array(self.curve.knotvector)

    def get_degree(self):
        return self.curve.degree

    def evaluate(self, t):
        v = self.curve.evaluate_single(t)
        return np.array(v)

    def evaluate_array(self, ts):
        t_min, t_max = self.get_u_bounds()
        ts[ts < t_min] = t_min
        ts[ts > t_max] = t_max
        vs = self.curve.evaluate_list(list(ts))
        return np.array(vs)

    def tangent(self, t):
        p, t = operations.tangent(self.curve, t, normalize=False)
        return np.array(t)

    def tangent_array(self, ts):
        t_min, t_max = self.get_u_bounds()
        ts[ts < t_min] = t_min
        ts[ts > t_max] = t_max
        vs = operations.tangent(self.curve, list(ts), normalize=False)
        tangents = [t[1] for t in vs]
        #print(f"ts: {ts}, vs: {tangents}")
        return np.array(tangents)

    def second_derivative(self, t):
        p, first, second = self.curve.derivatives(t, order=2)
        return np.array(second)

    def second_derivative_array(self, ts):
        return np.vectorize(self.second_derivative, signature='()->(3)')(ts)

    def third_derivative(self, t):
        p, first, second, third = self.curve.derivatives(t, order=3)
        return np.array(third)

    def third_derivative_array(self, ts):
        return np.vectorize(self.third_derivative, signature='()->(3)')(ts)

    def derivatives_array(self, n, ts):
        def derivatives(t):
            result = self.curve.derivatives(t, order=n)
            return np.array(result[1:])
        result = np.vectorize(derivatives, signature='()->(n,3)')(ts)
        result = np.transpose(result, axes=(1, 0, 2))
        return result

    def get_u_bounds(self):
        return self.u_bounds

    def extrude_along_vector(self, vector):
        vector = np.array(vector)
        my_control_points = self.get_control_points()
        my_weights = self.get_weights()
        other_control_points = my_control_points + vector
        control_points = np.stack((my_control_points, other_control_points))
        control_points = np.transpose(control_points, axes=(1,0,2)).tolist()
        weights = np.stack((my_weights, my_weights)).T.tolist()
        my_knotvector = self.get_knotvector()
        my_degree = self.get_degree()
        knotvector_v = sv_knotvector.generate(1, 2, clamped=True)
        surface = SvGeomdlSurface.build(degree_u = my_degree, degree_v = 1,
                        knotvector_u = my_knotvector, knotvector_v = knotvector_v,
                        control_points = control_points,
                        weights = weights)
        return surface

    def insert_knot(self, u, count=1):
        curve = operations.insert_knot(self.curve, [u], [count])
        return SvGeomdlCurve(curve)

class SvNativeNurbsCurve(SvNurbsCurve):
    def __init__(self, degree, knotvector, control_points, weights=None):
        self.control_points = np.array(control_points) # (k, 3)
        k = len(control_points)
        if weights is not None:
            self.weights = np.array(weights) # (k, )
        else:
            self.weights = np.ones((k,))
        self.knotvector = np.array(knotvector)
        self.degree = degree
        self.basis = SvNurbsBasisFunctions(knotvector)
        self.tangent_delta = 0.001
        self.__description__ = f"Native NURBS (degree={degree}, pts={k})"

    def get_control_points(self):
        return self.control_points

    def get_weights(self):
        return self.weights

    def get_knotvector(self):
        return self.knotvector

    def get_degree(self):
        return self.degree

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def fraction(self, deriv_order, ts):
        n = len(ts)
        p = self.degree
        k = len(self.control_points)
        ns = np.array([self.basis.derivative(i, p, deriv_order)(ts) for i in range(k)]) # (k, n)
        coeffs = ns * self.weights[np.newaxis].T # (k, n)
        coeffs_t = coeffs[np.newaxis].T # (n, k, 1)
        numerator = (coeffs_t * self.control_points) # (n, k, 3)
        numerator = numerator.sum(axis=1) # (n, 3)
        denominator = coeffs.sum(axis=0) # (n,)

        return numerator, denominator[np.newaxis].T

    def evaluate_array(self, ts):
        numerator, denominator = self.fraction(0, ts)
#         if (denominator == 0).any():
#             print("Num:", numerator)
#             print("Denom:", denominator)
        return nurbs_divide(numerator, denominator)

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        # curve = numerator / denominator
        # ergo:
        # numerator = curve * denominator
        # ergo:
        # numerator' = curve' * denominator + curve * denominator'
        # ergo:
        # curve' = (numerator' - curve*denominator') / denominator
        numerator, denominator = self.fraction(0, ts)
        curve = numerator / denominator
        numerator1, denominator1 = self.fraction(1, ts)
        curve1 = (numerator1 - curve*denominator1) / denominator
        return curve1

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        # numerator'' = (curve * denominator)'' =
        #  = curve'' * denominator + 2 * curve' * denominator' + curve * denominator''
        numerator, denominator = self.fraction(0, ts)
        curve = numerator / denominator
        numerator1, denominator1 = self.fraction(1, ts)
        curve1 = (numerator1 - curve*denominator1) / denominator
        numerator2, denominator2 = self.fraction(2, ts)
        curve2 = (numerator2 - 2*curve1*denominator1 - curve*denominator2) / denominator
        return curve2

    def third_derivative_array(self, ts):
        # numerator''' = (curve * denominator)''' = 
        #  = curve''' * denominator + 3 * curve'' * denominator' + 3 * curve' * denominator'' + denominator'''
        numerator, denominator = self.fraction(0, ts)
        curve = numerator / denominator
        numerator1, denominator1 = self.fraction(1, ts)
        curve1 = (numerator1 - curve*denominator1) / denominator
        numerator2, denominator2 = self.fraction(2, ts)
        curve2 = (numerator2 - 2*curve1*denominator1 - curve*denominator2) / denominator
        numerator3, denominator3 = self.fraction(3, ts)

        curve3 = (numerator3 - 3*curve2*denominator1 - 3*curve1*denominator2 - curve*denominator3) / denominator
        return curve3

    def derivatives_array(self, n, ts):
        result = []
        if n >= 1:
            numerator, denominator = self.fraction(0, ts)
            curve = numerator / denominator
            numerator1, denominator1 = self.fraction(1, ts)
            curve1 = (numerator1 - curve*denominator1) / denominator
            result.append(curve1)
        if n >= 2:
            numerator2, denominator2 = self.fraction(2, ts)
            curve2 = (numerator2 - 2*curve1*denominator1 - curve*denominator2) / denominator
            result.append(curve2)
        if n >= 3:
            numerator3, denominator3 = self.fraction(3, ts)
            curve3 = (numerator3 - 3*curve2*denominator1 - 3*curve1*denominator2 - curve*denominator3) / denominator
            result.append(curve3)
        return result

    def get_u_bounds(self):
        m = self.knotvector.min()
        M = self.knotvector.max()
        return (m, M)

#     def concatenate(self, curve2):
#         curve1 = self
#         curve2 = SvNurbsCurve.to_nurbs(curve2)
#         if curve2 is None:
#             raise UnsupportedCurveTypeException("second curve is not NURBS")
# 
#         w1 = curve1.get_weights()[-1]
#         w2 = curve1.get_weights()[0]
#         if w1 != w2:
#             raise UnsupportedCurveTypeException("Weights at endpoints do not match")
# 
#         p1, p2 = curve1.get_degree(), curve2.get_degree()
#         if p1 > p2:
#             curve2 = curve2.elevate_degree(delta = p1-p2)
#         elif p2 > p1:
#             curve1 = curve1.elevate_degree(delta = p2-p1)
# 
#         #cp1 = curve1.get_control_points()[-1]
#         #cp2 = curve2.get_control_points()[0]
# 
#         knotvector = sv_knotvector.concatenate(curve1.get_knotvector(), curve2.get_knotvector())
#         #print("KV:", knotvector)
#         weights = np.concatenate((curve1.get_weights(), curve2.get_weights()[1:]))
#         control_points = np.concatenate((curve1.get_control_points(), curve2.get_control_points()[1:]))
#         return SvNativeNurbsCurve(curve1.degree, knotvector, control_points, weights)

    def extrude_along_vector(self, vector):
        vector = np.array(vector)
        other_control_points = self.control_points + vector
        control_points = np.stack((self.control_points, other_control_points))
        control_points = np.transpose(control_points, axes=(1,0,2))
        weights = np.stack((self.weights, self.weights)).T
        knotvector_v = sv_knotvector.generate(1, 2, clamped=True)
        surface = SvNativeNurbsSurface(degree_u = self.degree, degree_v = 1,
                        knotvector_u = self.knotvector, knotvector_v = knotvector_v,
                        control_points = control_points,
                        weights = weights)
        return surface

    def make_ruled_surface(self, curve2, vmin, vmax):
        curve2 = SvNurbsCurve.to_nurbs(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("second curve is not NURBS")
        if self.get_degree() != curve2.get_degree():
            raise UnsupportedCurveTypeException("curves have different degrees")

        my_control_points = self.control_points
        other_control_points = curve2.get_control_points()
        if len(my_control_points) != len(other_control_points):
            raise UnsupportedCurveTypeException("curves have different number of control points")

        if (self.get_knotvector() != curve2.get_knotvector()).any():
            raise UnsupportedCurveTypeException("curves have different knot vectors")

        if vmin != 0:
            my_control_points = (1 - vmin) * my_control_points + vmin * other_control_points
        if vmax != 0:
            other_control_points = (1 - vmax) * my_control_points + vmax * other_control_points

        control_points = np.stack((my_control_points, other_control_points))
        control_points = np.transpose(control_points, axes=(1,0,2))

        weights = np.stack((self.weights, curve2.get_weights())).T
        knotvector_v = sv_knotvector.generate(1, 2, clamped=True)

        surface = SvNativeNurbsSurface(degree_u = self.degree, degree_v = 1,
                        knotvector_u = self.knotvector, knotvector_v = knotvector_v,
                        control_points = control_points,
                        weights = weights)
        return surface

    def get_nurbs_implementation(self):
        return SvNurbsCurve.NATIVE

    def insert_knot(self, u_bar, count=1):
        # "The NURBS book", 2nd edition, p.5.2, eq. 5.11
        s = sv_knotvector.find_multiplicity(self.knotvector, u_bar)
        #print(f"I: kv {self.knotvector}, u_bar {u_bar} => s {s}")
        k = np.searchsorted(self.knotvector, u_bar, side='right')-1
        p = self.degree
        u = self.knotvector
        new_knotvector = sv_knotvector.insert(self.knotvector, u_bar, count)
        N = len(self.control_points)
        control_points = self.get_homogenous_control_points()

        for r in range(1, count+1):
            prev_control_points = control_points
            control_points = []
            for i in range(N+1):
                #print(f"I: i {i}, k {k}, p {p}, r {r}, s {s}, k-p+r-1 {k-p+r-1}, k-s {k-s}")
                if i <= k-p+r-1:
                    point = prev_control_points[i]
                    #print(f"P[{r},{i}] := {i}{prev_control_points[i]}")
                elif k - p + r <= i <= k - s:
                    denominator = u[i+p-r+1] - u[i]
                    alpha = (u_bar - u[i]) / denominator
                    point = alpha * prev_control_points[i] + (1.0 - alpha) * prev_control_points[i-1]
                    #print(f"P[{r},{i}]: alpha {alpha}, pts {i}{prev_control_points[i]}, {i-1}{prev_control_points[i-1]} => {point}")
                else:
                    point = prev_control_points[i-1]
                    #print(f"P[{r},{i}] := {i-1}{prev_control_points[i-1]}")
                control_points.append(point)
            N += 1

        control_points, weights = from_homogenous(np.array(control_points))
        curve = SvNativeNurbsCurve(self.degree, new_knotvector,
                    control_points, weights)
        return curve

    def split_at(self, t):
        current_multiplicity = sv_knotvector.find_multiplicity(self.knotvector, t)
        to_add = self.degree - current_multiplicity # + 1
        curve = self.insert_knot(t, count=to_add)
        knot_span = np.searchsorted(curve.knotvector, t)

        ts = np.full((self.degree+1,), t)
        knotvector1 = np.concatenate((curve.knotvector[:knot_span], ts))
        knotvector2 = np.insert(curve.knotvector[knot_span:], 0, t)

        control_points_1 = curve.control_points[:knot_span]
        control_points_2 = curve.control_points[knot_span-1:]
        weights_1 = curve.weights[:knot_span]
        weights_2 = curve.weights[knot_span-1:]

        kv_error = sv_knotvector.check(curve.degree, knotvector1, len(control_points_1))
        if kv_error is not None:
            raise Exception(kv_error)
        kv_error = sv_knotvector.check(curve.degree, knotvector2, len(control_points_2))
        if kv_error is not None:
            raise Exception(kv_error)

        curve1 = SvNativeNurbsCurve(curve.degree, knotvector1,
                    control_points_1, weights_1)
        curve2 = SvNativeNurbsCurve(curve.degree, knotvector2,
                    control_points_2, weights_2)
        return curve1, curve2

