# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
#from math import sqrt

from sverchok.data_structure import zip_long_repeat
from sverchok.core.sv_custom_exceptions import ArgumentError, SvInvalidInputException
from sverchok.utils.math import binomial, binomial_array, np_dot
from sverchok.utils.geom import Spline, bounding_box, are_points_coplanar, get_common_plane, PlaneEquation, LineEquation
from sverchok.utils.nurbs_common import SvNurbsMaths, nurbs_divide, to_homogenous, from_homogenous
from sverchok.utils.nurbs_common import SvNurbsMaths, nurbs_divide, to_homogenous, from_homogenous
from sverchok.utils.curve.core import SvCurve, SvTaylorCurve, UnsupportedCurveTypeException, calc_taylor_nurbs_matrices
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.nurbs_common import elevate_bezier_degree

# Pure-python (+ numpy) Bezier curves implementation

def de_casteljau_matrices(n, t):
    binom = binomial_array(n)
    L = binom.copy()
    R = binom.copy()
    R = R[::-1,::-1]
    I = np.arange(n)
    ts = t ** I
    t1s = (1 - t) ** I
    t1s = t1s[::-1]
    for k in range(n):
        L[k,:k+1] *= ts[:k+1]
        L[k,:k+1] *= t1s[n-k-1:]
        R[k,k:] *= ts[:n-k]
        R[k,k:] *= t1s[k:]
    return L, R

class SvBezierSplitMixin:
    def de_casteljau_points(self, t):
        ndim = 3
        p = self.get_degree()
        n = p+1
        dpts = np.zeros((n, n, ndim))
        dpts[:] = self.get_control_points()
        for j in range(1, n):
            for k in range(n - j):
                dpts[j,k] = dpts[j-1, k] * (1 - t) + dpts[j-1, k+1] * t
        return dpts

    #DeCasteljau variant
    def split_at(self, t):
        L, R = de_casteljau_matrices(self.get_degree()+1, t)
        cpts = self.get_control_points()
        cpts_L = L @ cpts
        cpts_R = R @ cpts
        curve_L = SvBezierCurve.from_control_points(cpts_L)
        curve_R = SvBezierCurve.from_control_points(cpts_R)
        return curve_L, curve_R

    def cut_segment(self, new_t_min, new_t_max, rescale=False):
        t2p = (new_t_max - new_t_min) / (1 - new_t_min)
        n = self.get_degree() + 1
        _, B = de_casteljau_matrices(n, new_t_min)
        A, _ = de_casteljau_matrices(n, t2p)
        cpts = self.get_control_points()
        cpts_res = A @ B @ cpts
        return SvBezierCurve.from_control_points(cpts_res)
        # if new_t_min >= 0:
        #     c1, c2 = self.split_at(new_t_min)
        # else:
        #     c2 = self
        # if new_t_max <= 1.0:
        #     t1 = (new_t_max - new_t_min) / (1.0 - new_t_min)
        #     c3, c4 = c2.split_at(t1)
        # else:
        #     c3 = c2
        # return c3

    # def cut_segment(self, new_t_min, new_t_max, rescale=False):
    #     if new_t_min == new_t_max:
    #         return None
    #     p = self.get_degree()
    #     cpts = self.get_control_points()
    #
    #     matrices = calc_taylor_nurbs_matrices(p, u_bounds=(new_t_min, new_t_max), calc_M=True, calc_R=True, calc_M1=True, calc_R1=True)
    #     M = matrices['M']
    #     R1 = matrices['R1']
    #     M1 = matrices['M1']
    #
    #     MR1M = M1 @ R1 @ M
    #
    #     new_cpts = MR1M @ cpts
    #     return SvBezierCurve.from_control_points(new_cpts)
    #
    # def split_at(self, t):
    #     segment1 = self.cut_segment(0.0, t)
    #     segment2 = self.cut_segment(t, 1.0)
    #     return segment1, segment2

_binom_square_matrices_cache = dict()

def _get_binom_square_matrix(p):
    global _binom_square_matrices_cache
    if p not in _binom_square_matrices_cache:
        binom = binomial_array(2*p+1)
        A = np.zeros((2*p+1, p+1, p+1))
        for k in range(2*p+1):
            I = np.arange(k+1)
            J = k - I
            good_ij = np.logical_and(I <= p, J <= p) 
            I = I[good_ij]
            J = J[good_ij]
            A[k, I, J] = binom[p, I] * binom[p, J]
        _binom_square_matrices_cache[p] = A
    return _binom_square_matrices_cache[p]

def calc_bezier_square_cpts(cpts, return_sum = True):
    p = len(cpts) - 1
    ndim = cpts.shape[-1]
    binom = binomial_array(2*p+1)

    def calc_square(cs):
        #ds = np.zeros((2*p+1,))
        cT = cs[np.newaxis].T
        A = _get_binom_square_matrix(p)
        #for k in range(2*p+1):
        #    ds[k] = cs @ A[k] @ cT
        #print("Ds", ds)
        ds = (cs @ A[:] @ cT)[:,0]
        denominator = binom[2*p, :]
        return ds / denominator

    if return_sum:
        new_cpts = np.zeros((2*p+1, 1))
        for i in range(ndim):
            sq = calc_square(cpts[:,i])
            new_cpts[:,0] += sq
        return new_cpts
    else:
        new_cpts = np.zeros((2*p+1, ndim))
        for i in range(ndim):
            new_cpts[:,i] = calc_square(cpts[:,i])
        return new_cpts

class SvBezierCommon:
    def is_bezier(self):
        return True

    def to_bezier(self):
        return self

    def to_bezier_segments(self, to_bezier_class=True):
        return [self]

    def get_bounding_box(self):
        return bounding_box(self.get_control_points())

    def reparametrize(self, new_t_min, new_t_max):
        return self.to_nurbs().reparametrize(new_t_min, new_t_max)

    def concatenate(self, curve2, tolerance=None):
        curve2 = SvNurbsMaths.to_nurbs_curve(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("Second curve is not a NURBS")
        return self.to_nurbs().concatenate(curve2, tolerance=tolerance)

    def make_revolution_surface(self, point, direction, v_min, v_max, global_origin):
        return self.to_nurbs().make_revolution_surface(point, direction, v_min, v_max, global_origin)
    
    def extrude_along_vector(self, vector):
        return self.to_nurbs().extrude_along_vector(vector)

    def make_ruled_surface(self, curve2, vmin, vmax):
        return self.to_nurbs().make_ruled_surface(curve2, vmin, vmax)

    def extrude_to_point(self, point):
        return self.to_nurbs().extrude_to_point(point)

    def is_planar(self, tolerance=1e-6):
        return are_points_coplanar(self.points, tolerance)

    def get_plane(self, tolerance=1e-6):
        return get_common_plane(self.points, tolerance)

    def bezier_distance_curve(self, src_point):
        cpts = self.get_control_points() - np.array(src_point)
        new_cpts = calc_bezier_square_cpts(cpts)
        #print(f"Square: {cpts} => {new_cpts}")
        return SvBezierCurve.from_control_points(new_cpts)

    def bezier_distance_n_sign_changes(self, src_point):
        cpts = self.get_control_points() - np.array(src_point)
        square_cvalues = calc_bezier_square_cpts(cpts)[:,0]
        #print(f"Cvalues: {square_cvalues}")
        cvalue_deltas = square_cvalues[1:] - square_cvalues[:-1]
        #print(f"Deltas: {cvalue_deltas}")
        result = 0
        for delta1, delta2 in zip(cvalue_deltas[:-1], cvalue_deltas[1:]):
            if delta1 * delta2 < 0:
                result += 1
        return result

class SvBezierCurve(SvCurve, SvBezierSplitMixin):
    def is_inside_sphere(self, sphere_center, sphere_radius):
        """
        Check that the whole curve lies inside the specified sphere
        """
        # Because of NURBS curve's "strong convex hull property",
        # if all control points of the curve lie inside the sphere,
        # then the whole curve lies inside the sphere too.
        # This relies on the fact that the sphere is a convex set of points.
        cpts = self.get_control_points()
        #distances = np.linalg.norm(cpts - sphere_center, axis=1)
        #return (distances < sphere_radius).all()
        dvs = cpts - sphere_center
        distances2 = (dvs * dvs).sum(axis=1)
        return (distances2 < sphere_radius**2).all()

    def bezier_is_strongly_outside_sphere(self, sphere_center, sphere_radius):
        # See comment for SvNurbsCurve.bezier_is_strongly_outside_sphere()
        square_curve = self.bezier_distance_curve(sphere_center)
        square_coeffs = square_curve.get_control_points()[:,0]
        #print(f"Check: {square_coeffs - sphere_radius**2}")
        return (square_coeffs > sphere_radius**2).all()

    def bezier_has_one_nearest_point(self, src_point):
        distance_curve = self.bezier_distance_curve(src_point)
        square_cpts = distance_curve.get_control_points()
        square_coeffs = square_cpts[:,0]

        should_grow = False
        result = True
        for p1, p2 in zip(square_coeffs, square_coeffs[1:]):
            if not should_grow and not (p1 > p2):
                should_grow = True
            elif should_grow and not (p1 < p2):
                result = False
                break
        return result

class SvBezierCurve(SvCurve, SvBezierCommon, SvBezierSplitMixin):
    """
    Bezier curve of arbitrary degree.
    """
    def __init__(self, points):
        self.points = np.asarray(points)
        self.tangent_delta = 0.001
        n = self.degree = len(points) - 1
        self.__description__ = "Bezier[{}]".format(n)
        self.tilt_pairs = []

    def copy(self, control_points = None):
        if control_points is None:
            control_points = self.points
        return SvBezierCurve.from_control_points(control_points)

    @classmethod
    def from_control_points(cls, points):
        if len(points) == 4:
            return SvCubicBezierCurve(points[0], points[1], points[2], points[3])
        else:
            return SvBezierCurve(points)

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
        p2 = p0 + 0.4*v0 + a0/20.0
        p3 = p5 - 0.4*v5 + a5/20.0
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

#     @classmethod
#     def from_tangents_and_curvatures(cls, point1, point2, tangent1, tangent2, curvature1, curvature2):
#         A1 = point1
#         A2 = point2
#         B1 = point1 + tangent1 / 5
#         B2 = point2 - tangent2 / 5
#         t1dir = tangent1 / np.linalg.norm(tangent1)
#         t2dir = tangent2 / np.linalg.norm(tangent2)
#         B1B2 = B2 - B1
#         direction = B1B2 / np.linalg.norm(B1B2)
#         
#         r1 = curvature1 * np.linalg.norm(tangent1)**2 / 20
#         r2 = curvature2 * np.linalg.norm(tangent2)**2 / 20
#         
#         dot1 = (direction * t1dir).sum()
#         sin1 = sqrt(1 - dot1**2)
#         d1 = r1 / sin1
#         
#         dot2 = (-direction * t2dir).sum()
#         sin2 = sqrt(1 - dot2**2)
#         d2 = r2 / sin2
#         
#         C1 = B1 + d1 * direction
#         C2 = B2 - d2 * direction
#         
#         return SvBezierCurve([A1, B1, C1, C2, B2, A2])

    @classmethod
    def from_tangents_normals_curvatures(cls, point1, point2, tangent1, tangent2, normal1, normal2, curvature1, curvature2):
        """
        Build Bezier curve of 5th degree, which:
            
            * starts at point1 and end at point2
            * at start has tangent1 and normal1, at end has tangent2 and normal2
            * at start has curvature1, at end has curvature2.
        """
        A1 = point1
        A2 = point2
        B1 = point1 + tangent1 / 5
        B2 = point2 - tangent2 / 5
        t1dir = tangent1 / np.linalg.norm(tangent1)
        t2dir = tangent2 / np.linalg.norm(tangent2)
        n1dir = normal1 / np.linalg.norm(normal1)
        n2dir = normal2 / np.linalg.norm(normal2)

        r1 = curvature1 * np.linalg.norm(tangent1)**2 / 20
        r2 = curvature2 * np.linalg.norm(tangent2)**2 / 20

        b = (B2 - B1) / np.linalg.norm(B2 - B1)

#         cos_alpha1 = np.dot(t1dir, b)
#         cos_beta1 = np.dot(n1dir, b)
#         t12 = (r1 * cos_beta1) / (1 - cos_alpha1**2)
#         t11 = cos_alpha1 * t12
#         C1 = B1 + r1 * n1dir + t11 * t1dir
        C1 = B1 + r1 * n1dir + (B1 - A1)

#         cos_alpha2 = np.dot(t2dir, -b)
#         cos_beta2 = np.dot(n2dir, -b)
#         t22 = (r2 * cos_beta2) / (1 - cos_alpha2**2)
#         t21 = cos_alpha2 * t22
#         C2 = B2 + r2 * n2dir + t21 * t2dir
        C2 = B2 + r2 * n2dir + (B2 - A2)

        return SvBezierCurve([A1, B1, C1, C2, B2, A2])

    @classmethod
    def build_tangent_curve(cls, points, tangents, hermite=True, cyclic=False, concat=False, as_nurbs=False):
        """
        Build cubic Bezier curve spline, which goes through specified `points',
        having specified `tangents' at these points.

        inputs:
        * points, tangents: lists of 3-tuples
        * cyclic: whether the curve should be closed (cyclic)
        * concat: whether to concatenate all curve segments into single Curve object
        * hermite: if true, use Hermite spline - divide tangent vector by 3 to
            obtain middle control points; otherwise, divide by 2.

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
        if hermite:
            d = 3.0
        else:
            d = 2.0

        for pair1, pair2 in segments:
            point1, tangent1 = pair1
            point2, tangent2 = pair2
            point1, tangent1 = np.array(point1), np.array(tangent1)
            point2, tangent2 = np.array(point2), np.array(tangent2)
            tangent1, tangent2 = tangent1/d, tangent2/d
            curve = SvCubicBezierCurve(
                        point1,
                        point1 + tangent1,
                        point2 - tangent2,
                        point2)
            curve_controls = [curve.p0.tolist(), curve.p1.tolist(),
                              curve.p2.tolist(), curve.p3.tolist()]
            if as_nurbs:
                curve = curve.to_nurbs()
            new_curves.append(curve)
            new_controls.append(curve_controls)
        if concat:
            new_curve = concatenate_curves(new_curves)
            new_curves = [new_curve]
            if as_nurbs:
                new_controls = new_curve.get_control_points().tolist()

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

    def mirror(self, axis):
        m = np.eye(3)
        m[axis,axis] = -1
        controls = np.apply_along_axis(lambda p: m @ p, 1, self.points)
        return SvBezierCurve(controls)

    def translate(self, vector):
        vector = np.asarray(vector)
        return SvBezierCurve(vector + self.points)
    
    def is_line(self, tolerance=0.001):
        cpts = self.get_control_points()
        begin, end = cpts[0], cpts[-1]
        # direction from first to last point of the curve
        direction = end - begin
        if np.linalg.norm(direction) < tolerance:
            return True
        line = LineEquation.from_direction_and_point(direction, begin)
        distances = line.distance_to_points(cpts[1:-1])
        # Technically, this means that all control points lie
        # inside the cylinder, defined as "distance from line < tolerance";
        # As a consequence, the convex hull of control points lie in the
        # same cylinder; and the curve lies in that convex hull.
        return (distances < tolerance).all()

    def get_end_points(self):
        return self.points[0], self.points[-1]

    def get_tilt_pairs(self):
        return self.tilt_pairs

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

    def tangent(self, t, tangent_delta=None):
        return self.tangent_array(np.array([t]), tangent_delta=tangent_delta)[0]

    def tangent_array(self, ts, tangent_delta=None):
        coeffs = [self.coeff_deriv1(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C1", coeffs)
        return np.dot(coeffs.T, self.points)

    def second_derivative(self, t, tangent_delta=None):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts, tangent_delta=None):
        coeffs = [self.coeff_deriv2(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C2", coeffs)
        return np.dot(coeffs.T, self.points)

    def third_derivative_array(self, ts, tangent_delta=None):
        coeffs = [self.coeff_deriv3(k, ts) for k in range(len(self.points))]
        coeffs = np.array(coeffs)
        #print("C3", coeffs)
        return np.dot(coeffs.T, self.points)

    def derivatives_array(self, n, ts, tangent_delta=None):
        result = []
        if n >= 1:
            first = self.tangent_array(ts, tangent_delta=tangent_delta)
            result.append(first)
        if n >= 2:
            second = self.second_derivative_array(ts, tangent_delta=tangent_delta)
            result.append(second)
        if n >= 3:
            third = self.third_derivative_array(ts, tangent_delta=tangent_delta)
            result.append(third)
        return result

    def get_degree(self):
        return self.degree

    def is_rational(self):
        return False

    def get_control_points(self):
        return self.points

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

        points = elevate_bezier_degree(self.degree, self.points, delta)
        return SvBezierCurve(points)

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        knotvector = sv_knotvector.generate(self.degree, len(self.points))
        return SvNurbsMaths.build_curve(implementation,
                degree = self.degree, knotvector = knotvector,
                control_points = self.points)

    def lerp_to(self, curve2, coefficient):
        if isinstance(curve2, SvBezierCurve) and curve2.degree == self.degree:
            points = (1.0 - coefficient) * self.points + coefficient * curve2.points
            return SvBezierCurve(points)
        return self.to_nurbs().lerp_to(curve2, coefficient)

    def reverse(self):
        return SvBezierCurve(self.points[::-1])

    def bezier_to_taylor(self):
        # Refer to The NURBS Book, 2nd ed., p. 6.6
        p = self.get_degree()
        cpts = self.get_homogenous_control_points()
        ndim = cpts.shape[-1]
        #print(f"Cpts {cpts}")

        mr = calc_taylor_nurbs_matrices(p, self.get_u_bounds(), calc_R = False)
        M = mr['M']

        coeffs = np.zeros((ndim, p+1))
        for k in range(ndim):
            coeffs[k] = M @ cpts[:,k]

        taylor = SvTaylorCurve.from_coefficients(coeffs.T)
        taylor.u_bounds = self.get_u_bounds()
        return taylor

class SvCubicBezierCurve(SvCurve, SvBezierCommon, SvBezierSplitMixin):
    __description__ = "Bezier[3*]"
    def __init__(self, p0, p1, p2, p3):
        self.p0 = np.array(p0)
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)
        self.p3 = np.array(p3)
        self.tangent_delta = 0.001
        self.tilt_pairs = []

    def copy(self, control_points = None):
        if control_points is None:
            control_points = self.points
        return SvBezierCurve.from_control_points(control_points)


    @classmethod
    def from_four_points(cls, v0, v1, v2, v3):
        v0 = np.array(v0)
        v1 = np.array(v1)
        v2 = np.array(v2)
        v3 = np.array(v3)

        p1 = (-5*v0 + 18*v1 - 9*v2 + 2*v3)/6.0
        p2 = (2*v0 - 9*v1 + 18*v2 - 5*v3)/6.0

        return SvCubicBezierCurve(v0, p1, p2, v3)

    def mirror(self, axis):
        m = np.eye(3)
        m[axis,axis] = -1
        controls = np.apply_along_axis(lambda p: m @ p, 1, self.get_control_points())
        return SvCubicBezierCurve(*controls)

    def translate(self, vector):
        vector = np.asarray(vector)
        controls = vector + self.get_control_points()
        return SvCubicBezierCurve(*controls)

    def get_u_bounds(self):
        return (0.0, 1.0)

    def get_tilt_pairs(self):
        return self.tilt_pairs

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

    def tangent(self, t, tangent_delta=None):
        return self.tangent_array(np.array([t]), tangent_delta=tangent_delta)[0]

    def tangent_array(self, ts, tangent_delta=None):
        c0 = -3*(1 - ts)**2
        c1 = 3*(1-ts)**2 - 6*(1-ts)*ts
        c2 = 6*(1-ts)*ts - 3*ts**2
        c3 = 3*ts**2
        #print("C/C1", np.array([c0, c1, c2, c3]))
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def second_derivative(self, t, tangent_delta=None):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        c0 = 6*(1-ts)
        c1 = 6*ts - 12*(1-ts)
        c2 = 6*(1-ts) - 12*ts
        c3 = 6*ts
        c0, c1, c2, c3 = c0[:,np.newaxis], c1[:,np.newaxis], c2[:,np.newaxis], c3[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3

        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def third_derivative_array(self, ts, tangent_delta=None):
        c0 = np.full_like(ts, -6)[:,np.newaxis]
        c1 = np.full_like(ts, 18)[:,np.newaxis]
        c2 = np.full_like(ts, -18)[:,np.newaxis]
        c3 = np.full_like(ts, 6)[:,np.newaxis]
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3
        return c0*p0 + c1*p1 + c2*p2 + c3*p3

    def derivatives_array(self, n, ts, tangent_delta=None):
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

    def is_rational(self):
        return False

    def get_end_points(self):
        return self.p0, self.p3

    def get_control_points(self):
        return np.array([self.p0, self.p1, self.p2, self.p3])

    def get_homogenous_control_points(self):
        hom_cpts = np.ones((4, 4))
        hom_cpts[:,:3] = self.get_control_points()
        return hom_cpts

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        knotvector = sv_knotvector.generate(3, 4)
        control_points = np.array([self.p0, self.p1, self.p2, self.p3])
        return SvNurbsMaths.build_curve(implementation,
                degree = 3, knotvector = knotvector,
                control_points = control_points)

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

        points = elevate_bezier_degree(3, self.get_control_points(), delta)
        return SvBezierCurve(points)

    def get_bounding_box(self):
        return bounding_box(self.get_control_points())

    def lerp_to(self, curve2, coefficient):
        if isinstance(curve2, SvCubicBezierCurve):
            p0 = (1.0 - coefficient) * self.p0 + coefficient * curve2.p0
            p1 = (1.0 - coefficient) * self.p1 + coefficient * curve2.p1
            p2 = (1.0 - coefficient) * self.p2 + coefficient * curve2.p2
            p3 = (1.0 - coefficient) * self.p3 + coefficient * curve2.p3
            return SvCubicBezierCurve(p0, p1, p2, p3)
        return self.to_nurbs().lerp_to(curve2, coefficient)

    def is_line(self, tolerance=0.001):
        begin, end = self.p0, self.p3
        # direction from first to last point of the curve
        direction = end - begin
        if np.linalg.norm(direction) < tolerance:
            return True
        line = LineEquation.from_direction_and_point(direction, begin)
        distances = line.distance_to_points([self.p1, self.p2])
        # Technically, this means that all control points lie
        # inside the cylinder, defined as "distance from line < tolerance";
        # As a consequence, the convex hull of control points lie in the
        # same cylinder; and the curve lies in that convex hull.
        return (distances < tolerance).all()

    def is_planar(self, tolerance=1e-6):
        plane = PlaneEquation.from_three_points(self.p0, self.p1, self.p2)
        return plane.distance_to_point(self.p3) < tolerance

    def get_plane(self, tolerance=1e-6):
        plane = PlaneEquation.from_three_points(self.p0, self.p1, self.p2)
        if plane.distance_to_point(self.p3) < tolerance:
            return plane
        else:
            return None

    def to_bezier(self):
        return self

    def to_bezier_segments(self, to_bezier_class=True):
        return [self]

    def reverse(self):
        return SvCubicBezierCurve(self.p3, self.p2, self.p1, self.p0)

def split_homogenous(homogenous_pts):
    points = homogenous_pts[:,:-1]
    weights = homogenous_pts[:,-1]
    return points, weights

class SvRationalBezierCurve(SvCurve, SvBezierCommon):
    __description__ = "Rational Bezier"
    def __init__(self, points, weights):
        self.points = np.asarray(points)
        self.weights = np.asarray(weights)
        self.homogenous_curve = SvBezierCurve.from_control_points(to_homogenous(self.points, self.weights))

    @classmethod
    def build(cls, points, weights=None):
        if weights is None:
            n = len(points)
            weights = np.ones((n,))
        return SvRationalBezierCurve(points, weights)

    @classmethod
    def from_homogenous_curve(cls, homogenous_curve):
        homogenous_cpts = homogenous_curve.get_control_points()
        points, weights = from_homogenous(homogenous_cpts)
        return SvRationalBezierCurve(points, weights)

    def copy(self, control_points = None, weights = None):
        if control_points is None:
            control_points = self.points
        if weights is None:
            weights = self.weights
        return SvRationalBezierCurve(control_points, weights)

    def get_u_bounds(self):
        return (0.0, 1.0)

    def get_degree(self):
        return len(self.points) - 1

    def get_control_points(self):
        return self.points

    def get_weights(self):
        return self.weights

    def get_homogenous_control_points(self):
        return self.homogenous_curve.get_control_points()

    def get_end_points(self):
        return self.points[0], self.points[-1]

    def evaluate_array(self, ts):
        homogenous = self.homogenous_curve.evaluate_array(ts)
        points, weights = split_homogenous(homogenous)
        return nurbs_divide(points, weights)

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def tangent_array(self, ts, tangent_delta=None):
        # curve = numerator / denominator
        # ergo:
        # numerator = curve * denominator
        # ergo:
        # numerator' = curve' * denominator + curve * denominator'
        # ergo:
        # curve' = (numerator' - curve*denominator') / denominator
        homogenous = self.homogenous_curve.evaluate_array(ts)
        numerator, denominator = split_homogenous(homogenous)
        denominator = denominator[np.newaxis].T
        curve = numerator / denominator
        homogenous1 = self.homogenous_curve.tangent_array(ts)
        numerator1, denominator1 = split_homogenous(homogenous1)
        denominator1 = denominator1[np.newaxis].T
        curve1 = (numerator1 - curve*denominator1) / denominator
        return curve1

    def tangent(self, t, tangent_delta=None):
        return self.tangent_array(np.array([t]))[0]

    def reparametrize(self, new_t_min, new_t_max):
        return self.to_nurbs().reparametrize(new_t_min, new_t_max)

    def is_rational(self, tolerance=1e-6):
        weights = self.get_weights()
        w, W = weights.min(), weights.max()
        return (W - w) > tolerance

    def elevate_degree(self, delta=None, target=None):
        if delta is None and target is None:
            delta = 1
        if delta is not None and target is not None:
            raise ArgumentError("Of delta and target, only one parameter can be specified")
        degree = self.get_degree()
        if delta is None:
            delta = target - degree
            if delta < 0:
                raise SvInvalidInputException(f"Curve already has degree {degree}, which is greater than target {target}")
        if delta == 0:
            return self

        control_points = self.homogenous_curve.get_control_points()
        control_points = elevate_bezier_degree(degree, control_points, delta)
        control_points, weights = from_homogenous(control_points)
        return SvRationalBezierCurve(control_points, weights)

    def bezier_distance_curve(self, src_point):
        src_point = np.array(src_point)
        cpts = self.points - src_point
        homogenous = to_homogenous(cpts, self.weights)
        homogenous_square_cpts = calc_bezier_square_cpts(homogenous, return_sum=False)
        new_cpts, new_weights = from_homogenous(homogenous_square_cpts)
        new_cpts_1d = new_cpts.sum(axis=1)[np.newaxis].T
        return SvRationalBezierCurve(new_cpts_1d, new_weights)

    def to_nurbs(self, implementation=SvNurbsMaths.NATIVE):
        knotvector = sv_knotvector.generate(self.get_degree(), len(self.points))
        return SvNurbsMaths.build_curve(implementation,
                degree = self.get_degree(), knotvector = knotvector,
                control_points = self.points, weights = self.weights)
    
    def reverse(self):
        return SvRationalBezierCurve(self.points[::-1], self.weights[::-1])
    
    def split_at(self, t):
        hom1, hom2 = self.homogenous_curve.split_at(t)
        if hom1 is not None:
            segment1 = SvRationalBezierCurve.from_homogenous_curve(hom1)
        else:
            segment1 = None
        if hom2 is not None:
            segment2 = SvRationalBezierCurve.from_homogenous_curve(hom2)
        else:
            segment2 = None
        return segment1, segment2

    def cut_segment(self, new_t_min, new_t_max, rescale=False):
        hom = self.homogenous_curve.cut_segment(new_t_min, new_t_max)
        if hom is None:
            return None
        return SvRationalBezierCurve.from_homogenous_curve(hom)
        # if new_t_min >= 0:
        #     c1, c2 = self.split_at(new_t_min)
        # else:
        #     c2 = self
        # if new_t_max <= 1.0:
        #     t1 = (new_t_max - new_t_min) / (1.0 - new_t_min)
        #     c3, c4 = c2.split_at(t1)
        # else:
        #     c3 = c2
        # return c3

