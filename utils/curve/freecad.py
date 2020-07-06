# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sin, cos, pi, radians, sqrt

from mathutils import Vector, Matrix

from sverchok.utils.geom import PlaneEquation, LineEquation, LinearSpline, CubicSpline, CircleEquation2D, CircleEquation3D, Ellipse3D
from sverchok.utils.integrate import TrapezoidIntegral
from sverchok.utils.logging import error, exception
from sverchok.utils.math import (
        binomial,
        ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL,
        NORMAL_DIR
    )
from sverchok.utils.geom import autorotate_householder, autorotate_track, autorotate_diff
from sverchok.utils.curve.core import SvCurve

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

