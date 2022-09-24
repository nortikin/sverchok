# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.math import falloff_array
from sverchok.utils.geom import Spline
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import refine_curve, remove_excessive_knots
from sverchok.utils.curve.nurbs_solver import SvNurbsCurvePoints, SvNurbsCurveTangents, SvNurbsCurveSolver

def adjust_curve_points(curve, us_bar, points):
    """
    Modify NURBS curve so that it would pass through specified points
    at specified parameter values.
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
    Parameters:
    * curve - an instance of SvNurbsCurve
    * length_solver - a prepared instance of SvCurveLengthSolver
    * u_bar - float: parameter value, the point at which is to be moved
    * falloff_delta - half of length of curve segment, which is to be modified
    * falloff_type - falloff function type, see sverchok.utils.math.proportional_falloff_types
    * vector - np.array of shape (3,): the movement vector
    * refine_samples - number of additional knots to be inserted. More knots mean more precise
        transformation.
    * tolerance - tolerance for removing excessive knots at the end of procedure.
    Return value: an instance of SvNurbsCurve.
    """
    l_bar = length_solver.calc_length_params(np.array([u_bar]))[0]
    u_min, u_max = length_solver.solve(np.array([l_bar - falloff_delta, l_bar + falloff_delta]))
    #print(f"U {u_min} - {u_max}")
    curve = refine_curve(curve, refine_samples)
                #t_min = u_min, t_max = u_max)
    us = curve.calc_greville_ts()
    ls = length_solver.calc_length_params(us)
    #print(f"Ls {ls}, l_bar {l_bar}")
    weights = falloff_array(falloff_type, 1.0, falloff_delta)(abs(ls - l_bar))
    nonzero = np.where(weights > 0)
    us_nonzero = us[nonzero]
    weights_nonzero = weights[nonzero]
    #print("us", us_nonzero)
    #print("ws", weights_nonzero)
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

def approximate_nurbs_curve(degree, n_cpts, points, weights=None, metric='DISTANCE', implementation=SvNurbsCurve.NATIVE):
    points = np.asarray(points)
    tknots = Spline.create_knots(points, metric=metric)
    knotvector = sv_knotvector.from_tknots(degree, tknots, n_cpts)
    goal = SvNurbsCurvePoints(tknots, points, weights = weights, relative=False)
    solver = SvNurbsCurveSolver(degree=degree)
    solver.set_curve_params(n_cpts, knotvector = knotvector)
    solver.add_goal(goal)
    return solver.solve(implementation=implementation)

