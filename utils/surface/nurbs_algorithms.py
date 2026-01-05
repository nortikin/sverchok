# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.core.sv_custom_exceptions import ArgumentError, SvInvalidInputException, SvUnsupportedOptionException
from sverchok.utils.geom import Spline
from sverchok.utils.nurbs_common import (
        SvNurbsMaths,
        from_homogenous,
    )
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs_algorithms import unify_curves, nurbs_curve_to_xoy, nurbs_curve_matrix
from sverchok.utils.curve.algorithms import unify_curves_degree, SvCurveFrameCalculator, SvCurveLengthSolver
from sverchok.utils.curve.nurbs_solver_applications import interpolate_nurbs_curve_with_tangents
from sverchok.utils.sv_logging import get_logger
from sverchok.data_structure import repeat_last_for_length

def build_from_curves(curves, degree_u = None, implementation = SvNurbsMaths.NATIVE):
    curves = unify_curves(curves)
    degree_v = curves[0].get_degree()
    if degree_u is None:
        degree_u = degree_v
    control_points = [curve.get_control_points() for curve in curves]
    control_points = np.array(control_points)
    weights = np.array([curve.get_weights() for curve in curves])
    knotvector_u = sv_knotvector.generate(degree_u, len(curves))
    #knotvector_v = curves[0].get_knotvector()
    knotvector_v = sv_knotvector.average([curve.get_knotvector() for curve in curves])

    surface = SvNurbsMaths.build_surface(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)

    return curves, surface

def simple_loft(curves, degree_v = None, knots_u = 'UNIFY', knots_v = 'AVERAGE', knotvector_accuracy=6, metric='DISTANCE', tknots=None, implementation=SvNurbsMaths.NATIVE, logger = None):
    """
    Loft between given NURBS curves (a.k.a skinning).

    inputs:
    * degree_v - degree of resulting surface along V parameter; by default - use the same degree as provided curves
    * knots_u - one of:
        - 'UNIFY' - unify knotvectors of given curves by inserting additional knots
        - 'AVERAGE' - average knotvectors of given curves; this will work only if all curves have the same number of control points
    * metric - metric for interpolation; most useful are 'DISTANCE' and 'CENTRIPETAL'
    * implementation - NURBS maths implementation

    output: tuple:
        * list of curves - input curves after unification
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if knots_u not in {'UNIFY', 'AVERAGE'}:
        raise ArgumentError(f"Unsupported knots_u option: {knots_u}")
    if logger is None:
        logger = get_logger()
    curves = unify_curves_degree(curves)
    if knots_u == 'UNIFY':
        curves = unify_curves(curves, accuracy=knotvector_accuracy)
    else:
        kvs = [len(curve.get_control_points()) for curve in curves]
        max_kv, min_kv = max(kvs), min(kvs)
        if max_kv != min_kv:
            raise SvUnsupportedOptionException(f"U knotvector averaging is not applicable: Curves have different number of control points: {kvs}")

    degree_u = curves[0].get_degree()
    if degree_v is None:
        degree_v = degree_u

    if degree_v > len(curves):
        raise SvUnsupportedOptionException(f"V degree ({degree_v}) must be not greater than number of curves ({len(curves)}) minus 1")

    src_points = [curve.get_homogenous_control_points() for curve in curves]
    #print("P", [p.shape for p in src_points])
#     lens = [len(pts) for pts in src_points]
#     max_len, min_len = max(lens), min(lens)
#     if max_len != min_len:
#         raise Exception(f"Unify error: curves have different number of control points: {lens}")

    #print("Src:", src_points)
    src_points = np.array(src_points)
    src_points = np.transpose(src_points, axes=(1,0,2))

    if tknots is None:
        tknots_vs = [Spline.create_knots(src_points[i,:], metric=metric) for i in range(src_points.shape[0])]
        tknots_vs = np.array(tknots_vs)
        if knots_v == 'AVERAGE':
            tknots_vs[:] = np.mean(tknots_vs, axis=0)
    else:
        tknots_vs = np.zeros((len(src_points), len(tknots)))
        tknots_vs[:] = tknots

    v_curves = [SvNurbsMaths.interpolate_curve(implementation, degree_v, points, metric=metric, tknots=tknots_vs[j], logger=logger) for j, points in enumerate(src_points)]
    if knots_v == 'UNIFY':
        v_curves = unify_curves(v_curves, accuracy = knotvector_accuracy)
    control_points = [curve.get_homogenous_control_points() for curve in v_curves]
    control_points = np.array(control_points)
    #weights = [curve.get_weights() for curve in v_curves]
    #weights = np.array([curve.get_weights() for curve in curves]).T
    n,m,ndim = control_points.shape
    control_points = control_points.reshape((n*m, ndim))
    control_points, weights = from_homogenous(control_points)
    control_points = control_points.reshape((n,m,3))
    weights = weights.reshape((n,m))

    if knots_v == 'UNIFY':
        knotvector_v = v_curves[0].get_knotvector()
    else:
        knotvector_v = sv_knotvector.from_tknots(degree_v, tknots_vs[0])
    if knots_u == 'UNIFY':
        knotvector_u = curves[0].get_knotvector()
    else:
        knotvectors = np.array([curve.get_knotvector() for curve in curves])
        knotvector_u = knotvectors.mean(axis=0)
    print(f"Kv U: {knotvector_u.shape}, V: {knotvector_v.shape}")
    
    surface = SvNurbsMaths.build_surface(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)
    surface.u_bounds = curves[0].get_u_bounds()
    return curves, v_curves, surface

def loft_by_binormals(curves, degree_v = 3,
        binormals_scale = 1.0,
        metric = 'DISTANCE', tknots=None,
        knotvector_accuracy = 6,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):

    if logger is None:
        logger = get_logger()

    n_curves = len(curves)
    curves = unify_curves_degree(curves)
    curves = unify_curves(curves, accuracy=knotvector_accuracy)
    degree_u = curves[0].get_degree()

    src_points = [curve.get_homogenous_control_points() for curve in curves]
    src_points = np.array(src_points)
    src_points = np.transpose(src_points, axes=(1,0,2))
    
    greville_ts = [curve.calc_greville_ts() for curve in curves]
    
    binormals = [curve.binormal_array(ts, normalize=True) for curve, ts in zip(curves, greville_ts)]
    binormals = np.array(binormals)
    binormals = np.transpose(binormals, axes=(1,0,2))

    greville_pts = [curve.evaluate_array(ts) for curve, ts in zip(curves, greville_ts)]
    greville_pts = np.array(greville_pts)
    greville_dpts = greville_pts[1:] - greville_pts[:-1]
    greville_dpts_mean = np.mean(greville_dpts, axis=0)
    greville_dpts = np.concatenate((greville_dpts, [greville_dpts_mean]))
    binormal_lengths = np.linalg.norm(greville_dpts, axis=2, keepdims = True)
    binormal_lengths = np.transpose(binormal_lengths, axes=(1,0,2))
    
    cpts_mean_by_curve = np.mean(src_points, axis=0)
    cpts_direction = np.mean(cpts_mean_by_curve[1:] - cpts_mean_by_curve[:-1], axis=0)
    
    binormals *= binormal_lengths * binormals_scale / 3.0
    n,m,ndim = binormals.shape
    
    binormals = np.concatenate((binormals, np.zeros((n,m,1))), axis=2)
    
    r = np.sum(binormals * cpts_direction, axis=2)
    bad = (r < 0)
    binormals[bad] = - binormals[bad]

    tknots_vs = [Spline.create_knots(src_points[i,:], metric=metric) for i in range(n)]
    tknots_vs = np.array(tknots_vs)
    tknots_v = np.mean(tknots_vs, axis=0)
    
    v_curves = [interpolate_nurbs_curve_with_tangents(degree_v, points, tangents, tknots=tknots_v, implementation=implementation, logger=logger) for points, tangents in zip(src_points, binormals)]
    control_points = [curve.get_homogenous_control_points() for curve in v_curves]
    control_points = np.array(control_points)
    n,m,ndim = control_points.shape
    control_points = control_points.reshape((n*m, ndim))
    control_points, weights = from_homogenous(control_points)
    control_points = control_points.reshape((n,m,3))
    weights = weights.reshape((n,m))
    
    knotvector_u = curves[0].get_knotvector()
    knotvector_v = v_curves[0].get_knotvector()
    
    surface = SvNurbsMaths.build_surface(SvNurbsMaths.NATIVE,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)
    return surface

def loft_with_tangents(curves, tangent_fields, degree_v = 3,
        metric = 'DISTANCE', tknots=None,
        knotvector_accuracy = 6,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):

    if logger is None:
        logger = get_logger()

    n_curves = len(curves)
    curves = unify_curves_degree(curves)
    curves = unify_curves(curves, accuracy=knotvector_accuracy)
    degree_u = curves[0].get_degree()

    src_points = [curve.get_homogenous_control_points() for curve in curves]
    src_points = np.array(src_points)
    src_points = np.transpose(src_points, axes=(1,0,2))

    tangents = [field.evaluate_array(curve.get_control_points()) for curve, field in zip(curves, tangent_fields)]
    tangents = np.array(tangents)
    tangents = np.transpose(tangents, axes=(2,0,1))

    n,m,ndim = tangents.shape
    tangents = np.concatenate((tangents, np.zeros((n,m,1))), axis=2)

    tknots_vs = [Spline.create_knots(src_points[i,:], metric=metric) for i in range(n_curves)]
    tknots_vs = np.array(tknots_vs)
    tknots_v = np.mean(tknots_vs, axis=0)

    v_curves = [interpolate_nurbs_curve_with_tangents(degree_v, points, tangents, tknots=tknots_v, implementation=implementation, logger=logger) for points, tangents in zip(src_points, tangents)]
    control_points = [curve.get_homogenous_control_points() for curve in v_curves]
    control_points = np.array(control_points)
    n,m,ndim = control_points.shape
    control_points = control_points.reshape((n*m, ndim))
    control_points, weights = from_homogenous(control_points)
    control_points = control_points.reshape((n,m,3))
    weights = weights.reshape((n,m))
    
    knotvector_u = curves[0].get_knotvector()
    knotvector_v = v_curves[0].get_knotvector()
    
    surface = SvNurbsMaths.build_surface(SvNurbsMaths.NATIVE,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)
    return surface

def interpolate_nurbs_curves(curves, base_vs, target_vs,
        degree_v = None, knots_u = 'UNIFY',
        knotvector_accuracy = 6,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):
    """
    Interpolate many NURBS curves between a list of NURBS curves, by lofting.
    Inputs:
    * curves: list of SvNurbsCurve
    * base_vs: np.array of shape (M,) - T values corresponding to `curves'
        input. M must be equal to len(curves).
    * target_vs: np.array of shape (N,) - T values at which to calculate interpolated curves.
    * rest: arguments for simple_loft.
    Returns: list of SvNurbsCurve of length N.
    """
    min_v, max_v = min(base_vs), max(base_vs)
    # Place input curves along Z axis and loft between them
    vectors = np.array([(0,0,v) for v in base_vs])
    to_loft = [curve.transform(None, vector) for curve, vector in zip(curves, vectors)]
    #to_loft = curves
    tknots = (base_vs - min_v) / (max_v - min_v)
    _,_,lofted = simple_loft(to_loft,
                degree_v = degree_v, knots_u = knots_u,
                knotvector_accuracy = knotvector_accuracy,
                #metric = 'POINTS',
                tknots = tknots,
                implementation = implementation,
                logger = logger)

    rebased_vs = np.linspace(min_v, max_v, num=len(target_vs))
    iso_curves = [lofted.iso_curve(fixed_direction='V', param=v) for v in rebased_vs]
    # Calculate iso_curves of the lofted surface, and move them back along Z axis
    back_vectors = []
    for v in rebased_vs:
        back_vector = np.array([0, 0, -v])
        back_vectors.append(back_vector)

    return [curve.transform(None, back) for curve, back in zip(iso_curves, back_vectors)]

def interpolate_nurbs_surface(degree_u, degree_v, points, metric='DISTANCE', uknots=None, vknots=None, implementation = SvNurbsMaths.NATIVE, logger=None):
    points = np.asarray(points)
    n = len(points)
    m = len(points[0])

    if (uknots is None) != (vknots is None):
        raise ArgumentError("uknots and vknots must be either both provided or both omitted")

    if logger is None:
        logger = get_logger()

    if uknots is None:
        knots = np.array([Spline.create_knots(points[i,:], metric=metric) for i in range(n)])
        uknots = knots.mean(axis=0)
    if vknots is None:
        knots = np.array([Spline.create_knots(points[:,j], metric=metric) for j in range(m)])
        vknots = knots.mean(axis=0)

    knotvector_u = sv_knotvector.from_tknots(degree_u, uknots)
    knotvector_v = sv_knotvector.from_tknots(degree_v, vknots)

    u_curves = [SvNurbsMaths.interpolate_curve(implementation, degree_u, points[i,:], tknots=uknots, logger=logger) for i in range(n)]
    u_curves_cpts = np.array([curve.get_control_points() for curve in u_curves])
    v_curves = [SvNurbsMaths.interpolate_curve(implementation, degree_v, u_curves_cpts[:,j], tknots=vknots, logger=logger) for j in range(m)]

    control_points = np.array([curve.get_control_points() for curve in v_curves])

    surface = SvNurbsMaths.build_surface(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights=None)

    return surface

def nurbs_sweep_impl(path, profiles, ts, frame_calculator,
        knots_u = 'UNIFY',
        knotvector_accuracy = 6,
        metric = 'DISTANCE',
        implementation = SvNurbsMaths.NATIVE,
        logger = None):
    """
    NURBS Sweep implementation.
    Interface of this function is not flexible, so you usually want to call `nurbs_sweep' instead.

    Inputs:
    * path: SvNurbsCurve
    * profiles: list of SvNurbsCurve
    * ts: T values along path which correspond to profiles. Number of ts must
        be equal to number of profiles.
    * frame_calculator: a function, which takes np.array((n,)) of T values and
        returns np.array((n, 3, 3)) of curve frames.
    * rest: arguments for simple_loft function.

    output: tuple:
        * list of curves - initial profile curves placed / rotated along the path curve
        * list of curves - interpolated profile curves
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if len(profiles) != len(ts):
        raise ArgumentError(f"Number of profiles ({len(profiles)}) is not equal to number of T values ({len(ts)})")
    if len(ts) < 2:
        raise ArgumentError("At least 2 profiles are required")

    path_points = path.evaluate_array(ts)
    frames = frame_calculator(ts)
    to_loft = []
    for profile, path_point, frame in zip(profiles, path_points, frames):
        profile = profile.transform(frame, path_point)
        #cpt = profile.evaluate(profile.get_u_bounds()[0])
        #profile = profile.transform(None, -cpt + path_point)
        to_loft.append(profile)

    unified_curves, v_curves, surface = simple_loft(to_loft, degree_v = path.get_degree(),
            knots_u = knots_u, metric = metric,
            knotvector_accuracy = knotvector_accuracy,
            implementation = implementation,
            logger = logger)
    return to_loft, unified_curves, v_curves, surface

def nurbs_sweep_with_tangents_impl(path, profiles, ts, frame_calculator,
        knots_u = 'UNIFY',
        knotvector_accuracy = 6,
        metric = 'DISTANCE',
        implementation = SvNurbsMaths.NATIVE,
        logger = None):

    if len(profiles) != len(ts):
        raise ArgumentError(f"Number of profiles ({len(profiles)}) is not equal to number of T values ({len(ts)})")
    if len(ts) < 2:
        raise ArgumentError("At least 2 profiles are required")

    profiles = unify_curves_degree(profiles)
    profiles = unify_curves(profiles, method=knots_u, accuracy=knotvector_accuracy)

    path_points = path.evaluate_array(ts)
    frames = frame_calculator(ts)
    placed_profiles = []
    for profile, path_point, frame in zip(profiles, path_points, frames):
        profile = profile.transform(frame, path_point)
        placed_profiles.append(profile)

    degree_u = placed_profiles[0].get_degree()
    degree_v = path.get_degree()

    src_points = [profile.get_homogenous_control_points() for profile in placed_profiles]
    src_points = np.array(src_points)
    src_points = np.transpose(src_points, axes=(1,0,2))

    path_tangents = path.tangent_array(ts)
    curvatures = path.curvature_array(ts)
    normals = path.main_normal_array(ts, normalize=True)

    #offset_vectors = [profile.get_control_points() - pt0 for profile, pt0 in zip(placed_profiles, path_points)]
    offset_vectors = [profile.calc_greville_points() - pt0 for profile, pt0 in zip(placed_profiles, path_points)]
    offset_vectors = np.array(offset_vectors)
    normals = np.transpose(normals[np.newaxis], axes=(1,0,2))
    prod = np.sum(offset_vectors * normals, axis=2)
    profile_tangents = (1.0 - prod * curvatures[np.newaxis].T)[np.newaxis].T * path_tangents

    n,m,ndim = profile_tangents.shape
    profile_tangents = np.concatenate((profile_tangents, np.zeros((n,m,1))), axis=2)

    v_curves = [interpolate_nurbs_curve_with_tangents(degree_v, points, tangents, tknots=ts, implementation=implementation, logger=logger) for points, tangents in zip(src_points, profile_tangents)]
    control_points = [curve.get_homogenous_control_points() for curve in v_curves]
    control_points = np.array(control_points)
    n,m,ndim = control_points.shape
    control_points = control_points.reshape((n*m, ndim))
    control_points, weights = from_homogenous(control_points)
    control_points = control_points.reshape((n,m,3))
    weights = weights.reshape((n,m))
    
    knotvector_u = placed_profiles[0].get_knotvector()
    knotvector_v = v_curves[0].get_knotvector()

    surface = SvNurbsMaths.build_surface(SvNurbsMaths.NATIVE,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)
    return None, placed_profiles, v_curves, surface

SWEEP_GREVILLE = object()

def nurbs_sweep(
    path,
    profiles,
    ts,
    min_profiles,
    algorithm,
    use_tangents = False,
    knots_u="UNIFY",
    knotvector_accuracy=6,
    metric="DISTANCE",
    implementation=SvNurbsMaths.NATIVE,
    logger=None,
    **kwargs,
):
    """
    NURBS Sweep surface.
    
    Inputs:
    * path: SvNurbsCurve
    * profiles: list of SvNurbsCurve
    * ts: T values along path which correspond to profiles. Number of ts must
        be equal to number of profiles. If None, the function will calculate
        appropriate values automatically.
    * min_profiles: minimal number of (copies of) profile curves to be placed
        along the path: bigger number correspond to better precision, within
        certain limits. If min_profiles > len(profiles), additional profiles
        will be generated by interpolation (by lofting).
    * algorithm: rotation calculation algorithm: one of NONE, ZERO, FRENET,
        HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL, NORMAL_DIR.
    * knots_u: 'UNIFY' or 'AVERAGE'
    * metric: interpolation metric
    * implementation: surface implementation
    * kwargs: arguments for rotation calculation algorithm

    output: tuple:
        * list of curves - initial profile curves placed / rotated along the path curve
        * list of curves - interpolated profile curves
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if logger is None:
        logger = get_logger()

    n_profiles = len(profiles)
    use_greville = ts is SWEEP_GREVILLE
    have_ts = ts is not None and not use_greville and len(ts) > 0
    if have_ts and n_profiles != len(ts):
        raise ArgumentError(f"Number of profiles ({n_profiles}) is not equal to number of T values ({len(ts)})")

    t_min, t_max = path.get_u_bounds()
    if not have_ts and not use_greville:
        ts = np.linspace(t_min, t_max, num=n_profiles)
    elif use_greville:
        ts = path.calc_greville_ts()
        min_profiles = len(ts)

    if n_profiles == 1:
        p = profiles[0]
        if not have_ts and not use_greville:
            logger.debug("N profiles == 1, T values are not provided, Greville points are not used: calculate T vlaues linearly")
            ts = np.linspace(t_min, t_max, num=min_profiles)
        profiles = [p] * len(ts)
    elif n_profiles == 2 and n_profiles < min_profiles:
        coeffs = np.linspace(0.0, 1.0, num=min_profiles)
        p0, p1 = profiles
        profiles = [p0.lerp_to(p1, coeff) for coeff in coeffs]
        if not use_greville:
            logger.debug("N profiles == 2, T values are not provided, Greville points are not used: calculate T vlaues linearly")
            ts = np.linspace(t_min, t_max, num=min_profiles)
    elif n_profiles < min_profiles:
        if use_greville:
            src_profile_ts = np.linspace(t_min, t_max, num=n_profiles)
        else:
            src_profile_ts = ts
        target_vs = np.linspace(0.0, 1.0, num=min_profiles)
        max_degree = n_profiles - 1
        logger.debug(f"N profiles {n_profiles} < min_profiles {min_profiles}, interpolate profiles")
        profiles = interpolate_nurbs_curves(profiles, src_profile_ts, target_vs,
                    degree_v = min(max_degree, path.get_degree()),
                    knots_u = knots_u,
                    knotvector_accuracy = knotvector_accuracy,
                    implementation = implementation,
                    logger = logger)
        if not use_greville:
            logger.debug("Greville points are not used, calculate T values linearly")
            ts = np.linspace(t_min, t_max, num=min_profiles)
    else:
        profiles = repeat_last_for_length(profiles, min_profiles)

    frame_calculator = SvCurveFrameCalculator(path, algorithm, **kwargs).get_matrices

#     for i, p in enumerate(profiles):
#         print(f"P#{i}: {p.get_control_points()}")

    if not use_tangents:
        return nurbs_sweep_impl(path, profiles, ts, frame_calculator,
                    knots_u=knots_u, metric=metric,
                    knotvector_accuracy = knotvector_accuracy,
                    implementation=implementation,
                    logger = logger)
    else:
        return nurbs_sweep_with_tangents_impl(path, profiles, ts, frame_calculator,
                    knots_u=knots_u, metric=metric,
                    knotvector_accuracy = knotvector_accuracy,
                    implementation=implementation,
                    logger = logger)

def nurbs_birail_copy_profiles(profiles, min_profiles, degree_v,
                               knots_u = 'UNIFY', knotvector_accuracy = 6,
                               implementation = SvNurbsMaths.NATIVE,
                               logger = None):
    n_profiles = len(profiles)
    if n_profiles == 1:
        p = profiles[0]
        profiles = [p] * min_profiles
    elif n_profiles == 2 and n_profiles < min_profiles:
        coeffs = np.linspace(0.0, 1.0, num=min_profiles)
        p0, p1 = profiles
        profiles = [p0.lerp_to(p1, coeff) for coeff in coeffs]
    elif n_profiles < min_profiles:
        target_vs = np.linspace(0.0, 1.0, num=min_profiles)
        max_degree = n_profiles - 1
        ts = np.linspace(0.0, 1.0, num=n_profiles)
        profiles = interpolate_nurbs_curves(profiles, ts, target_vs,
                    degree_v = min(max_degree, degree_v),
                    knots_u = knots_u,
                    knotvector_accuracy = knotvector_accuracy,
                    implementation = implementation,
                    logger = logger)
    else:
        profiles = repeat_last_for_length(profiles, min_profiles)
        profiles = unify_curves(profiles)
    return profiles

def nurbs_birail_calc_key_points(path1, path2, n_profiles,
        ts1 = None, ts2 = None,
        length_resolution = None):

    have_ts1 = ts1 is not None and len(ts1) > 0
    have_ts2 = ts2 is not None and len(ts2) > 0
    if have_ts1 and n_profiles != len(ts1):
        raise ArgumentError(f"Number of profiles ({n_profiles}) is not equal to number of T1 values ({len(ts1)})")
    if have_ts2 and n_profiles != len(ts2):
        raise ArgumentError(f"Number of profiles ({n_profiles}) is not equal to number of T2 values ({len(ts2)})")

    if length_resolution is not None:
        solver1 = SvCurveLengthSolver(path1)
        solver1.prepare('SPL', length_resolution)
        solver2 = SvCurveLengthSolver(path2)
        solver2.prepare('SPL', length_resolution)

    t_min_1, t_max_1 = path1.get_u_bounds()
    t_min_2, t_max_2 = path2.get_u_bounds()

    def calc_ts1(n):
        if length_resolution is None:
            return np.linspace(t_min_1, t_max_1, num=n)
        else:
            path1_length = solver1.get_total_length()
            lengths = np.linspace(0.0, path1_length, num=n)
            return solver1.solve(lengths)

    def calc_ts2(n):
        if length_resolution is None:
            return np.linspace(t_min_2, t_max_2, num=n)
        else:
            path2_length = solver2.get_total_length()
            lengths = np.linspace(0.0, path2_length, num=n)
            return solver2.solve(lengths)

    if not have_ts1:
        ts1 = calc_ts1(n_profiles)
    if not have_ts2:
        ts2 = calc_ts2(n_profiles)

    points1 = path1.evaluate_array(ts1)
    points2 = path2.evaluate_array(ts2)

    return ts1, ts2, points1, points2


def nurbs_birail_place_profiles(path1, path2, profiles,
        ts1, ts2, points1, points2,
        scale_uniform = True,
        auto_rotate = False,
        use_tangents = 'PATHS_AVG',
        y_axis = None):

    orig_profiles = profiles[:]

    if use_tangents == 'PATHS_AVG':
        tangents1 = path1.tangent_array(ts1)
        tangents2 = path2.tangent_array(ts2)
        tangents = 0.5 * (tangents1 + tangents2)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    elif use_tangents == 'FROM_PATH1':
        tangents = path1.tangent_array(ts1)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    elif use_tangents == 'FROM_PATH2':
        tangents = path2.tangent_array(ts2)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    elif use_tangents == 'FROM_PROFILE':
        tangents = []
        for profile in orig_profiles:
            matrix = nurbs_curve_matrix(profile)
            yy = matrix @ np.array([0, 0, -1])
            yy /= np.linalg.norm(yy)
            tangents.append(yy)
        tangents = np.array(tangents)
    elif use_tangents == 'CUSTOM':
        tangents = None

    binormals = points2 - points1
    scales = np.linalg.norm(binormals, axis=1, keepdims=True)
    if scales.min() < 1e-6:
        raise SvInvalidInputException("Paths go too close")
    binormals /= scales

    if use_tangents != 'CUSTOM':
        normals = np.cross(tangents, binormals)
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)

        tangents = np.cross(binormals, normals)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    else:
        if y_axis is None:
            raise SvInvalidInputException("Y axis is not provided for custom orientation")
        if np.linalg.norm(y_axis) < 1e-6:
            raise SvInvalidInputException("Y axis is too small")
        y_axis /= np.linalg.norm(y_axis)
        tangents = np.cross(binormals, y_axis)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
        normals = np.cross(tangents, binormals)
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)

    matrices = np.dstack((normals, binormals, tangents))
    matrices = np.transpose(matrices, axes=(0,2,1))
    matrices = np.linalg.inv(matrices)

    scales = scales.flatten()
    placed_profiles = []
    for pt1, pt2, profile, tangent, scale, matrix in zip(points1, points2, profiles, tangents, scales, matrices):

        if auto_rotate:
            profile = nurbs_curve_to_xoy(profile, tangent)

        t_min, t_max = profile.get_u_bounds()
        pr_start = profile.evaluate(t_min)
        pr_end = profile.evaluate(t_max)
        pr_vector = pr_end - pr_start
        pr_length = np.linalg.norm(pr_vector)
        if pr_length < 1e-6:
            raise SvInvalidInputException(f"One of profiles is closed: t={t_min} {pr_start} - t={t_max} {pr_end}")
        pr_dir = pr_vector / pr_length
        pr_x, pr_y, _ = tuple(pr_dir)

        rotation = np.array([
                (pr_y, -pr_x, 0),
                (pr_x, pr_y, 0),
                (0, 0, 1)
            ])

        scale /= pr_length
        if scale_uniform:
            scale_m = np.array([
                    (scale, 0, 0),
                    (0, scale, 0),
                    (0, 0, scale)
                ])
        else:
            scale_m = np.array([
                    (1, 0, 0),
                    (0, scale, 0),
                    (0, 0, 1)
                ])
        cpts = [matrix @ scale_m @ rotation @ (pt - pr_start) + pt1 for pt in profile.get_control_points()]
        cpts = np.array(cpts)

        profile = profile.copy(control_points = cpts)
        placed_profiles.append(profile)
    return ts1, ts2, placed_profiles

def prepare_nurbs_birail(path1, path2, profiles,
        ts1 = None, ts2 = None,
        length_resolution = None,
        min_profiles = 10,
        knots_u = 'UNIFY',
        knotvector_accuracy = 6,
        degree_v = None,
        scale_uniform = True,
        auto_rotate = False,
        use_tangents = 'PATHS_AVG',
        y_axis = None,
        implementation=SvNurbsMaths.NATIVE,
        logger = None):

    if degree_v is None:
        degree_v = path1.get_degree()

    profiles = nurbs_birail_copy_profiles(profiles, min_profiles, degree_v,
                                          knots_u = knots_u,
                                          knotvector_accuracy = knotvector_accuracy,
                                          implementation = implementation,
                                          logger = logger)

    ts1, ts2, points1, points2 = nurbs_birail_calc_key_points(path1, path2, len(profiles),
                                        ts1 = ts1, ts2 = ts2,
                                       length_resolution = length_resolution)

    return nurbs_birail_place_profiles(path1, path2, profiles,
                                       ts1 = ts1, ts2 = ts2,
                                       points1 = points1, points2 = points2,
                                       scale_uniform = scale_uniform,
                                       auto_rotate = auto_rotate,
                                       use_tangents = use_tangents,
                                       y_axis = y_axis)

def nurbs_birail_by_tensor_product(path1, path2, profiles,
        degree_v = None,
        knots_u = 'UNIFY',
        knotvector_accuracy = 6,
        scale_uniform = True,
        auto_rotate = False,
        use_tangents = 'PATHS_AVG',
        y_axis = None,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):
    """
    NURBS BiRail: implementation based on control points tensor product.

    Args:
        * path1, path2: SvNurbsCurve.
        * profiles: list of SvNurbsCurve.
        * ts: T values along path which correspond to profiles. Number of ts must
            be equal to number of profiles. If None, the function will calculate
            appropriate values automatically.
        * knots_u: 'UNIFY' or 'AVERAGE'
        * degree_v: degree of the surface along V direction; if not specified,
            degree of the first path will be used.
        * scale_uniform: If True, profile curves will be scaled along all axes
            uniformly; if False, they will be scaled only along one axis, in order to
            fill space between two path curves.
        * auto_rotate: if False, the profile curves are supposed to lie in XOY plane.
            Otherwise, try to figure out their rotation automatically.
        * implementation: surface implementation

    Returns:
        an instance of SvNurbsSurface.
    """

    path1, path2 = unify_curves_degree([path1, path2])
    path1, path2 = unify_curves([path1, path2])

    if degree_v is None:
        degree_v = path1.get_degree()
    profiles = nurbs_birail_copy_profiles(profiles,
                                          min_profiles = len(path1.get_control_points()),
                                          degree_v = degree_v,
                                          knots_u = knots_u,
                                          knotvector_accuracy = knotvector_accuracy,
                                          implementation = implementation,
                                          logger = logger)
    ts1 = path1.calc_greville_ts()
    ts2 = path2.calc_greville_ts()
    points1 = path1.get_control_points()
    points2 = path2.get_control_points()

    ts1, ts2, profiles = nurbs_birail_place_profiles(path1, path2, profiles,
                                       ts1 = ts1, ts2 = ts2,
                                       points1 = points1, points2 = points2,
                                       scale_uniform = scale_uniform,
                                       auto_rotate = auto_rotate,
                                       use_tangents = use_tangents,
                                       y_axis = y_axis)
    control_points = [curve.get_control_points() for curve in profiles]
    control_points = np.array(control_points)
    control_points = np.transpose(control_points, axes=(1,0,2))

    # Calc Greville Ts for each profile, and scale them all to [0..1].
    # These values will be used to interpolate weights.
    betas = [profile.calc_greville_ts() for profile in profiles]
    betas = np.array(betas)
    betas /= betas[:,-1][np.newaxis].T
    
    weights1 = path1.get_weights()[np.newaxis].T
    weights2 = path2.get_weights()[np.newaxis].T
    interpolated_weights = weights1 * (1 - betas) + weights2 * betas
    profile_weights = [profile.get_weights() for profile in profiles]
    profile_weights = np.array(profile_weights)
    weights = interpolated_weights * profile_weights

    knotvector_u = profiles[0].get_knotvector()
    knotvector_v = path1.get_knotvector()
    degree_u = profiles[0].get_degree()
    degree_v = path1.get_degree()
    surface = SvNurbsMaths.build_surface(implementation = implementation,
                degree_u = degree_u, degree_v = degree_v,
                knotvector_u = knotvector_u, knotvector_v = knotvector_v,
                control_points = control_points, weights=weights.T)
    return surface

def nurbs_birail(path1, path2, profiles,
        ts1 = None, ts2 = None,
        length_resolution = None,
        min_profiles = 10,
        knots_u = 'UNIFY',
        knotvector_accuracy = 6,
        degree_v = None, metric = 'DISTANCE',
        scale_uniform = True,
        auto_rotate = False,
        use_tangents = 'PATHS_AVG',
        y_axis = None,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):
    """
    NURBS BiRail: original Loft-based implementation.

    Args:
        * path1, path2: SvNurbsCurve.
        * profiles: list of SvNurbsCurve.
        * ts: T values along path which correspond to profiles. Number of ts must
            be equal to number of profiles. If None, the function will calculate
            appropriate values automatically.
        * min_profiles: minimal number of (copies of) profile curves to be placed
            along the path: bigger number correspond to better precision, within
            certain limits. If min_profiles > len(profiles), additional profiles
            will be generated by interpolation (by lofting).
        * knots_u: 'UNIFY' or 'AVERAGE'
        * degree_v: degree of the surface along V direction; if not specified,
            degree of the first path will be used.
        * metric: interpolation metric
        * scale_uniform: If True, profile curves will be scaled along all axes
            uniformly; if False, they will be scaled only along one axis, in order to
            fill space between two path curves.
        * auto_rotate: if False, the profile curves are supposed to lie in XOY plane.
            Otherwise, try to figure out their rotation automatically.
        * implementation: surface implementation

    Returns: tuple:
        * list of curves - initial profile curves placed / rotated along the path curve
        * list of curves - interpolated profile curves
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if logger is None:
        logger = get_logger()

    path1, path2 = unify_curves_degree([path1, path2])
    path1, path2 = unify_curves([path1, path2])

    if (ts1 is SWEEP_GREVILLE) != (ts2 is SWEEP_GREVILLE):
        raise ArgumentError("Both ts1 and ts2 must be either both SWEEP_GREVILLE, or both have another value")
    if ts1 is SWEEP_GREVILLE:
        ts1 = path1.calc_greville_ts()
        ts2 = path2.calc_greville_ts()
        min_profiles = len(ts1)

    _, _, placed_profiles = prepare_nurbs_birail(path1, path2, profiles,
            ts1 = ts1, ts2 = ts2,
            length_resolution = length_resolution,
            min_profiles = min_profiles,
            degree_v = degree_v,
            scale_uniform = scale_uniform,
            auto_rotate = auto_rotate,
            use_tangents = use_tangents,
            y_axis = y_axis,
            knotvector_accuracy = knotvector_accuracy)

    unified_curves, v_curves, surface = simple_loft(placed_profiles, degree_v = degree_v,
            knots_u = knots_u, metric = metric,
            knotvector_accuracy = knotvector_accuracy,
            implementation = implementation,
            logger = logger)

    return placed_profiles, unified_curves, v_curves, surface

