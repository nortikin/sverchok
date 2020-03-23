
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvExCurve, SvExConcatCurve

class SvExConcatCurvesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Concatenate Curves
        Tooltip: Concatenate several curves into one
        """
        bl_idname = 'SvExConcatCurvesNode'
        bl_label = 'Concat Curves'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_CONCAT_CURVES'

        check : BoolProperty(
            name = "Check coincidence",
            default = False,
            update = updateNode)

        max_rho : FloatProperty(
            name = "Max. distance",
            min = 0.0,
            default = 0.001,
            precision = 4,
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'check')
            if self.check:
                layout.prop(self, 'max_rho')

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', "Curves")
            self.outputs.new('SvExCurveSocket', "Curve")

        def run_check(self, curves):
            for idx, (curve1, curve2) in enumerate(zip(curves, curves[1:])):
                _, t_max_1 = curve1.get_u_bounds()
                t_min_2, _ = curve2.get_u_bounds()
                end1 = curve1.evaluate(t_max_1)
                begin2 = curve2.evaluate(t_min_2)
                distance = np.linalg.norm(begin2 - end1)
                if distance > self.max_rho:
                    raise Exception("Distance between the end of {}'th curve and the start of {}'th curve is {} - too much".format(idx, idx+1, distance))

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curves'].sv_get()
            if isinstance(curve_s[0], SvExCurve):
                curve_s = [curve_s]

            curves_out = []
            for curves in curve_s:
                if self.check:
                    self.run_check(curves)
                new_curve = SvExConcatCurve(curves)
                curves_out.append(new_curve)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvExConcatCurvesNode)

def unregister():
    bpy.utils.unregister_class(SvExConcatCurvesNode)

