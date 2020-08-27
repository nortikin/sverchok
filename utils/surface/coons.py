# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.core import UnsupportedCurveTypeException
from sverchok.utils.curve.nurbs import SvNurbsCurve, unify_two_curves
from sverchok.utils.curve.algorithms import reverse_curve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface

class SvCoonsSurface(SvSurface):
    __description__ = "Coons Patch"
    def __init__(self, curve1, curve2, curve3, curve4):
        self.curve1 = curve1
        self.curve2 = curve2
        self.curve3 = curve3
        self.curve4 = curve4
        self.linear1 = SvCurveLerpSurface(curve1, SvFlipCurve(curve3))
        self.linear2 = SvCurveLerpSurface(curve2, SvFlipCurve(curve4))
        self.c1_t_min, self.c1_t_max = curve1.get_u_bounds()
        self.c3_t_min, self.c3_t_max = curve3.get_u_bounds()

        self.corner1 = self.curve1.evaluate(self.c1_t_min)
        self.corner2 = self.curve1.evaluate(self.c1_t_max)
        self.corner3 = self.curve3.evaluate(self.c3_t_max)
        self.corner4 = self.curve3.evaluate(self.c3_t_min)

        self.normal_delta = 0.001
    
    def get_u_min(self):
        return 0
    
    def get_u_max(self):
        return 1
    
    def get_v_min(self):
        return 0
    
    def get_v_max(self):
        return 1

    def _calc_b(self, u, v, is_array):
        corner1, corner2, corner3, corner4 = self.corner1, self.corner2, self.corner3, self.corner4
        if is_array:
            u = u[np.newaxis].T
            v = v[np.newaxis].T
        b = (corner1 * (1 - u) * (1 - v) + corner2 * u * (1 - v) + corner3 * (1 - u) * v + corner4 * u * v)
        return b
    
    def evaluate(self, u, v):    
        return self.linear1.evaluate(u, v) + self.linear2.evaluate(v, 1-u) - self._calc_b(u, v, False)
    
    def evaluate_array(self, us, vs):
        return self.linear1.evaluate_array(us, vs) + self.linear2.evaluate_array(vs, 1-us) - self._calc_b(us, vs, True)

def coons_surface(curve1, curve2, curve3, curve4):
    curves = [curve1, curve2, curve3, curve4]
    nurbs_curves = [SvNurbsCurve.to_nurbs(c) for c in curves]
    if any(c is None for c in nurbs_curves):
        return SvCoonsSurface(*curves)
    degrees = [c.get_degree() for c in nurbs_curves]
    implementation = nurbs_curves[0].get_nurbs_implementation()

    try:
        if degrees[0] > degrees[2]:
            nurbs_curves[2] = nurbs_curves[2].elevate_degree(delta = degrees[0] - degrees[2])
        if degrees[2] > degrees[0]:
            nurbs_curves[0] = nurbs_curves[0].elevate_degree(delta = degrees[2] - degrees[0])
        if degrees[1] > degrees[3]:
            nurbs_curves[3] = nurbs_curves[3].elevate_degree(delta = degrees[1] - degrees[3])
        if degrees[3] > degrees[1]:
            nurbs_curves[1] = nurbs_curves[1].elevate_degree(delta = degrees[3] - degrees[1])
    except UnsupportedCurveTypeException:
        return SvCoonsSurface(*curves)

    degree_u = nurbs_curves[0].get_degree()
    degree_v = nurbs_curves[1].get_degree()
    #print(f"Target degrees UxV: {degree_u} x {degree_v}")

    knotvectors = [c.get_knotvector() for c in nurbs_curves]
    if not sv_knotvector.equal(knotvectors[0], knotvectors[2]):
        nurbs_curves[0], nurbs_curves[2] = unify_two_curves(nurbs_curves[0], nurbs_curves[2])
    if not sv_knotvector.equal(knotvectors[1], knotvectors[3]):
        nurbs_curves[1], nurbs_curves[3] = unify_two_curves(nurbs_curves[1], nurbs_curves[3])

    #nurbs_curves[2] = reverse_curve(nurbs_curves[2])
    nurbs_curves[0] = reverse_curve(nurbs_curves[0])
    nurbs_curves[3] = reverse_curve(nurbs_curves[3])
    #nurbs_curves[1] = reverse_curve(nurbs_curves[1])

    ruled1 = nurbs_curves[0].make_ruled_surface(nurbs_curves[2], 0, 1)
    #ruled1 = nurbs_curves[2].make_ruled_surface(nurbs_curves[0], 0, 1)
    ruled2 = nurbs_curves[1].make_ruled_surface(nurbs_curves[3], 0, 1).swap_uv()
    #ruled2 = nurbs_curves[3].make_ruled_surface(nurbs_curves[1], 0, 1).swap_uv()
    ruled1 = ruled1.elevate_degree(SvNurbsSurface.V, target=degree_v)
    ruled2 = ruled2.elevate_degree(SvNurbsSurface.U, target=degree_u)

    #print(f"Src: Ruled1 CP: {ruled1.get_control_points().shape}; Ruled2 CP: {ruled2.get_control_points().shape}")

    diff_1to2 = sv_knotvector.difference(ruled1.get_knotvector_v(), ruled2.get_knotvector_v())
    diff_2to1 = sv_knotvector.difference(ruled2.get_knotvector_u(), ruled1.get_knotvector_u())

    for v, count in diff_1to2:
        ruled1 = ruled1.insert_knot(SvNurbsSurface.V, v, count)
    for u, count in diff_2to1:
        ruled2 = ruled2.insert_knot(SvNurbsSurface.U, u, count)

    #print(f"Ruled1 CP: {ruled1.get_control_points().shape}; Ruled2 CP: {ruled2.get_control_points().shape}")

    linear_kv = sv_knotvector.generate(1, 2)

    c1_t_min, c1_t_max = nurbs_curves[0].get_u_bounds()
    c3_t_min, c3_t_max = nurbs_curves[2].get_u_bounds()
    c2_t_min, c2_t_max = nurbs_curves[1].get_u_bounds()
    c4_t_min, c4_t_max = nurbs_curves[3].get_u_bounds()

    pt1 = nurbs_curves[0].evaluate(c1_t_min)
    pt2 = nurbs_curves[0].evaluate(c1_t_max)
    pt3 = nurbs_curves[2].evaluate(c3_t_min)
    pt4 = nurbs_curves[2].evaluate(c3_t_max)

    #linear_pts = np.array([[pt2,pt4], [pt1,pt3]])
    #linear_pts = np.array([[pt4,pt2], [pt3,pt1]])
    linear_pts = np.array([[pt1,pt3], [pt2,pt4]])
    linear_weights = np.array([[1,1], [1,1]])
    bilinear = SvNurbsSurface.build(implementation,
                1, 1,
                linear_kv, linear_kv,
                linear_pts, linear_weights)

    bilinear = bilinear.elevate_degree(SvNurbsSurface.U, target=degree_u)
    bilinear = bilinear.elevate_degree(SvNurbsSurface.V, target=degree_v)

    knotvector_u = ruled1.get_knotvector_u()
    knotvector_v = ruled2.get_knotvector_v()
    for u in sv_knotvector.get_internal_knots(knotvector_u):
        #print(f"Insert U = {u}")
        bilinear = bilinear.insert_knot(SvNurbsSurface.U, u)
    for v in sv_knotvector.get_internal_knots(knotvector_v):
        #print(f"Insert V = {v}")
        bilinear = bilinear.insert_knot(SvNurbsSurface.V, v)

    #print(f"Bilinear CP: {bilinear.get_control_points().shape}")

    control_points = ruled1.get_control_points() + ruled2.get_control_points() - bilinear.get_control_points()
    weights = ruled1.get_weights() + ruled2.get_weights() - bilinear.get_weights()
    result = SvNurbsSurface.build(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)
    return ruled1, ruled2, bilinear, result

