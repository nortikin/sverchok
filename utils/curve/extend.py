# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve.core import SvTaylorCurve
from sverchok.utils.curve.primitives import SvLine, SvCircle
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.algorithms import SvCurveLengthSolver, reverse_curve
from sverchok.utils.geom import circle_by_two_derivatives

def set_length(base_curve, curve, t_ext, sign=1, len_mode='T', len_resolution=50):
    if curve is None:
        return None
    if len_mode == 'T':
        curve.u_bounds = (0, t_ext)
        if isinstance(curve, SvLine) and sign < 0:
            unit = curve.direction / np.linalg.norm(curve.direction)
            t_target = t_ext / np.linalg.norm(curve.direction)
            start = curve.point + curve.direction - t_ext*unit
            curve.point = start
            curve.u_bounds = (0, t_target)
    elif len_mode == 'L':
        if isinstance(curve, SvLine):
            if sign > 0:
                curve.direction = curve.direction
                t_ext = t_ext / np.linalg.norm(curve.direction)
                curve.u_bounds = (0, t_ext)
            else:
                unit = curve.direction / np.linalg.norm(curve.direction)
                t_target = t_ext / np.linalg.norm(curve.direction)
                start = curve.point + curve.direction - t_ext*unit
                curve.point = start
                curve.u_bounds = (0, t_target)
        else:
            u_min, u_max = base_curve.get_u_bounds()
            base_length = base_curve.calc_length(u_min, u_max, len_resolution)
            # base_length / (u_max - u_min) ~= t_ext / (t_target - 0)
            t_mid = t_ext * (u_max - u_min) / base_length
            curve.u_bounds = (0, t_mid)
            solver = SvCurveLengthSolver(curve)
            solver.prepare('SPL', len_resolution)
            t_target = solver.solve(np.array([t_ext]))[0]
            curve.u_bounds = (0, t_target)
    return curve

def extend_curve(curve, t_before, t_after, mode = 'LINE', len_mode='T', len_resolution=50):

    def make_line(point, tangent, t_ext, sign):
        if sign < 0:
            before_start = point - t_ext*tangent # / np.linalg.norm(tangent_start)
            return SvLine.from_two_points(before_start, point)
        else:
            after_end = point + t_ext*tangent # / np.linalg.norm(tangent_end)
            return SvLine.from_two_points(point, after_end)

    u_min, u_max = curve.get_u_bounds()
    start, end = curve.evaluate(u_min), curve.evaluate(u_max)
    start_extent, end_extent = None, None
    is_nurbs = isinstance(curve, SvNurbsCurve)

    if mode == 'LINE':
        tangent_start = curve.tangent(u_min)
        tangent_end = curve.tangent(u_max)

        if t_before > 0:
            start_extent = make_line(start, tangent_start, t_before, -1)
            start_extent = set_length(curve, start_extent, t_before, -1, len_mode=len_mode, len_resolution=len_resolution)
        if t_after > 0:
            end_extent = make_line(end, tangent_end, t_after, +1)
            end_extent = set_length(curve, end_extent, t_after, +1, len_mode=len_mode, len_resolution=len_resolution)

    elif mode == 'ARC':
        tangent_start = curve.tangent(u_min)
        tangent_end = curve.tangent(u_max)
        second_start = curve.second_derivative(u_min)
        second_end = curve.second_derivative(u_max)

        if t_before > 0:
            if np.linalg.norm(second_start) > 1e-6:
                eq1 = circle_by_two_derivatives(start, -tangent_start, second_start)
                start_extent = SvCircle.from_equation(eq1)
                start_extent = set_length(curve, start_extent, t_before, -1, len_mode=len_mode, len_resolution=len_resolution)
                if is_nurbs:
                    start_extent = start_extent.to_nurbs()
                start_extent = reverse_curve(start_extent)
            else:
                start_extent = make_line(start, tangent_start, t_before, -1)
                start_extent = set_length(curve, start_extent, t_before, -1, len_mode=len_mode, len_resolution=len_resolution)

        if t_after > 0:
            if np.linalg.norm(second_end) > 1e-6:
                eq2 = circle_by_two_derivatives(end, tangent_end, second_end)
                end_extent = SvCircle.from_equation(eq2)
            else:
                end_extent = make_line(end, tangent_end, t_after, +1)
            end_extent = set_length(curve, end_extent, t_after, +1, len_mode=len_mode, len_resolution=len_resolution)

    elif mode == 'QUAD':
        tangent_start = curve.tangent(u_min)
        tangent_end = curve.tangent(u_max)
        second_start = curve.second_derivative(u_min)
        second_end = curve.second_derivative(u_max)

        if t_before > 0:
            start_extent = SvTaylorCurve(start, [-tangent_start, second_start])
            start_extent = set_length(curve, start_extent, t_before, len_mode=len_mode, len_resolution=len_resolution)
            if is_nurbs:
                start_extent = start_extent.to_nurbs()
            start_extent = reverse_curve(start_extent)

        if t_after > 0:
            end_extent = SvTaylorCurve(end, [tangent_end, second_end])
            end_extent = set_length(curve, end_extent, t_after, len_mode=len_mode, len_resolution=len_resolution)

    elif mode == 'CUBIC':
        tangent_start = curve.tangent(u_min)
        tangent_end = curve.tangent(u_max)
        second_start = curve.second_derivative(u_min)
        second_end = curve.second_derivative(u_max)
        third_start, third_end = curve.third_derivative_array(np.array([u_min, u_max]))

        if t_before > 0:
            start_extent = SvTaylorCurve(start, [-tangent_start, second_start, -third_start])
            start_extent = set_length(curve, start_extent, t_before, len_mode=len_mode, len_resolution=len_resolution)
            if is_nurbs:
                start_extent = start_extent.to_nurbs()
            start_extent = reverse_curve(start_extent)
        if t_after > 0:
            end_extent = SvTaylorCurve(end, [tangent_end, second_end, third_end])
            end_extent = set_length(curve, end_extent, t_after, len_mode=len_mode, len_resolution=len_resolution)

    else:
        raise Exception("Unsupported mode")

    if is_nurbs:
        if start_extent is not None and not isinstance(start_extent, SvNurbsCurve):
            start_extent = start_extent.to_nurbs(implementation=curve.get_nurbs_implementation())
        if end_extent is not None and not isinstance(end_extent, SvNurbsCurve):
            end_extent = end_extent.to_nurbs(implementation=curve.get_nurbs_implementation())

    return start_extent, end_extent

