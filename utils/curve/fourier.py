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
    
    def evaluate_array(self, ts):
        n = len(ts)
        result = np.broadcast_to(self.start, (n,3))
        o = self.omega
        for i, coeff in enumerate(self.coeffs):
            j = i // 2
            if i % 2 == 0:
                cost = np.cos((j+1)*o*ts)[np.newaxis].T
                result = result + coeff*cost
            else:
                sint = np.sin((j+1)*o*ts)[np.newaxis].T
                result = result + coeff*sint
                
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

    @classmethod
    def approximate(cls, verts, degree, metric='DISTANCE'):

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

    @classmethod
    def interpolate(cls, verts, omega, metric='DISTANCE', is_cyclic=False):
        ndim = 3

        n_verts = len(verts)
        verts = np.asarray(verts)
        if is_cyclic:
            verts = np.append(verts, verts[0][np.newaxis], axis=0)
            n_verts += 1
            n_equations = n_verts + 1
        else:
            n_equations = n_verts
        
        tknots = Spline.create_knots(verts, metric=metric)
        A = np.zeros((ndim*n_equations, ndim*n_equations))
        
        for equation_idx, t in enumerate(tknots):
            for unknown_idx in range(n_equations):
                i = (unknown_idx // 2) + 1
                if unknown_idx % 2 == 0:
                    coeff = cos(omega*i*t)
                else:
                    coeff = sin(omega*i*t)
                row = ndim*equation_idx
                col = ndim*unknown_idx
                for d in range(ndim):
                    A[row+d, col+d] = coeff

        if is_cyclic:
            equation_idx = len(tknots)
            for unknown_idx in range(n_equations):
                i = (unknown_idx // 2) + 1
                if unknown_idx % 2 == 0:
                    coeff = -omega*i*sin(omega*i) # - 0
                else:
                    coeff = omega*i*cos(omega*i) - omega*i
                row = ndim*equation_idx
                col = ndim*unknown_idx
                for d in range(ndim):
                    A[row+d, col+d] = coeff
        #print(A)

        B = np.empty((ndim*n_equations,1))
        for point_idx, point in enumerate(verts):
            row = ndim*point_idx
            B[row:row+ndim] = point[:,np.newaxis]
        
        if is_cyclic:
            point_idx = len(verts)
            row = ndim*point_idx
            B[row:row+ndim] = np.array([[0,0,0]]).T

        #print(B)

        x = np.linalg.solve(A, B)
        coeffs = []
        for i in range(n_equations):
            row = i*ndim
            coeff = x[row:row+ndim,0].T
            coeffs.append(coeff)
        coeffs = np.array(coeffs)
        #print(coeffs)
        
        return SvFourierCurve(omega, np.array([0.0,0.0,0.0]), coeffs)

