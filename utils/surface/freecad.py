# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from sverchok.utils.surface.core import SvSurface

class SvSolidFaceSurface(SvSurface):
    __description__ = "Solid Face"
    def __init__(self, solid_face):
        self.face = solid_face
        self.surface = solid_face.Surface
        self.u_bounds = solid_face.ParameterRange[:2]
        self.v_bounds = solid_face.ParameterRange[2:]
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
        return np.array(self.surface.value(u, v))

    def evaluate_array(self, us, vs):
        v_out = []
        for u, v in zip(us, vs):
            v_out.append(self.surface.value(u, v))
        return np.array(v_out)

    def gauss_curvature_array(self, us, vs):
        v_out = []
        for u, v in zip(us, vs):
            v_out.append(self.surface.curvature(u, v, "Gauss"))
        return np.array(v_out)
    def mean_curvature_array(self, us, vs):
        v_out = []
        for u,v in zip(us, vs):
            v_out.append(self.surface.curvature(u, v, "Mean"))
        return np.array(v_out)

    def normal(self, u, v):
        return np.array(self.surface.normal(u, v))

    def normal_array(self, us, vs):
        v_out = []
        for u,v in zip(us, vs):
            v_out.append(self.surface.normal(u, v))
        return np.array(v_out)
