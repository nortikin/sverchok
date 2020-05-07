
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.field.scalar import SvScalarField, SvScalarFieldGaussCurvature

class SvScalarFieldCurvatureNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Curvature
    Tooltip: Scalar Field Curvature
    """
    bl_idname = 'SvScalarFieldCurvatureNode'
    bl_label = 'Scalar Field Curvature'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SCALAR_FIELD_MATH'

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.outputs.new('SvScalarFieldSocket', "Gauss")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field_s = self.inputs['Field'].sv_get()
        field_s = ensure_nesting_level(field_s, 2, data_types=(SvScalarField,))

        fields_out = []
        for fields in field_s:
            for field in fields:
                step = 0.001
                new_field = SvScalarFieldGaussCurvature(field, step)
                fields_out.append(new_field)

        self.outputs['Gauss'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvScalarFieldCurvatureNode)

def unregister():
    bpy.utils.unregister_class(SvScalarFieldCurvatureNode)

