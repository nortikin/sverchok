
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList

from sverchok.utils.curve import SvDeformedByFieldCurve

class SvApplyFieldToCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Apply field to curve
        Tooltip: Apply vector field to curve
        """
        bl_idname = 'SvExApplyFieldToCurveNode'
        bl_label = 'Apply Field to Curve'
        bl_icon = 'CURVE_NCURVE'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_CURVE_VFIELD'

        coefficient : FloatProperty(
                name = "Coefficient",
                default = 1.0,
                update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVectorFieldSocket', "Field")
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
            self.outputs.new('SvCurveSocket', "Curve")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            field_s = self.inputs['Field'].sv_get()
            coeff_s = self.inputs['Coefficient'].sv_get()

            curve_out = []
            for curve, field, coeff in zip_long_repeat(curve_s, field_s, coeff_s):
                if isinstance(coeff, (list, tuple)):
                    coeff = coeff[0]

                new_curve = SvDeformedByFieldCurve(curve, field, coeff)
                curve_out.append(new_curve)

            self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvApplyFieldToCurveNode)

def unregister():
    bpy.utils.unregister_class(SvApplyFieldToCurveNode)

