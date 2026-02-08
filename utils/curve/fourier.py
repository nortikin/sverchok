# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sin, cos, pi

from sverchok.utils.geom import linear_approximation, Spline
from sverchok.utils.curve.core import SvCurve
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.optimize import curve_fit

class SvFourierCurve(SvCurve):
    def __init__(self, omega, start, coeffs):
        self.omega = omega
        self.start = start
        self.coeffs = coeffs
        self.u_bounds = (0.0, 1.0)
    
    def get_u_bounds(self):
        return self.u_bounds
    
    def evaluate(self, t):
        result = self.start
        o = self.omega
        for i, coeff in enumerate(self.coeffs):
            j = i // 2
            if i % 2 == 0:
                result += coeff * cos((j+1)*o*t)
            else:
                result += coeff * sin((j+1)*o*t)
        return result

    @staticmethod
    def basis_function(omega, i):
        def function(ts):
            j = i // 2
            if i % 2 == 0:
                cost = np.cos((j+1)*omega*ts)[np.newaxis].T
                return cost
            else:
                sint = np.sin((j+1)*omega*ts)[np.newaxis].T
                return sint
        return function
    
    def evaluate_array(self, ts):
        n = len(ts)
        result = np.broadcast_to(self.start, (n,3))
        for i, coeff in enumerate(self.coeffs):
            result = result + coeff * SvFourierCurve.basis_function(self.omega, i)(ts)
        return result

    def tangent(self, t, tangent_delta=None):
        result = np.array([0, 0, 0])
        o = self.omega
        for i, coeff in enumerate(self.coeffs):
            j = i // 2
            if i % 2 == 0:
                result += - (j+1)*o * coeff * sin((j+1)*o*t) 
            else:
                result += (j+1)*o * coeff * cos((j+1)*o*t)
        return result

    def tangent_array(self, ts, tangent_delta=None):
        n = len(ts)
        result = np.zeros((n, 3))
        o = self.omega
        for i, coeff in enumerate(self.coeffs):
            j = i // 2
            if i % 2 == 0:
                cost = - np.sin((j+1)*o*ts)[np.newaxis].T
                result = result + (j+1)*o* coeff*cost 
            else:
                sint = np.cos((j+1)*o*ts)[np.newaxis].T
                result = result + (j+1)*o* coeff*sint
        return result

    def second_derivative(self, t, tangent_delta=None):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts, tangent_delta=None):
        n = len(ts)
        result = np.zeros((n, 3))
        o = self.omega
        for i, coeff in enumerate(self.coeffs):
            j = i // 2
            if i % 2 == 0:
                cost = - np.cos((j+1)*o*ts)[np.newaxis].T
                result = result + ((j+1)*o)**2 * coeff*cost
            else:
                sint = - np.sin((j+1)*o*ts)[np.newaxis].T
                result = result + ((j+1)*o)**2 * coeff*sint
        return result

    @staticmethod
    def approximate_fit(verts, degree, metric='DISTANCE'):

        def init_guess(verts, n):
            return np.array([pi] + list(verts[0]) + [0,0,0]*2*n)

        def goal(ts, *xs):
            n3 = len(xs)-1
            n = n3 // 3
            omega = xs[0]
            points = np.array(xs[1:]).reshape((n,3))
            curve = SvFourierCurve(omega, points[0], points[1:])
            pts = curve.evaluate_array(ts)
            return np.ravel(pts)

        xdata = Spline.create_knots(verts, metric=metric)
        ydata = np.ravel(verts)

        p0 = init_guess(verts, degree)
        popt, pcov = curve_fit(goal, xdata, ydata, p0)
        n3 = len(popt)-1
        ncoeffs = n3 // 3
        omega = popt[0]
        points = popt[1:].reshape((ncoeffs,3))
        curve = SvFourierCurve(omega, points[0], points[1:])
        return curve

    @staticmethod
    def approximate_lstsq(verts, omega, degree, metric='DISTANCE'):
        verts = np.array(verts)
        n = len(verts)
        degree = min(n, degree)
        tknots = Spline.create_knots(verts, metric=metric)
        A = np.zeros((n, degree))
        for i in range(degree):
            A[:,i] = SvFourierCurve.basis_function(omega, i)(tknots)[:,0]
        coeffs, residuals, rank, s = np.linalg.lstsq(A, verts)
        curve = SvFourierCurve(omega, np.array([0.0, 0.0, 0.0]), coeffs)
        return curve

    @staticmethod
    def interpolate(verts, omega, metric='DISTANCE', is_cyclic=False):
        verts = np.array(verts)
        n = len(verts)
        degree = n
        tknots = Spline.create_knots(verts, metric=metric)
        A = np.zeros((n, degree))
        for i in range(degree):
            A[:,i] = SvFourierCurve.basis_function(omega, i)(tknots)[:,0]

        print(A)
        print("DA", np.linalg.det(A))
        coeffs = np.linalg.solve(A, verts)
        
        return SvFourierCurve(omega, np.array([0.0,0.0,0.0]), coeffs)

class SvSineCurve(SvCurve):
    def __init__(self, coeffs):
        self.coeffs = np.array(coeffs)

    def get_u_bounds(self):
        return (0.0, 1.0)

    def evaluate_array(self, ts):
        n = len(ts)
        ndim = self.coeffs.shape[-1]
        points = np.zeros((n,ndim))
        points[:,0] = ts
        p = len(self.coeffs)
        js = np.arange(1, p+1)
        tsj = pi * ts[np.newaxis].T * js
        rs = np.transpose(np.sin(tsj)[np.newaxis], axes=(1,2,0)) * self.coeffs
        points += np.sum(rs, axis=1)
        return points

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def tangent_array(self, ts, tangent_delta=None):
        n = len(ts)
        ndim = self.coeffs.shape[-1]
        points = np.zeros((n,ndim))
        points[:,0] = ts
        js = np.arange(1, n+1)
        tsj = pi * ts[np.newaxis].T * js
        rs = np.transpose(np.cos(tsj)[np.newaxis], axes=(1,2,0)) * self.coeffs
        points += np.sum(rs, axis=1)
        return points

    def tangent(self, t, tangent_delta=None):
        return self.tangent_array(np.array([t]))[0]

