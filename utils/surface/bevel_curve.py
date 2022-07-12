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
from sverchok.utils.geom import LineEquation, rotate_vector_around_vector_np, autorotate_householder
from sverchok.utils.math import np_vectors_angle, np_signed_angle
from sverchok.utils.curve.core import UnsupportedCurveTypeException
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import (
            SvNormalTrack, curve_frame_on_surface_array,
            MathutilsRotationCalculator, DifferentialRotationCalculator,
            SvCurveFrameCalculator,
            SvCurveLengthSolver,
            reparametrize_curve
        )
from sverchok.utils.curve.nurbs_algorithms import refine_curve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.data import *
from sverchok.utils.surface.gordon import gordon_surface
from sverchok.utils.surface.algorithms import SvDeformedByFieldSurface, SvTaperSweepSurface
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

def bend_surface(field, surface):
    control_points = np.copy(surface.get_control_points())
    m, n, _ = control_points.shape
    control_points = control_points.reshape((m*n, 3))
    cpt_xs = control_points[:,0]
    cpt_ys = control_points[:,1]
    cpt_zs = control_points[:,2]

    cpt_dxs, cpt_dys, cpt_dzs = field.evaluate_grid(cpt_xs, cpt_ys, cpt_zs)
    xs = cpt_xs + cpt_dxs
    ys = cpt_ys + cpt_dys
    zs = cpt_zs + cpt_dzs

    control_points = np.stack((xs, ys, zs)).T
    control_points = control_points.reshape((m,n,3))

    return surface.copy(control_points = control_points)

def place_profile_z(curve, z, scale):
    control_points = np.copy(curve.get_control_points())
    control_points[:,0] *= scale
    control_points[:,1] *= scale
    control_points[:,2] += z
    return curve.copy(control_points = control_points)

def place_profile(control_points, origin, scale):
    control_points = origin + control_points * scale
    return control_points

def rotate_curve_z(curve, angle, scale):
    control_points = np.copy(curve.get_control_points())
    control_points = control_points[:,0], control_points[:,1], control_points[:,2]
    rhos, phis, zs = to_cylindrical_np(control_points, mode='radians')
    xs, ys, zs = from_cylindrical_np(rhos*scale, phis+angle, zs, mode='radians')
    control_points = np.stack((xs, ys, zs)).T
    return curve.copy(control_points = control_points)

def rotate_curve(curve, axis, angle, scale):
    control_points = np.copy(curve.get_control_points())
    control_points = rotate_vector_around_vector_np(control_points, axis, angle)

    rotation_m = np.array(autorotate_householder(Vector(axis), Vector((0.0, 0.0, 1.0))).to_3x3())
    rotation_inv_m = np.linalg.inv(rotation_m)
    scale_m = np.eye(3)
    scale_m[0][0] = scale
    scale_m[1][1] = -scale
    #print("Scale", scale_m)
    #print("Rot", rotation_m)
    nonuniform_scale_m = np.linalg.inv(rotation_m) @ scale_m @ rotation_m

    control_points = [nonuniform_scale_m @ pt for pt in control_points]
    control_points = np.array(control_points)
    return curve.copy(control_points = control_points)

def nurbs_taper_sweep(profile, taper,
        point, direction, scale_base = SvTaperSweepSurface.UNIT):

    axis = LineEquation.from_direction_and_point(direction, point)

    taper_cpts = taper.get_control_points()
    taper_weights = taper.get_weights()

    taper_projections = axis.projection_of_points(taper_cpts)

    control_points = []
    weights = []

    if scale_base == SvTaperSweepSurface.TAPER:
        profile_t_min, profile_t_max = profile.get_u_bounds()
        profile_start = profile.evaluate(profile_t_min)
        profile_start_projection = axis.projection_of_point(profile_start)
        divisor = np.linalg.norm(profile_start - profile_start_projection)
    elif scale_base == SvTaperSweepSurface.PROFILE:
        taper_t_min, taper_t_max = taper.get_u_bounds()
        taper_start = taper.evaluate(taper_t_min)
        taper_start_projection = np.array(axis.projection_of_point(taper_start))
        divisor = np.linalg.norm(taper_start_projection - taper_start)
    else:
        divisor = 1.0

    profile_cpts = profile.get_control_points()
    n = len(profile_cpts)
    profile_knotvector = profile.get_knotvector()
    profile_weights = profile.get_weights()

    for taper_control_point, taper_projection, taper_weight in zip(taper_cpts, taper_projections, taper_weights):
        radius = np.linalg.norm(taper_control_point - taper_projection)
        if radius < 1e-8:
            parallel_points = np.empty((n,3))
            parallel_points[:] = taper_projection
        else:
            parallel_points = place_profile(profile_cpts, taper_projection, radius / divisor)
        parallel_weights = profile_weights * taper_weight

        control_points.append(parallel_points)
        weights.append(parallel_weights)

    control_points = np.array(control_points)
    control_points -= point

    weights = np.array(weights)

    degree_u = taper.get_degree()
    degree_v = profile.get_degree()

    return SvNurbsSurface.build(taper.get_nurbs_implementation(),
            degree_u, degree_v,
            taper.get_knotvector(), profile_knotvector,
            control_points, weights)

def nurbs_bevel_curve_simple(path, profile, taper,
        algorithm=SvBendAlongCurveField.HOUSEHOLDER,
        scale_all=False, path_axis=2,
        path_length_mode = 'T',
        path_length_resolution = 50,
        up_axis=None):

    taper_t_min, taper_t_max = taper.get_u_bounds()
    profile_t_min, profile_t_max = profile.get_u_bounds()
    taper_start = taper.evaluate(taper_t_min)
    taper_end = taper.evaluate(taper_t_max)
    z_min = taper_start[path_axis]
    z_max = taper_end[path_axis]

    field = SvBendAlongCurveField(path, algorithm, scale_all=scale_all, axis=path_axis, t_min=z_min, t_max=z_max, length_mode=path_length_mode, resolution=path_length_resolution, up_axis=up_axis)

    origin = np.zeros((3,), dtype=np.float64)
    direction = np.zeros((3,), dtype=np.float64)
    direction[path_axis] = 1.0
    sweeped = nurbs_taper_sweep(profile, taper, origin, direction, scale_base = SvTaperSweepSurface.TAPER)

    return bend_surface(field, sweeped).swap_uv()

def nurbs_bevel_curve_refined(path, profile, taper,
        algorithm=SvBendAlongCurveField.HOUSEHOLDER,
        scale_all=False, path_axis=2,
        path_length_mode = 'T',
        path_length_resolution = 50,
        up_axis=None,
        taper_refine=20):

    if path_length_mode == 'L':
        solver = SvCurveLengthSolver(taper)
        solver.prepare('SPL', path_length_resolution)
    else:
        solver = None
    taper = refine_curve(taper, taper_refine, solver=solver)
    return nurbs_bevel_curve_simple(path, profile, taper,
            algorithm = algorithm,
            scale_all = scale_all, path_axis = path_axis,
            path_length_mode = path_length_mode,
            path_length_resolution = path_length_resolution,
            up_axis = up_axis)

def nurbs_bevel_curve_gordon(path, profile, taper,
        algorithm=SvBendAlongCurveField.HOUSEHOLDER,
        scale_all=False, path_axis=2,
        path_length_mode = 'T',
        path_length_resolution = 50,
        up_axis=None,
        taper_samples=10, taper_refine=20, profile_samples=10):

    if profile.is_rational():
        raise Exception("Rational profile curves are not supported by Gordon algorithm")
    if taper.is_rational():
        raise Exception("Rational taper curves are not supported by Gordon algorithm")

    taper_t_min, taper_t_max = taper.get_u_bounds()
    profile_t_min, profile_t_max = profile.get_u_bounds()
    taper_start = taper.evaluate(taper_t_min)
    taper_end = taper.evaluate(taper_t_max)
    z_min = taper_start[path_axis]
    z_max = taper_end[path_axis]

    field = SvBendAlongCurveField(path, algorithm, scale_all=scale_all, axis=path_axis, t_min=z_min, t_max=z_max, length_mode=path_length_mode, resolution=path_length_resolution, up_axis=up_axis)

    if path_length_mode == 'T':
        taper_ts = np.linspace(taper_t_min, taper_t_max, num=taper_samples)
    else:
        solver = SvCurveLengthSolver(taper)
        solver.prepare('SPL', path_length_resolution)
        total_length = solver.get_total_length()
        input_lengths = np.linspace(0.0, total_length, num=taper_samples)
        taper_ts = solver.solve(input_lengths)

    taper_pts = taper.evaluate_array(taper_ts)
    taper_pts = taper_pts[:,0], taper_pts[:,1], taper_pts[:,2]
    taper_rhos, _, taper_zs = to_cylindrical_np(taper_pts)
    profile_start_rho = to_cylindrical(profile.evaluate(profile_t_min))[0]
    taper_start_rho, taper_start_angle, _ = to_cylindrical(taper.evaluate(taper_t_min))

    profiles = [place_profile_z(profile, z, scale) for z, scale in zip(taper_zs, taper_rhos / profile_start_rho)]
    profiles = [bend_curve(field, profile) for profile in profiles]
    profiles = [profile.reverse() for profile in profiles]

    profile_ts = np.linspace(profile_t_min, profile_t_max, num=profile_samples, endpoint=True)
    profile_pts = profile.evaluate_array(profile_ts)
    profile_pts = profile_pts[:,0], profile_pts[:,1], profile_pts[:,2]
    profile_rhos, profile_angles, _ = to_cylindrical_np(profile_pts, mode='radians')

    if path_length_mode == 'L':
        solver = SvCurveLengthSolver(taper)
        solver.prepare('SPL', path_length_resolution)
    else:
        solver = None
    taper = refine_curve(taper, taper_refine, solver=solver)

    tapers = [rotate_curve_z(taper, angle-taper_start_angle, scale) for angle, scale in zip(profile_angles, profile_rhos / profile_start_rho)]
    tapers = [bend_curve(field, taper) for taper in tapers]

    #intersections = [[taper.evaluate(t) for t in taper_ts] for taper in tapers]
    intersections = [[taper.evaluate(t) for taper in tapers] for t in taper_ts]

    return gordon_surface(tapers, profiles, intersections)[-1]

BEVEL_SIMPLE = 'SIMPLE'
BEVEL_REFINE = 'REFINE'
BEVEL_GORDON = 'GORDON'

def nurbs_bevel_curve(path, profile, taper,
        algorithm=SvBendAlongCurveField.HOUSEHOLDER,
        scale_all=False, path_axis=2,
        path_length_mode = 'T',
        path_length_resolution = 50,
        up_axis=None,
        precision_method = BEVEL_GORDON,
        taper_samples=10, taper_refine=20, profile_samples=10):
    
    if precision_method == BEVEL_GORDON:
        return nurbs_bevel_curve_gordon(path, profile, taper,
                algorithm = algorithm,
                scale_all = scale_all, path_axis = path_axis,
                path_length_mode = path_length_mode,
                path_length_resolution = path_length_resolution,
                up_axis = up_axis,
                taper_samples = taper_samples, taper_refine = taper_refine,
                profile_samples = profile_samples)
    elif precision_method == BEVEL_REFINE:
        return nurbs_bevel_curve_refined(path, profile, taper,
                algorithm = algorithm,
                scale_all = scale_all, path_axis = path_axis,
                path_length_mode = path_length_mode,
                path_length_resolution = path_length_resolution,
                up_axis = up_axis,
                taper_refine = taper_refine)
    elif precision_method == BEVEL_SIMPLE:
        return nurbs_bevel_curve_simple(path, profile, taper,
                algorithm = algorithm,
                scale_all = scale_all, path_axis = path_axis,
                path_length_mode = path_length_mode,
                path_length_resolution = path_length_resolution,
                up_axis = up_axis)
    else:
        raise Exception("Unknown method")

def generic_bevel_curve(path, profile, taper,
        algorithm=SvBendAlongCurveField.HOUSEHOLDER,
        scale_all=False, path_axis=2,
        path_length_mode = 'T',
        path_length_resolution = 50,
        up_axis=None,
        scale_base = SvTaperSweepSurface.PROFILE):

    taper_t_min, taper_t_max = taper.get_u_bounds()
    profile_t_min, profile_t_max = profile.get_u_bounds()
    taper_start = taper.evaluate(taper_t_min)
    taper_end = taper.evaluate(taper_t_max)
    z_min = taper_start[path_axis]
    z_max = taper_end[path_axis]

    origin = np.array([0.0, 0.0, 0.0])
    direction = np.eye(3)[path_axis]

    sweep_surface = SvTaperSweepSurface(profile, taper,
                        origin, direction,
                        scale_base = scale_base)

    bend_field = SvBendAlongCurveField(path, algorithm, scale_all=scale_all, axis=path_axis, t_min=z_min, t_max=z_max, length_mode=path_length_mode, resolution=path_length_resolution, up_axis=up_axis)

    return SvDeformedByFieldSurface(sweep_surface, bend_field, 1.0)

