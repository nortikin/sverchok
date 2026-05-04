# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.nurbs_common import (
    SvNurbsMaths
)
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.bezier import SvBezierCurve, SvCubicBezierCurve
from sverchok.utils.curve.primitives import SvLine
from sverchok.utils.curve.biarc import SvBiArc

class BlendCurveSmoothness:
    C0 = '0'
    C1 = '1'
    C1_BIARC = '1b'
    C2_BEZIER = '2'
    C3_BEZIER = '3'
    G2_BEZIER = 'G2'
    C2_NURBS = '2n'
    G2_NURBS = 'G2n'

class AbstractBlendCurveDataProvider:
    def evaluate(self):
        raise NotImplementedError()

    def tangent(self):
        raise NotImplementedError()

    def second_derivative(self):
        raise NotImplementedError()

    def third_derivative(self):
        raise NotImplementedError()

    def curvature(self):
        raise NotImplementedError()

    def unit_normal(self):
        raise NotImplementedError()

class BlendCurveDataProvider(AbstractBlendCurveDataProvider):
    def __init__(self, curve, t):
        self.curve = curve
        self.t = t

    def evaluate(self):
        return self.curve.evaluate(self.t)
    
    def tangent(self):
        return self.curve.tangent(self.t)
    
    def second_derivative(self):
        return self.curve.second_derivative(self.t)
    
    def third_derivative(self):
        return self.curve.third_derivative_array(np.array([self.t]))[0]
    
    def curvature(self):
        return self.curve.curvature(self.t)
    
    def unit_normal(self):
        return self.curve.main_normal(self.t)

def blend_curves_impl(data1, data2, smoothness = BlendCurveSmoothness.C0,
                 factor1 = 1.0, factor2 = 1.0,
                 parameter = 1.0, planar_tolerance=1e-6):
    curve1_end = data1.evaluate()
    curve2_begin = data2.evaluate()

    if smoothness == BlendCurveSmoothness.C0:
        new_curve = SvLine.from_two_points(curve1_end, curve2_begin)
        controls = [curve1_end, curve2_begin]
    elif smoothness == BlendCurveSmoothness.C1:
        tangent_1_end = data1.tangent()
        tangent_2_begin = data2.tangent()

        tangent1 = factor1 * tangent_1_end
        tangent2 = factor2 * tangent_2_begin

        new_curve = SvCubicBezierCurve(
                curve1_end,
                curve1_end + tangent1 / 3.0,
                curve2_begin - tangent2 / 3.0,
                curve2_begin
            )
        controls = [new_curve.p0.tolist(), new_curve.p1.tolist(),
                        new_curve.p2.tolist(), new_curve.p3.tolist()]
    elif smoothness == BlendCurveSmoothness.C1_BIARC:
        tangent_1_end = data1.tangent()
        tangent_2_begin = data2.tangent()

        new_curve = SvBiArc.calc(
                curve1_end, curve2_begin,
                tangent_1_end, tangent_2_begin,
                parameter,
                planar_tolerance = planar_tolerance)
        
        controls = [new_curve.junction.tolist()]
    elif smoothness == BlendCurveSmoothness.C2_BEZIER:
        tangent_1_end = data1.tangent()
        tangent_2_begin = data2.tangent()
        second_1_end = data1.second_derivative()
        second_2_begin = data2.second_derivative()

        new_curve = SvBezierCurve.blend_second_derivatives(
                        curve1_end, tangent_1_end, second_1_end,
                        curve2_begin, tangent_2_begin, second_2_begin)
        controls = [p.tolist() for p in new_curve.points]
    elif smoothness == BlendCurveSmoothness.C3_BEZIER:
        tangent_1_end = data1.tangent()
        tangent_2_begin = data2.tangent()
        second_1_end = data1.second_derivative()
        second_2_begin = data2.second_derivative()
        third_1_end = data1.third_derivative()
        third_2_begin = data2.third_derivative()

        new_curve = SvBezierCurve.blend_third_derivatives(
                        curve1_end, tangent_1_end, second_1_end, third_1_end,
                        curve2_begin, tangent_2_begin, second_2_begin, third_2_begin)
        controls = [p.tolist() for p in new_curve.points]
    elif smoothness == BlendCurveSmoothness.G2_BEZIER:
        tangent_1_end = data1.tangent()
        tangent_2_begin = data2.tangent()
        tangent1 = factor1 * tangent_1_end
        tangent2 = factor2 * tangent_2_begin
        normal_1_end = data1.unit_normal()
        normal_2_begin = data2.unit_normal()
        curvature_1_end = data1.curvature()
        curvature_2_begin = data2.curvature()
        
        #print(f"Bz: P1 {curve1_end}, P2 {curve2_begin}, T1 {tangent1}, T2 {tangent2}, n1 {normal_1_end}, n2 {normal_2_begin}, c1 {curvature_1_end}, c2 {curvature_2_begin}")
        new_curve = SvBezierCurve.from_tangents_normals_curvatures(
                        curve1_end, curve2_begin,
                        tangent1, tangent2,
                        normal_1_end, normal_2_begin,
                        curvature_1_end, curvature_2_begin)
        controls = new_curve.get_control_points().tolist()
    elif smoothness == BlendCurveSmoothness.C2_NURBS:
        tangent_1_end = data1.tangent()
        tangent_2_begin = data2.tangent()
        tangent1 = factor1 * tangent_1_end
        tangent2 = factor2 * tangent_2_begin
        second_1_end = data1.second_derivative()
        second_2_begin = data2.second_derivative()

        pt2 = curve1_end + tangent_1_end / 9.0
        pt5 = curve2_begin - tangent_2_begin / 9.0

        pt3 = curve1_end + tangent_1_end / 3.0 + second_1_end / 27.0
        pt4 = curve2_begin - tangent_2_begin / 3.0 + second_2_begin / 27.0

        new_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                            degree = 3,
                            knotvector = sv_knotvector.generate(3, 6),
                            control_points = [
                                   curve1_end, pt2, pt3,
                                   pt4, pt5, curve2_begin
                                ]
                            )
        controls = new_curve.get_control_points().tolist()
    elif smoothness == BlendCurveSmoothness.G2_NURBS:
        tangent_1_end = data1.tangent()
        tangent_2_begin = data2.tangent()
        tangent1 = factor1 * tangent_1_end
        tangent2 = factor2 * tangent_2_begin
        normal_1_end = data1.unit_normal()
        normal_2_begin = data2.unit_normal()
        curvature_1_end = data1.curvature()
        curvature_2_begin = data2.curvature()

        pt2 = curve1_end + tangent_1_end / 9.0
        pt5 = curve2_begin - tangent_2_begin / 9.0

        d1 = curvature_1_end * (tangent_1_end * tangent_1_end).sum() / 27.0
        d2 = curvature_2_begin * (tangent_2_begin * tangent_2_begin).sum() / 27.0

        pt3 = curve1_end + 2 * tangent_1_end / 9.0 + d1 * normal_1_end
        pt4 = curve2_begin - 2 * tangent_2_begin / 9.0 + d2 * normal_2_begin

        new_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                            degree = 3,
                            knotvector = sv_knotvector.generate(3, 6),
                            control_points = [
                                   curve1_end, pt2, pt3,
                                   pt4, pt5, curve2_begin
                                ]
                            )
        controls = new_curve.get_control_points().tolist()

    return new_curve, controls

def blend_curves(curve1, curve2, smoothness = BlendCurveSmoothness.C0,
                 factor1 = 1.0, factor2 = 1.0,
                 parameter = 1.0, planar_tolerance=1e-6):
    data1 = BlendCurveDataProvider(curve1, curve1.get_u_bounds()[1])
    data2 = BlendCurveDataProvider(curve2, curve2.get_u_bounds()[0])
    return blend_curves_impl(data1, data2,
                             smoothness = smoothness,
                             factor1 = factor1, factor2 = factor2,
                             parameter = parameter, planar_tolerance = planar_tolerance)

