# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.math import binomial

def nurbs_divide(numerator, denominator):
    if denominator.ndim != 2:
        denominator = denominator[np.newaxis].T
    good = (denominator != 0)
    good_num = good.flatten()
    result = np.zeros_like(numerator)
    result[good_num] = numerator[good_num] / denominator[good][np.newaxis].T
    return result

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

def from_homogenous(control_points):
    weights = control_points[:,3]
    weighted = control_points[:,0:3]
    points = weighted / weights[np.newaxis].T
    return points, weights

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
                try:
                    denom2 = (u[i+p+1] - u[i+1])
                except IndexError as e:
                    print(f"u: {u}, i: {i}, p: {p}")
                    raise e
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

