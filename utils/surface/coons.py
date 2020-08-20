# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve.core import UnsupportedCurveTypeException
from sverchok.utils.curve.nurbs import SvNurbsCurve, unify_two_curves
from sverchok.utils.surface.core import SvSurface

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

    knotvectors = [c.get_knotvector() for c in nurbs_curves]
    if knotvectors[0] != knotvectors[2]:
        nurbs_curves[0], nurbs_curves[2] = unify_two_curves(nurbs_curves[0], nurbs_curves[2])
    if knotvectors[1] != knotvectors[3]:
        nurbs_curves[1], nurbs_curves[3] = unify_two_curves(nurbs_curves[1], nurbs_curves[3])

    knotvector_u = nurbs_curves[0].get_knotvector()
    knotvector_v = nurbs_curves[1].get_knotvector()

    ruled1 = nurbs_curves[0].make_ruled_surface(nurbs_curves[2], 0, 1)
    ruled2 = nurbs_curves[1].make_ruled_surface(nurbs_curves[3], 0, 1)




