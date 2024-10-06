# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from sverchok.utils.curve.nurbs_solver_applications import adjust_curve_points
from sverchok.utils.manifolds import nearest_point_on_curve

COUNT = 'COUNT'
FIT = 'FIT'
EXPLICIT = 'EXPLICIT'
PRIMARY_U = 'U'
PRIMARY_V = 'V'

def prepare_curves_net(u_curves, v_curves,
                       u_values, v_values,
                       bias = PRIMARY_U,
                       u_mode = COUNT,
                       v_mode = COUNT,
                       fit_samples = 50,
                       preserve_tangents = False):

    if u_mode == FIT and v_mode == FIT:
        raise Exception("Automatic T values fitting can not be enabled for both directions")

    def prepare_t_by_count(curves, n):
        bounds = np.array([c.get_u_bounds() for c in curves])
        ts_min = bounds[:,0]
        ts_max = bounds[:,1]
        t_values = np.linspace(ts_min, ts_max, num=n).T
        pts = [c.evaluate_array(t) for c, t in zip(curves, t_values)]
        pts = np.array(pts)
        return t_values, pts

    def prepare_t(mode, curves, t_values, n):
        if mode == EXPLICIT:
            target_pts = [c.evaluate_array(t) for c, t in zip(curves, t_values)]
            target_pts = np.array(target_pts)
        elif mode == COUNT:
            t_values, target_pts = prepare_t_by_count(curves, n)
        else: # FIT
            raise Exception("Can't fit T values for base curves")
        return t_values, target_pts

    def fit_t(primary_curves, primary_t_values, secondary_curves):
        primary_curve_pts = [c.evaluate_array(primary_t_values[i]) for i, c in enumerate(primary_curves)]
        primary_curve_pts = np.array(primary_curve_pts)
        secondary_t_values = [nearest_point_on_curve(primary_curve_pts[:,i], curve, samples=fit_samples, output_points=False) for i, curve in enumerate(secondary_curves)]
        secondary_t_values = np.array(secondary_t_values)
        return secondary_t_values

    def prepare_uv():
        nonlocal u_values, v_values
        if u_mode != FIT:
            u_values, u_pts = prepare_t(u_mode, u_curves, u_values, len(v_curves))
        else:
            u_values, u_pts = None, None
        if v_mode != FIT:
            v_values, v_pts = prepare_t(v_mode, v_curves, v_values, len(u_curves))
        else:
            v_values, v_pts = None, None
        if bias == PRIMARY_U:
            return u_values, v_values, u_pts
        else:
            return u_values, v_values, v_pts

    u_values, v_values, target_pts = prepare_uv()
    if u_mode == FIT and v_mode != FIT:
        u_values = fit_t(v_curves, v_values, u_curves)
    elif u_mode != FIT and v_mode == FIT:
        v_values = fit_t(u_curves, u_values, v_curves)
    if target_pts is None:
        if bias == PRIMARY_U:
            target_pts = [c.evaluate_array(t) for c, t in zip(u_curves, u_values)]
        else:
            target_pts = [c.evaluate_array(t) for c, t in zip(v_curves, v_values)]
        target_pts = np.array(target_pts)

    if bias == PRIMARY_U:
        new_u_curves = u_curves
        new_v_curves = []
        for i, v_curve in enumerate(v_curves):
            pts = target_pts[:,i]
            new_curve = adjust_curve_points(v_curve, v_values[i], pts,
                                            preserve_tangents = preserve_tangents)
            new_v_curves.append(new_curve)
    else:
        new_u_curves = []
        new_v_curves = v_curves
        for i, u_curve in enumerate(u_curves):
            pts = target_pts[:,i]
            new_curve = adjust_curve_points(u_curve, u_values[i], pts,
                                            preserve_tangents = preserve_tangents)
            new_u_curves.append(new_curve)
    if bias == PRIMARY_U:
        target_pts = np.transpose(target_pts, axes=(1,0,2))
    return new_u_curves, new_v_curves, target_pts, u_values, v_values

