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

def gordon_surface_impl(u_curves, v_curves, intersections, degree_u=None, degree_v=None, metric='DISTANCE'):
    if degree_u is None:
        degree_u = u_curves[0].get_degree()

    if degree_v is None:
        degree_v = v_curves[0].get_degree()

    intersections = np.asarray(intersections)

    n = len(intersections)
    m = len(intersections[0])

    knots = np.array([Spline.create_knots(intersections[i,:], metric=metric) for i in range(n)])
    u_knots = knots.mean(axis=0)

    knots = np.array([Spline.create_knots(intersections[:,j], metric=metric) for j in range(m)])
    v_knots = knots.mean(axis=0)

    _,_,lofted_v = simple_loft(u_curves, degree_v=degree_v, tknots=u_knots)
    _,_,lofted_u = simple_loft(v_curves, degree_v=degree_u, tknots=v_knots)
    lofted_u = lofted_u.swap_uv()

    interpolated = interpolate_nurbs_surface(degree_u, degree_v, intersections, uknots=u_knots, vknots=v_knots)
    interpolated = interpolated.swap_uv()
    print(f"Loft.U: {lofted_u.get_degree_u()}x{lofted_u.get_degree_v()}")
    print(f"Loft.V: {lofted_v.get_degree_u()}x{lofted_v.get_degree_v()}")
    print(f"Interp: {interpolated.get_degree_u()}x{interpolated.get_degree_v()}")

    lofted_u, lofted_v, interpolated = unify_nurbs_surfaces([lofted_u, lofted_v, interpolated])

    control_points = lofted_u.get_control_points() + \
                        lofted_v.get_control_points() - \
                        interpolated.get_control_points()

    surface = SvNurbsSurface.build(SvNurbsSurface.NATIVE,
                interpolated.get_degree_u(), interpolated.get_degree_v(),
                interpolated.get_knotvector_u(), interpolated.get_knotvector_v(),
                control_points, weights=None)

    return lofted_u, lofted_v, interpolated, surface
