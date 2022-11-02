# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sqrt

from sverchok.utils.math import binomial
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.dependencies import geomdl

class SvNurbsMaths(object):
    """
    This class allows modules such as curve.primitives and others to
    create NURBS curves or surfaces without need to import curves.nurbs
    or surfaces.nurbs. It is required to exclude such imports because
    curves.nurbs and surfaces.nurbs require curves.primitives and several
    other curves.* and surfaces.* modules.
    """
    NATIVE = 'NATIVE'
    GEOMDL = 'GEOMDL'
    FREECAD = 'FREECAD'

    # Classes by implementation
    curve_classes = dict()
    surface_classes = dict()

    @staticmethod
    def build_curve(implementation, degree, knotvector, control_points, weights=None, normalize_knots=False):
        kv_error = sv_knotvector.check(degree, knotvector, len(control_points))
        if kv_error is not None:
            raise Exception(kv_error)
        nurbs_class = SvNurbsMaths.curve_classes.get(implementation)
        if nurbs_class is None and isinstance(implementation, type):
            nurbs_class = implementation
        if nurbs_class is None:
            raise Exception(f"Unsupported NURBS Curve implementation: {implementation}")
        else:
            return nurbs_class.build(implementation, degree, knotvector, control_points, weights, normalize_knots)

    @staticmethod
    def build_surface(implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        kv_error = sv_knotvector.check(degree_u, knotvector_u, len(control_points))
        if kv_error is not None:
            raise Exception("U direction: " + kv_error)
        kv_error = sv_knotvector.check(degree_v, knotvector_v, len(control_points[0]))
        if kv_error is not None:
            raise Exception("V direction: " + kv_error)

        nurbs_class = SvNurbsMaths.surface_classes.get(implementation)
        if nurbs_class is None:
            raise Exception(f"Unsupported NURBS Surface implementation: {implementation}")
        else:
            return nurbs_class.build(implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights)

    @staticmethod
    def interpolate_curve(implementation, degree, points, metric='DISTANCE', **kwargs):
        nurbs_class = SvNurbsMaths.curve_classes.get(implementation)
        if nurbs_class is None and isinstance(implementation, type):
            nurbs_class = implementation
        return nurbs_class.interpolate(degree, points, metric=metric, **kwargs)

    @staticmethod
    def to_nurbs_curve(curve, implementation = NATIVE):
        nurbs_class = SvNurbsMaths.curve_classes.get(implementation)
        if nurbs_class is None:
            raise Exception(f"Unsupported NURBS Curve implementation: {implementation}")
        else:
            return nurbs_class.to_nurbs(curve, implementation)

    @staticmethod
    def to_nurbs_surface(surface, implementation = NATIVE):
        nurbs_class = SvNurbsMaths.surface_classes.get(implementation)
        if nurbs_class is None:
            raise Exception(f"Unsupported NURBS Surface implementation: {implementation}")
        else:
            return nurbs_class.to_nurbs(surface, implementation)

def nurbs_divide(numerator, denominator):
    if denominator.ndim < 2:
        denominator = denominator[np.newaxis].T
    good = (denominator != 0)
    good_num = good.flatten()
    result = np.zeros_like(numerator)
    result[good_num] = numerator[good_num] / denominator[good][np.newaxis].T
    return result

def nurbs_divide_flat(numerator, denominator):
    good = (denominator != 0)
    result = np.zeros_like(numerator)
    result[good] = numerator[good] / denominator[good]
    return result

def bezier_coefficient(n, k, ts):
    C = binomial(n, k)
    return C * ts**k * (1 - ts)**(n-k)

def elevate_bezier_degree(self_degree, control_points, delta=1):
    # See "The NURBS book" (2nd edition), p.5.5, eq. 5.36
    t = delta
    p = self_degree
    new_points = []
    P = control_points
    for i in range(p+t+1):
        j0 = max(0, i-t)
        j1 = min(p, i)
        js = range(j0, j1+1)
        c1 = np.array([binomial(p, j) for j in js])
        c2 = np.array([binomial(t, i-j) for j in js])
        ps = P[j0:j1+1, :]
        numerator = (c1 * c2)[np.newaxis].T * ps
        denominator = binomial(p+t, i)
        #print(f"E: p {p}, i {i}, c1 {c1}, c2 {c2}, denom {denominator}, ps {ps}")
        point = numerator.sum(axis=0) / denominator
        new_points.append(point)
    return np.array(new_points)

def reduce_bezier_degree_once(self_degree, control_points):
    # See "The NURBS Book" (2nd edition), p.5.6 eq. 5.40, 5.41, 5.42
    # Also, from eq. 5.43 and 5.44 there, we derive estimations of error
    # bounds more precise than those which are given in eq. 5.45, 5.46
    # in the same paragraph later.
    p = self_degree
    r = (p-1) // 2
    ndim = control_points.shape[1]
    alpha = [float(i) / float(p) for i in range(p)]
    new_control_points = np.zeros((p, ndim))
    new_control_points[0] = control_points[0]
    new_control_points[p-1] = control_points[p]
    if p % 2 == 0:
        for i in range(1, r+1):
            new_control_points[i] = (control_points[i] - alpha[i] * new_control_points[i-1]) / (1 - alpha[i])
        for i in range(p-2, r, -1): # reverse order
            new_control_points[i] = (control_points[i+1] - (1 - alpha[i+1])*new_control_points[i+1]) / alpha[i+1]
        error = np.linalg.norm(control_points[r+1] - 0.5*(new_control_points[r] + new_control_points[r+1]))
        # directly follows from eq. 5.43
        error *= bezier_coefficient(p, r+1, 0.5)
    else:
        for i in range(1, r):
            new_control_points[i] = (control_points[i] - alpha[i] * new_control_points[i-1]) / (1 - alpha[i])
        for i in range(p-2, r, -1): # reverse order
            new_control_points[i] = (control_points[i+1] - (1 - alpha[i+1])*new_control_points[i+1]) / alpha[i+1]
        p_l = (control_points[r] - alpha[r]*new_control_points[r-1]) / (1 - alpha[r])
        p_r = (control_points[r+1] - (1 - alpha[r+1])*new_control_points[r+1]) / alpha[r+1]
        new_control_points[r] = 0.5 * (p_l + p_r)
        error = np.linalg.norm(p_l - p_r)
        # See eq. 5.44. Knowing that r == (p-1)/2 and p is odd, and
        # knowing properties of binomial coefficients, we know that
        # C(p,r) == C(p, r+1); from that, one can write that
        # B[r,p](u) - B[r+1,p](u) = C(p,r) * u^r * (1-u)^(r+1) * (1 - 2*u)        (*)
        # By manually differentiating this, one can find out that it
        # reaches maximums at u = (p +- sqrt(p)) / (2*p)
        # (both maximums are equal due to symmetry).
        max_u = (p - sqrt(p)) / (2*p)
        # from (*); it's quite obvious that this is positive since max_u < 1/2
        b_error = binomial(p,r) * max_u**r * (1 - max_u)**(r+1) * (1 - 2*max_u)
        error *= 0.5 * (1 - alpha[r]) * b_error
    return new_control_points, error

def reduce_bezier_degree(self_degree, control_points, delta=1):
    max_error = 0.0
    degree = self_degree
    for i in range(delta):
        control_points, error = reduce_bezier_degree_once(degree, control_points)
        max_error = max(max_error, error)
    return control_points, max_error

def to_homogenous(control_points, weights):
    if weights.ndim == 1:
        weights = weights[np.newaxis].T
    weighted = weights * control_points
    return np.concatenate((weighted, weights), axis=1)

def from_homogenous(control_points):
    if control_points.ndim == 2: # curve
        weights = control_points[:,3]
        weighted = control_points[:,0:3]
        points = weighted / weights[np.newaxis].T
        return points, weights
    elif control_points.ndim == 3: # surface
        weights = control_points[:,:,3]
        weighted = control_points[:,:,0:3]
        points = weighted / np.transpose(weights[np.newaxis], axes=(1,2,0))
        return points, weights
    else:
        raise Exception(f"control_points have ndim={control_points.ndim}, supported are only 2 and 3")

class SvNurbsBasisFunctions(object):
    def __init__(self, knotvector):
        self.knotvector = np.array(knotvector)
        self._cache = dict()

    def function(self, i, p, reset_cache=True):
        if reset_cache:
            self._cache = dict()
        def calc(us):
            value = self._cache.get((i,p, 0))
            if value is not None:
                return value

            u = self.knotvector
            if p <= 0:
                if i < 0 or i >= len(u):

                    value = np.zeros_like(us)
                    self._cache[(i,p,0)] = value
                    return value
                        
                else:

                    if i+1 >= len(u):
                        u_next = u[-1]
                        is_last = True
                    else:
                        u_next = u[i+1]
                        is_last = u_next >= u[-1]
                    if is_last:
                        c2 = us <= u_next
                    else:
                        c2 = us < u_next
                    condition = np.logical_and(u[i] <= us, c2)
                    value = np.where(condition, 1.0, 0.0)
                    self._cache[(i,p,0)] = value
                    return value

            else:
                denom1 = (u[i+p] - u[i])
                denom2 = (u[i+p+1] - u[i+1])

                if denom1 != 0:
                    n1 = self.function(i, p-1, reset_cache=False)(us)
                if denom2 != 0:
                    n2 = self.function(i+1, p-1, reset_cache=False)(us)

                if denom1 == 0 and denom2 == 0:
                    value = np.zeros_like(us)
                    self._cache[(i,p,0)] = value
                    return value
                elif denom1 == 0 and denom2 != 0:
                    c2 = (u[i+p+1] - us) / denom2
                    value = c2 * n2
                    self._cache[(i,p,0)] = value
                    return value
                elif denom1 != 0 and denom2 == 0:
                    c1 = (us - u[i]) / denom1
                    value = c1 * n1
                    self._cache[(i,p,0)] = value
                    return value
                else: # denom1 != 0 and denom2 != 0
                    c1 = (us - u[i]) / denom1
                    c2 = (u[i+p+1] - us) / denom2
                    value = c1 * n1 + c2 * n2
                    self._cache[(i,p,0)] = value
                    return value
        return calc

    def derivative(self, i, p, k, reset_cache=True):
        if reset_cache:
            self._cache = dict()

        if k == 0:
            return self.function(i, p, reset_cache=False)

        def calc(us):
            value = self._cache.get((i, p, k))
            if value is not None:
                return value
            
            n1 = self.derivative(i, p-1, k-1, reset_cache=False)(us)
            n2 = self.derivative(i+1, p-1, k-1, reset_cache=False)(us)
            u = self.knotvector

            denom1 = u[i+p] - u[i]
            denom2 = u[i+p+1] - u[i+1]

            if denom1 == 0:
                s1 = np.zeros_like(us)
            else:
                s1 = n1 / denom1

            if denom2 == 0:
                s2 = np.zeros_like(us)
            else:
                s2 = n2 / denom2

            value = p*(s1 - s2)
            self._cache[(i,p,k)] = value
            return value
        
        return calc

    def fraction(self, i, p, weights, reset_cache=True):

        if reset_cache:
            self._cache = dict()
        n = len(weights)

        def calc(us):
            numerator = self.function(i,p, reset_cache=reset_cache)(us) * weights[i]
            ds = [self.function(j,p, reset_cache=False)(us) * weights[j] for j in range(n)]
            denominator = sum(ds)
            return nurbs_divide_flat(numerator, denominator)

        return calc

    def weighted_derivative(self, i, p, k, weights, reset_cache=True):
        if reset_cache:
            self._cache = dict()
        n = len(weights)

        def calc(us):
            ns = self.derivative(i, p, k)(us)
            numerator = ns * weights[i]
            denominator = weights.sum()
            return numerator / denominator
        
        return calc


class CantInsertKnotException(Exception):
    pass

class CantRemoveKnotException(Exception):
    pass

class CantReduceDegreeException(Exception):
    pass

