
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.curve import SvCurve, SvCubicBezierCurve

class SvBlendCurvesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Blend curves
    Tooltip: Blend two or more curves by use of Bezier curve segment
    """
    bl_idname = 'SvExBlendCurvesNode'
    bl_label = 'Blend Curves'
    bl_icon = 'CURVE_NCURVE'

    factor1 : FloatProperty(
        name = "Factor 1",
        default = 0.1,
        update = updateNode)

    factor2 : FloatProperty(
        name = "Factor 2",
        default = 0.1,
        update = updateNode)

    modes = [
        ('TWO', "Two curves", "Blend two curves", 0),
        ('N', "List of curves", "Blend several curves", 1)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Curve1'].hide_safe = self.mode != 'TWO'
        self.inputs['Curve2'].hide_safe = self.mode != 'TWO'
        self.inputs['Curves'].hide_safe = self.mode != 'N'

    mode : EnumProperty(
        name = "Blend",
        items = modes,
        default = 'TWO',
        update = update_sockets)

    cyclic : BoolProperty(
        name = "Cyclic",
        default = False,
        update = updateNode)

    output_src : BoolProperty(
        name = "Output source curves",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text='')
        if self.mode == 'N':
            layout.prop(self, 'cyclic', toggle=True)
            layout.prop(self, 'output_src', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', 'Curve1')
        self.inputs.new('SvCurveSocket', 'Curve2')
        self.inputs.new('SvCurveSocket', 'Curves')
        self.inputs.new('SvStringsSocket', "Factor1").prop_name = 'factor1'
        self.inputs.new('SvStringsSocket', "Factor2").prop_name = 'factor2'
        self.outputs.new('SvCurveSocket', 'Curve')
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

        curves_out = []
        is_first = True
        for curve1, curve2, factor1, factor2 in self.get_inputs():
            _, t_max_1 = curve1.get_u_bounds()
            t_min_2, _ = curve2.get_u_bounds()

            curve1_end = curve1.evaluate(t_max_1)
            curve2_begin = curve2.evaluate(t_min_2)
            tangent_1_end = curve1.tangent(t_max_1)
            tangent_2_begin = curve2.tangent(t_min_2)

            tangent1 = factor1 * tangent_1_end / np.linalg.norm(tangent_1_end)
            tangent2 = factor2 * tangent_2_begin / np.linalg.norm(tangent_2_begin)

            new_curve = SvCubicBezierCurve(
                    curve1_end,
                    curve1_end + tangent1,
                    curve2_begin - tangent2,
                    curve2_begin
                )
            if self.mode == 'N' and not self.cyclic and self.output_src and is_first:
                curves_out.append(curve1)
            curves_out.append(new_curve)
            if self.mode == 'N' and self.output_src:
                curves_out.append(curve2)

            is_first = False

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvBlendCurvesNode)

def unregister():
    bpy.utils.unregister_class(SvBlendCurvesNode)

