
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList

from sverchok.utils.curve import SvExDeformedByFieldCurve

class SvExApplyFieldToCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Apply field to curve
        Tooltip: Apply vector field to curve
        """
        bl_idname = 'SvExApplyFieldToCurveNode'
        bl_label = 'Apply Field to Curve'
        bl_icon = 'CURVE_NCURVE'

        coefficient : FloatProperty(
                name = "Coefficient",
                default = 1.0,
                update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvExVectorFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
            self.inputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
            self.outputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'

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

                new_curve = SvExDeformedByFieldCurve(curve, field, coeff)
                curve_out.append(new_curve)

            self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvExApplyFieldToCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExApplyFieldToCurveNode)

