
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.curve import SvCurve
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.vector import SvScalarFieldCurveMap

class SvScalarFieldCurveMapNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Curve Map
    Tooltip: Map scalar field by curve
    """
    bl_idname = 'SvScalarFieldCurveMapNode'
    bl_label = 'Scalar Field Curve Map'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VFIELD_IN'

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.inputs.new('SvCurveSocket', 'Curve')
        self.outputs.new('SvVectorFieldSocket', 'Field')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sfields_s = self.inputs['Field'].sv_get()
        sfields_s = ensure_nesting_level(sfields_s, 2, data_types=(SvScalarField,))
        curves_s = self.inputs['Curve'].sv_get()
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

        vfields_out = []
        for sfields, curves in zip_long_repeat(sfields_s, curves_s):
            for sfield, curve in zip_long_repeat(sfields, curves):
                vfield = SvScalarFieldCurveMap(sfield, curve)
                vfields_out.append(vfield)

        self.outputs['Field'].sv_set(vfields_out)

def register():
    bpy.utils.register_class(SvScalarFieldCurveMapNode)

def unregister():
    bpy.utils.unregister_class(SvScalarFieldCurveMapNode)

