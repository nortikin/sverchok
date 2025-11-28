# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from audioop import mul
import numpy as np
from collections import defaultdict

from sverchok.utils.math import distribute_int, solve_quadratic, solve_cubic, np_dot, FRENET
from sverchok.utils.polynomial import Polynomial
from sverchok.utils.geom import (
    LineEquation,
    linear_approximation,
    intersect_segment_segment,
    SEGMENTS_PARALLEL,
)
from sverchok.utils.nurbs_common import (
    SvNurbsBasisFunctions,
    SvNurbsMaths,
    CantInsertKnotException,
)
from sverchok.utils.curve.core import UnsupportedCurveTypeException
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import (
    unify_curves_degree,
    SvCurveLengthSolver,
    SvCurveFrameCalculator,
)
from sverchok.utils.decorators import deprecated
from sverchok.utils.sv_logging import get_logger
from sverchok.dependencies import scipy

if scipy is not None:
    import scipy.optimize


def unify_two_curves(curve1, curve2):
    return unify_curves([curve1, curve2])
    # curve1 = curve1.to_knotvector(curve2)
    # curve2 = curve2.to_knotvector(curve1)
    # return curve1, curve2


@deprecated("Use sverchok.utils.curve.algorithms.unify_curves_degree")
def unify_degrees(curves):
    max_degree = max(curve.get_degree() for curve in curves)
    curves = [curve.elevate_degree(target=max_degree) for curve in curves]
    return curves

class CurvesUnificationException(Exception):
    """Raised when NURBS curve unification code can not unify curves with
    specified tolerance."""
    __description__ = "NURBS curves unification exception"
    pass

def unify_curves(curves, method="UNIFY", accuracy=6):
    tolerance = 10 ** (-accuracy)
    curves = [curve.reparametrize(0.0, 1.0) for curve in curves]
    kvs = [curve.get_knotvector() for curve in curves]
    lens = [len(kv) for kv in kvs]
    # if all(l == lens[0] for l in lens):
    #     diffs = np.array([kv - kvs[0] for kv in kvs])
    #     if abs(diffs).max() < tolerance:
    #         return curves

    if method == "UNIFY":
        dst_knots = sv_knotvector.KnotvectorDict(tolerance)
        for i, curve in enumerate(curves):
            m = sv_knotvector.to_multiplicity(curve.get_knotvector(), tolerance=None)
            # print(f"Curve #{i}: degree={curve.get_degree()}, cpts={len(curve.get_control_points())}, {m}")
            prev_u = None
            for u, count in m:
                if prev_u is not None and abs(prev_u - u) < tolerance:
                    raise CurvesUnificationException(f"Knots in original curve #{i} differ less than for tolerance: {prev_u}, {u}")
                prev_u = u
                dst_knots.put(u, count)
        # print("Dst", dst_knots)
        dst_knots.calc_averages()

        result = []
        #     for i, curve1 in enumerate(curves):
        #         for j, curve2 in enumerate(curves):
        #             if i != j:
        #                 curve1 = curve1.to_knotvector(curve2)
        #         result.append(curve1)

        for idx, curve in enumerate(curves):
            kv = curve.get_knotvector().copy()
            ms = dict(
                sv_knotvector.to_multiplicity(kv)
            )
            #print(f"Curve #{idx}, orig kv: {ms}")
            updates = dst_knots.get_updates(ms.keys())
            #print(f"Curve #{idx}, updates: {updates}")
            updated_ms = []
            for knot_idx, (knot, multiplicity) in enumerate(ms.items()):
                if knot_idx in updates:
                    updated_ms.append((updates[knot_idx], multiplicity))
                else:
                    updated_ms.append((knot, multiplicity))
            ms = dict(updated_ms)
            updated_kv = sv_knotvector.from_multiplicity(updated_ms)
            curve = curve.copy(knotvector = updated_kv)
            insertions = dst_knots.get_insertions(ms)
            #print("Insertions", insertions)
            for knot, diff in insertions.items():
                if diff > 0:
                    curve = curve.insert_knot(knot, diff)
            #                     if u in dst_knots.skip_insertions[idx]:
            #                         pass
            #                         print(f"C: skip insertion T = {u}")
            #                     else:
            #                         #kv = curve.get_knotvector()
            #                         print(f"C: Insert T = {u} x {diff}")
            #                         curve = curve.insert_knot(u, diff)
            result.append(curve)

        return result

    elif method == "AVERAGE":
        kvs = [len(curve.get_control_points()) for curve in curves]
        max_kv, min_kv = max(kvs), min(kvs)
        if max_kv != min_kv:
            raise CurvesUnificationException(
                f"Knotvector averaging is not applicable: Curves have different number of control points: {kvs}"
            )

        knotvectors = np.array([curve.get_knotvector() for curve in curves])
        knotvector_u = knotvectors.mean(axis=0)

        result = [curve.copy(knotvector=knotvector_u) for curve in curves]
        return result


def interpolate_nurbs_curve(
    cls, degree, points, metric="DISTANCE", tknots=None, **kwargs
):
    return SvNurbsMaths.interpolate_curve(
        cls, degree, points, metric=metric, tknots=tknots, **kwargs
    )


def concatenate_nurbs_curves(curves, tolerance=1e-6):
    if not curves:
        raise Exception("List of curves must be not empty")
    curves = unify_curves_degree(curves)
    result = curves[0]
    for i, curve in enumerate(curves[1:]):
        try:
            result = result.concatenate(curve, tolerance=tolerance)
        except Exception as e:
            raise Exception(f"Can't append curve #{i + 1}: {e}")
    return result


def nurbs_curve_to_xoy(curve, target_normal=None):
    cpts = curve.get_control_points()

    approx = linear_approximation(cpts)
    plane = approx.most_similar_plane()
    normal = plane.normal

    if target_normal is not None:
        a = np.dot(normal, target_normal)
        if a > 0:
            normal = -normal

    xx = cpts[-1] - cpts[0]
    xx /= np.linalg.norm(xx)

    yy = np.cross(normal, xx)

    matrix = np.stack((xx, yy, normal)).T
    matrix = np.linalg.inv(matrix)
    center = approx.center
    new_cpts = np.array([matrix @ (cpt - center) for cpt in cpts])
    return curve.copy(control_points=new_cpts)


def nurbs_curve_matrix(curve):
    cpts = curve.get_control_points()

    approx = linear_approximation(cpts)
    plane = approx.most_similar_plane()
    normal = plane.normal

    xx = cpts[-1] - cpts[0]
    xx /= np.linalg.norm(xx)

    yy = np.cross(normal, xx)

    matrix = np.stack((xx, yy, normal)).T
    return matrix


def _get_curve_direction(curve):
    cpts = curve.get_control_points()
    return (cpts[0], cpts[-1])


def _intersect_curves_line(curve1, curve2, precision=0.001, logger=None):
    if logger is None:
        logger = get_logger()

    t1_min, t1_max = curve1.get_u_bounds()
    t2_min, t2_max = curve2.get_u_bounds()

    v1, v2 = _get_curve_direction(curve1)
    v3, v4 = _get_curve_direction(curve2)

    logger.debug(f"Call L: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")
    r = intersect_segment_segment(
        v1, v2, v3, v4, tolerance=precision, endpoint_tolerance=0.0
    )
    if r is SEGMENTS_PARALLEL:
        return SEGMENTS_PARALLEL
    elif not r:
        # logger.debug(f"({v1} - {v2}) x ({v3} - {v4}): no intersection")
        return []
    else:
        u, v, pt = r
        t1 = (1 - u) * t1_min + u * t1_max
        t2 = (1 - v) * t2_min + v * t2_max
        logger.debug(f"({v1} - {v2}) x ({v3} - {v4}) => {pt}")
        return [(t1, t2, pt)]


NUMERIC_TOO_FAR = "TOO_FAR"


def _intersect_curves_equation(
    curve1, curve2, method="SLSQP", precision=0.001, logger=None
):
    if logger is None:
        logger = get_logger()

    t1_min, t1_max = curve1.get_u_bounds()
    t2_min, t2_max = curve2.get_u_bounds()

    def goal(ts):
        p1 = curve1.evaluate(ts[0])
        p2 = curve2.evaluate(ts[1])
        dv = p2 - p1
        return dv @ dv
        # return np.array([r, r])

    mid1 = (t1_min + t1_max) * 0.5
    mid2 = (t2_min + t2_max) * 0.5

    x0 = np.array([mid1, mid2])

    #     def callback(ts, rs):
    #         logger.debug(f"=> {ts} => {rs}")

    # logger.debug(f"Call R: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")

    # Find minimum distance between two curves with a numeric method.
    # If this minimum distance is small enough, we will say that curves
    # do intersect.
    res = scipy.optimize.minimize(
        goal,
        x0,
        method=method,
        bounds=[(t1_min, t1_max), (t2_min, t2_max)],
        tol=0.5 * precision,
    )
    if res.success:
        t1, t2 = tuple(res.x)
        t1 = np.clip(t1, t1_min, t1_max)
        t2 = np.clip(t2, t2_min, t2_max)
        pt1 = curve1.evaluate(t1)
        pt2 = curve2.evaluate(t2)
        dist = np.linalg.norm(pt2 - pt1)
        if dist < precision:
            # logger.debug(f"Found: T1 {t1}, T2 {t2}, Pt1 {pt1}, Pt2 {pt2}")
            pt = (pt1 + pt2) * 0.5
            return [(t1, t2, pt)]
        else:
            logger.debug(
                f"numeric method found a point, but it's too far: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]: {dist}"
            )
            return NUMERIC_TOO_FAR
    else:
        logger.debug(
            f"numeric method fail: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]: {res.message}"
        )
        return []


def _intersect_endpoints(segment1, segment2, tolerance=0.001):
    cpts1 = segment1.get_control_points()
    cpts2 = segment2.get_control_points()
    s1, e1 = cpts1[0], cpts1[-1]
    s2, e2 = cpts2[0], cpts2[-1]

    t1_min, t1_max = segment1.get_u_bounds()
    t2_min, t2_max = segment2.get_u_bounds()

    if np.linalg.norm(s1 - s2) < tolerance:
        return t1_min, t2_min, 0.5 * (s1 + s2)
    elif np.linalg.norm(e1 - e2) < tolerance:
        return t1_max, t2_max, 0.5 * (e1 + e2)
    elif np.linalg.norm(s1 - e2) < tolerance:
        return t1_min, t2_max, 0.5 * (s1 + e2)
    elif np.linalg.norm(e1 - s2) < tolerance:
        return t1_max, t2_min, 0.5 * (e1 + s2)
    else:
        return None


def cut_closed_segments(segments, tolerance=1e-6):
    unclosed = []
    for segment in segments:
        if segment.is_closed(tolerance=tolerance):
            u1, u2 = segment.get_u_bounds()
            mid = (u1 + u2) * 0.5
            unclosed.extend(segment.split_at(mid))
        else:
            unclosed.append(segment)
    return unclosed


def _intersect_segments(
    segment1,
    segment2,
    method="SLSQP",
    numeric_method_threshold=0.02,
    numeric_precision=0.001,
    logger=None,
):
    if logger is None:
        logger = get_logger()

    # Float precision problems workaround
    bbox_tolerance = 1e-4

    # "Recursive bounding box" algorithm:
    # * if bounding boxes of two curves do not intersect, then curves do not intersect
    # * Otherwise, split each curves in half, and check if bounding boxes of these halves intersect.
    # * When this subdivision gives very small parts of curves, try to find intersections numerically.
    #
    # This implementation depends heavily on the fact that curves are NURBS. Because only NURBS curves
    # give us a simple way to calculate bounding box of the curve: it's a bounding box of curve's
    # control points.

    def _intersect_recursively(segment1, segment2, c1_bounds, c2_bounds, i=0):
        if segment1 is None or segment2 is None:
            return []

        t1_min, t1_max = c1_bounds
        t2_min, t2_max = c2_bounds

        bbox1 = segment1.get_bounding_box().increase(bbox_tolerance)
        bbox2 = segment2.get_bounding_box().increase(bbox_tolerance)

        # logger.debug(f"check: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}], bbox1: {bbox1.size()}, bbox2: {bbox2.size()}")
        if not bbox1.intersects(bbox2):
            return []

        r = _intersect_endpoints(segment1, segment2, numeric_precision)
        if r:
            logger.debug(
                "Endpoint intersection after %d iterations; bbox1: %s, bbox2: %s",
                i,
                bbox1.size(),
                bbox2.size(),
            )
            return [r]

        if segment1.is_line(0.5 * numeric_precision) and segment2.is_line(
            0.5 * numeric_precision
        ):
            logger.debug("Calling Lin() after %d iterations", i)
            r = _intersect_curves_line(
                segment1, segment2, numeric_precision, logger=logger
            )
            if r is SEGMENTS_PARALLEL:
                return []
            elif r:
                return r

        if (
            bbox1.size() < numeric_method_threshold
            and bbox2.size() < numeric_method_threshold
        ):
            logger.debug("Calling Eq() after %d iterations", i)
            eq_result = _intersect_curves_equation(
                segment1,
                segment2,
                method=method,
                precision=numeric_precision,
                logger=logger,
            )
            if eq_result is not NUMERIC_TOO_FAR:
                return eq_result

        mid1 = (t1_min + t1_max) * 0.5
        mid2 = (t2_min + t2_max) * 0.5

        c11, c12 = segment1.split_at(mid1)
        c21, c22 = segment2.split_at(mid2)

        r1 = _intersect_recursively(c11, c21, (t1_min, mid1), (t2_min, mid2), i + 1)
        r2 = _intersect_recursively(c11, c22, (t1_min, mid1), (mid2, t2_max), i + 1)
        r3 = _intersect_recursively(c12, c21, (mid1, t1_max), (t2_min, mid2), i + 1)
        r4 = _intersect_recursively(c12, c22, (mid1, t1_max), (mid2, t2_max), i + 1)

        return r1 + r2 + r3 + r4

    return _intersect_recursively(
        segment1, segment2, segment1.get_u_bounds(), segment2.get_u_bounds()
    )


def _intersect_each_pair(
    segments1,
    segments2,
    method="SLSQP",
    numeric_method_threshold=0.02,
    numeric_precision=0.001,
    logger=None,
):
    result = []
    for segment1 in segments1:
        for segment2 in segments2:
            # print(f"Check {segment1.get_u_bounds()} x {segment2.get_u_bounds()}")
            r = _intersect_segments(
                segment1,
                segment2,
                method=method,
                numeric_method_threshold=numeric_method_threshold,
                numeric_precision=numeric_precision,
                logger=logger,
            )
            result.extend(r)
    return result


def intersect_nurbs_curves(
    curve1,
    curve2,
    method="SLSQP",
    numeric_method_threshold=0.02,
    numeric_precision=0.001,
    logger=None,
):
    if logger is None:
        logger = get_logger()
    segments1 = curve1.to_bezier_segments(to_bezier_class=False)
    segments2 = curve2.to_bezier_segments(to_bezier_class=False)
    segments1 = cut_closed_segments(segments1, tolerance=numeric_precision)
    segments2 = cut_closed_segments(segments2, tolerance=numeric_precision)
    return _intersect_each_pair(
        segments1,
        segments2,
        method=method,
        numeric_method_threshold=numeric_method_threshold,
        numeric_precision=numeric_precision,
        logger=logger,
    )


def self_intersect_nurbs_curve(
    curve,
    method="SLSQP",
    numeric_method_threshold=0.02,
    numeric_precision=0.001,
    logger=None,
):
    if logger is None:
        logger = get_logger()

    intersections = []
    eps = 1e-8

    def _check_segments(i, j, segment1, segment2):
        res = _intersect_segments(
            segment1,
            segment2,
            method=method,
            numeric_method_threshold=numeric_method_threshold,
            numeric_precision=numeric_precision,
            logger=logger,
        )
        u_min, u_max = segment1.get_u_bounds()
        v_min, v_max = segment2.get_u_bounds()
        if j == i + 1:
            for t1, t2, pt in res:
                if abs(t1 - u_max) < eps and abs(t2 - v_min) < eps:
                    continue
                print(f"T1 {t1}, T2 {t2}, S1 {u_min} - {u_max}, S2 {v_min} - {v_max}")
                intersections.append((t1, t2, pt))
        else:
            intersections.extend(res)

    segments = curve.to_bezier_segments(to_bezier_class=False)
    if len(segments) == 1:
        t_min, t_max = curve.get_u_bounds()
        mid = (t_min + t_max) * 0.5
        segments = curve.split_at(mid)
    for i, segment1 in enumerate(segments):
        for j, segment2 in enumerate(segments):
            if j <= i:
                continue
            _check_segments(i, j, segment1, segment2)
    return intersections


def remove_excessive_knots(curve, tolerance=1e-6):
    kv = curve.get_knotvector()
    for u in sv_knotvector.get_internal_knots(kv):
        curve = curve.remove_knot(u, count="ALL", if_possible=True, tolerance=tolerance)
    return curve


REFINE_TRIVIAL = "TRIVIAL"
REFINE_DISTRIBUTE = "DISTRIBUTE"
REFINE_BISECT = "BISECT"


def refine_curve(
    curve,
    samples,
    t_min=None,
    t_max=None,
    algorithm=REFINE_DISTRIBUTE,
    refine_max=False,
    solver=None,
    output_new_knots=False,
):
    if refine_max:
        degree = curve.get_degree()
        inserts_count = degree
    else:
        inserts_count = 1

    if t_min is None:
        t_min = curve.get_u_bounds()[0]
    if t_max is None:
        t_max = curve.get_u_bounds()[1]

    existing_knots = curve.get_knotvector()
    existing_knots = np.unique(existing_knots)
    cond = np.logical_and(existing_knots >= t_min, existing_knots <= t_max)
    existing_knots = existing_knots[cond]

    start_knots = existing_knots.copy()
    if t_min not in start_knots:
        start_knots = np.concatenate(([t_min], start_knots))
    if t_max not in start_knots:
        start_knots = np.concatenate((start_knots, [t_max]))

    if algorithm == REFINE_TRIVIAL:
        new_knots = np.linspace(t_min, t_max, num=samples + 1, endpoint=False)[1:]

    elif algorithm == REFINE_DISTRIBUTE:
        if solver is not None:
            length_params = solver.calc_length_params(start_knots)
            sizes = length_params[1:] - length_params[:-1]
            new_knots = np.array([])
            counts = distribute_int(samples, sizes)
            for l1, l2, count in zip(length_params[1:], length_params[:-1], counts):
                ls = np.linspace(l1, l2, num=count + 2, endpoint=True)[1:-1]
                ts = solver.solve(ls)
                new_knots = np.concatenate((new_knots, ts))
        else:
            sizes = start_knots[1:] - start_knots[:-1]
            counts = distribute_int(samples, sizes)
            new_knots = np.array([])
            for t1, t2, count in zip(start_knots[1:], start_knots[:-1], counts):
                ts = np.linspace(t1, t2, num=count + 2, endpoint=True)[1:-1]
                new_knots = np.concatenate((new_knots, ts))

    elif algorithm == REFINE_BISECT:
        if solver is not None:

            def iteration(knots, remaining):
                if remaining == 0:
                    return knots

                knots_np = np.asarray(list(knots))
                knots_np.sort()
                length_params = solver.calc_length_params(knots_np)
                sizes = length_params[1:] - length_params[:-1]
                i_max = sizes.argmax()
                half_length = 0.5 * (length_params[i_max + 1] + length_params[i_max])
                half_t = solver.solve(np.array([half_length]))[0]
                return iteration(knots | set([half_t]), remaining - 1)

            all_knots = set(list(start_knots))
            new_knots = np.asarray(list(iteration(all_knots, samples)))

        else:

            def iteration(knots, remaining):
                if remaining == 0:
                    return knots

                knots_np = np.asarray(list(knots))
                knots_np.sort()
                sizes = knots_np[1:] - knots_np[:-1]
                i_max = sizes.argmax()
                half_t = 0.5 * (knots_np[i_max + 1] + knots_np[i_max])
                return iteration(knots | set([half_t]), remaining - 1)

            all_knots = set(list(start_knots))
            new_knots = np.asarray(list(iteration(all_knots, samples)))

    else:
        raise Exception("Unsupported algorithm")

    if t_min not in existing_knots:
        new_knots = np.concatenate(([t_min], new_knots))
    if t_max not in existing_knots:
        new_knots = np.concatenate((new_knots, [t_max]))
    new_knots = np.unique(new_knots)
    new_knots.sort()
    # print("New:", new_knots)

    for t in new_knots:
        if t in existing_knots:
            continue
        try:
            curve = curve.insert_knot(t, count=inserts_count, if_possible=True)
        except CantInsertKnotException:
            continue

    if output_new_knots:
        return new_knots, curve
    else:
        return curve


class SvNurbsCurveLengthSolver(SvCurveLengthSolver):
    def __init__(self, curve):
        self.curve = curve
        self._reverse_spline = None
        self._prime_spline = None

    def _calc_tknots(self, resolution, tolerance):
        def middle(segment):
            u1, u2 = segment.get_u_bounds()
            u = (u1 + u2) * 0.5
            return u

        def split(segment):
            u = middle(segment)
            return segment.split_at(u)

        def calc_tknots(segment):
            if segment.is_line(tolerance, use_length_tolerance=True):
                u1, u2 = segment.get_u_bounds()
                return set([u1, u2])
            else:
                segment1, segment2 = split(segment)
                knots1 = calc_tknots(segment1)
                knots2 = calc_tknots(segment2)
                knots = knots1.union(knots2)
                return knots

        t_min, t_max = self.curve.get_u_bounds()
        init_knots = np.linspace(t_min, t_max, num=resolution)
        segments = [
            self.curve.cut_segment(u1, u2) for u1, u2 in zip(init_knots, init_knots[1:])
        ]

        all_knots = set()
        for segment in segments:
            knots = calc_tknots(segment)
            all_knots = all_knots.union(knots)

        return np.array(sorted(all_knots))

    def prepare(self, mode, resolution=50, tolerance=1e-3):
        if tolerance is None:
            tolerance = 1e-3
        tknots = self._calc_tknots(resolution, tolerance)
        lengths = self.calc_length_segments(tknots)
        self._length_params = np.cumsum(np.insert(lengths, 0, 0))
        self._reverse_spline = self._make_spline(mode, tknots, self._length_params)
        self._prime_spline = self._make_spline(mode, self._length_params, tknots)


def cast_nurbs_curve(curve, target, coeff=1.0):
    if not hasattr(target, "projection_of_points"):
        raise TypeError("Target object does not support projection_of_points method")

    cpts = curve.get_control_points()
    target_cpts = target.projection_of_points(cpts)

    result_cpts = (1 - coeff) * cpts + coeff * target_cpts

    return curve.copy(control_points=result_cpts)


def offset_nurbs_curve(
    curve,
    offset_vector,
    plane_normal = None,
    src_ts = None,
    algorithm=FRENET,
    algorithm_resolution=50
):
    """
    Offset a NURBS curve to obtain another NURBS curve.

    The algorithm is as follows:
    * Offset some number of points from the curve
    * then interpolate a NURBS curve through these offsetted points
    * remove excessive knots from the resulting curve

    Parameters:
    * curve - the curve to be offsetted
    * offset_vector - np.array of shape (3,)
    * src_ts - T parameters of the points to be offsetted (the more points you take,
        the more precise the offset will be). If None, Greville nodes will be used.
    * algorithm
    * algorithm_resolution
    """
    if src_ts is None:
        src_ts = curve.calc_greville_ts()

    curve_pts = curve.evaluate_array(src_ts)
    n = len(src_ts)
    calc = SvCurveFrameCalculator(curve, algorithm, resolution=algorithm_resolution, normal = plane_normal)
    matrices = calc.get_matrices(src_ts)
    offset_vectors = np.tile(offset_vector[np.newaxis].T, n)
    offset_vectors = (matrices @ offset_vectors)[:, :, 0]
    offset_points = curve_pts + offset_vectors

    tangents = curve.tangent_array(src_ts)
    curvatures = curve.curvature_array(src_ts)
    normals = curve.main_normal_array(src_ts, normalize = True)
    prod = np_dot(offset_vectors, normals)
    offset_tangents = (1.0 - prod * curvatures)[np.newaxis].T * tangents

    return SvNurbsMaths.interpolate_with_tangents(
                curve.get_nurbs_implementation(),
                curve.get_degree(),
                offset_points, offset_tangents,
                tknots = src_ts)

def move_curve_point_by_moving_control_point(curve, u_bar, k, vector, relative=True):
    """
    Adjust the given curve so that at parameter u_bar it goes through
    the point C[u_bar] + vector instead of C[u_bar].
    The adjustment is done by moving one control point and not modifying
    curve weights.

    See The NURBS Book, 2nd ed, p.11.2.

    Parameters:
    * curve - the curve to be adjusted
    * u_bar - curve's parameter, indicating the point you want to move
    * k - index of control point to be moved
    * vector - the vector indicating the direction and distance for which
        you want the point to be moved
    """
    p = curve.get_degree()
    cpts = curve.get_control_points().copy()
    weights = curve.get_weights()
    vector = np.array(vector)
    if not relative:
        src_pt = curve.evaluate(u_bar)
        vector = vector - src_pt
    distance = np.linalg.norm(vector)
    vector = vector / distance
    functions = SvNurbsBasisFunctions(curve.get_knotvector())
    x = functions.fraction(k, p, weights)(np.array([u_bar]))[0]
    if abs(x) < 1e-6:
        raise Exception(
            f"Specified control point #{k} is too far from curve parameter U = {u_bar}"
        )
    alpha = distance / x
    cpts[k] = cpts[k] + alpha * vector
    return curve.copy(control_points=cpts)


def move_curve_point_by_adjusting_one_weight(curve, u_bar, k, distance):
    """
    Adjust the given curve so that curve's point at parameter u_bar is moved
    by given distance towards (or away from) k'th control point.

    See The NURBS Book, 2nd ed, p.11.3.1.

    Parameters:
    * curve - the curve to be adjusted
    * u_bar - curve's parameter, point at which is to be moved
    * k - index of curve's weight, which is to be changed
    * distance - the distance to move the point by. If > 0,
        then the point is moved towards the corresponding control point;
        otherwise, the point is moved away from it.
    """
    p = curve.get_degree()
    weights = curve.get_weights().copy()
    pt = curve.evaluate(u_bar)
    pk = curve.get_control_points()[k]
    pkpt = np.linalg.norm(pt - pk)
    functions = SvNurbsBasisFunctions(curve.get_knotvector())
    r = functions.fraction(k, p, weights)(np.array([u_bar]))[0]
    denominator = r * (pkpt - distance)
    coeff = 1 + distance / denominator
    target_w = weights[k] * coeff
    weights[k] = target_w
    return curve.copy(weights=weights)


def move_curve_point_by_adjusting_two_weights(
    curve, u_bar, k, distance=None, scale=None
):
    """
    Adjust the given curve so that curve's point at parameter u_bar is moved towards
    (or away from) curve's control polygon leg P[k] - P[k+1].
    If distance is specified, then the point is moved by given distance. Distance > 0
    indicates movement towards curve's control polygon leg. Note that if you try to
    move the point farther than curve's control polygon leg, this method will produce
    some fancy curve.
    If scale is specified, then the distance will be calculated automatically, so that:
    * scale = 0 means do not move anything;
    * scale = 1.0 means move the point all the way to control polygon leg, making a small
        fragment of the curve a straight line;
    * scale = -1.0 means move the point all the way from control polygon leg, making a larger
        fragment of the curve a straight line.
    Of distance and scale, exactly one parameter must be provided.

    See The NURBS Book, 2nd ed., p.11.3.2.
    """

    if distance is None and scale is None:
        raise Exception("Either distance or scale must be specified")
    if distance is not None and scale is not None:
        raise Exception("Of distance and scale, only one parameter must be specified")

    p = curve.get_degree()
    cpts = curve.get_control_points()
    weights = curve.get_weights().copy()

    weights0 = weights.copy()
    weights0[k] = weights0[k + 1] = 0.0
    R = curve.copy(weights=weights0).evaluate(u_bar)

    pk = cpts[k]
    pk1 = cpts[k + 1]
    control_leg = LineEquation.from_two_points(pk, pk1)
    control_leg_len = np.linalg.norm(pk1 - pk)

    P = curve.evaluate(u_bar)

    direction = LineEquation.from_two_points(R, P)
    Q = direction.intersect_with_line_coplanar(control_leg)
    Q = np.asarray(Q)

    pkQ = Q - pk
    pk1Q = Q - pk1

    RQ = np.linalg.norm(Q - R)
    RP = np.linalg.norm(P - R)

    direction = (P - R) / RP

    if distance is None:
        if scale >= 0:
            distance = scale * np.linalg.norm(Q - P)
        else:
            distance = scale * np.linalg.norm(R - P)

    target_pt = P + distance * direction
    Rtarget = RP + distance

    qRP = RP / RQ
    qRtarget = Rtarget / RQ

    A = pk + qRP * pkQ
    B = pk1 + qRP * pk1Q
    C = pk + qRtarget * pkQ
    D = pk1 + qRtarget * pk1Q

    ak = np.linalg.norm(B - pk1) / control_leg_len
    ak1 = np.linalg.norm(A - pk) / control_leg_len
    abk = np.linalg.norm(D - pk1) / control_leg_len
    abk1 = np.linalg.norm(C - pk) / control_leg_len

    eps = 1e-6
    if abs(ak) < eps or abs(abk) < eps or abs(ak1) < eps or abs(abk1) < eps:
        raise Exception(
            f"Specified control point #{k} is too far from curve parameter U = {u_bar}"
        )

    numerator = 1.0 - ak - ak1
    numerator_brave = 1.0 - abk - abk1

    beta_k = (numerator / ak) / (numerator_brave / abk)
    beta_k1 = (numerator / ak1) / (numerator_brave / abk1)

    weights[k] = beta_k * weights[k]
    weights[k + 1] = beta_k1 * weights[k + 1]

    new_curve = curve.copy(weights=weights)
    return new_curve


WEIGHTS_NONE = "NONE"
WEIGHTS_EUCLIDIAN = "EUCLIDIAN"
TANGENT_PRESERVE = "PRESERVE"


def move_curve_point_by_moving_control_points(
    curve, u_bar, vector, weights_mode=WEIGHTS_NONE, tangent=None, relative=True
):
    """
    Adjust the given curve so that at parameter u_bar it goues through
    the point C[u_bar] + vector instead of C[u_bar].
    The adjustment is done by moving several control points of the curve
    (approximately `p` of them, where p is curve's degree). The adjustment is
    calculated so that total movement of control points is minimal.
    Curve's weights are not changed.
    This method tends to create more smooth curves compared to
    move_curve_point_by_moving_control_point, but it involves more calculations,
    so probably it is less performant.

    Parameters:
    * curve - NURBS curve to be adjusted.
    * u_bar - curve's parameter, indicating the point you want to move
    * vector - the vector indicating the direction and distance for which
        you want the point to be moved
    * weights_mode - defines whether the method will try to keep some control points
        in place more than other control points. With WEIGHTS_NONE, it will
        try to keep all control points in place equally. With WEIGHTS_EUCLIDIAN,
        it will tend to move more the points which are nearer to the new location of
        C[u_bar].

    Underlying theory:
    Given curve's knotvector, curve weights and u_bar, we can say that C[u_bar] is some
    linear combination of curve's control points, where coefficients of that linear
    combination are some functions of u_bar. So, the equation

        C[u_bar] = Pt0            (1)

    is actually an underdetermined system of linear equations on coordinates of curve
    control points. Similarly, if we want to find a curve C1, which is similar to C,
    but goes through Pt1 instead of Pt0, the equation

        C1[u_bar] = Pt1           (2)

    is also an underdetermined system of linear equations of coordinates of curve control
    points.
    Now, if we substract (1) from (2), we will have a new underdetermined system of
    linear equations on *movements* of curve control points (i.e. on how should we move
    control points of C in order to obtain C1).
    This underdetermined system, obviously, will have infinite number of solutions (in
    other words, we obviously have infinite ways of moving curve control points so that
    the new curve will go through Pt1). But, among this infinite number of solutions, let's
    peek one which makes us move control points by the least amount. If we will understand
    "the least amount" as "the minimum sum of squares of movement vectors", than we will
    see that this is a standard least squares problem. We may want to assign some weights
    to different control points, if we want to try to move less control points, and keep
    ones which are far from Pt1 more or less in place. In such case, we will have weighted
    least squares problem.
    Both weighted and unweighted least squares problems are solved by use of Moore-Penrose
    pseudo-inverse matrix - numpy.linalg.pinv.
    """
    ndim = 3
    cpts = curve.get_control_points().copy()
    curve_weights = curve.get_weights()
    if not relative:
        src_pt = curve.evaluate(u_bar)
        vector = vector - src_pt
    if weights_mode == WEIGHTS_EUCLIDIAN:
        pt0 = curve.evaluate(u_bar)
        pt1 = pt0 + vector
        move_weights = [np.linalg.norm(pt1 - cpt[:3]) ** (-2) for cpt in cpts]
    else:
        move_weights = [1 for cpt in cpts]
    n = len(cpts)
    p = curve.get_degree()
    kv = curve.get_knotvector()
    basis = SvNurbsBasisFunctions(kv)
    alphas = [
        basis.fraction(k, p, curve_weights)(np.array([u_bar]))[0] for k in range(n)
    ]
    if tangent is None:
        A = np.zeros((ndim, ndim * n))
    else:
        if tangent == TANGENT_PRESERVE:
            tangent = curve.tangent(u_bar)
        A = np.zeros((2 * ndim, ndim * n))
        ns = np.array(
            [basis.derivative(k, p, 1)(np.array([u_bar]))[0] for k in range(n)]
        )
        numerator = ns * curve_weights  # [np.newaxis].T
        denominator = curve_weights.sum()
        betas = numerator / denominator
    for i in range(n):
        for j in range(ndim):
            A[j, ndim * i + j] = alphas[i] * move_weights[i]
            if tangent is not None:
                A[ndim + j, ndim * i + j] = betas[i] * move_weights[i]
    A1 = np.linalg.pinv(A)
    if tangent is None:
        B = np.zeros((ndim, 1))
        B[0:3, 0] = vector[np.newaxis]
    else:
        B = np.zeros((2 * ndim, 1))
        B[0:3, 0] = vector[np.newaxis]
        # B[3:6,0] = tangent[np.newaxis]
    X = (A1 @ B).T
    W = np.diag(move_weights)
    d_cpts = W @ X.reshape((n, ndim))
    cpts = cpts + d_cpts
    return curve.copy(control_points=cpts)


def move_curve_point_by_inserting_knot(curve, u_bar, vector, relative=True):
    """
    Adjust the given curve so that at parameter u_bar it goues through
    the point C[u_bar] + vector instead of C[u_bar].
    The adjustment is made by inserting additional knot at u_bar, and
    then moving two control points.

    Parameters:
    * curve - NURBS curve to be adjusted.
    * u_bar - curve's parameter, indicating the point you want to move
    * vector - the vector indicating the direction and distance for which
        you want the point to be moved
    """
    pt0 = curve.evaluate(u_bar)
    if not relative:
        vector = vector - pt0
    p = curve.get_degree()
    curve2 = curve.insert_knot(u_bar, p - 1, if_possible=True)
    cpts = curve2.get_control_points().copy()
    n = len(cpts)
    k = np.linalg.norm(cpts - pt0, axis=1).argmin()
    cpts[k] += vector
    if k >= 1:
        cpts[k - 1] += vector
    if k < n - 1:
        cpts[k + 1] += vector
    return curve2.copy(control_points=cpts)


def wrap_nurbs_curve(
    curve,
    t_min,
    t_max,
    refinement_samples,
    function,
    scale=1.0,
    direction=None,
    refinement_algorithm=REFINE_TRIVIAL,
    refinement_solver=None,
    tolerance=1e-4,
):
    curve = refine_curve(
        curve,
        refinement_samples,
        t_min=t_min,
        t_max=t_max,
        algorithm=refinement_algorithm,
        solver=refinement_solver,
    )
    cpts = curve.get_control_points().copy()
    greville_ts = curve.calc_greville_ts()
    wrap_idxs = np.where(np.logical_and(greville_ts >= t_min, greville_ts <= t_max))
    wrap_ts = greville_ts[wrap_idxs]
    normalized_ts = (wrap_ts - wrap_ts[0]) / (wrap_ts[-1] - wrap_ts[0])
    wrap_cpts = cpts[wrap_idxs]
    if direction is None:
        wrap_dirs = curve.main_normal_array(wrap_ts)
    else:
        direction = np.asarray(direction)
        direction /= np.linalg.norm(direction)
        wrap_dirs = direction[: np.newaxis].T
    wrap_values = scale * function(normalized_ts)
    # print("Wv", wrap_values)
    wrap_vectors = wrap_dirs * wrap_values[np.newaxis].T
    cpts[wrap_idxs] = cpts[wrap_idxs] + wrap_vectors
    curve = curve.copy(control_points=cpts)
    return remove_excessive_knots(curve, tolerance)


def nurbs_curve_extremes(curve, direction, sign=1, global_only=False):
    if curve.is_rational():
        raise NotImplementedError("Rational curves are not supported (yet)")
    degree = curve.get_degree()
    direction = np.array(direction)
    if degree > 4:
        raise UnsupportedCurveTypeException(
            f"Curve degree of {degree} is not supported"
        )
    t_values = set()
    for segment in curve.to_bezier_segments(to_bezier_class=False):
        taylor = segment.bezier_to_taylor()
        coeffs = taylor.derivative().get_coefficients()
        poly_coeffs = (
            coeffs[:, 0] * direction[0]
            + coeffs[:, 1] * direction[1]
            + coeffs[:, 2] * direction[2]
        )
        t1, t2 = segment.get_u_bounds()
        if degree == 1:
            t_values.update([t1, t2])
        elif degree == 2:
            b, a = poly_coeffs
            t = -b / a
            if t1 <= t <= t2:
                t_values.add(t)
        elif degree == 3:
            c, b, a = poly_coeffs
            ts = solve_quadratic(a, b, c)
            ts = [t for t in ts if t1 <= t <= t2]
            t_values.update(ts)
        elif degree == 4:
            d, c, b, a = poly_coeffs
            ts = solve_cubic(a, b, c, d)
            ts = [t for t in ts if t1 <= t <= t2]
            t_values.update(ts)
    ts = np.array(list(sorted(t_values)))
    second_derivs = curve.second_derivative_array(ts)
    dots = (direction * second_derivs).sum(axis=1)
    signs = np.sign(dots)
    mask = -np.sign(sign) == signs
    ts = ts[mask]
    if global_only:
        pts = curve.evaluate_array(ts)
        dots = (direction * pts).sum(axis=1)
        if sign > 0:
            idx = np.argmax(dots)
        else:
            idx = np.argmin(dots)
        return np.array([ts[idx]])
    else:
        return ts

