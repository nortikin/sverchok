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

from sverchok.core.sv_custom_exceptions import ArgumentError
from sverchok.utils.math import falloff_array, distribute_int
from sverchok.utils.geom import Spline
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import SvCurveOnSurface, SvCurveLengthSolver, CurvatureIntegral
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.nurbs_algorithms import refine_curve, remove_excessive_knots, concatenate_nurbs_curves
from sverchok.utils.curve.nurbs_solver import SvNurbsCurvePoints, SvNurbsCurveTangents, SvNurbsCurveSolver
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
    if len(points) != n_target_points:
        raise ArgumentError("Number of U parameters must be equal to number of points")
    if preserve_tangents and tangents is not None:
        raise ArgumentError("preserve_tangents and tangents can not be provided simultaneously")

    solver = SvNurbsCurveSolver(src_curve=curve)
    orig_pts = curve.evaluate_array(us_bar)
    solver.add_goal(SvNurbsCurvePoints(us_bar, points - orig_pts, relative=True))
    if preserve_tangents:
        #print("Add preserve_tangents")
        zeros = np.zeros((n_target_points,3))
        solver.add_goal(SvNurbsCurveTangents(us_bar, zeros, relative=True))
    elif tangents is not None:
        #print(f"Add: Us {len(us_bar)}, tangents {len(tangents)}, target pts {n_target_points}")
        solver.add_goal(SvNurbsCurveTangents(us_bar, tangents, relative=False))
    solver.set_curve_params(len(curve.get_control_points()), curve.get_knotvector(), weights=curve.get_weights())
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

def approximate_nurbs_curve(degree, n_cpts, points, weights=None, metric='DISTANCE', implementation=SvNurbsMaths.NATIVE):
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
        metric: metric to be used.
        implementation: NURBS mathematics implementation.

    Returns:
        an instance of SvNurbsCurve.
    """
    points = np.asarray(points)
    tknots = Spline.create_knots(points, metric=metric)
    knotvector = sv_knotvector.from_tknots(degree, tknots, n_cpts=n_cpts)
    goal = SvNurbsCurvePoints(tknots, points, weights = weights, relative=False)
    solver = SvNurbsCurveSolver(degree=degree)
    solver.set_curve_params(n_cpts, knotvector = knotvector)
    solver.add_goal(goal)
    return solver.solve(implementation=implementation)

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

