# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from copy import deepcopy
import numpy as np
from math import pi, sqrt
import traceback

from sverchok.utils.logging import info
from sverchok.utils.curve.core import SvCurve, SvTaylorCurve, UnsupportedCurveTypeException, calc_taylor_nurbs_matrices
from sverchok.utils.curve.bezier import SvBezierCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import unify_curves_degree
from sverchok.utils.curve.nurbs_algorithms import interpolate_nurbs_curve, unify_two_curves, unify_curves
from sverchok.utils.nurbs_common import (
        SvNurbsMaths,SvNurbsBasisFunctions,
        nurbs_divide, elevate_bezier_degree, from_homogenous,
        CantInsertKnotException, CantRemoveKnotException
    )
from sverchok.utils.surface.nurbs import SvNativeNurbsSurface, SvGeomdlSurface
from sverchok.utils.surface.algorithms import nurbs_revolution_surface
from sverchok.utils.math import binomial_array, cmp
from sverchok.utils.geom import bounding_box, LineEquation
from sverchok.utils.logging import getLogger
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

    ALL = 'ALL'
    ALL_BUT_ONE = 'ALL_BUT_ONE'

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

    def copy(self, implementation = None, knotvector = None, control_points = None, weights = None, normalize_knots=False):
        if implementation is None:
            implementation = self.get_nurbs_implementation()
        if knotvector is None:
            knotvector = self.get_knotvector()
        if control_points is None:
            control_points = self.get_control_points()
        if weights is None:
            weights = self.get_weights()

        return SvNurbsCurve.build(implementation,
                    self.get_degree(), knotvector,
                    control_points, weights,
                    normalize_knots = normalize_knots)

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

    def get_bounding_box(self):
        if not hasattr(self, '_bounding_box') or self._bounding_box is None:
            self._bounding_box = bounding_box(self.get_control_points())
        return self._bounding_box

    def concatenate(self, curve2, tolerance=1e-6, remove_knots=False):
        curve1 = self
        curve2 = SvNurbsCurve.to_nurbs(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("second curve is not NURBS")
        
        c1_end = curve1.get_u_bounds()[1]
        c2_start = curve2.get_u_bounds()[0]
        if sv_knotvector.is_clamped(curve1.get_knotvector(), curve1.get_degree(), check_start=True, check_end=False):
            pt1 = curve1.get_control_points()[-1]
        else:
            pt1 = curve1.evaluate(c1_end)
        if sv_knotvector.is_clamped(curve2.get_knotvector(), curve2.get_degree(), check_start=False, check_end=True):
            pt2 = curve2.get_control_points()[0]
        else:
            pt2 = curve2.evaluate(c2_start)
        dpt = np.linalg.norm(pt1 - pt2)
        if dpt > tolerance:
            raise UnsupportedCurveTypeException(f"Curve end points do not match: C1({c1_end}) = {pt1} != C2({c2_start}) = {pt2}, distance={dpt}")

        cp1 = curve1.get_control_points()[-1]
        cp2 = curve2.get_control_points()[0]
        if np.linalg.norm(cp1 - cp2) > tolerance:
            raise UnsupportedCurveTypeException("End control points do not match")

        w1 = curve1.get_weights()[-1]
        w2 = curve2.get_weights()[0]
        if abs(w1 - w2) > tolerance:
            raise UnsupportedCurveTypeException(f"Weights at endpoints do not match: {w1} != {w2}")

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

        result = SvNurbsCurve.build(self.get_nurbs_implementation(),
                p, knotvector, control_points, weights)
        if remove_knots is not None:
            if remove_knots == True:
                remove_knots = p-1
            join_point = kv1[-1]
            result = result.remove_knot(join_point, count=remove_knots, if_possible=True)
        return result

    def lerp_to(self, curve2, coefficient):
        curve1 = self
        curve2 = SvNurbsCurve.to_nurbs(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("second curve is not NURBS")
        curve1, curve2 = unify_curves_degree([curve1, curve2])
        curve1, curve2 = unify_two_curves(curve1, curve2)

        #c1cp = curve1.get_homogenous_control_points()
        #c2cp = curve2.get_homogenous_control_points()
        c1cp = curve1.get_control_points()
        c2cp = curve2.get_control_points()
        ws1 = curve1.get_weights()
        ws2 = curve2.get_weights()

        points = c1cp * (1 - coefficient) + coefficient * c2cp

        weights = ws1 * (1 - coefficient) + coefficient * ws2

        return SvNurbsCurve.build(curve1.get_nurbs_implementation(),
                curve1.get_degree(),
                curve1.get_knotvector(),
                points, weights)

    def make_ruled_surface(self, curve2, vmin, vmax):
        curve = self
        curve2 = SvNurbsCurve.to_nurbs(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("second curve is not NURBS")
        curve, curve2 = unify_curves_degree([curve, curve2])
        if curve.get_degree() != curve2.get_degree():
            raise UnsupportedCurveTypeException(f"curves have different degrees: {curve.get_degree()} != {curve2.get_degree()}")

        #print(f"kv1: {curve.get_knotvector().shape}, kv2: {curve2.get_knotvector().shape}")
        kv1, kv2 = curve.get_knotvector(), curve2.get_knotvector()
        if kv1.shape != kv2.shape or (kv1 != kv2).any():
            curve, curve2 = unify_two_curves(curve, curve2)
            #raise UnsupportedCurveTypeException("curves have different knot vectors")

        my_control_points = curve.get_control_points()
        other_control_points = curve2.get_control_points()
        if len(my_control_points) != len(other_control_points):
            raise UnsupportedCurveTypeException("curves have different number of control points")

        if vmin != 0:
            my_control_points = (1 - vmin) * my_control_points + vmin * other_control_points
        if vmax != 0:
            other_control_points = (1 - vmax) * my_control_points + vmax * other_control_points

        control_points = np.stack((my_control_points, other_control_points))
        control_points = np.transpose(control_points, axes=(1,0,2))

        weights = np.stack((curve.get_weights(), curve2.get_weights())).T
        knotvector_v = sv_knotvector.generate(1, 2, clamped=True)

        surface = SvNurbsMaths.build_surface(self.get_nurbs_implementation(),
                        degree_u = curve.get_degree(), degree_v = 1,
                        knotvector_u = curve.get_knotvector(), knotvector_v = knotvector_v,
                        control_points = control_points,
                        weights = weights)
        return surface

    def extrude_to_point(self, point):
        my_control_points = self.get_control_points()
        n = len(my_control_points)
        other_control_points = np.empty((n,3))
        other_control_points[:] = point

        control_points = np.stack((my_control_points, other_control_points))
        control_points = np.transpose(control_points, axes=(1,0,2))

        my_weights = self.get_weights()
        other_weights = my_weights
        #other_weights = np.ones((n,))
        weights = np.stack((my_weights, other_weights)).T

        knotvector_u = self.get_knotvector()
        knotvector_v = sv_knotvector.generate(1, 2, clamped=True)

        degree_u = self.get_degree()
        degree_v = 1

        surface = SvNurbsMaths.build_surface(self.get_nurbs_implementation(),
                        degree_u, degree_v,
                        knotvector_u, knotvector_v,
                        control_points, weights)
        return surface

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

    def is_rational(self, tolerance=1e-6):
        weights = self.get_weights()
        w, W = weights.min(), weights.max()
        return (W - w) > tolerance

    def get_knotvector(self):
        """
        returns: np.array of shape (X,)
        """
        raise Exception("Not implemented!")

    def get_degree(self):
        raise Exception("Not implemented!")

    def elevate_degree(self, delta=None, target=None):
        orig_delta, orig_target = delta, target
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
            src_t_min, src_t_max = self.get_u_bounds()
            segments = self.to_bezier_segments(to_bezier_class=False)
            segments = [segment.elevate_degree(orig_delta, orig_target) for segment in segments]
            result = segments[0]
            for segment in segments[1:]:
                result = result.concatenate(segment)
            result = result.reparametrize(src_t_min, src_t_max)
            return result
            #raise UnsupportedCurveTypeException("Degree elevation is not implemented for non-bezier curves yet")

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

    def _split_at(self, t):
        # Split without building SvNurbsCurve objects:
        # Some implementations (geomdl in particular)
        # can check number of control points vs curve degree,
        # and that can be bad for very small segments;
        # on the other hand, we may not care about it
        # if we are throwing away that small segment and
        # going to use only the bigger one.

        t_min, t_max = self.get_u_bounds()

        # corner cases
        if t <= t_min:
            return None, (self.get_knotvector(), self.get_control_points(), self.get_weights())
        if t >= t_max:
            return (self.get_knotvector(), self.get_control_points(), self.get_weights()), None

        current_multiplicity = sv_knotvector.find_multiplicity(self.get_knotvector(), t)
        to_add = self.get_degree() - current_multiplicity # + 1
        curve = self.insert_knot(t, count=to_add)
        knot_span = np.searchsorted(curve.get_knotvector(), t)

        ts = np.full((self.get_degree()+1,), t)
        knotvector1 = np.concatenate((curve.get_knotvector()[:knot_span], ts))
        knotvector2 = np.insert(curve.get_knotvector()[knot_span:], 0, t)

        control_points_1 = curve.get_control_points()[:knot_span]
        control_points_2 = curve.get_control_points()[knot_span-1:]
        weights_1 = curve.get_weights()[:knot_span]
        weights_2 = curve.get_weights()[knot_span-1:]

        #print(f"S: ctlpts1: {len(control_points_1)}, 2: {len(control_points_2)}")
        kv_error = sv_knotvector.check(curve.get_degree(), knotvector1, len(control_points_1))
        if kv_error is not None:
            raise Exception(kv_error)
        kv_error = sv_knotvector.check(curve.get_degree(), knotvector2, len(control_points_2))
        if kv_error is not None:
            raise Exception(kv_error)

        curve1 = (knotvector1, control_points_1, weights_1)
        curve2 = (knotvector2, control_points_2, weights_2)
        return curve1, curve2

    def split_at(self, t):
        c1, c2 = self._split_at(t)
        degree = self.get_degree()
        implementation = self.get_nurbs_implementation()

        if c1 is not None:
            knotvector1, control_points_1, weights_1 = c1
            curve1 = SvNurbsCurve.build(implementation,
                        degree, knotvector1,
                        control_points_1, weights_1)
        else:
            curve1 = None

        if c2 is not None:
            knotvector2, control_points_2, weights_2 = c2

            curve2 = SvNurbsCurve.build(implementation,
                        degree, knotvector2,
                        control_points_2, weights_2)
        else:
            curve2 = None

        return curve1, curve2

    def cut_segment(self, new_t_min, new_t_max, rescale=False):
        t_min, t_max = self.get_u_bounds()
        degree = self.get_degree()
        implementation = self.get_nurbs_implementation()
        curve = self
        params = (self.get_knotvector(), self.get_control_points(), self.get_weights())
        if new_t_min > t_min:
            _, params = curve._split_at(new_t_min)
            if params is None:
                raise Exception(f"Cut 1: {new_t_min} - {new_t_max} from {t_min} - {t_max}")
            knotvector, control_points, weights = params
            curve = SvNurbsCurve.build(implementation,
                        degree, knotvector,
                        control_points, weights)
        if new_t_max < t_max:
            params, _ = curve._split_at(new_t_max)
            if params is None:
                raise Exception(f"Cut 2: {new_t_min} - {new_t_max} from {t_min} - {t_max}")
            knotvector, control_points, weights = params
            curve = SvNurbsCurve.build(implementation,
                        degree, knotvector,
                        control_points, weights)
        t1, t2 = curve.get_u_bounds()
        if rescale:
            curve = curve.reparametrize(0, 1)
        return curve

    def get_end_points(self):
        if sv_knotvector.is_clamped(self.get_knotvector(), self.get_degree()):
            cpts = self.get_control_points()
            return cpts[0], cpts[-1]
        else:
            u_min, u_max = self.get_u_bounds()
            begin = self.evaluate(u_min)
            end = self.evaluate(u_max)
            return begin, end

    def is_closed(self, tolerance=1e-6):
        begin, end = self.get_end_points()
        return np.linalg.norm(begin - end) < tolerance

    def is_line(self, tolerance=0.001):
        """
        Check that the curve is nearly a straight line segment.
        This implementation relies on the property of NURBS curves,
        known as "strong convex hull property": the whole curve is lying
        inside the convex hull of it's control points.
        """

        begin, end = self.get_end_points()
        cpts = self.get_control_points()
        # direction from first to last point of the curve
        direction = cpts[-1] - cpts[0]
        line = LineEquation.from_direction_and_point(direction, begin)
        distances = line.distance_to_points(cpts)
        # Technically, this means that all control points lie
        # inside the cylinder, defined as "distance from line < tolerance";
        # As a consequence, the convex hull of control points lie in the
        # same cylinder; and the curve lies in that convex hull.
        return (distances < tolerance).all()

    def calc_linear_segment_knots(self, splits=2, tolerance=0.001):
        """
        Calculate T values, which split the curve into segments in
        such a way that each segment is nearly a straight line segment.
        """

        def calc_knots(segment, u1, u2):
            if not segment.is_closed(tolerance) and segment.is_line(tolerance):
                return set([u1, u2])
            else:
                us = np.linspace(u1, u2, num=int(splits+1))
                ranges = list(zip(us, us[1:]))
                segments = [segment.cut_segment(u, v) for u, v in ranges]
                all_knots = [calc_knots(segment, u1, u2) for segment, (u1, u2) in zip(segments, ranges)]
                knots = set()
                for ks in all_knots:
                    knots = knots.union(ks)
                return knots
        
        u1, u2 = self.get_u_bounds()
        knots = np.array(sorted(calc_knots(self, u1, u2)))
        return knots

    def to_bezier(self):
        points = self.get_control_points()
        if not self.is_bezier():
            n = len(points)
            p = self.get_degree()
            raise UnsupportedCurveTypeException(f"Curve with {n} control points and {p}'th degree can not be converted into Bezier curve")
        return SvBezierCurve(points)

    def to_bezier_segments(self, to_bezier_class=True):
        if to_bezier_class and self.is_rational():
            raise UnsupportedCurveTypeException("Rational NURBS curve can not be converted into non-rational Bezier curves")
        if self.is_bezier():
            if to_bezier_class:
                return [self.to_bezier()]
            else:
                return [self]

        segments = []
        rest = self
        for u in sv_knotvector.get_internal_knots(self.get_knotvector()):
            segment, rest = rest.split_at(u)
            if to_bezier_class:
                segments.append(segment.to_bezier())
            else:
                segments.append(segment)
        if to_bezier_class:
            segments.append(rest.to_bezier())
        else:
            segments.append(rest)
        return segments

    def bezier_to_taylor(self):
        # Refer to The NURBS Book, 2nd ed., p. 6.6
        if not self.is_bezier():
            raise Exception("Non-Bezier NURBS curve cannot be converted to Taylor curve")

        p = self.get_degree()
        cpts = self.get_homogenous_control_points()

        M, R = calc_taylor_nurbs_matrices(p, self.get_u_bounds())

        coeffs = np.zeros((4, p+1))
        for k in range(4):
            coeffs[k] = R @ M @ cpts[:,k]
        #print(f"T: {self.get_u_bounds()} => {coeffs.T}")
        #print(f"C: {c}, D: {d} => R {R}")

        taylor = SvTaylorCurve.from_coefficients(coeffs.T)
        taylor.u_bounds = self.get_u_bounds()
        return taylor

    def to_taylor_segments(self):
        return [segment.bezier_to_taylor() for segment in self.to_bezier_segments()]

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

    def insert_knot(self, u, count=1, if_possible=False):
        raise Exception("Not implemented!")

    def remove_knot(self, u, count=1, target=None, tolerance=1e-6):
        raise Exception("Not implemented!")

    def get_min_continuity(self):
        """
        Return minimum continuity degree of the curve (guaranteed by curve's knotvector):
        0 - point-wise continuity only (C0),
        1 - tangent continuity (C1),
        2 - 2nd derivative continuity (C2), and so on.
        """
        kv = self.get_knotvector()
        degree = self.get_degree()
        return sv_knotvector.get_min_continuity(kv, degree)

    def transform(self, frame, vector):
        """
        Apply transformation matrix to the curve.
        Inputs:
        * frame: np.array of shape (3,3) - transformation matrix
        * vector: np.array of shape (3,) - translation vector
        Output: new NURBS curve of the same implementation.
        """
        if frame is None and vector is None:
            return self
        elif frame is None and vector is not None:
            fn = lambda p: p + vector
        elif frame is not None and vector is None:
            fn = lambda p: frame @ p
        else:
            fn = lambda p: (frame @ p) + vector
        new_controls = np.apply_along_axis(fn, 1, self.get_control_points())
        return SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                    self.get_degree(),
                    self.get_knotvector(),
                    new_controls,
                    self.get_weights())

    def is_inside_sphere(self, sphere_center, sphere_radius):
        """
        Check that the whole curve lies inside the specified sphere
        """
        # Because of NURBS curve's "strong convex hull property",
        # if all control points of the curve lie inside the sphere,
        # then the whole curve lies inside the sphere too.
        # This relies on the fact that the sphere is a convex set of points.
        cpts = self.get_control_points()
        distances = np.linalg.norm(sphere_center - cpts)
        return (distances < sphere_radius).all()

    def bezier_distance_curve(self, src_point):
        taylor = self.bezier_to_taylor()
        taylor.start[:3] -= src_point
        return taylor.square(to_axis=0).to_nurbs()

    def bezier_distance_coeffs(self, src_point):
        distance_curve = self.bezier_distance_curve(src_point)
        square_cpts = distance_curve.get_control_points()
        square_coeffs = square_cpts[:,0]
        return square_coeffs

    def bezier_is_strongly_outside_sphere(self, sphere_center, sphere_radius):
        # Complement of the sphere is not a convex set of points;
        # Thus, we can not directly use "strong convex hull property" here.
        # For example, consider a sphere with center = origin and radius = 2,
        # and a straight line segment from [-2, 1, 0] to [2, 1, 0]: both control
        # points are outside the sphere, but part of the segment lies inside it.
        #
        # So, here we are using "Property 1" from the paper [1]:
        # Xiao-Diao Chen, Jun-Hai Yong, Guozhao Wang, Jean-Claude Paul, Gang
        # Xu. Computing the minimum distance between a point and a NURBS curve.
        # Computer-Aided Design, Elsevier, 2008, 40 (10-11), pp.1051-1054.
        # 10.1016/j.cad.2008.06.008. inria-00518359
        # available at: https://hal.inria.fr/inria-00518359

        if not self.is_bezier():
            raise Exception("this method is not applicable to non-Bezier curves")

        square_coeffs = self.bezier_distance_coeffs(sphere_center)
        return (square_coeffs >= sphere_radius**2).all()

    def is_strongly_outside_sphere(self, sphere_center, sphere_radius):
        """
        If this method returns True, then the whole curve lies outside the
        specified sphere.
        If this method returns False, then the curve may partially or wholly
        lie inside the sphere, or may not touch it at all.
        """
        # See comment to bezier_is_strongly_outside_sphere()
        return all(segment.bezier_is_strongly_outside_sphere(sphere_center, sphere_radius) for segment in self.to_bezier_segments(to_bezier_class=False))

    def bezier_has_one_nearest_point(self, src_point):
        square_coeffs = self.bezier_distance_coeffs(src_point)

        should_grow = False
        result = True
        for p1, p2 in zip(square_coeffs, square_coeffs[1:]):
            if not should_grow and not (p1 > p2):
                should_grow = True
            elif should_grow and not (p1 < p2):
                result = False
                break
        return result

    def has_exactly_one_nearest_point(self, src_point):
        # This implements Property 2 from the paper [1]
        segments = self.to_bezier_segments(to_bezier_class=False)
        if len(segments) > 1:
            return False
        return segments[0].bezier_has_one_nearest_point(src_point)

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
        if degree == 0:
            raise Exception("Zero degree!?")
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

    def is_rational(self, tolerance=1e-4):
        if self.curve.weights is None:
            return False
        w, W = min(self.curve.weights), max(self.curve.weights)
        return (W - w) > tolerance

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

    def tangent(self, t, tangent_delta=None):
        p, t = operations.tangent(self.curve, t, normalize=False)
        return np.array(t)

    def tangent_array(self, ts, tangent_delta=None):
        t_min, t_max = self.get_u_bounds()
        ts[ts < t_min] = t_min
        ts[ts > t_max] = t_max
        vs = operations.tangent(self.curve, list(ts), normalize=False)
        tangents = [t[1] for t in vs]
        #print(f"ts: {ts}, vs: {tangents}")
        return np.array(tangents)

    def second_derivative(self, t, tangent_delta=None):
        p, first, second = self.curve.derivatives(t, order=2)
        return np.array(second)

    def second_derivative_array(self, ts, tangent_delta=None):
        return np.vectorize(self.second_derivative, signature='()->(3)')(ts)

    def third_derivative(self, t, tangent_delta=None):
        p, first, second, third = self.curve.derivatives(t, order=3)
        return np.array(third)

    def third_derivative_array(self, ts, tangent_delta=None):
        return np.vectorize(self.third_derivative, signature='()->(3)')(ts)

    def derivatives_array(self, n, ts, tangent_delta=None):
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

    def insert_knot(self, u, count=1, if_possible=False):
        curve = self.copy()
        curve = operations.insert_knot(curve.curve, [u], [count])
        r = SvGeomdlCurve(curve)
        r.u_bounds = self.u_bounds
        return r

    def remove_knot(self, u, count=1, target=None, if_possible=False):
        if (count is None) == (target is None):
            raise Exception("Either count or target must be specified")

        knotvector = self.get_knotvector()
        orig_multiplicity = sv_knotvector.find_multiplicity(knotvector, u)
        if count == SvNurbsCurve.ALL:
            count = orig_multiplicity
        elif count == SvNurbsCurve.ALL_BUT_ONE:
            count = orig_multiplicity - 1
        elif count is None:
            count = orig_multiplicity - target

        curve = self.copy()
        curve = operations.remove_knot(curve.curve, [u], [count])
        result = SvGeomdlCurve(curve)
        result.u_bounds = self.u_bounds

        new_kv = result.get_knotvector()
        new_multiplicity = sv_knotvector.find_multiplicity(new_kv, u)
        if not if_possible and (orig_multiplicity - count < new_multiplicity):
            raise CantRemoveKnotException(f"Asked to remove knot t={u} for {count} times, but could remove it only {orig_multiplicity - count} times")

        return result

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

    def is_rational(self, tolerance=1e-6):
        w, W = self.weights.min(), self.weights.max()
        return (W - w) > tolerance

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

    def tangent(self, t, tangent_delta=None):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts, tangent_delta=None):
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

    def second_derivative(self, t, tangent_delta=None):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts, tangent_delta=None):
        # numerator'' = (curve * denominator)'' =
        #  = curve'' * denominator + 2 * curve' * denominator' + curve * denominator''
        numerator, denominator = self.fraction(0, ts)
        curve = numerator / denominator
        numerator1, denominator1 = self.fraction(1, ts)
        curve1 = (numerator1 - curve*denominator1) / denominator
        numerator2, denominator2 = self.fraction(2, ts)
        curve2 = (numerator2 - 2*curve1*denominator1 - curve*denominator2) / denominator
        return curve2

    def third_derivative_array(self, ts, tangent_delta=None):
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

    def derivatives_array(self, n, ts, tangent_delta=None):
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
            m = self.knotvector[0]
            M = self.knotvector[-1]
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

    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsCurve.NATIVE

    def insert_knot(self, u_bar, count=1, if_possible=False):
        # "The NURBS book", 2nd edition, p.5.2, eq. 5.11
        N = len(self.control_points)
        u = self.get_knotvector()
        s = sv_knotvector.find_multiplicity(u, u_bar)
        #print(f"I: kv {len(u)}{u}, u_bar {u_bar} => s {s}")
        #k = np.searchsorted(u, u_bar, side='right')-1
        k = sv_knotvector.find_span(u, N, u_bar)
        p = self.get_degree()
        new_knotvector = sv_knotvector.insert(u, u_bar, count)
        control_points = self.get_homogenous_control_points()

        if (u_bar == u[0] or u_bar == u[-1]):
            if s+count > p+1:
                if if_possible:
                    count = (p+1) - s
                else:
                    raise CantInsertKnotException(f"Can't insert first/last knot t={u_bar} for {count} times")
        else:
            if s+count > p:
                if if_possible:
                    count = p - s
                else:
                    raise CantInsertKnotException(f"Can't insert knot t={u_bar} for {count} times")

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
                    if abs(denominator) < 1e-6:
                        raise Exception(f"Can't insert the knot t={u_bar} for {i}th time: u[i+p-r+1]={u[i+p-r+1]}, u[i]={u[i]}, denom={denominator}")
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

    def remove_knot(self, u, count=1, target=None, tolerance=1e-6, if_possible=False):
        # Implementation adapted from Geomdl
        logger = getLogger()

        if (count is None) == (target is None):
            raise Exception("Either count or target must be specified")

        orig_multiplicity = sv_knotvector.find_multiplicity(self.get_knotvector(), u)

        if count == SvNurbsCurve.ALL:
            count = orig_multiplicity
        elif count == SvNurbsCurve.ALL_BUT_ONE:
            count = orig_multiplicity - 1
        elif count is None:
            count = orig_multiplicity - target

        degree = self.get_degree()
        order = degree+1

        if not if_possible and (count > orig_multiplicity):
            raise CantRemoveKnotException(f"Asked to remove knot t={u} for {count} times, but it's multiplicity is only {orig_multiplicity}")

        # Edge case
        if count < 1:
            return self

        def knot_removal_alpha_i(u, knotvector, idx):
            return (u - knotvector[idx]) / (knotvector[idx + order] - knotvector[idx])

        def knot_removal_alpha_j(u, knotvector, idx):
            return (u - knotvector[idx]) / (knotvector[idx + order] - knotvector[idx])

        def point_distance(p1, p2):
            return np.linalg.norm(p1 - p2)
            #return np.linalg.norm(np.array(p1) - np.array(p2))

        def remove_one_knot(curve):
            ctrlpts = curve.get_homogenous_control_points()
            N = len(ctrlpts)
            knotvector = curve.get_knotvector()
            orig_multiplicity = sv_knotvector.find_multiplicity(knotvector, u)
            knot_span = sv_knotvector.find_span(knotvector, N, u)

            # Initialize variables
            first = knot_span - degree
            last = knot_span - orig_multiplicity

            # Don't change input variables, prepare new ones for updating
            ctrlpts_new = deepcopy(ctrlpts)

            # Initialize temp array for storing new control points
            temp_i = np.zeros((2*degree+1, 4))
            temp_j = np.zeros((2*degree+1, 4))

            removed_count = 0
            # Loop for Eqs 5.28 & 5.29
            t = 0
            offset = first - 1 # difference in index between `temp` and ctrlpts
            temp_i[0] = ctrlpts[offset]
            temp_j[last + 1 - offset] = ctrlpts[last + 1]
            i = first
            j = last
            ii = 1
            jj = last - offset
            can_remove = False

            # Compute control points for one removal step
            while j - i > t:
                alpha_i = knot_removal_alpha_i(u, knotvector, i)
                alpha_j = knot_removal_alpha_j(u, knotvector, j)
                
                temp_i[ii] = (ctrlpts[i] - (1.0 - alpha_i)*temp_i[ii - 1]) / alpha_i
                temp_j[jj] = (ctrlpts[j] - alpha_j*temp_j[jj + 1]) / (1.0 - alpha_j)
                
                i += 1
                j -= 1
                ii += 1
                jj -= 1

            # Check if the knot is removable
            if j - i < t:
                dist = point_distance(temp_i[ii - 1], temp_j[jj + 1]) 
                if dist <= tolerance:
                    can_remove = True
                else:
                    logger.debug(f"remove_knot: stop, distance={dist}")
            else:
                alpha_i = knot_removal_alpha_i(u, knotvector, i)
                ptn = alpha_i * temp_j[ii + t + 1] + (1.0 - alpha_i)*temp_i[ii - 1]
                dist = point_distance(ctrlpts[i], ptn) 
                if dist <= tolerance:
                    can_remove = True
                else:
                    logger.debug(f"remove_knot: stop, distance={dist}")

            # Check if we can remove the knot and update new control points array
            if can_remove:
                i = first
                j = last
                while j - i > t:
                    ctrlpts_new[i] = temp_i[i - offset]
                    ctrlpts_new[j] = temp_j[j - offset]
                    i += 1
                    j -= 1
                # Update indices
                first -= 1
                last += 1
                removed_count += 1

            else:
                raise CantRemoveKnotException()

            new_kv = np.copy(curve.get_knotvector())

            if removed_count > 0:
                m = N + degree + 1
                for k in range(knot_span+1, m):
                    new_kv[k-removed_count] = new_kv[k]
                new_kv = new_kv[:m-removed_count]
                #new_kv = np.delete(curve.get_knotvector(), np.s_[(r-t+1):(r+1)])

                # Shift control points (refer to p.183 of The NURBS Book, 2nd Edition)
                j = int((2*knot_span - orig_multiplicity - degree) / 2)  # first control point out
                i = j
                for k in range(1, removed_count):
                    if k % 2 == 1:
                        i += 1
                    else:
                        j -= 1
                for k in range(i+1, N):
                    ctrlpts_new[j] = ctrlpts_new[k]
                    j += 1

                # Slice to get the new control points
                ctrlpts_new = ctrlpts_new[0:-removed_count]
            
            ctrlpts_new = np.array(ctrlpts_new)
            control_points, weights = from_homogenous(ctrlpts_new)

            return curve.copy(knotvector = new_kv, control_points = control_points, weights = weights)

        curve = self
        removed_count = 0
        for i in range(count):
            try:
                curve = remove_one_knot(curve)
                removed_count += 1
            except CantRemoveKnotException as e:
                break

        if not if_possible and (removed_count < count):
            raise CantRemoveKnotException(f"Asked to remove knot t={u} for {count} times, but could remove it only {removed_count} times")
        #print(f"Removed knot t={u} for {removed_count} times")
        return curve


SvNurbsMaths.curve_classes[SvNurbsMaths.NATIVE] = SvNativeNurbsCurve
if geomdl is not None:
    SvNurbsMaths.curve_classes[SvNurbsMaths.GEOMDL] = SvGeomdlCurve

