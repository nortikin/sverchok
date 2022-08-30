import numpy as np
from collections import defaultdict

from sverchok.utils.geom import Spline
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions,
        nurbs_divide, from_homogenous
    )
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs_algorithms import interpolate_nurbs_curve, unify_curves, nurbs_curve_to_xoy, nurbs_curve_matrix
from sverchok.utils.curve.algorithms import unify_curves_degree, SvCurveFrameCalculator
from sverchok.utils.surface.core import UnsupportedSurfaceTypeException
from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.utils.surface.nurbs import SvNurbsSurface, simple_loft, interpolate_nurbs_surface
from sverchok.utils.surface.algorithms import unify_nurbs_surfaces
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

def gordon_surface(u_curves, v_curves, intersections, metric='POINTS', u_knots=None, v_knots=None, knotvector_accuracy=6, reparametrize_tolerance=1e-2):
    """
    Generate a NURBS surface from a net of NURBS curves, by use of Gordon's algorithm.

    :param u_curves - list of NURBS curves along U direciton (length N)
    :param v_curves - list of NURBS curves along V direcion (length M)
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

    intersections = np.array(intersections)

    if u_knots is not None:
        loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': 'POINTS'}

        u_curves = [reparametrize_by_segments(c, knots, reparametrize_tolerance) for c, knots in zip(u_curves, u_knots)]
        v_curves = [reparametrize_by_segments(c, knots, reparametrize_tolerance) for c, knots in zip(v_curves, v_knots)]
        #print("U", u_curves)
        #print("V", v_curves)

    else:
        loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': metric}

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

