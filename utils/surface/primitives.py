# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from sverchok.utils.logging import info, exception
from sverchok.utils.surface.core import SvSurface

class SvPlane(SvSurface):
    __description__ = "Plane"
    
    def __init__(self, point, vector1, vector2):
        self.point = point
        self.vector1 = vector1
        self.vector2 = vector2
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

