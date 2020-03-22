
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.curve import SvExCurve, SvExCurveLerpCurve

class SvExCurveLerpCurveNode(bpy.types.Node, SverchCustomTreeNode):
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
        self.inputs.new('SvExCurveSocket', "Curve1").display_shape = 'DIAMOND'
        self.inputs.new('SvExCurveSocket', "Curve2").display_shape = 'DIAMOND'
        self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
        self.outputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve1_s = self.inputs['Curve1'].sv_get()
        curve2_s = self.inputs['Curve2'].sv_get()
        coeff_s = self.inputs['Coefficient'].sv_get()

        if isinstance(curve1_s[0], SvExCurve):
            curve1_s = [curve1_s]
        if isinstance(curve2_s[0], SvExCurve):
            curve2_s = [curve2_s]
        coeff_s = ensure_nesting_level(coeff_s, 2)

        curves_out = []
        for curve1s, curve2s, coeffs in zip_long_repeat(curve1_s, curve2_s, coeff_s):
            for curve1, curve2, coeff in zip_long_repeat(curve1s, curve2s, coeffs):
                curve = SvExCurveLerpCurve(curve1, curve2, coeff)
                curves_out.append(curve)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvExCurveLerpCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExCurveLerpCurveNode)

