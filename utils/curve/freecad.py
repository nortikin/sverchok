# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve

class SvSolidEdgeCurve(SvCurve):
    __description__ = "Solid Edge"
    def __init__(self, solid_edge):
        self.edge = solid_edge
        self.curve = solid_edge.Curve
        self.u_bounds = (self.edge.FirstParameter, self.edge.LastParameter)

    def evaluate(self, t):
        return np.array(self.curve.value(t))

    def evaluate_array(self, ts):
        t_out = []
        for t in ts:
            t_out.append(self.curve.value(t))
        return np.array(t_out)

    def tangent(self, t):
        return np.array(self.edge.tangentAt(t))

    def tangent_array(self, ts):
        tangents = []
        for t in ts:
            tangents.append(self.edge.tangentAt(t))
        return np.array(tangents)

    def get_u_bounds(self):
        return self.u_bounds

    def to_nurbs(self, implementation = SvNurbsCurve.NATIVE):
        curve = self.curve.toBSpline(*self.u_bounds)
        curve.transform(self.edge.Matrix)
        control_points = curve.getPoles()
        #print(control_points)
        curve = SvNurbsCurve.build(implementation,
                    curve.Degree, curve.KnotSequence,
                    control_points,
                    curve.getWeights())
        #curve.u_bounds = self.u_bounds
        return curve

