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

from sverchok.utils.math import falloff_array
from sverchok.utils.geom import Spline
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.nurbs_algorithms import refine_curve, remove_excessive_knots
from sverchok.utils.curve.nurbs_solver import SvNurbsCurvePoints, SvNurbsCurveTangents, SvNurbsCurveCotangents, SvNurbsCurveSolver

def adjust_curve_points(curve, us_bar, points):
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
    n_target_points = len(us_bar)
    if len(points) != n_target_points:
        raise Exception("Number of U parameters must be equal to number of points")

    solver = SvNurbsCurveSolver(src_curve=curve)
    solver.add_goal(SvNurbsCurvePoints(us_bar, points))
    solver.set_curve_params(len(curve.get_control_points()))
    return solver.solve()

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
    knotvector = sv_knotvector.from_tknots(degree, tknots, n_cpts)
    goal = SvNurbsCurvePoints(tknots, points, weights = weights, relative=False)
    solver = SvNurbsCurveSolver(degree=degree)
    solver.set_curve_params(n_cpts, knotvector = knotvector)
    solver.add_goal(goal)
    return solver.solve(implementation=implementation)

def interpolate_nurbs_curve(degree, points, metric='DISTANCE', tknots=None, cyclic=False, implementation=SvNurbsMaths.NATIVE, logger=None):
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
    points_goal = SvNurbsCurvePoints(tknots, points, relative=False)
    solver = SvNurbsCurveSolver(degree=degree, ndim=ndim)
    solver.add_goal(points_goal)
    if cyclic:
        k = 1.0/float(degree)
        tangent = k*(points[1] - points[-2])
        solver.add_goal(SvNurbsCurveTangents.single(0.0, tangent))
        solver.add_goal(SvNurbsCurveTangents.single(1.0, tangent))
        n_cpts = solver.guess_n_control_points()
        t1 = k*tknots[0] + (1-k)*tknots[1]
        t2 = k*tknots[-1] + (1-k)*tknots[-2]
        tknots = np.insert(tknots, [1,-1], [t1,t2])
        knotvector = sv_knotvector.from_tknots(degree, tknots)
        solver.set_curve_params(n_cpts, knotvector)
    else:
        knotvector = sv_knotvector.from_tknots(degree, tknots)
        n_cpts = solver.guess_n_control_points()
        solver.set_curve_params(n_cpts, knotvector)

    problem_type, residue, curve = solver.solve_ex(problem_types = {SvNurbsCurveSolver.PROBLEM_WELLDETERMINED},
                                    implementation = implementation,
                                    logger = logger)
    return curve

def curve_to_nurbs(degree, curve, samples, logger=None):
    is_cyclic = curve.is_closed()
    t_min, t_max = curve.get_u_bounds()
    ts = np.linspace(t_min, t_max, num=samples)
    if is_cyclic:
        ts = ts[:-1]
    points = curve.evaluate_array(ts)
    return interpolate_nurbs_curve(degree, points, cyclic=is_cyclic, logger=logger)

