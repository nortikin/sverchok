# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from sverchok.utils.logging import info, exception
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve import knotvector as sv_knotvector

class SvPlane(SvSurface):
    __description__ = "Plane"
    
    def __init__(self, point, vector1, vector2):
        self.point = point
        self.vector1 = np.array(vector1)
        self.vector2 = np.array(vector2)
        self._normal = np.cross(vector1, vector2)
        n = np.linalg.norm(self._normal)
        self._normal = self._normal / n
        self.u_bounds = (0.0, 1.0)
        self.v_bounds = (0.0, 1.0)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        return self.point + u*self.vector1 + v*self.vector2

    def evaluate_array(self, us, vs):
        us = us[np.newaxis].T
        vs = vs[np.newaxis].T
        return self.point + us*self.vector1 + vs*self.vector2

    def gauss_curvature_array(self, us, vs):
        return np.zeros_like(us, dtype=np.float64)

    def normal(self, u, v):
        return self._normal

    def normal_array(self, us, vs):
        normal = self._normal[np.newaxis].T
        n = np.linalg.norm(normal)
        normal = normal / n
        return np.tile(normal, len(us)).T

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        u_min, u_max = self.u_bounds
        v_min, v_max = self.v_bounds
        pt1 = self.evaluate(u_min, v_min)
        pt2 = self.evaluate(u_min, v_max)
        pt3 = self.evaluate(u_max, v_min)
        pt4 = self.evaluate(u_max, v_max)

        control_points = np.array([[pt1, pt2], [pt3, pt4]])
        weights = np.array([[1,1], [1, 1]])
        degree_u = degree_v = 1
        knotvector_u = knotvector_v = sv_knotvector.generate(1, 2)

        return SvNurbsMaths.build_surface(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)

