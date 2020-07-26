# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve import SvCurve
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS

##################
#                #
#  Curves        #
#                #
##################

class SvGeomdlCurve(SvCurve):
    """
    geomdl-based implementation of NURBS curves
    """
    def __init__(self, curve):
        self.curve = curve
        self.u_bounds = (0.0, 1.0)

    @classmethod
    def build(cls, degree, knotvector, control_points, weights, normalize_knots=False):
        curve = NURBS.Curve(normalize_kv = normalize_knots)
        curve.degree = degree
        curve.ctrlpts = control_points
        curve.weights = weights
        curve.knotvector = knotvector
        return SvGeomdlCurve(curve)

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

class SvNurbsBasisFunctions(object):
    def __init__(self, knotvector):
        self.knotvector = np.array(knotvector)
        self._cache = dict()

    def function(self, i, p):
        f = self._cache.get((i,p, 0))
        if f is not None:
            return f

        u = self.knotvector
        if p == 0:
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

class SvNativeNurbsCurve(SvCurve):
    def __init__(self, degree, knotvector, control_points, weights):
        self.control_points = np.array(control_points) # (k, 3)
        self.weights = np.array(weights) # (k, )
        self.knotvector = np.array(knotvector)
        self.degree = degree
        self.basis = SvNurbsBasisFunctions(knotvector)
        self.tangent_delta = 0.001

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def fraction(self, deriv_order, ts):
        p = self.degree
        k = len(self.control_points)
        ns = np.array([self.basis.derivative(i, p, deriv_order)(ts) for i in range(k)]) # (k, n)
        coeffs = ns * self.weights[np.newaxis].T # (k, n)
        numerator = (coeffs[np.newaxis].T * self.control_points).sum(axis=1)
        denominator = coeffs.sum(axis=0) # (n,1)
        #print(denominator)

        return numerator, denominator[np.newaxis].T

    def evaluate_array(self, ts):
        numerator, denominator = self.fraction(0, ts)
        return numerator / denominator

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        N, D = self.fraction(0, ts)
        C = N / D
        N1, D1 = self.fraction(1, ts)
        C1 = (N1 - C*D1) / D
        return C1

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        N, D = self.fraction(0, ts)
        C = N / D
        N1, D1 = self.fraction(1, ts)
        C1 = (N1 - C*D1) / D
        N2, D2 = self.fraction(2, ts)
        C2 = (N2 - 2*C1*D1 - C*D2) / D
        return C2

    def third_derivative_array(self, ts):
        N, D = self.fraction(0, ts)
        C = N / D
        N1, D1 = self.fraction(1, ts)
        C1 = (N1 - C*D1) / D
        N2, D2 = self.fraction(2, ts)
        C2 = (N2 - 2*C1*D1 - C*D2) / D
        N3, D3 = self.fraction(3, ts)

        C3 = (N3 - 3*C2*D1 - 3*C1*D2 - C*D3) / D
        return C3

    def derivatives_array(self, n, ts):
        result = []
        if n >= 1:
            N, D = self.fraction(0, ts)
            C = N / D
            N1, D1 = self.fraction(1, ts)
            C1 = (N1 - C*D1) / D
            result.append(C1)
        if n >= 2:
            N2, D2 = self.fraction(2, ts)
            C2 = (N2 - 2*C1*D1 - C*D2) / D
            result.append(C2)
        if n >= 3:
            N3, D3 = self.fraction(3, ts)
            C3 = (N3 - 3*C2*D1 - 3*C1*D2 - C*D3) / D
            result.append(C3)
        return result

    def get_u_bounds(self):
        m = self.knotvector.min()
        M = self.knotvector.max()
        return (m, M)

