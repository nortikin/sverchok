# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.primitives import SvLine
from sverchok.utils.curve.bezier import SvBezierCurve, SvCubicBezierCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.algorithms import concatenate_curves, reparametrize_curve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves

class SvSplineCurve(SvCurve):
    __description__ = "Spline"

    def __init__(self, spline):
        self.spline = spline
        self.u_bounds = (0.0, 1.0)

    @classmethod
    def from_points(cls, points, metric=None, is_cyclic=False):
        if not points or len(points) < 2:
            raise Exception("At least two points are required")
        if len(points) < 3:
            return SvLine.from_two_points(points[0], points[1])
        spline = CubicSpline(points, metric=metric, is_cyclic=is_cyclic)
        return SvSplineCurve(spline)

    def evaluate(self, t):
        v = self.spline.eval_at_point(t)
        return np.array(v)

    def evaluate_array(self, ts):
        vs = self.spline.eval(ts)
        return np.array(vs)

    def tangent(self, t):
        vs = self.spline.tangent(np.array([t]))
        return vs[0]

    def tangent_array(self, ts):
        return self.spline.tangent(ts)

    def get_u_bounds(self):
        return self.u_bounds

    def to_nurbs(self, implementation=SvNurbsCurve.NATIVE):
        control_points = self.spline.get_control_points()
        degree = 3 if isinstance(self.spline, CubicSpline) else 1
        n_points = 4 if isinstance(self.spline, CubicSpline) else 2
        knotvector = sv_knotvector.generate(degree, n_points)
        t_segments = self.spline.get_t_segments()
        segments = [SvNurbsCurve.build(implementation,
                        degree, knotvector, points) for points in control_points]
        segments = [reparametrize_curve(segment, t_min, t_max) for segment, (t_min, t_max) in zip(segments, t_segments)]
#         pairs = [f"#{i}: {t_min}-{t_max}: {segment.evaluate(t_min)} -- {segment.evaluate(t_max)}" for i, (segment, (t_min, t_max)) in enumerate(zip(segments, t_segments))]
#         pairs = ", ".join(pairs)
#         print(f"S: {pairs}")
        return concatenate_nurbs_curves(segments)

    def to_bezier_segments(self):
        control_points = self.spline.get_control_points()
        is_cubic = isinstance(self.spline, CubicSpline)
        curve_constructor = lambda cs: SvCubicBezierCurve(*cs) if is_cubic else SvBezierCurve
        segments = [curve_constructor(points) for points in control_points]
        return segments

    def make_revolution_surface(self, point, direction, v_min, v_max, global_origin):
        return self.to_nurbs().make_revolution_surface(point, direction, v_min, v_max, global_origin)

    def extrude_along_vector(self, vector):
        return self.to_nurbs().extrude_along_vector(vector)

    def make_ruled_surface(self, curve2, vmin, vmax):
        return self.to_nurbs().make_ruled_surface(curve2, vmin, vmax)

    def extrude_to_point(self, point):
        return self.to_nurbs().extrude_to_point(point)
    
    def lerp_to(self, curve2, coefficient):
        return self.to_nurbs().lerp_to(curve2, coefficient)

    def split_at(self, t):
        return self.to_nurbs().split_at(t)

    def cut_segment(self, new_t_min, new_t_max, rescale=False):
        return self.to_nurbs().cut_segment(new_t_min, new_t_max, rescale=rescale)

