
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvExCurve, SvExFlipCurve

class SvExFlipCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Flip Curve
        Tooltip: Reverse parameterization of the curve - swap the beginning and the end of the curve
        """
        bl_idname = 'SvExFlipCurveNode'
        bl_label = 'Flip Curve'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_FLIP_CURVE'

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'
            self.outputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            if isinstance(curve_s[0], SvExCurve):
                out_level = 1
                curve_s = [curve_s]
            else:
                out_level = 2

            curves_out = []
            for curves in curve_s:
                new_curves = []
                for curve in curves:
                    new_curve = SvExFlipCurve(curve)
                    new_curves.append(new_curve)
                if out_level == 1:
                    curves_out.extend(new_curves)
                else:
                    curves_out.append(new_curve)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvExFlipCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExFlipCurveNode)

