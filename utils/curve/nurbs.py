# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi
import traceback

from sverchok.utils.logging import info
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import interpolate_nurbs_curve
from sverchok.utils.nurbs_common import (
        SvNurbsMaths,SvNurbsBasisFunctions,
        nurbs_divide, elevate_bezier_degree, from_homogenous
    )
from sverchok.utils.surface.nurbs import SvNativeNurbsSurface, SvGeomdlSurface
from sverchok.utils.surface.algorithms import nurbs_revolution_surface
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS, BSpline, operations, fitting

##################
#                #
#  Curves        #
#                #
##################

class SvNurbsCurve(SvCurve):
    """
    Base abstract class for all supported implementations of NURBS curves.
    """
    NATIVE = SvNurbsMaths.NATIVE
    GEOMDL = SvNurbsMaths.GEOMDL

    @classmethod
    def build(cls, implementation, degree, knotvector, control_points, weights=None, normalize_knots=False):
        return SvNurbsMaths.build_curve(implementation, degree, knotvector, control_points, weights, normalize_knots)

    @classmethod
    def to_nurbs(cls, curve, implementation = NATIVE):
        """
        Try to convert arbitrary curve into NURBS.
        Returns: an instance of SvNurbsCurve, or None,
                 if this curve can not be converted to NURBS.
        """
        if isinstance(curve, SvNurbsCurve):
            return curve
        if hasattr(curve, 'to_nurbs'):
            try:
                return curve.to_nurbs(implementation = implementation)
            except UnsupportedCurveTypeException as e:
                info("Can't convert %s to NURBS curve: %s", curve, e)
                pass
        return None

    @classmethod
    def interpolate(cls, degree, points, metric='DISTANCE'):
        return interpolate_nurbs_curve(cls, degree, points, metric)

    @classmethod
    def interpolate_list(cls, degree, points, metric='DISTANCE'):
        n_curves, n_points, _ = points.shape
        tknots = [Spline.create_knots(points[i], metric=metric) for i in range(n_curves)]
        knotvectors = [sv_knotvector.from_tknots(degree, tknots[i]) for i in range(n_curves)]
        functions = [SvNurbsBasisFunctions(knotvectors[i]) for i in range(n_curves)]
        coeffs_by_row = [[functions[curve_idx].function(idx, degree)(tknots[curve_idx]) for idx in range(n_points)] for curve_idx in range(n_curves)]
        coeffs_by_row = np.array(coeffs_by_row)
        A = np.zeros((n_curves, 3*n_points, 3*n_points))
        for curve_idx in range(n_curves):
            for equation_idx, t in enumerate(tknots[curve_idx]):
                for unknown_idx in range(n_points):
                    coeff = coeffs_by_row[curve_idx][unknown_idx][equation_idx]
                    row = 3*equation_idx
                    col = 3*unknown_idx
                    A[curve_idx,row,col] = A[curve_idx,row+1,col+1] = A[curve_idx,row+2,col+2] = coeff

        B = np.zeros((n_curves, 3*n_points,1))
        for curve_idx in range(n_curves):
            for point_idx, point in enumerate(points[curve_idx]):
                row = 3*point_idx
                B[curve_idx, row:row+3] = point[:,np.newaxis]

        x = np.linalg.solve(A, B)

        curves = []
        weights = np.ones((n_points,))
        for curve_idx in range(n_curves):
            control_points = []
            for i in range(n_points):
                row = i*3
                control = x[curve_idx][row:row+3,0].T
                control_points.append(control)
            control_points = np.array(control_points)

            curve = SvNurbsCurve.build(cls.get_nurbs_implementation(),
                    degree, knotvectors[curve_idx],
                    control_points, weights)
            curves.append(curve)

        return curves

    def concatenate(self, curve2, tolerance=1e-6):
        curve1 = self
        curve2 = SvNurbsCurve.to_nurbs(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("second curve is not NURBS")
        
        pt1 = curve1.evaluate(curve1.get_u_bounds()[1])
        pt2 = curve2.evaluate(curve2.get_u_bounds()[0])
        if np.linalg.norm(pt1 - pt2) > tolerance:
            raise UnsupportedCurveTypeException(f"Curve end points do not match: {pt1} != {pt2}")

        cp1 = curve1.get_control_points()[-1]
        cp2 = curve2.get_control_points()[0]
        if np.linalg.norm(cp1 - cp2) > tolerance:
            raise UnsupportedCurveTypeException("End control points do not match")

        w1 = curve1.get_weights()[-1]
        w2 = curve1.get_weights()[0]
        if w1 != w2:
            raise UnsupportedCurveTypeException("Weights at endpoints do not match")

        p1, p2 = curve1.get_degree(), curve2.get_degree()
        if p1 > p2:
            curve2 = curve2.elevate_degree(delta = p1-p2)
        elif p2 > p1:
            curve1 = curve1.elevate_degree(delta = p2-p1)
        p = curve1.get_degree()

        kv1 = curve1.get_knotvector()
        kv2 = curve2.get_knotvector()
        kv1_end_multiplicity = sv_knotvector.to_multiplicity(kv1)[-1][1]
        kv2_start_multiplicity = sv_knotvector.to_multiplicity(kv2)[0][1]
        if kv1_end_multiplicity != p+1:
            raise UnsupportedCurveTypeException(f"End knot multiplicity of the first curve ({kv1_end_multiplicity}) is not equal to degree+1 ({p+1})")
        if kv2_start_multiplicity != p+1:
            raise UnsupportedCurveTypeException(f"Start knot multiplicity of the second curve ({kv2_start_multiplicity}) is not equal to degree+1 ({p+1})")

        knotvector = sv_knotvector.concatenate(kv1, kv2, join_multiplicity=p)
        #print(f"Concat KV: {kv1} + {kv2} => {knotvector}")
        weights = np.concatenate((curve1.get_weights(), curve2.get_weights()[1:]))
        control_points = np.concatenate((curve1.get_control_points(), curve2.get_control_points()[1:]))

        return SvNurbsCurve.build(self.get_nurbs_implementation(),
                p, knotvector, control_points, weights)

    @classmethod
    def get_nurbs_implementation(cls):
        raise Exception("NURBS implementation is not defined")

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

    def elevate_degree(self, delta=None, target=None):
        if delta is None and target is None:
            delta = 1
        if delta is not None and target is not None:
            raise Exception("Of delta and target, only one parameter can be specified")
        degree = self.get_degree()
        if delta is None:
            delta = target - degree
            if delta < 0:
                raise Exception(f"Curve already has degree {degree}, which is greater than target {target}")
        if delta == 0:
            return self

        if self.is_bezier():
            control_points = self.get_homogenous_control_points()
            control_points = elevate_bezier_degree(degree, control_points, delta)
            control_points, weights = from_homogenous(control_points)
            knotvector = self.get_knotvector()
            knotvector = sv_knotvector.elevate_degree(knotvector, delta)
            return SvNurbsCurve.build(self.get_nurbs_implementation(),
                    degree+delta, knotvector, control_points, weights)
        else:
            raise UnsupportedCurveTypeException("Degree elevation is not implemented for non-bezier curves yet")

    def reparametrize(self, new_t_min, new_t_max):
        kv = self.get_knotvector()
        t_min, t_max = kv[0], kv[-1]
        if t_min == new_t_min and t_max == new_t_max:
            return self

        knotvector = sv_knotvector.rescale(kv, new_t_min, new_t_max)
        return SvNurbsCurve.build(self.get_nurbs_implementation(),
                self.get_degree(), knotvector, self.get_control_points(), self.get_weights())

    def reverse(self):
        knotvector = sv_knotvector.reverse(self.get_knotvector())
        control_points = self.get_control_points()[::-1]
        weights = self.get_weights()[::-1]
        return SvNurbsCurve.build(self.get_nurbs_implementation(),
                self.get_degree(), knotvector, control_points, weights)

    def cut_segment(self, new_t_min, new_t_max, rescale=False):
        t_min, t_max = 0.0, 1.0
        curve = self
        if new_t_min > t_min:
            start, curve = curve.split_at(new_t_min)
        if new_t_max < t_max:
            curve, end = curve.split_at(new_t_max)
        if rescale:
            curve = curve.reparametrize(0, 1)
        return curve

    def make_revolution_surface(self, origin, axis, v_min=0, v_max=2*pi, global_origin=True):
        return nurbs_revolution_surface(self, origin, axis, v_min, v_max, global_origin)

    def to_knotvector(self, curve2):
        if curve2.get_degree() != self.get_degree():
            raise Exception("Degrees of the curves are not equal")
        curve = self
        new_kv = curve2.get_knotvector()
        curve = curve.reparametrize(new_kv[0], new_kv[-1])
        old_kv = curve.get_knotvector()
        diff = sv_knotvector.difference(old_kv, new_kv)
        #print(f"old {old_kv}, new {new_kv} => diff {diff}")
        # TODO: use knot refinement when possible
        for u, count in diff:
            curve = curve.insert_knot(u, count)
        return curve

    def insert_knot(self, u, count=1):
        raise Exception("Not implemented!")

def unify_two_curves(curve1, curve2):
    curve1 = curve1.to_knotvector(curve2)
    curve2 = curve2.to_knotvector(curve1)
    return curve1, curve2

class SvGeomdlCurve(SvNurbsCurve):
    """
    geomdl-based implementation of NURBS curves
    """
    def __init__(self, curve):
        self.curve = curve
        self.u_bounds = (0.0, 1.0)
        self.__description__ = f"Geomdl NURBS (degree={curve.degree}, pts={len(curve.ctrlpts)})"

    @classmethod
    def build_geomdl(cls, degree, knotvector, control_points, weights=None, normalize_knots=False):
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

        result = SvGeomdlCurve(curve)
        result.u_bounds = curve.knotvector[0], curve.knotvector[-1]
        return result

    @classmethod
    def build(cls, implementation, degree, knotvector, control_points, weights=None, normalize_knots=False):
        return SvGeomdlCurve.build_geomdl(degree, knotvector, control_points, weights, normalize_knots)

    @classmethod
    def interpolate(cls, degree, points, metric='DISTANCE'):
        if metric not in {'DISTANCE', 'CENTRIPETAL'}:
            raise Exception("Unsupported metric")
        centripetal = metric == 'CENTRIPETAL'
        curve = fitting.interpolate_curve(points.tolist(), degree, centripetal=centripetal)
        return SvGeomdlCurve(curve)

    @classmethod
    def interpolate_list(cls, degree, points, metric='DISTANCE'):
        if metric not in {'DISTANCE', 'CENTRIPETAL'}:
            raise Exception("Unsupported metric")
        centripetal = metric == 'CENTRIPETAL'
        curves = []
        for curve_points in points:
            curve = fitting.interpolate_curve(curve_points.tolist(), degree, centripetal=centripetal)
            curve = SvGeomdlCurve(curve)
            curves.append(curve)
        return curves

    @classmethod
    def from_any_nurbs(cls, curve):
        if not isinstance(curve, SvNurbsCurve):
            raise TypeError("Invalid curve type")
        if isinstance(curve, SvGeomdlCurve):
            return curve
        return SvGeomdlCurve.build_geomdl(curve.get_degree(), curve.get_knotvector(),
                    curve.get_control_points(), 
                    curve.get_weights())

    @classmethod
    def get_nurbs_implementation(cls):
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
        surface = SvGeomdlSurface.build_geomdl(degree_u = my_degree, degree_v = 1,
                        knotvector_u = my_knotvector, knotvector_v = knotvector_v,
                        control_points = control_points,
                        weights = weights)
        return surface

    def insert_knot(self, u, count=1):
        curve = operations.insert_knot(self.curve, [u], [count])
        return SvGeomdlCurve(curve)

class SvNativeNurbsCurve(SvNurbsCurve):
    def __init__(self, degree, knotvector, control_points, weights=None, normalize_knots=False):
        self.control_points = np.array(control_points) # (k, 3)
        k = len(control_points)
        if weights is not None:
            self.weights = np.array(weights) # (k, )
        else:
            self.weights = np.ones((k,))
        self.knotvector = np.array(knotvector)
        if normalize_knots:
            self.knotvector = sv_knotvector.normalize(self.knotvector)
        self.degree = degree
        self.basis = SvNurbsBasisFunctions(knotvector)
        self.tangent_delta = 0.001
        self.u_bounds = None # take from knotvector
        self.__description__ = f"Native NURBS (degree={degree}, pts={k})"

    @classmethod
    def build(cls, implementation, degree, knotvector, control_points, weights=None, normalize_knots=False):
        return SvNativeNurbsCurve(degree, knotvector, control_points, weights, normalize_knots)

    def get_control_points(self):
        return self.control_points

    def get_weights(self):
        return self.weights

    def get_knotvector(self):
        return self.knotvector

    def get_degree(self):
        return self.degree

    def evaluate(self, t):
        #return self.evaluate_array(np.array([t]))[0]
        numerator, denominator = self.fraction_single(0, t)
        if denominator == 0:
            return np.array([0,0,0])
        else:
            return numerator / denominator

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

    def fraction_single(self, deriv_order, t):
        p = self.degree
        k = len(self.control_points)
        ts = np.array([t])
        ns = np.array([self.basis.derivative(i, p, deriv_order)(ts)[0] for i in range(k)]) # (k,)
        coeffs = ns * self.weights # (k, )
        coeffs_t = coeffs[np.newaxis].T
        numerator = (coeffs_t * self.control_points) # (k, 3)
        numerator = numerator.sum(axis=0) # (3,)
        denominator = coeffs.sum(axis=0) # ()

        return numerator, denominator

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
        if self.u_bounds is None:
            m = self.knotvector.min()
            M = self.knotvector.max()
            return (m, M)
        else:
            return self.u_bounds

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
        curve = self
        curve2 = SvNurbsCurve.to_nurbs(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("second curve is not NURBS")
        if curve.get_degree() != curve2.get_degree():
            raise UnsupportedCurveTypeException("curves have different degrees")

        #print(f"kv1: {curve.get_knotvector().shape}, kv2: {curve2.get_knotvector().shape}")
        kv1, kv2 = curve.get_knotvector(), curve2.get_knotvector()
        if kv1.shape != kv2.shape or (kv1 != kv2).any():
            curve, curve2 = unify_two_curves(curve, curve2)
            #raise UnsupportedCurveTypeException("curves have different knot vectors")

        my_control_points = curve.control_points
        other_control_points = curve2.get_control_points()
        if len(my_control_points) != len(other_control_points):
            raise UnsupportedCurveTypeException("curves have different number of control points")

        if vmin != 0:
            my_control_points = (1 - vmin) * my_control_points + vmin * other_control_points
        if vmax != 0:
            other_control_points = (1 - vmax) * my_control_points + vmax * other_control_points

        control_points = np.stack((my_control_points, other_control_points))
        control_points = np.transpose(control_points, axes=(1,0,2))

        weights = np.stack((curve.weights, curve2.get_weights())).T
        knotvector_v = sv_knotvector.generate(1, 2, clamped=True)

        surface = SvNativeNurbsSurface(degree_u = curve.degree, degree_v = 1,
                        knotvector_u = curve.knotvector, knotvector_v = knotvector_v,
                        control_points = control_points,
                        weights = weights)
        return surface

    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsCurve.NATIVE

    def insert_knot(self, u_bar, count=1):
        # "The NURBS book", 2nd edition, p.5.2, eq. 5.11
        s = sv_knotvector.find_multiplicity(self.knotvector, u_bar)
        #print(f"I: kv {len(self.knotvector)}{self.knotvector}, u_bar {u_bar} => s {s}")
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

SvNurbsMaths.curve_classes[SvNurbsMaths.NATIVE] = SvNativeNurbsCurve
if geomdl is not None:
    SvNurbsMaths.curve_classes[SvNurbsMaths.GEOMDL] = SvGeomdlCurve

