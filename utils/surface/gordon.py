import numpy as np
from collections import defaultdict

from sverchok.utils.geom import Spline
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions,
        nurbs_divide, from_homogenous
    )
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.bezier import SvBezierCurve
from sverchok.utils.curve.nurbs_algorithms import unify_curves, nurbs_curve_to_xoy, nurbs_curve_matrix
from sverchok.utils.curve.algorithms import unify_curves_degree, SvCurveFrameCalculator, SvCurveOnSurface, SvCurveOnSurfaceCurvaturesCalculator
from sverchok.utils.curve.nurbs_solver_applications import interpolate_nurbs_curve_with_tangents, interpolate_nurbs_curve
from sverchok.utils.surface.core import UnsupportedSurfaceTypeException
from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.utils.surface.nurbs import SvNurbsSurface, simple_loft, interpolate_nurbs_surface
from sverchok.utils.surface.algorithms import unify_nurbs_surfaces
from sverchok.utils.logging import getLogger
from sverchok.data_structure import repeat_last_for_length

def reparametrize_by_segments(curve, t_values, tolerance=1e-2):
    # Reparametrize given curve so that parameter values from t_values parameter
    # would map to 1.0, 2.0, 3.0...

    # This algorithm is somewhat rude, reparametrization function
    # is not smooth. And this algorithm can produce additional
    # control points.

    t_min, t_max = curve.get_u_bounds()
    #print(f"Reparametrize: {t_min} - {t_max}: {t_values}")
    #t_values = [t_min] + t_values + [t_max]

    kv = curve.get_knotvector()

    def adjust(t):
        i = kv.searchsorted(t)
        if i > 0:
            smaller = kv[i-1]
            if (t - smaller) < tolerance:
                return smaller
        if i < len(kv):
            greater = kv[i]
            if (greater - t) < tolerance:
                return greater
        return t

    t_values = [adjust(t) for t in t_values]

    segments = []
    for t1, t2 in zip(t_values, t_values[1:]):
        segment = curve.cut_segment(t1, t2, rescale=True)
        segments.append(segment)
    
    result = segments[0]
    for segment in segments[1:]:
        result = result.concatenate(segment)
    
    return result

def gordon_surface(u_curves, v_curves, intersections, metric='POINTS', u_knots=None, v_knots=None, knotvector_accuracy=6, reparametrize_tolerance=1e-2, logger=None):
    """
    Generate a NURBS surface from a net of NURBS curves, by use of Gordon's algorithm.

    :param u_curves - list of NURBS curves along U direction (length N)
    :param v_curves - list of NURBS curves along V direction (length M)
    :param intersections - np.array of shape (N, M, 3): points of curves intersection
    :param metric - metric function that can be used to calculate T values of curves
                    intersections from their positions.
    :param u_knots - np.array, T values of curves intersection for each curve from u_curves
    :param v_knots - np.array, T values of curves intersection for each curve from v_curves

    return value: a NURBS surface.

    See also: The NURBS Book, 2nd ed., p.10.5.
    """

    if not u_curves or not v_curves:
        raise Exception("U or V curves are not provided")

    if (u_knots is None) != (v_knots is None):
        raise Exception("u_knots and v_knots must be either both provided or both omitted")

    if any(c.is_rational() for c in u_curves):
        raise Exception("Some of U-curves are rational. Rational curves are not supported for Gordon surface.")
    if any(c.is_rational() for c in v_curves):
        raise Exception("Some of V-curves are rational. Rational curves are not supported for Gordon surface.")

    if logger is None:
        logger = getLogger()

    intersections = np.array(intersections)

    if u_knots is not None:
        loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': 'POINTS'}

        u_curves = [reparametrize_by_segments(c, knots, reparametrize_tolerance) for c, knots in zip(u_curves, u_knots)]
        v_curves = [reparametrize_by_segments(c, knots, reparametrize_tolerance) for c, knots in zip(v_curves, v_knots)]
        #print("U", u_curves)
        #print("V", v_curves)

    else:
        loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': metric}
    interpolate_kwargs['logger'] = logger

    u_curves = unify_curves_degree(u_curves)
    u_curves = unify_curves(u_curves, accuracy=knotvector_accuracy)#, method='AVERAGE')
    v_curves = unify_curves_degree(v_curves)
    v_curves = unify_curves(v_curves, accuracy=knotvector_accuracy)#, method='AVERAGE')

    u_curves_degree = u_curves[0].get_degree()
    v_curves_degree = v_curves[0].get_degree()
    n = len(intersections)
    m = len(intersections[0])

    loft_v_degree = min(len(u_curves)-1, v_curves_degree)
    loft_u_degree = min(len(v_curves)-1, u_curves_degree)

    _,_,lofted_v = simple_loft(u_curves, degree_v=loft_v_degree, knotvector_accuracy = knotvector_accuracy, **loft_v_kwargs)
    _,_,lofted_u = simple_loft(v_curves, degree_v=loft_u_degree, knotvector_accuracy = knotvector_accuracy, **loft_u_kwargs)
    lofted_u = lofted_u.swap_uv()

    int_degree_u = min(m-1, u_curves_degree)
    int_degree_v = min(n-1, v_curves_degree)
    interpolated = interpolate_nurbs_surface(int_degree_u, int_degree_v, intersections, **interpolate_kwargs)
    interpolated = interpolated.swap_uv()
    #print(f"Loft.U: {lofted_u}")
    #print(f"Loft.V: {lofted_v}")
    #print(f"Interp: {interpolated}")
    #print(f"        {interpolated.get_knotvector_u()}")
    #print(f"        {interpolated.get_knotvector_v()}")

    lofted_u, lofted_v, interpolated = unify_nurbs_surfaces([lofted_u, lofted_v, interpolated], knotvector_accuracy=knotvector_accuracy)

    control_points = lofted_u.get_control_points() + \
                        lofted_v.get_control_points() - \
                        interpolated.get_control_points()

    surface = SvNurbsSurface.build(SvNurbsSurface.NATIVE,
                interpolated.get_degree_u(), interpolated.get_degree_v(),
                interpolated.get_knotvector_u(), interpolated.get_knotvector_v(),
                control_points, weights=None)
    #print(f"Result: {surface}")

    return lofted_u, lofted_v, interpolated, surface

TANGENCY_G1 = 'G1'
TANGENCY_G2 = 'G2'

ORTHO_3D = '3D'
ORTHO_UV = 'UV'

def nurbs_blend_surfaces(surface1, surface2, curve1, curve2, bulge1, bulge2, u_degree, u_samples, absolute_bulge = True, tangency = TANGENCY_G1, ortho_mode = ORTHO_UV, logger=None):
    t_min, t_max = curve1.get_u_bounds()
    ts1 = np.linspace(t_min, t_max, num=u_samples)

    t_min, t_max = curve2.get_u_bounds()
    ts2 = np.linspace(t_min, t_max, num=u_samples)

    calc1 = SvCurveOnSurfaceCurvaturesCalculator(curve1, surface1, ts1)
    calc2 = SvCurveOnSurfaceCurvaturesCalculator(curve2, surface2, ts2)
    _, c1_points, c1_tangents, c1_normals, c1_binormals = calc1.curve_frame_on_surface_array(normalize=False)
    _, c2_points, c2_tangents, c2_normals, c2_binormals = calc2.curve_frame_on_surface_array(normalize=False)

    if ortho_mode == ORTHO_UV:
        c1_binormals = calc1.uv_normals_in_3d
        c2_binormals = calc2.uv_normals_in_3d

    if absolute_bulge:
        c1_binormals = bulge1 * c1_binormals / np.linalg.norm(c1_binormals, axis=1, keepdims=True)
        c2_binormals = bulge2 * c2_binormals / np.linalg.norm(c2_binormals, axis=1, keepdims=True)
    else:
        c1_binormals = bulge1 * c1_binormals
        c2_binormals = bulge2 * c2_binormals

    c1_across = calc1.calc_curvatures_across_curve()
    c2_across = calc2.calc_curvatures_across_curve()
    #c1_along = calc1.calc_curvatures_along_curve()
    #c2_along = calc2.calc_curvatures_along_curve()
    #print(f"C1: {list(zip(ts1, c1_across, c1_along))}")
    #print(f"C2: {list(zip(ts2, c2_across, c1_along))}")

    #bad1 = (c1_across * c1_along) < 0
    #bad2 = (c2_across * c2_along) < 0
    #print(f"Bad1: {bad1}")
    #print(f"Bad2: {bad2}")
    #c1_normals[bad1] = - c1_normals[bad1]
    #c2_normals[bad2] = - c2_normals[bad2]

    #curve1 = interpolate_nurbs_curve_with_tangents(u_degree, c1_points, c1_tangents, tknots=ts1, logger=logger)
    #curve2 = interpolate_nurbs_curve_with_tangents(u_degree, c2_points, c2_tangents, tknots=ts2, logger=logger)
    curve1 = interpolate_nurbs_curve(u_degree, c1_points, tknots=ts1, logger=logger)
    curve2 = interpolate_nurbs_curve(u_degree, c2_points, tknots=ts2, logger=logger)
    u_curves = [curve1, curve2]

    if tangency == TANGENCY_G1:
        v_curves = [SvBezierCurve.from_control_points([p1, p1+t1, p2+t2, p2]) for p1, t1, p2, t2 in zip(c1_points, c1_binormals, c2_points, c2_binormals)]
    else: # G2
        v_curves = []
        for u1, u2, p1, p2, t1, t2, n1, n2, c1, c2 in zip(ts1, ts2, c1_points, c2_points, c1_binormals, c2_binormals, c1_normals, c2_normals, c1_across, c2_across):
            #print(f"T1 {u1}, T2 {u2}: P1 {p1}, P2 {p2}, T1 {t1}, -T2 {-t2}, n1 {n1}, n2 {n2}, c1 {c1}, c2 {c2}")
            v_curve = SvBezierCurve.from_tangents_normals_curvatures(p1, p2, t1, -t2, n1, n2, c1, c2)
            v_curves.append(v_curve)

    intersections = np.transpose(np.asarray([c1_points, c2_points]), axes=(1,0,2))

    return gordon_surface(u_curves, v_curves, intersections, logger=logger)[-1]

