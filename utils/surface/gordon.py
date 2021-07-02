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

def reparametrize_by_segments(curve, t_values):
    t_min, t_max = curve.get_u_bounds()
    #print(f"Reparametrize: {t_min} - {t_max}: {t_values}")
    #t_values = [t_min] + t_values + [t_max]

    segments = []
    for t1, t2 in zip(t_values, t_values[1:]):
        segment = curve.cut_segment(t1, t2, rescale=True)
        segments.append(segment)
    
    result = segments[0]
    for segment in segments[1:]:
        result = result.concatenate(segment)
    
    return result

def find_knot_multiplicities(curve, knots, tolerance=None):
    return [(knot, sv_knotvector.find_multiplicity(curve.get_knotvector(), knot)) for knot in knots]

def sum_multiplicities(multiplicities):
    #print(multiplicities)
    result = defaultdict(int)
    for ms in multiplicities:
        for u, count in ms:
            result[u] = max(result[u], count)
    return result.items()

def gordon_surface(u_curves, v_curves, intersections, metric='POINTS', u_knots=None, v_knots=None, knotvector_accuracy=6):

    if (u_knots is None) != (v_knots is None):
        raise Exception("u_knots and v_knots must be either both provided or both omited")

    if any(c.is_rational() for c in u_curves):
        raise Exception("Some of U-curves are rational. Rational curves are not supported for Gordon surface.")
    if any(c.is_rational() for c in v_curves):
        raise Exception("Some of V-curves are rational. Rational curves are not supported for Gordon surface.")

    intersections = np.array(intersections)
    knotvector_tolerance = 10**(-knotvector_accuracy)

    if u_knots is not None:
        loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': 'POINTS'}

        u_curves = [reparametrize_by_segments(c, knots) for c, knots in zip(u_curves, u_knots)]
        v_curves = [reparametrize_by_segments(c, knots) for c, knots in zip(v_curves, v_knots)]
        #print("U", u_curves)
        #print("V", v_curves)

        target_u_knots = np.linspace(0.0, 1.0, num = len(v_curves))
        target_v_knots = np.linspace(0.0, 1.0, num = len(u_curves))

        orig_ints_ms_u = sum_multiplicities([find_knot_multiplicities(c, knots) for c, knots in zip(u_curves, u_knots)])
        orig_ints_ms_v = sum_multiplicities([find_knot_multiplicities(c, knots) for c, knots in zip(v_curves, v_knots)])

    else:
        loft_u_kwargs = loft_v_kwargs = interpolate_kwargs = {'metric': metric}
        orig_ints_ms_u = None
        orig_ints_ms_v = None

    #u_curves = unify_curves_degree(u_curves)
    #u_curves = unify_curves(u_curves, accuracy=knotvector_accuracy)#, method='AVERAGE')
    #v_curves = unify_curves_degree(v_curves)
    #v_curves = unify_curves(v_curves, accuracy=knotvector_accuracy)#, method='AVERAGE')

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

#     if orig_ints_ms_u is not None:
#         print("KV.U", surface.get_knotvector_u())
#         ms_u = dict(sv_knotvector.to_multiplicity(surface.get_knotvector_u()))
#         for (u, orig_count), target_u in zip(orig_ints_ms_u, target_u_knots):
#             current_count = ms_u.get(target_u, 0)
#             diff = current_count - orig_count - 1
#             print(f"R: U = {u} => {target_u}, orig = {orig_count}, now = {current_count}")
#             if diff > 0:
#                 print(f"R: remove U = {target_v} x {diff}")
#                 surface = surface.remove_knot(SvNurbsSurface.U, target_u, diff)
# 
#     if orig_ints_ms_v is not None:
#         print("KV.V", surface.get_knotvector_v())
#         ms_v = dict(sv_knotvector.to_multiplicity(surface.get_knotvector_v()))
#         for (v, orig_count), target_v in zip(orig_ints_ms_v, target_v_knots):
#             current_count = ms_v.get(target_v, 0)
#             diff = current_count - orig_count - 1
#             print(f"R: V = {v} => {target_v}, orig = {orig_count}, now = {current_count}")
#             if diff > 0:
#                 print(f"R: remove V = {target_v} x {diff}")
#                 surface = surface.remove_knot(SvNurbsSurface.V, target_v, diff)

    return lofted_u, lofted_v, interpolated, surface

