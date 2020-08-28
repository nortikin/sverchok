
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve, SvCurveLerpCurve

class SvCurveLerpCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Lerp
    Tooltip: Generate a curve by linear interpolation of two curves
    """
    bl_idname = 'SvExCurveLerpCurveNode'
    bl_label = 'Curve Lerp'
    bl_icon = 'MOD_THICKNESS'

    coefficient : FloatProperty(
            name = "Coefficient",
            default = 0.5,
            update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve1")
        self.inputs.new('SvCurveSocket', "Curve2")
        self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve1_s = self.inputs['Curve1'].sv_get()
        curve2_s = self.inputs['Curve2'].sv_get()
        coeff_s = self.inputs['Coefficient'].sv_get()

        if isinstance(curve1_s[0], SvCurve):
            curve1_s = [curve1_s]
        if isinstance(curve2_s[0], SvCurve):
            curve2_s = [curve2_s]
        coeff_s = ensure_nesting_level(coeff_s, 2)

        curves_out = []
        for curve1s, curve2s, coeffs in zip_long_repeat(curve1_s, curve2_s, coeff_s):
            for curve1, curve2, coeff in zip_long_repeat(curve1s, curve2s, coeffs):
                curve = SvCurveLerpCurve.build(curve1, curve2, coeff)
                curves_out.append(curve)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCurveLerpCurveNode)

def unregister():
    bpy.utils.unregister_class(SvCurveLerpCurveNode)

