
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.algorithms import reverse_curve

class SvFlipCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Flip Curve
        Tooltip: Reverse parameterization of the curve - swap the beginning and the end of the curve
        """
        bl_idname = 'SvExFlipCurveNode'
        bl_label = 'Flip Curve'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_FLIP_CURVE'

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.outputs.new('SvCurveSocket', "Curve")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            if isinstance(curve_s[0], SvCurve):
                out_level = 1
                curve_s = [curve_s]
            else:
                out_level = 2

            curves_out = []
            for curves in curve_s:
                new_curves = []
                for curve in curves:
                    new_curve = reverse_curve(curve)
                    new_curves.append(new_curve)
                if out_level == 1:
                    curves_out.extend(new_curves)
                else:
                    curves_out.append(new_curves)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvFlipCurveNode)

def unregister():
    bpy.utils.unregister_class(SvFlipCurveNode)

