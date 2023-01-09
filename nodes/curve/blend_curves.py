
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, zip_long_repeat, ensure_nesting_level,
                                     repeat_last_for_length)
from sverchok.utils.curve import SvCurve, SvCubicBezierCurve, SvBezierCurve, SvLine
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.biarc import SvBiArc

class SvBlendCurvesMk2Node(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Blend curves
    Tooltip: Blend two or more curves by use of Bezier curve segment
    """
    bl_idname = 'SvExBlendCurvesMk2Node'
    bl_label = 'Blend Curves'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_BLEND_CURVE'

    factor1 : FloatProperty(
        name = "Factor 1",
        description = "Bulge factor for the first curve",
        default = 1.0,
        update = updateNode)

    factor2 : FloatProperty(
        name = "Factor 2",
        description = "Bulge factor for the second curve",
        default = 1.0,
        update = updateNode)

    parameter : FloatProperty(
        name = "Parameter",
        description = "P parameter for the family of biarcs",
        default = 1.0,
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['Curve1'].hide_safe = self.mode != 'TWO'
        self.inputs['Curve2'].hide_safe = self.mode != 'TWO'
        self.inputs['Curves'].hide_safe = self.mode != 'N'
        self.inputs['Factor1'].hide_safe = self.smooth_mode not in ['1', 'G2']
        self.inputs['Factor2'].hide_safe = self.smooth_mode not in ['1', 'G2']
        self.inputs['Parameter'].hide_safe = self.smooth_mode != '1b'
        updateNode(self, context)

    modes = [
        ('TWO', "Two curves", "Blend two curves", 0),
        ('N', "List of curves", "Blend several curves", 1)
    ]

    mode : EnumProperty(
        name = "Blend",
        items = modes,
        default = 'TWO',
        update = update_sockets)

    smooth_modes = [
            ('0', "C0 - Position", "Connect ends of curves with straight line segment", 0),
            ('1', "G1 - Tangency", "Connect curves such that their tangents are continuosly joined", 1),
            ('1b', "G1 - Bi Arc", "Connect curves with Bi Arc, such that tangents are continuosly joined", 2),
            ('2', "C2 - Smooth Normals", "Connect curves such that their second derivatives are continuosly joined", 3),
            ('3', "C3 - Smooth Curvature", "Connect curves such that their third derivatives are continuosly joined", 4),
            ('G2', "G2 - Curvature", "Connect curves such that their tangents, normals and curvatures are continuosly joined", 5)
        ]

    smooth_mode : EnumProperty(
        name = "Continuity",
        description = "How smooth should be the blending; bigger value give more smooth curves",
        items = smooth_modes,
        default = '1',
        update = update_sockets)

    cyclic : BoolProperty(
        name = "Cyclic",
        default = False,
        update = updateNode)

    output_src : BoolProperty(
        name = "Output source curves",
        default = True,
        update = updateNode)

    join : BoolProperty(
            name = "Join",
            description = "Output single flat list of curves",
            default = True,
            update = updateNode)

    concat : BoolProperty(
        name = "Concatenate",
        description = "Concatenate source curves and blending curves into one curve",
        default = True,
        update = updateNode)

    planar_tolerance : FloatProperty(
            name = "Planar Tolerance",
            description = "Tolerance value for checking if the curve is planar",
            default = 1e-6,
            precision = 8,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Continuity:")
        layout.prop(self, 'smooth_mode', text='')
        layout.prop(self, "mode", text='')
        layout.prop(self, 'join')
        layout.prop(self, 'concat')
        if self.mode == 'N':
            layout.prop(self, 'cyclic')
            if not self.concat:
                layout.prop(self, 'output_src')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'planar_tolerance')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', 'Curve1')
        self.inputs.new('SvCurveSocket', 'Curve2')
        self.inputs.new('SvCurveSocket', 'Curves')
        self.inputs.new('SvStringsSocket', "Factor1").prop_name = 'factor1'
        self.inputs.new('SvStringsSocket', "Factor2").prop_name = 'factor2'
        self.inputs.new('SvStringsSocket', "Parameter").prop_name = 'parameter'
        self.outputs.new('SvCurveSocket', 'Curve')
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.update_sockets(context)

    def get_inputs(self):
        factor1_s = self.inputs['Factor1'].sv_get()
        factor2_s = self.inputs['Factor2'].sv_get()
        params_s = self.inputs['Parameter'].sv_get()

        factor1_s = ensure_nesting_level(factor1_s, 2)
        factor2_s = ensure_nesting_level(factor2_s, 2)
        params_s = ensure_nesting_level(params_s, 2)

        if self.mode == 'TWO':
            curve1_s = self.inputs['Curve1'].sv_get()
            curve2_s = self.inputs['Curve2'].sv_get()
            curve1_s = ensure_nesting_level(curve1_s, 2, data_types=(SvCurve,))
            curve2_s = ensure_nesting_level(curve2_s, 2, data_types=(SvCurve,))

            results = []
            for inputs in zip_long_repeat(curve1_s, curve2_s, factor1_s, factor2_s, params_s):
                results.append(zip_long_repeat(*inputs))

            return results

        else:
            curves_s = self.inputs['Curves'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

            results = []
            for curves, factor1s, factor2s, params in zip_long_repeat(curves_s, factor1_s, factor2_s, params_s):
                factor1s = repeat_last_for_length(factor1s, len(curves))
                factor2s = repeat_last_for_length(factor2s, len(curves))
                params = repeat_last_for_length(params, len(curves))

                item = list(zip(curves, curves[1:], factor1s, factor2s, params))
                if self.cyclic:
                    item.append((curves[-1], curves[0], factor1s[-1], factor2s[-1], params[-1]))

                results.append(item)

            return results

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        output_src = self.output_src or self.concat

        curves_out = []
        controls_out = []
        is_first = True

        for params in self.get_inputs():
            new_curves = []
            new_controls = []
            for curve1, curve2, factor1, factor2, parameter in params:
                _, t_max_1 = curve1.get_u_bounds()
                t_min_2, _ = curve2.get_u_bounds()

                curve1_end = curve1.evaluate(t_max_1)
                curve2_begin = curve2.evaluate(t_min_2)

                smooth = self.smooth_mode

                if smooth == '0':
                    new_curve = SvLine.from_two_points(curve1_end, curve2_begin)
                    controls = [curve1_end, curve2_begin]
                elif smooth == '1':
                    tangent_1_end = curve1.tangent(t_max_1)
                    tangent_2_begin = curve2.tangent(t_min_2)

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
                elif smooth == '1b':
                    tangent_1_end = curve1.tangent(t_max_1)
                    tangent_2_begin = curve2.tangent(t_min_2)

                    new_curve = SvBiArc.calc(
                            curve1_end, curve2_begin,
                            tangent_1_end, tangent_2_begin,
                            parameter,
                            planar_tolerance = self.planar_tolerance)
                    
                    controls = [new_curve.junction.tolist()]
                elif smooth == '2':
                    tangent_1_end = curve1.tangent(t_max_1)
                    tangent_2_begin = curve2.tangent(t_min_2)
                    second_1_end = curve1.second_derivative(t_max_1)
                    second_2_begin = curve2.second_derivative(t_min_2)

                    new_curve = SvBezierCurve.blend_second_derivatives(
                                    curve1_end, tangent_1_end, second_1_end,
                                    curve2_begin, tangent_2_begin, second_2_begin)
                    controls = [p.tolist() for p in new_curve.points]
                elif smooth == '3':
                    tangent_1_end = curve1.tangent(t_max_1)
                    tangent_2_begin = curve2.tangent(t_min_2)
                    second_1_end = curve1.second_derivative(t_max_1)
                    second_2_begin = curve2.second_derivative(t_min_2)
                    third_1_end = curve1.third_derivative_array(np.array([t_max_1]))[0]
                    third_2_begin = curve2.third_derivative_array(np.array([t_min_2]))[0]

                    new_curve = SvBezierCurve.blend_third_derivatives(
                                    curve1_end, tangent_1_end, second_1_end, third_1_end,
                                    curve2_begin, tangent_2_begin, second_2_begin, third_2_begin)
                    controls = [p.tolist() for p in new_curve.points]
                elif smooth == 'G2':
                    tangent_1_end = curve1.tangent(t_max_1)
                    tangent_2_begin = curve2.tangent(t_min_2)
                    tangent1 = factor1 * tangent_1_end
                    tangent2 = factor2 * tangent_2_begin
                    normal_1_end = curve1.main_normal(t_max_1)
                    normal_2_begin = curve2.main_normal(t_min_2)
                    curvature_1_end = curve1.curvature(t_max_1)
                    curvature_2_begin = curve2.curvature(t_min_2)
                    
                    #print(f"Bz: P1 {curve1_end}, P2 {curve2_begin}, T1 {tangent1}, T2 {tangent2}, n1 {normal_1_end}, n2 {normal_2_begin}, c1 {curvature_1_end}, c2 {curvature_2_begin}")
                    new_curve = SvBezierCurve.from_tangents_normals_curvatures(
                                    curve1_end, curve2_begin,
                                    tangent1, tangent2,
                                    normal_1_end, normal_2_begin,
                                    curvature_1_end, curvature_2_begin)
                    controls = new_curve.get_control_points().tolist()
                else:
                    raise Exception("Unsupported smooth level")

                if self.mode == 'N' and not self.cyclic and output_src and is_first:
                    new_curves.append(curve1)
                new_curves.append(new_curve)
                if self.mode == 'N' and output_src:
                    new_curves.append(curve2)
                new_controls.append(controls)

                is_first = False

                if self.concat:
                    new_curves = [concatenate_curves(new_curves)]

            if self.join:
                curves_out.extend(new_curves)
                controls_out.extend(new_controls)
            else:
                curves_out.append(new_curves)
                controls_out.append(new_controls)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(controls_out)

def register():
    bpy.utils.register_class(SvBlendCurvesMk2Node)

def unregister():
    bpy.utils.unregister_class(SvBlendCurvesMk2Node)

