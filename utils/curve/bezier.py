# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.data_structure import zip_long_repeat
from sverchok.utils.math import binomial
from sverchok.utils.geom import Spline
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve, SvConcatCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.nurbs_common import elevate_bezier_degree

# Pure-python (+ numpy) Bezier curves implementation

class SvBezierCurve(SvCurve):
    """
    Bezier curve of arbitrary degree.
    """
    def __init__(self, points):
        self.points = points
        self.tangent_delta = 0.001
        n = self.degree = len(points) - 1
        self.__description__ = "Bezier[{}]".format(n)

    @classmethod
    def from_points_and_tangents(cls, p0, t0, t1, p1):
        """
        Build cubic Bezier curve, which goes from p0 to p1,
        and has tangent at 0 equal to t0 and tangent at 1 equal to t1.
        This is also called Hermite spline.

        inputs: p0, t0, t1, p1 - numpy arrays of shape (3,).
        """
        return SvCubicBezierCurve(
                p0,
                p0 + t0 / 3.0,
                p1 - t1 / 3.0,
                p1)

    @classmethod
    def blend_second_derivatives(cls, p0, v0, a0, p5, v5, a5):
        """
        Build Bezier curve of 5th order, which goes from p0 to p5, and has:
        * first derivative at 0 = v0, second derivative at 0 = a0;
        * first derivative at 1 = v5, second derivative at 1 = a1.

        inputs: numpy arrays of shape (3,).
        """
        p1 = p0 + v0 / 5.0
        p4 = p5 - v5 / 5.0
        p2 = a0/20.0 + 2*p1 - p0
        p3 = a5/20.0 + 2*p4 - p5
        return SvBezierCurve([p0, p1, p2, p3, p4, p5])

    @classmethod
    def blend_third_derivatives(cls, p0, v0, a0, k0, p7, v7, a7, k7):
        """
        Build Bezier curve of 7th order, which goes from p0 to p7, and has:
        * first derivative at 0 = v0, second derivative at 0 = a0, third derivative at 0 = k0;
        * first derivative at 1 = v7, second derivative at 1 = a7, third derivative at 1 = k7.

        inputs: numpy arrays of shape (3,).
        """
        p1 = p0 + v0 / 7.0
        p6 = p7 - v7 / 7.0
        p2 = a0/42.0 + 2*p1 - p0
        p5 = a7/42.0 + 2*p6 - p7
        p3 = k0/210.0 + 3*p2 - 3*p1 + p0
        p4 = -k7/210.0 + 3*p5 - 3*p6 + p7
        return SvBezierCurve([p0, p1, p2, p3, p4, p5, p6, p7])

    @classmethod
    def build_tangent_curve(cls, points, tangents, cyclic=False, concat=False):
        """
        Build cubic Bezier curve spline, which goes through specified `points',
        having specified `tangents' at these points.

        inputs:
        * points, tangents: lists of 3-tuples
        * cyclic: whether the curve should be closed (cyclic)
        * concat: whether to concatenate all curve segments into single Curve object

        outputs: tuple:
        * list of curve control points - list of lists of 3-tuples
        * list of generated curves; if concat == True, then this list will contain single curve.
        """
        new_curves = []
        new_controls = []

        pairs = list(zip_long_repeat(points, tangents))
        segments = list(zip(pairs, pairs[1:]))
        if cyclic:
            segments.append((pairs[-1], pairs[0]))

        for pair1, pair2 in segments:
            point1, tangent1 = pair1
            point2, tangent2 = pair2
            point1, tangent1 = np.array(point1), np.array(tangent1)
            point2, tangent2 = np.array(point2), np.array(tangent2)
            tangent1, tangent2 = tangent1/2.0, tangent2/2.0
            curve = SvCubicBezierCurve(
                        point1,
                        point1 + tangent1,
                        point2 - tangent2,
                        point2)
            curve_controls = [curve.p0.tolist(), curve.p1.tolist(),
                              curve.p2.tolist(), curve.p3.tolist()]
            new_curves.append(curve)
            new_controls.append(curve_controls)
        if concat:
            new_curves = [SvConcatCurve(new_curves)]

        return new_controls, new_curves

    @classmethod
    def interpolate(cls, points, metric='DISTANCE'):
        n = len(points)
        tknots = Spline.create_knots(points, metric=metric)
        matrix = np.zeros((3*n, 3*n))
        for equation_idx, t in enumerate(tknots):
            for unknown_idx in range(n):
                coeff = SvBezierCurve.coefficient(n-1, unknown_idx, np.array([t]))[0]
                #print(f"C[{equation_idx}][{unknown_idx}] = {coeff}")
                row = 3*equation_idx
                col = 3*unknown_idx
                matrix[row,col] = matrix[row+1, col+1] = matrix[row+2,col+2] = coeff
        #print(matrix)
        B = np.zeros((3*n, 1))
        for point_idx, point in enumerate(points):
            row = 3*point_idx
            B[row:row+3] = point[:,np.newaxis]
        #print(B)
        x = np.linalg.solve(matrix, B)
        #print(x)
        controls = []
        for i in range(n):
            row = i*3
            control = x[row:row+3,0].T
            controls.append(control)
            #print(control)
        return SvBezierCurve(controls)

    @classmethod
    def coefficient(cls, n, k, ts):
        C = binomial(n, k)
        return C * ts**k * (1 - ts)**(n-k)

    def coeff(self, k, ts):
        n = self.degree
        return SvBezierCurve.coefficient(n, k, ts)

    def coeff_deriv1(self, k, t):
        n = self.degree
        C = binomial(n, k)
        if k >= 1:
            s1 = k*(1-t)**(n-k)*t**(k-1)
        else:
            s1 = np.zeros_like(t)
        if n-k-1 > 0:
            s2 = - (n-k)*(1-t)**(n-k-1)*t**k
        elif n-k == 1:
            s2 = - t**k
        else:
            s2 = np.zeros_like(t)
        coeff = s1 + s2
        return C*coeff

    def coeff_deriv2(self, k, t):
        n = self.degree
        C = binomial(n, k)
        if n-k-2 > 0:
            s1 = (n-k-1)*(n-k)*(1-t)**(n-k-2)*t**k
        elif n-k == 2:
            s1 = 2*t**k
        else:
            s1 = np.zeros_like(t)
        if k >= 1 and n-k-1 > 0:
            s2 = - 2*k*(n-k)*(1-t)**(n-k-1)*t**(k-1)
        elif k >= 1 and n-k == 1:
            s2 = - 2*k*t**(k-1)
        else:
            s2 = np.zeros_like(t)
        if k >= 2:
            s3 = (k-1)*k*(1-t)**(n-k)*t**(k-2)
        else:
            s3 = np.zeros_like(t)
        coeff = s1 + s2 + s3
        return C*coeff

    def coeff_deriv3(self, k, t):
        n = self.degree
        C = binomial(n, k)
        if n-k-2 > 0:
            s1 = -(n-k-2)*(n-k-1)*(n-k)*(1-t)**(n-k-3)*t**k
        else:
            s1 = np.zeros_like(t)
        if k >= 1 and n-k-2 > 0:
            s2 = 3*k*(n-k-1)*(n-k)*(1-t)**(n-k-2)*t**(k-1)
        elif k >= 1 and n-k == 2:
            s2 = 6*k*t**(k-1)
        else:
            s2 = np.zeros_like(t)
        if k >= 2 and n-k-1 > 0:
            s3 = - 3*(k-1)*k*(n-k)*(1-t)**(n-k-1)*t**(k-2)
        elif k >= 2 and n-k == 1:
            s3 = -3*(k-1)*k*t**(k-2)
        else:
            s3 = np.zeros_like(t)
        if k >= 3:
            s4 = (k-2)*(k-1)*k*(1-t)**(n-k)*t**(k-3)
        else:
            s4 = np.zeros_like(t)
        coeff = s1 + s2 + s3 + s4
        return C*coeff

    def get_u_bounds(self):
        return (0.0, 1.0)

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        coeffs = [SvBezierCurve.coefficient(self.degree, k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        return np.dot(coeffs.T, self.points)

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        coeffs = [self.coeff_deriv1(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C1", coeffs)
        return np.dot(coeffs.T, self.points)

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        coeffs = [self.coeff_deriv2(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C2", coeffs)
        return np.dot(coeffs.T, self.points)

    def third_derivative_array(self, ts):
        coeffs = [self.coeff_deriv3(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C3", coeffs)
        return np.dot(coeffs.T, self.points)

    def derivatives_array(self, n, ts):
        result = []
        if n >= 1:
            first = self.tangent_array(ts)
            result.append(first)
        if n >= 2:
            second = self.second_derivative_array(ts)
            result.append(second)
        if n >= 3:
            third = self.third_derivative_array(ts)
            result.append(third)
        return result

    def get_degree(self):
        return self.degree

    def get_control_points(self):
        return self.points

    def elevate_degree(self, delta=1):
        points = elevate_bezier_degree(self.degree, self.points, delta)
        return SvBezierCurve(points)

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        knotvector = sv_knotvector.generate(self.degree, len(self.points))
        return SvNurbsMaths.build_curve(implementation,
                degree = self.degree, knotvector = knotvector,
                control_points = self.points)

class SvCubicBezierCurve(SvCurve):
    __description__ = "Bezier[3*]"
    def __init__(self, p0, p1, p2, p3):
        self.p0 = np.array(p0)
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)
        self.p3 = np.array(p3)
        self.tangent_delta = 0.001

    @classmethod
    def from_four_points(cls, v0, v1, v2, v3):
        v0 = np.array(v0)
        v1 = np.array(v1)
        v2 = np.array(v2)
        v3 = np.array(v3)

        p1 = (-5*v0 + 18*v1 - 9*v2 + 2*v3)/6.0
        p2 = (2*v0 - 9*v1 + 18*v2 - 5*v3)/6.0

        return SvCubicBezierCurve(v0, p1, p2, v3)

    def get_u_bounds(self):
        return (0.0, 1.0)

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        c0 = (1 - ts)**3
        c1 = 3*ts*(1-ts)**2
        c2 = 3*ts**2*(1-ts)
        c3 = ts**3
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        c0 = -3*(1 - ts)**2
        c1 = 3*(1-ts)**2 - 6*(1-ts)*ts
        c2 = 6*(1-ts)*ts - 3*ts**2
        c3 = 3*ts**2
        #print("C/C1", np.array([c0, c1, c2, c3]))
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        c0 = 6*(1-ts)
        c1 = 6*ts - 12*(1-ts)
        c2 = 6*(1-ts) - 12*ts
        c3 = 6*ts
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def third_derivative_array(self, ts):
        c0 = np.full_like(ts, -6)[:,np.newaxis]
        c1 = np.full_like(ts, 18)[:,np.newaxis]
        c2 = np.full_like(ts, -18)[:,np.newaxis]
        c3 = np.full_like(ts, 6)[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3
        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def derivatives_array(self, n, ts):
        result = []
        if n >= 1:
            first = self.tangent_array(ts)
            result.append(first)
        if n >= 2:
            second = self.second_derivative_array(ts)
            result.append(second)
        if n >= 3:
            third = self.third_derivative_array(ts)
            result.append(third)
        return result

    def get_degree(self):
        return 3

    def get_control_points(self):
        return np.array([self.p0, self.p1, self.p2, self.p3])

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        knotvector = sv_knotvector.generate(3, 4)
        control_points = np.array([self.p0, self.p1, self.p2, self.p3])
        return SvNurbsMaths.build_curve(implementation,
                degree = 3, knotvector = knotvector,
                control_points = control_points)

    def elevate_degree(self, delta=1):
        points = elevate_bezier_degree(3, self.get_control_points(), delta)
        return SvBezierCurve(points)

