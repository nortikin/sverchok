
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.curve import SvCurve, SvCubicBezierCurve, SvBezierCurve, SvLine, SvConcatCurve

class SvBlendCurvesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Blend curves
    Tooltip: Blend two or more curves by use of Bezier curve segment
    """
    bl_idname = 'SvExBlendCurvesNode'
    bl_label = 'Blend Curves'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_BLEND_CURVE'

    factor1 : FloatProperty(
        name = "Factor 1",
        default = 1.0,
        update = updateNode)

    factor2 : FloatProperty(
        name = "Factor 2",
        default = 1.0,
        update = updateNode)

    @throttled
    def update_sockets(self, context):
        self.inputs['Curve1'].hide_safe = self.mode != 'TWO'
        self.inputs['Curve2'].hide_safe = self.mode != 'TWO'
        self.inputs['Curves'].hide_safe = self.mode != 'N'
        self.inputs['Factor1'].hide_safe = self.smooth_mode != '1'
        self.inputs['Factor2'].hide_safe = self.smooth_mode != '1'

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
            ('0', "0 - Position", "Connect ends of curves with straight line segment", 0),
            ('1', "1 - Tangency", "Connect curves such that their tangents are smoothly joined", 1),
            ('2', "2 - Normals", "Connect curves such that their normals (second derivatives) are smoothly joined", 2),
            ('3', "3 - Curvature", "Connect curves such that their curvatures (third derivatives) are smoothly joined", 3)
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

    concat : BoolProperty(
        name = "Concatenate",
        description = "Concatenate source curves and blending curves into one curve",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Continuity:")
        layout.prop(self, 'smooth_mode', text='')
        layout.prop(self, "mode", text='')
        layout.prop(self, 'concat', toggle=True)
        if self.mode == 'N':
            layout.prop(self, 'cyclic', toggle=True)
            if not self.concat:
                layout.prop(self, 'output_src', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', 'Curve1')
        self.inputs.new('SvCurveSocket', 'Curve2')
        self.inputs.new('SvCurveSocket', 'Curves')
        self.inputs.new('SvStringsSocket', "Factor1").prop_name = 'factor1'
        self.inputs.new('SvStringsSocket', "Factor2").prop_name = 'factor2'
        self.outputs.new('SvCurveSocket', 'Curve')
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.update_sockets(context)

    def get_inputs(self):
        factor1_s = self.inputs['Factor1'].sv_get()
        factor2_s = self.inputs['Factor2'].sv_get()

        factor1_s = ensure_nesting_level(factor1_s, 2)
        factor2_s = ensure_nesting_level(factor2_s, 2)

        if self.mode == 'TWO':
            curve1_s = self.inputs['Curve1'].sv_get()
            curve2_s = self.inputs['Curve2'].sv_get()
            if isinstance(curve1_s[0], SvCurve):
                curve1_s = [curve1_s]
            if isinstance(curve2_s[0], SvCurve):
                curve2_s = [curve2_s]
            for curve1s, curve2s, factor1s, factor2s in zip_long_repeat(curve1_s, curve2_s, factor1_s, factor2_s):
                for curve1, curve2, factor1, factor2 in zip_long_repeat(curve1s, curve2s, factor1s, factor2s):
                    yield curve1, curve2, factor1, factor2
        else:
            curves_s = self.inputs['Curves'].sv_get()
            if isinstance(curves_s[0], SvCurve):
                curves_s = [curves_s]
            for curves, factor1s, factor2s in zip_long_repeat(curves_s, factor1_s, factor2_s):
                factor1s = repeat_last_for_length(factor1s, len(curves))
                factor2s = repeat_last_for_length(factor2s, len(curves))
                for curve1, curve2, factor1, factor2 in zip(curves, curves[1:], factor1s, factor2s):
                    yield curve1, curve2, factor1, factor2
                if self.cyclic:
                    yield curves[-1], curves[0], factor1s[-1], factor2s[-1]

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        output_src = self.output_src or self.concat

        curves_out = []
        controls_out = []
        is_first = True
        for curve1, curve2, factor1, factor2 in self.get_inputs():
            _, t_max_1 = curve1.get_u_bounds()
            t_min_2, _ = curve2.get_u_bounds()

            curve1_end = curve1.evaluate(t_max_1)
            curve2_begin = curve2.evaluate(t_min_2)

            smooth = int(self.smooth_mode)

            if smooth == 0:
                new_curve = SvLine.from_two_points(curve1_end, curve2_begin)
                new_controls = [curve1_end, curve2_begin]
            elif smooth == 1:
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
                new_controls = [new_curve.p0.tolist(), new_curve.p1.tolist(),
                                new_curve.p2.tolist(), new_curve.p3.tolist()]
            elif smooth == 2:
                tangent_1_end = curve1.tangent(t_max_1)
                tangent_2_begin = curve2.tangent(t_min_2)
                second_1_end = curve1.second_derivative(t_max_1)
                second_2_begin = curve2.second_derivative(t_min_2)

                new_curve = SvBezierCurve.blend_second_derivatives(
                                curve1_end, tangent_1_end, second_1_end,
                                curve2_begin, tangent_2_begin, second_2_begin)
                new_controls = [p.tolist() for p in new_curve.points]
            elif smooth == 3:
                tangent_1_end = curve1.tangent(t_max_1)
                tangent_2_begin = curve2.tangent(t_min_2)
                second_1_end = curve1.second_derivative(t_max_1)
                second_2_begin = curve2.second_derivative(t_min_2)
                third_1_end = curve1.third_derivative_array(np.array([t_max_1]))[0]
                third_2_begin = curve2.third_derivative_array(np.array([t_min_2]))[0]

                new_curve = SvBezierCurve.blend_third_derivatives(
                                curve1_end, tangent_1_end, second_1_end, third_1_end,
                                curve2_begin, tangent_2_begin, second_2_begin, third_2_begin)
                new_controls = [p.tolist() for p in new_curve.points]
            else:
                raise Exception("Unsupported smooth level")

            if self.mode == 'N' and not self.cyclic and output_src and is_first:
                curves_out.append(curve1)
            curves_out.append(new_curve)
            if self.mode == 'N' and output_src:
                curves_out.append(curve2)
            controls_out.append(new_controls)

            is_first = False

        if self.concat:
            curves_out = [SvConcatCurve(curves_out)]

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(controls_out)

def register():
    bpy.utils.register_class(SvBlendCurvesNode)

def unregister():
    bpy.utils.unregister_class(SvBlendCurvesNode)

