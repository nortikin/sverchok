
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
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
    bl_label = 'Map Scalar Field by Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SCALAR_FIELD_CURVE_MAP'

    modes = [
            ('VALUE', "Curve points", "Use radius-vector of points of the curve as values of the vector field", 0),
            ('TANGENT', "Curve tangents", "Use curve tangents as values of the vector field", 1),
            ('NORMAL', "Curve normals", "Use curve normals as values of the vector field", 2)
        ]

    mode : EnumProperty(
        name = "Curve usage",
        description = "How the curve is used",
        items = modes,
        default = 'VALUE',
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Curve usage:')
        layout.prop(self, 'mode', text='')

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
                vfield = SvScalarFieldCurveMap(sfield, curve, mode=self.mode)
                vfields_out.append(vfield)

        self.outputs['Field'].sv_set(vfields_out)

def register():
    bpy.utils.register_class(SvScalarFieldCurveMapNode)

def unregister():
    bpy.utils.unregister_class(SvScalarFieldCurveMapNode)

