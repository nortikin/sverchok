# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve import SvCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS, BSpline

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

    def get_knotvector(self):
        """
        returns: np.array of shape (X,)
        """
        raise Exception("Not implemented!")

    def get_degree(self):
        raise Exception("Not implemented!")

class SvGeomdlCurve(SvNurbsCurve):
    """
    geomdl-based implementation of NURBS curves
    """
    def __init__(self, curve):
        self.curve = curve
        self.u_bounds = (0.0, 1.0)

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

    def get_control_points(self):
        return np.array(self.curve.ctrlpts)

    def get_weights(self):
        return np.array(self.curve.weights)

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
        p, t = self.curve.tangent(t, normalize=False)
        return np.array(t)

    def tangent_array(self, ts):
        t_min, t_max = self.get_u_bounds()
        ts[ts < t_min] = t_min
        ts[ts > t_max] = t_max
        vs = self.curve.tangent(list(ts), normalize=False)
        return np.array([t[1] for t in vs])

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

def nurbs_divide(numerator, denominator):
    if denominator.ndim != 2:
        denominator = denominator[np.newaxis].T
    good = (denominator != 0)
    good_num = good.flatten()
    result = np.zeros_like(numerator)
    result[good_num] = numerator[good_num] / denominator[good][np.newaxis].T
    return result

class SvNurbsBasisFunctions(object):
    def __init__(self, knotvector):
        self.knotvector = np.array(knotvector)
        self._cache = dict()

    def function(self, i, p):
        f = self._cache.get((i,p, 0))
        if f is not None:
            return f

        u = self.knotvector
        if p <= 0:
            if i < 0 or i >= len(self.knotvector):

                def n0(us):
                    return np.zeros_like(us)
            else:

                def n0(us):
                    is_last = u[i+1] >= self.knotvector[-1]
                    if is_last:
                        c2 = us <= u[i+1]
                    else:
                        c2 = us < u[i+1]
                    condition = np.logical_and(u[i] <= us, c2)
                    return np.where(condition, 1.0, 0.0)

            self._cache[(i,p,0)] = n0
            return n0
        else:
            n1 = self.function(i, p-1)
            n2 = self.function(i+1, p-1)

            def f(us):
                denom1 = (u[i+p] - u[i])
                denom2 = (u[i+p+1] - u[i+1])
                if denom1 == 0:
                    c1 = 0
                else:
                    c1 = (us - u[i]) / denom1
                if denom2 == 0:
                    c2 = 0
                else:
                    c2 = (u[i+p+1] - us) / denom2
                return c1 * n1(us) + c2 * n2(us)

            self._cache[(i,p,0)] = f
            return f

    def derivative(self, i, p, k):
        if k == 0:
            return self.function(i, p)
        f = self._cache.get((i, p, k))
        if f is not None:
            return f
        
        n1 = self.derivative(i, p-1, k-1)
        n2 = self.derivative(i+1, p-1, k-1)
        u = self.knotvector

        def f(us):
            denom1 = u[i+p] - u[i]
            denom2 = u[i+p+1] - u[i+1]

            if denom1 == 0:
                s1 = 0
            else:
                s1 = n1(us) / denom1

            if denom2 == 0:
                s2 = 0
            else:
                s2 = n2(us) / denom2

            return p*(s1 - s2)
        
        self._cache[(i,p,k)] = f
        return f

class SvNativeNurbsCurve(SvNurbsCurve):
    def __init__(self, degree, knotvector, control_points, weights=None):
        self.control_points = np.array(control_points) # (k, 3)
        if weights is not None:
            self.weights = np.array(weights) # (k, )
        else:
            k = len(control_points)
            self.weights = np.ones((k,))
        self.knotvector = np.array(knotvector)
        self.degree = degree
        self.basis = SvNurbsBasisFunctions(knotvector)
        self.tangent_delta = 0.001

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

