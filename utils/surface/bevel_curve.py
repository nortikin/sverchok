# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi, cos, sin
from collections import defaultdict

from mathutils import Matrix, Vector

from sverchok.utils.math import (
        ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL,
        to_cylindrical_np, to_cylindrical,
        from_cylindrical_np
    )
from sverchok.utils.curve.core import UnsupportedCurveTypeException
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import (
            SvNormalTrack, curve_frame_on_surface_array,
            MathutilsRotationCalculator, DifferentialRotationCalculator,
            SvCurveFrameCalculator,
            reparametrize_curve
        )
from sverchok.utils.curve.nurbs_algorithms import refine_curve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.data import *
from sverchok.utils.surface.gordon import gordon_surface
from sverchok.utils.field.vector import SvBendAlongCurveField

def bend_curve(field, curve):
    control_points = np.copy(curve.get_control_points())
    cpt_xs = control_points[:,0]
    cpt_ys = control_points[:,1]
    cpt_zs = control_points[:,2]
    cpt_dxs, cpt_dys, cpt_dzs = field.evaluate_grid(cpt_xs, cpt_ys, cpt_zs)
    xs = cpt_xs + cpt_dxs
    ys = cpt_ys + cpt_dys
    zs = cpt_zs + cpt_dzs
    control_points = np.stack((xs, ys, zs)).T

    return curve.copy(control_points = control_points)

def place_profile(curve, z, scale):
    control_points = np.copy(curve.get_control_points())
    control_points[:,0] *= scale
    control_points[:,1] *= scale
    control_points[:,2] += z
    return curve.copy(control_points = control_points)

def rotate_curve(curve, angle, scale):
    control_points = np.copy(curve.get_control_points())
    control_points = control_points[:,0], control_points[:,1], control_points[:,2]
    rhos, phis, zs = to_cylindrical_np(control_points, mode='radians')
    xs, ys, zs = from_cylindrical_np(rhos*scale, phis+angle, zs, mode='radians')
    control_points = np.stack((xs, ys, zs)).T
    return curve.copy(control_points = control_points)

def bevel_curve(path, profile, taper, taper_samples=10, taper_refine=20, profile_samples=10):
    taper_t_min, taper_t_max = taper.get_u_bounds()
    profile_t_min, profile_t_max = profile.get_u_bounds()
    taper_start = taper.evaluate(taper_t_min)
    taper_end = taper.evaluate(taper_t_max)
    z_min = taper_start[2]
    z_max = taper_end[2]

    field = SvBendAlongCurveField(path, SvBendAlongCurveField.HOUSEHOLDER, scale_all=False, axis=2, t_min=z_min, t_max=z_max, length_mode='L')

    taper_ts = np.linspace(taper_t_min, taper_t_max, num=taper_samples)
    taper_pts = taper.evaluate_array(taper_ts)
    taper_pts = taper_pts[:,0], taper_pts[:,1], taper_pts[:,2]
    taper_rhos, _, taper_zs = to_cylindrical_np(taper_pts)
    profile_start_rho = to_cylindrical(profile.evaluate(profile_t_min))[0]
    taper_start_rho = to_cylindrical(taper.evaluate(taper_t_min))[0]

    profiles = [place_profile(profile, z, scale) for z, scale in zip(taper_zs, taper_rhos / profile_start_rho)]
    profiles = [bend_curve(field, profile) for profile in profiles]

    profile_ts = np.linspace(profile_t_min, profile_t_max, num=profile_samples, endpoint=True)
    profile_pts = profile.evaluate_array(profile_ts)
    profile_pts = profile_pts[:,0], profile_pts[:,1], profile_pts[:,2]
    profile_rhos, profile_angles, _ = to_cylindrical_np(profile_pts, mode='radians')

    taper = refine_curve(taper, taper_refine)

    tapers = [rotate_curve(taper, angle-pi, scale) for angle, scale in zip(profile_angles, profile_rhos / profile_start_rho)]
    tapers = [bend_curve(field, taper) for taper in tapers]

    #intersections = [[taper.evaluate(t) for t in taper_ts] for taper in tapers]
    intersections = [[taper.evaluate(t) for taper in tapers] for t in taper_ts]

    return tapers, profiles, gordon_surface(tapers, profiles, intersections)[-1]

