import numpy as np

from sverchok.core.sv_custom_exceptions import ArgumentError, SvInvalidInputException
from sverchok.utils.math import distribute_int
from sverchok.utils.curve.bezier import SvBezierCurve
from sverchok.utils.curve.nurbs_algorithms import CurvesUnificationException, remove_excessive_knots, unify_curves
from sverchok.utils.curve.algorithms import unify_curves_degree, curve_frame_on_surface_array, SvCurveOnSurfaceCurvaturesCalculator
from sverchok.utils.curve.nurbs_solver_applications import interpolate_nurbs_curve_with_tangents, interpolate_nurbs_curve
from sverchok.utils.curve.splines import SvMonotoneSpline
from sverchok.utils.surface.core import UnsupportedSurfaceTypeException
from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.utils.surface.nurbs import SvNurbsSurface, simple_loft, interpolate_nurbs_surface, prepare_nurbs_birail
from sverchok.utils.surface.algorithms import unify_nurbs_surfaces
from sverchok.utils.sv_logging import get_logger

class Reparametrizer:
    pass

class SegmentsReparametrizer(Reparametrizer):
    def __init__(self, remove_knots = False, tolerance = 1e-6):
        self.tolerance = tolerance
        self.remove_knots = remove_knots

    def reparametrize(self, direction, curve, t_values, target_t_values):
        # Reparametrize given curve so that parameter values from t_values parameter
        # would map to 1.0, 2.0, 3.0...

        # This algorithm is somewhat rude, reparametrization function
        # is not smooth. And this algorithm can produce additional
        # control points.

        segments = []
        for t1, t2, tgt_t1, tgt_t2 in zip(t_values, t_values[1:], target_t_values, target_t_values[1:]):
            segment = curve.cut_segment(t1, t2)
            if segment is not None:
                segment = segment.reparametrize(0.0, tgt_t2 - tgt_t1)
                segments.append(segment)
        
        result = segments[0]
        for segment in segments[1:]:
            if segment is not None:
                result = result.concatenate(segment, remove_knots=False)
        
        if self.remove_knots:
            return remove_excessive_knots(result, tolerance = self.tolerance)
        else:
            return result

class MonotoneReparametrizer(Reparametrizer):
    def __init__(self, n_samples_u = 50, n_samples_v = 50, remove_knots = False, tolerance = 1e-6, logger = None):
        self.n_samples_u = n_samples_u
        self.n_samples_v = n_samples_v
        self.remove_knots = remove_knots
        self.tolerance = tolerance
        self.logger = logger

    def reparametrize(self, direction, curve, t_values, target_t_values):
        if direction == SvNurbsSurface.U:
            n_samples = self.n_samples_u
        else:
            n_samples = self.n_samples_v
        #print(f"Reparametrize: {t_values} => {target_t_values}")
        segment_deltas = t_values[1:] - t_values[:-1]
        t_counts = distribute_int(n_samples - 1, segment_deltas)
        ts = []
        for t1, t2, cnt in zip(t_values[:-1], t_values[1:], t_counts):
            local_ts = np.linspace(t1, t2, num=cnt, endpoint=False)
            ts.extend(local_ts)
        ts.append(t_values[-1])
        ts = np.array(ts)
        #spline = SvMonotoneSpline(target_t_values, t_values)
        spline = SvMonotoneSpline(t_values, target_t_values)
        target_ts = spline.evaluate_array(ts)[:,1]
        #print(f"R: {ts} => {target_ts}")
        curve_pts = curve.evaluate_array(ts)
        new_curve = interpolate_nurbs_curve(curve.get_degree(), curve_pts,
                                            tknots = target_ts, logger = self.logger)
        if self.remove_knots:
            return remove_excessive_knots(new_curve, tolerance = self.tolerance)
        else:
            return new_curve

class GordonUnificationException(ArgumentError):
    """Raised when we cannot unify curves provided to Gordon algorithm."""
    __description__ = "Gordon algorithm: NURBS unification exception"
    pass

def gordon_surface(u_curves, v_curves, intersections,
        metric='POINTS',
        u_knots=None, v_knots=None,
        knots_unification_method = 'UNIFY',
        knotvector_accuracy=6,
        reparametrizer = None,
        implementation = SvNurbsSurface.NATIVE,
        logger=None):
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
        raise ArgumentError("U or V curves are not provided")

    if (u_knots is None) != (v_knots is None):
        raise ArgumentError("u_knots and v_knots must be either both provided or both omitted")

    if any(c.is_rational() for c in u_curves):
        raise SvInvalidInputException("Some of U-curves are rational. Rational curves are not supported for Gordon surface.")
    if any(c.is_rational() for c in v_curves):
        raise SvInvalidInputException("Some of V-curves are rational. Rational curves are not supported for Gordon surface.")

    if logger is None:
        logger = get_logger()

    if reparametrizer is None:
        reparametrizer = SegmentsReparametrizer(tolerance = 1e-6)

    intersections = np.array(intersections)

    if u_knots is not None:
        avg_u_knots = np.mean(u_knots, axis=0)
        avg_v_knots = np.mean(v_knots, axis=0)
        #loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': 'POINTS'}
        loft_u_kwargs = {'tknots': avg_u_knots}
        loft_v_kwargs = {'tknots': avg_v_knots}
        interpolate_kwargs = {'uknots': avg_v_knots, 'vknots': avg_u_knots}

        u_curves = [reparametrizer.reparametrize(SvNurbsSurface.U, c, knots, avg_u_knots) for c, knots in zip(u_curves, u_knots)]
        v_curves = [reparametrizer.reparametrize(SvNurbsSurface.V, c, knots, avg_v_knots) for c, knots in zip(v_curves, v_knots)]
        #print("U", u_curves)
        #print("V", v_curves)

    else:
        loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': metric}
    interpolate_kwargs['logger'] = logger

    u_curves = unify_curves_degree(u_curves)
    try:
        u_curves = unify_curves(u_curves, accuracy=knotvector_accuracy, method=knots_unification_method)
    except CurvesUnificationException as e:
        if u_knots is not None:
            explain = " (after reparametrization)"
        else:
            explain = ""
        raise GordonUnificationException(f"Cannot unify U curves{explain}: {e}") from e
    v_curves = unify_curves_degree(v_curves)
    try:
        v_curves = unify_curves(v_curves, accuracy=knotvector_accuracy, method=knots_unification_method)
    except CurvesUnificationException as e:
        if u_knots is not None:
            explain = " (after reparametrization)"
        else:
            explain = ""
        raise GordonUnificationException(f"Cannot unify V curves{explain}: {e}") from e

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

    surface = SvNurbsSurface.build(implementation,
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

def nurbs_birail_by_gordon(path1, path2, profiles,
        ts1 = None, ts2 = None,
        length_resolution = None,
        min_profiles = 2,
        degree_v = None,
        metric = 'POINTS',
        scale_uniform = True,
        auto_rotate = False,
        use_tangents = 'PATHS_AVG',
        y_axis = None,
        knots_unification_method = 'UNIFY',
        knotvector_accuracy = 6,
        reparametrizer = None,
        implementation = SvNurbsSurface.NATIVE,
        logger = None):

    placed_ts1, placed_ts2, u_curves = prepare_nurbs_birail(path1, path2, profiles,
                ts1 = ts1, ts2 = ts2,
                length_resolution = length_resolution,
                min_profiles = min_profiles,
                degree_v = degree_v,
                scale_uniform = scale_uniform,
                auto_rotate = auto_rotate,
                use_tangents = use_tangents,
                y_axis = y_axis,
                knotvector_accuracy = knotvector_accuracy)
    v_curves = [path1, path2]
    intersections = np.array([u_curve.get_end_points() for u_curve in u_curves])
    intersections = np.transpose(intersections, axes=(1,0,2))
    if length_resolution is not None:
        u_knots = np.array([u_curve.get_u_bounds() for u_curve in u_curves])
        v_knots = np.array([placed_ts1, placed_ts2])
    else:
        u_knots = None
        v_knots = None
    surface = gordon_surface(
        u_curves,
        v_curves,
        intersections = intersections,
        u_knots = u_knots,
        v_knots = v_knots,
        metric=metric,
        implementation=implementation,
        logger=logger,
        knots_unification_method=knots_unification_method,
        knotvector_accuracy=knotvector_accuracy,
        reparametrizer = reparametrizer
    )[-1]
    return u_curves, v_curves, surface

