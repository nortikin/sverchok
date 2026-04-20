# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
This module contains several algorithms which are based on the NURBS curve
solver (`sverchok.utils.curve.nurbs_solver` module).
"""

import numpy as np

from sverchok.data_structure import apply_mask
from sverchok.core.sv_custom_exceptions import ArgumentError
from sverchok.utils.math import falloff_array, distribute_int
from sverchok.utils.geom import Spline
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import SvCurveOnSurface, SvCurveLengthSolver, CurvatureIntegral
from sverchok.utils.nurbs_common import SvNurbsMaths, to_homogenous
from sverchok.utils.curve.nurbs_algorithms import refine_curve, remove_excessive_knots, concatenate_nurbs_curves
from sverchok.utils.curve.nurbs_solver import SvNurbsCurveCotangents, SvNurbsCurvePoints, SvNurbsCurveSelfIntersections, SvNurbsCurveTangents, SvNurbsCurveSolver
from sverchok.utils.curve.splines import SvMonotoneSpline
from sverchok.utils.adaptive_curve import populate_curve
from sverchok.utils.sv_logging import get_logger

def adjust_curve_points(curve, us_bar, points, preserve_tangents=False, tangents = None, logger=None):
    """
    Modify NURBS curve so that it would pass through specified points
    at specified parameter values.

    Args:
        curve: an instance of SvNurbsCurve
        us_bar: values of curve parameter, np.array of shape (n,)
        points: new positions of curve points at specified parameter values, np.array of shape (n,3).

    Returns:
        an instance of SvNurbsCurve.
    """
    if logger is None:
        logger = get_logger()
    n_target_points = len(us_bar)
    ndim = points.shape[-1]
    if len(points) != n_target_points:
        raise ArgumentError("Number of U parameters must be equal to number of points")
    if preserve_tangents and tangents is not None:
        raise ArgumentError("preserve_tangents and tangents can not be provided simultaneously")

    solver = SvNurbsCurveSolver(src_curve=curve, ndim=ndim)
    solver.set_curve_params(len(curve.get_control_points()), curve.get_knotvector(), weights=curve.get_weights())
    if ndim == 4:
        orig_pts = curve.evaluate_homogenous_array(us_bar)
        #orig_pts = curve.evaluate_array(us_bar)
        #weights = np.ones((n_target_points,))
        #orig_pts = to_homogenous(orig_pts, weights)
    else:
        orig_pts = curve.evaluate_array(us_bar)
    solver.add_goal(SvNurbsCurvePoints(us_bar, points - orig_pts, relative=True))
    #print("Target delta: ", points - orig_pts)
    if preserve_tangents:
        #print("Add preserve_tangents")
        zeros = np.zeros((n_target_points,ndim))
        solver.add_goal(SvNurbsCurveTangents(us_bar, zeros, relative=True))
    elif tangents is not None:
        if ndim == 4 and tangents.shape[-1] == 3:
            ones = np.ones((len(tangents),))
            tangents = to_homogenous(tangents, ones)
        #print(f"Add: Us {len(us_bar)}, tangents {tangents.shape}, target pts {n_target_points}")
        solver.add_goal(SvNurbsCurveTangents(us_bar, tangents, relative=False))
    problem_type, residue, curve = solver.solve_ex(
                    problem_types = {SvNurbsCurveSolver.PROBLEM_UNDERDETERMINED,
                                     SvNurbsCurveSolver.PROBLEM_WELLDETERMINED},
                    logger = logger
                )
    return curve

def deform_curve_with_falloff(curve, length_solver, u_bar, falloff_delta, falloff_type, vector, refine_samples=30, tolerance=1e-4):
    """
    Modify NURBS curve by moving it's point at parameter value at u_bar by specified vector,
    and moving nearby points within specified falloff_delta according to provided falloff function.

    Args:
        curve: an instance of SvNurbsCurve
        length_solver: a prepared instance of SvCurveLengthSolver
        u_bar: float: parameter value, the point at which is to be moved
        falloff_delta: half of length of curve segment, which is to be modified
        falloff_type: falloff function type, see sverchok.utils.math.proportional_falloff_types
        vector: np.array of shape (3,): the movement vector
        refine_samples: number of additional knots to be inserted. More knots mean more precise
            transformation.
        tolerance: tolerance for removing excessive knots at the end of procedure.

    Returns:
        an instance of SvNurbsCurve.
    """
    l_bar = length_solver.calc_length_params(np.array([u_bar]))[0]
    u_min, u_max = length_solver.solve(np.array([l_bar - falloff_delta, l_bar + falloff_delta]))
    curve = refine_curve(curve, refine_samples)
                #t_min = u_min, t_max = u_max)
    us = curve.calc_greville_ts()
    ls = length_solver.calc_length_params(us)
    weights = falloff_array(falloff_type, 1.0, falloff_delta)(abs(ls - l_bar))
    nonzero = np.where(weights > 0)
    us_nonzero = us[nonzero]
    weights_nonzero = weights[nonzero]
    points = curve.evaluate_array(us_nonzero)
    new_points = weights_nonzero[np.newaxis].T * vector
    points_goal = SvNurbsCurvePoints(us_nonzero, new_points, relative=True)
    zero_tangents = np.zeros_like(points)
    #tangents_goal = SvNurbsCurveTangents(us_nonzero, zero_tangents, weights=weights_nonzero, relative=True)
    solver = SvNurbsCurveSolver(src_curve=curve)
    solver.add_goal(points_goal)
    #solver.add_goal(tangents_goal)
    solver.set_curve_params(len(curve.get_control_points()))
    result = solver.solve()
    return remove_excessive_knots(result, tolerance)

def approximate_nurbs_curve(degree, n_cpts, points, weights=None, exact_mask=None, metric='DISTANCE', tknots = None, is_cyclic=False, implementation=SvNurbsMaths.NATIVE, logger=None):
    """
    Approximate points by a NURBS curve.

    Args:
        degree: curve degree (usually 3 or 5).
        n_cpts: number of curve control points. If this is equal to number of
            points being approximated, then this method will do interpolation.
        points: points to be approximated. np.array of shape (n, 3).
        weights: points weights. Bigger weight means that the curve should be
            attracted to corresponding point more than to points with smaller
            weights. None means all weights are equal.
        exact_mask: optional mask indicating points through which the curve
            must pass exactly. If provided, the length of mask must be equal
            to number of points. None means all points are approximated.
        metric: metric to be used.
        tknots: specific T parameter values for points. If provided, their
            count must be equal to number of points.
        is_cyclic: set to True if the curve must be cyclic (closed).
        implementation: NURBS mathematics implementation.
        logger: logger instance.

    Returns:
        an instance of SvNurbsCurve.
    """
    points = np.asarray(points)
    if tknots is None:
        tknots = Spline.create_knots(points, metric=metric)
    else:
        if len(tknots) != len(points):
            raise ArgumentError("Number of tknots must be equal to number of points")
    knotvector = sv_knotvector.from_tknots(degree, tknots, n_cpts=n_cpts)
    solver = SvNurbsCurveSolver(degree=degree)
    solver.set_curve_params(n_cpts, knotvector = knotvector)
    if exact_mask is None:
        goal = SvNurbsCurvePoints(tknots, points, weights = weights, relative=False)
        solver.add_goal(goal)
    else:
        if len(exact_mask) != len(points):
            raise ArgumentError("Length of exact_mask must be equal to number of points")
        t_exact, t_inexact = apply_mask(exact_mask, tknots)
        points_exact, points_inexact = apply_mask(exact_mask, points)
        if weights is None:
            weights_exact, weights_inexact = None, None
        else:
            weights_exact, weights_inexact = apply_mask(exact_mask, weights)
            weights_exact = np.array(weights_exact)
            weights_inexact = np.array(weights_inexact)
        if t_exact:
            exact_goal = SvNurbsCurvePoints(np.array(t_exact), np.array(points_exact), weights = weights_exact, relative=False, exact=True)
            solver.add_goal(exact_goal)
        if t_inexact:
            inexact_goal = SvNurbsCurvePoints(np.array(t_inexact), np.array(points_inexact), weights = weights_inexact, relative=False, exact=False)
            solver.add_goal(inexact_goal)
    if is_cyclic:
        closed = SvNurbsCurveSelfIntersections.single(0.0, 1.0, weight=1.0, relative_u=True, relative=False,exact=True)
        solver.add_goal(closed)
        tangents = SvNurbsCurveCotangents.single(0.0, 1.0, weight=1.0, relative_u=True, relative=False, exact=True)
        solver.add_goal(tangents)
    return solver.solve(implementation=implementation, logger=logger)

def reparametrize_nurbs_curve(curve, n_cpts, samples, src_key_ts, dst_key_ts,
                        degree = None,
                        samples_by_curvature = True,
                        samples_by_length = False,
                        weights_by_curvature = False,
                        populate_resolution = 200,
                        nurbs_implementation = SvNurbsMaths.NATIVE,
                        logger = None):
    if degree is None:
        if hasattr(curve, 'get_degree'):
            degree = curve.get_degree()
        else:
            raise ArgumentError("Curve degree is not provided, and original curve does not have get_degree() method")

    src_key_ts = np.array(src_key_ts)
    dst_key_ts = np.array(dst_key_ts)
    spline = SvMonotoneSpline(src_key_ts, dst_key_ts)
    
    t_min, t_max = curve.get_u_bounds()
    if samples_by_curvature or samples_by_length:
        src_ts = populate_curve(curve, samples, resolution=populate_resolution, by_length = samples_by_length, by_curvature = samples_by_curvature)
    else:
        src_ts = np.linspace(t_min, t_max, num=samples)
    
    dst_ts = spline.evaluate_array(src_ts)[:,1]
    curve_pts = curve.evaluate_array(src_ts)
    curve_key_pts = curve.evaluate_array(src_key_ts)

    # all_src_ts = np.array(list(set(list(src_key_ts) + list(src_ts))))
    # all_src_ts = np.sort(all_src_ts)
    # src_knotvector = sv_knotvector.from_tknots(degree, all_src_ts, n_cpts = n_cpts)
    # knotvector = spline.evaluate_array(src_knotvector)[:,1]
    
    all_ts = np.array(list(set(list(dst_key_ts) + list(dst_ts))))
    t_idxs = np.argsort(all_ts)
    all_ts = all_ts[t_idxs]

    # all_pts = np.concatenate((curve_key_pts, curve_pts), axis=0)
    # sorted_pts = all_pts[t_idxs]
    # metric_tknots = Spline.create_knots(sorted_pts, metric='DISTANCE')
    # knotvector = sv_knotvector.from_tknots(degree, metric_tknots, n_cpts = n_cpts)
    
    orig_idxs = np.linspace(t_min, t_max, num = n_cpts)
    dst_idxs = spline.evaluate_array(orig_idxs)[:,1]
    knotvector = sv_knotvector.from_tknots(degree, dst_idxs)
    # knotvector = sv_knotvector.from_tknots(degree, all_ts, n_cpts = n_cpts)
    # knotvector = sv_knotvector.from_tknots(degree, src_ts, n_cpts = n_cpts)
    
    solver = SvNurbsCurveSolver(degree=degree)
    solver.set_curve_params(n_cpts, knotvector = knotvector)
    
    exact_goal = SvNurbsCurvePoints(dst_key_ts, curve_key_pts, relative=False, exact=True)
    solver.add_goal(exact_goal)
    
    if weights_by_curvature:
        weights = np.sqrt(curve.curvature_array(src_ts))
    else:
        weights = None
    inexact_goal = SvNurbsCurvePoints(dst_ts, curve_pts, weights = weights, relative=False, exact=False)
    solver.add_goal(inexact_goal)
    
    new_curve = solver.solve(implementation = nurbs_implementation, logger = logger)
    new_curve_pts = new_curve.evaluate_array(dst_ts)
    deltas = new_curve_pts - curve_pts
    diff = (deltas * deltas).sum() / samples
    return new_curve, diff

def prepare_solver_for_interpolation(degree, points,
                                     metric='DISTANCE',
                                     tknots=None,
                                     knotvector = None,
                                     t_range = None,
                                     cyclic=False):
    n_points = len(points)
    points = np.asarray(points)
    if points.ndim != 2:
        raise Exception(f"Array of points was expected, but got {points.shape}: {points}")
    ndim = points.shape[1] # 3 or 4
    if ndim not in {3,4}:
        raise Exception(f"Only 3D and 4D points are supported, but ndim={ndim}")
    if cyclic:
        points = np.concatenate((points, points[0][np.newaxis]))
    if tknots is None:
        tknots = Spline.create_knots(points, metric=metric)
    if t_range is not None:
        tknots *= t_range
    solver = SvNurbsCurveSolver(degree=degree, ndim=ndim)
    solver.add_goal(SvNurbsCurvePoints(tknots, points, relative=False))
    if cyclic:
        k = 1.0/float(degree)
        tangent = k*(points[1] - points[-2])
        solver.add_goal(SvNurbsCurveTangents.single(tknots[0], tangent))
        solver.add_goal(SvNurbsCurveTangents.single(tknots[-1], tangent))
    if knotvector is None:
        if cyclic:
            knotvector = sv_knotvector.from_tknots(degree, tknots, include_endpoints=True)
        else:
            knotvector = sv_knotvector.from_tknots(degree, tknots)

    n_cpts = solver.guess_n_control_points()
    solver.set_curve_params(n_cpts, knotvector)
    return solver

def interpolate_nurbs_curve(degree, points,
                            metric='DISTANCE',
                            tknots=None,
                            knotvector=None,
                            t_range = None,
                            cyclic=False,
                            implementation=SvNurbsMaths.NATIVE, logger=None):
    """
    Interpolate points by a NURBS curve.

    Args:
        degree: curve degree (usually 3 or 5).
        points: points to be approximated. np.array of shape (n,3).
        metric: metric to be used.
        tknots: curve parameter values corresponding to points. np.array of
            shape (n,). If None, these values will be calculated based on metric.
        cyclic: if True, this will generate cyclic (closed) curve.
        implementation: NURBS mathematics implementation.

    Returns:
        an instance of SvNurbsCurve.
    """
    solver = prepare_solver_for_interpolation(degree, points,
                    metric = metric, tknots = tknots,
                    knotvector = knotvector,
                    t_range = t_range,
                    cyclic = cyclic)
    problem_type, residue, curve = solver.solve_ex(problem_types = {SvNurbsCurveSolver.PROBLEM_WELLDETERMINED},
                                    implementation = implementation,
                                    logger = logger)
    return curve

def knotvector_with_tangents_from_tknots(degree, u):
    n = len(u)
    if degree == 2:
        kv = [u[0], u[0], u[0]]
        for i in range(1, n-1):
            kv.append((u[i-1] + u[i]) / 2.0)
            kv.append(u[i])
        kv.extend([u[-1], u[-1]])
        return np.array(kv)
    elif degree == 3:
        if len(u) == 2:
            return np.array([u[0], u[0], u[0], u[0],
                             u[1], u[1], u[1], u[1]])
        kv = [u[0], u[0], u[0],u[0]]
        kv.append(u[1]/2.0)
        for i in range(1, n-2):
            u1 = (2*u[i] + u[i+1]) / 3.0
            kv.append(u1)
            u2 = (u[i] + 2*u[i+1]) / 3.0
            kv.append(u2)
        kv.append((u[-2] + u[-1])/2.0)
        kv.extend([u[-1], u[-1], u[-1], u[-1]])
        return np.array(kv)
    else:
        raise Exception(f"Degrees other than 2 and 3 are not supported yet")

def interpolate_nurbs_curve_with_tangents(degree, points, tangents,
            metric='DISTANCE', tknots=None,
            t_range = None,
            cyclic = False,
            implementation = SvNurbsMaths.NATIVE,
            logger = None):

    n_points = len(points)
    points = np.asarray(points)
    tangents = np.asarray(tangents)
    if len(points) != len(tangents):
        raise Exception(f"Number of points ({len(points)}) must be equal to number of tangent vectors ({len(tangents)})")
    ndim = points.shape[-1]
    if ndim not in {3,4}:
        raise Exception(f"Points must be 3 or 4 dimensional, not {ndim}")

    if cyclic:
        points = np.append(points, [points[0]], axis=0)
        tangents = np.append(tangents, [tangents[0]], axis=0)

    if tknots is None:
        tknots = Spline.create_knots(points, metric=metric)
    if t_range is not None:
        tknots *= t_range

    solver = SvNurbsCurveSolver(degree=degree, ndim=ndim)
    solver.add_goal(SvNurbsCurvePoints(tknots, points, relative=False))
    solver.add_goal(SvNurbsCurveTangents(tknots, tangents, relative=False))
    knotvector = knotvector_with_tangents_from_tknots(degree, tknots)
    #print(f"Tknots {tknots} => Kv {knotvector}")
    n_cpts = solver.guess_n_control_points()
    solver.set_curve_params(n_cpts, knotvector)
    problem_type, residue, curve = solver.solve_ex(problem_types = {SvNurbsCurveSolver.PROBLEM_WELLDETERMINED},
                                    implementation = implementation,
                                    logger = logger)
    return curve

def interpolate_nurbs_curve_with_end_tangents(degree, points,
                                              start_tangent, end_tangent,
                                              metric = 'DISTANCE', tknots = None,
                                              t_range = None,
                                              cyclic = False,
                                              implementation = SvNurbsMaths.NATIVE,
                                              logger = None):
    points = np.asarray(points)
    ndim = points.shape[-1]
    if ndim not in {3,4}:
        raise Exception(f"Points must be 3 or 4 dimensional, not {ndim}")

    if cyclic:
        points = np.append(points, [points[0]], axis=0)

    if tknots is None:
        tknots = Spline.create_knots(points, metric=metric)
    if t_range is not None:
        tknots *= t_range
    t_min, t_max = tknots[0], tknots[-1]

    endknots = np.array([t_min, t_max])
    tangents = np.array([start_tangent, end_tangent])

    solver = SvNurbsCurveSolver(degree=degree, ndim=ndim)
    solver.add_goal(SvNurbsCurvePoints(tknots, points, relative=False))
    solver.add_goal(SvNurbsCurvePoints(endknots, tangents, relative=False))
    knotvector = sv_knotvector.from_tknots(degree, tknots, include_endpoints=True)
    n_cpts = solver.guess_n_control_points()
    solver.set_curve_params(n_cpts, knotvector)
    problem_type, residue, curve = solver.solve_ex(problem_types = {SvNurbsCurveSolver.PROBLEM_WELLDETERMINED},
                                    implementation = implementation,
                                    logger = logger)
    return curve

CURVE_LENGTH = 'L'
CURVE_PARAMETER = 'T'
CURVE_CURVATURE = 'C'
CURVE_ARBITRARY = 'A'

def curve_to_nurbs(degree, curve,
                   samples,
                   method = CURVE_PARAMETER,
                   parametrization = None,
                   resolution = 50,
                   use_tangents = False, logger=None):

    if method not in {CURVE_PARAMETER, CURVE_LENGTH, CURVE_CURVATURE, CURVE_ARBITRARY}:
        raise Exception("Unsupported conversion method")

    t_min, t_max = curve.get_u_bounds()
    nurbs_curve = SvNurbsMaths.to_nurbs_curve(curve)
    if nurbs_curve is not None:
        split_ts, split_points, segments = nurbs_curve.split_at_fracture_points(order=1, return_details=True)
        split_ts = [t_min] + split_ts + [t_max]
    else:
        split_ts = [t_min, t_max]
        segments = [curve]
    split_ts = np.asarray(split_ts)

    if method == CURVE_PARAMETER:
        samples_by_split = distribute_int(samples, split_ts[1:] - split_ts[:-1])
        ts_by_split = []
        for t1, t2, s in zip(split_ts[:-1], split_ts[1:], samples_by_split):
            local_ts = np.linspace(t1, t2, num=s)
            ts_by_split.append(local_ts)
        ranges = [None for i in samples_by_split]
        metric = 'POINTS'
    elif method == CURVE_LENGTH:
        solver = SvCurveLengthSolver(curve)
        solver.prepare('SPL', resolution=resolution)
        lengths = [solver.calc_length(t_min, t) for t in split_ts]
        lengths = np.array(lengths)
        segment_lengths = lengths[1:] - lengths[:-1]
        samples_by_split = distribute_int(samples, segment_lengths)
        ts_by_split = []
        for l1, l2, s in zip(lengths[:-1], lengths[1:], samples_by_split):
            local_ls = np.linspace(l1, l2, num=s)
            local_ts = solver.solve(local_ls)
            ts_by_split.append(local_ts)
        ranges = segment_lengths
        metric = 'DISTANCE'
    elif method == CURVE_CURVATURE:
        integral = CurvatureIntegral(curve, resolution, rescale_t=False, rescale_curvature=True)
        curvatures = integral.evaluate_curvatures(split_ts)
        curvature_deltas = curvatures[1:] - curvatures[:-1]
        samples_by_split = distribute_int(samples, curvature_deltas)
        ts_by_split = []
        for c1, c2, s in zip(curvatures[:-1], curvatures[1:], samples_by_split):
            local_cs = np.linspace(c1, c2, num=s)
            local_ts = integral.evaluate_reverse(local_cs)
            ts_by_split.append(local_ts)
        ranges = curvature_deltas
        metric = 'POINTS'

    else: # ARBITRARY
        if parametrization is None:
            raise Exception("Parametrization curve is required")
        u_min, u_max = parametrization.get_u_bounds()
        split_ts_rescaled = (u_max - u_min) * (split_ts - t_min) / (t_max - t_min)
        ps = parametrization.evaluate_array(split_ts_rescaled)[:,1]
        ps_deltas = ps[1:] - ps[:-1]
        samples_by_split = distribute_int(samples, ps_deltas)
        ts_by_split = []
        for p1, p2, s in zip(ps[:-1], ps[1:], samples_by_split):
            local_ps = np.linspace(p1, p2, num=s)
            local_pts = (t_max - t_min) * parametrization.evaluate_array(local_ps)
            local_ts = local_pts[:,1]
            ts_by_split.append(local_ts)
        ranges = ps_deltas
        metric = 'POINTS'

    new_segments = []
    for segment, ts, t_range in zip(segments, ts_by_split, ranges):
        is_cyclic = segment.is_closed()
        if is_cyclic:
            ts = ts[:-1]
        points = curve.evaluate_array(ts)
        if use_tangents:
            tangent1 = curve.tangent(ts[0])
            tangent2 = curve.tangent(ts[-1])
            new_segment = interpolate_nurbs_curve_with_end_tangents(degree, points,
                                                                    tangent1, tangent2,
                                                                    metric=metric,
                                                                    t_range=t_range,
                                                                    logger=logger)
        else:
            new_segment = interpolate_nurbs_curve(degree, points, cyclic=is_cyclic, metric=metric, t_range=t_range, logger=logger)
        new_segments.append(new_segment)
    if len(new_segments) == 1:
        return new_segments[0]
    return concatenate_nurbs_curves(new_segments)

def curve_on_surface_to_nurbs(degree, uv_curve, surface, samples, metric = 'DISTANCE', use_tangents = False, logger = None):
    #is_cyclic = uv_curve.is_closed()
    is_cyclic = False
    t_min, t_max = uv_curve.get_u_bounds()
    ts = np.linspace(t_min, t_max, num=samples)
    curve = SvCurveOnSurface(uv_curve, surface, axis=2)
    if is_cyclic:
        ts = ts[:-1]
    uv_points = uv_curve.evaluate_array(ts)
    points = surface.evaluate_array(uv_points[:,0], uv_points[:,1])
    tknots = Spline.create_knots(points, metric=metric)
    if use_tangents:
        tangents = curve.tangent_array(ts)
        return interpolate_nurbs_curve_with_tangents(degree, points, tangents, tknots = tknots, logger=logger)
    else:
        return interpolate_nurbs_curve(degree, points, cyclic=is_cyclic, tknots = tknots, logger=logger)


BIAS_CURVE1 = 'C1'
BIAS_CURVE2 = 'C2'
BIAS_MID = 'M'

TANGENT_ANY = 'A'
TANGENT_PRESERVE = 'P'
TANGENT_MATCH = 'M'
TANGENT_CURVE1 = 'C1'
TANGENT_CURVE2 = 'C2'

def snap_curves(curves, bias=BIAS_CURVE1, tangent=TANGENT_ANY, cyclic=False):

    class Problem:
        def __init__(self,curve):
            self.curve = curve
            self.t1, self.t2 = curve.get_u_bounds()
            self.point1 = None
            self.point2 = None
            self.tangent1 = None
            self.tangent2 = None

        def solve(self):
            solver = SvNurbsCurveSolver(src_curve = self.curve)
            if self.point1 is not None:
                orig_pt1 = self.curve.evaluate(self.t1)
                solver.add_goal(SvNurbsCurvePoints.single(self.t1, self.point1 - orig_pt1, relative=True))
            if self.point2 is not None:
                orig_pt2 = self.curve.evaluate(self.t2)
                solver.add_goal(SvNurbsCurvePoints.single(self.t2, self.point2 - orig_pt2, relative=True))
            if self.tangent1 is not None:
                orig_tangent1 = self.curve.tangent(self.t1)
                solver.add_goal(SvNurbsCurveTangents.single(self.t1, self.tangent1 - orig_tangent1, relative=True))
            if self.tangent2 is not None:
                orig_tangent2 = self.curve.tangent(self.t2)
                solver.add_goal(SvNurbsCurveTangents.single(self.t2, self.tangent2 - orig_tangent2, relative=True))
            solver.set_curve_params(len(self.curve.get_control_points()), self.curve.get_knotvector())
            problem_type, residue, curve = solver.solve_ex(
                            problem_types = {SvNurbsCurveSolver.PROBLEM_UNDERDETERMINED,
                                             SvNurbsCurveSolver.PROBLEM_WELLDETERMINED}
                        )
            return curve

    def setup_problems(p1, p2):
        if bias == BIAS_CURVE1:
            target_pt = p1.curve.evaluate(p1.t2)
        elif bias == BIAS_CURVE2:
            target_pt = p2.curve.evaluate(p2.t1)
        else:
            pt1 = p1.curve.evaluate(p1.t2)
            pt2 = p2.curve.evaluate(p2.t1)
            target_pt = 0.5 * (pt1 + pt2)
        p1.point2 = target_pt
        p2.point1 = target_pt

        if tangent == TANGENT_ANY:
            target_tangent1 = None
            target_tangent2 = None
        elif tangent == TANGENT_PRESERVE:
            target_tangent1 = p1.curve.tangent(p1.t2)
            target_tangent2 = p2.curve.tangent(p2.t1)
        elif tangent == TANGENT_CURVE1:
            target_tangent1 = p1.curve.tangent(p1.t2)
            target_tangent2 = target_tangent1
        elif tangent == TANGENT_CURVE2:
            target_tangent2 = p2.curve.tangent(p2.t1)
            target_tangent1 = target_tangent2
        else:
            tgt1 = p1.curve.tangent(p1.t2)
            tgt2 = p2.curve.tangent(p2.t1)
            target_tangent1 = 0.5 * (tgt1 + tgt2)
            target_tangent2 = target_tangent1
        p1.tangent2 = target_tangent1
        p2.tangent1 = target_tangent2

    problems = [Problem(c) for c in curves]
    for p1, p2 in zip(problems[:-1], problems[1:]):
        setup_problems(p1, p2)
    if cyclic:
        setup_problems(problems[-1], problems[0])

    return [p.solve() for p in problems]

