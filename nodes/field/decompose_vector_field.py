
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import throttle_and_update_node
from sverchok.utils.logging import info, exception

from sverchok.utils.math import coordinate_modes
from sverchok.utils.field.scalar import SvVectorFieldDecomposed

class SvDecomposeVectorFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Decompose Vector Field
    Tooltip: Decompose vector field into three scalar fields
    """
    bl_idname = 'SvExDecomposeVectorFieldNode'
    bl_label = 'Decompose Vector Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VFIELD_OUT'

    @throttle_and_update_node
    def update_sockets(self, context):
        if self.output_mode == 'XYZ':
            self.outputs[0].name = 'X'
            self.outputs[1].name = 'Y'
            self.outputs[2].name = 'Z'
        elif self.output_mode == 'CYL':
            self.outputs[0].name = 'Rho'
            self.outputs[1].name = 'Phi'
            self.outputs[2].name = 'Z'
        else: # SPH
            self.outputs[0].name = 'Rho'
            self.outputs[1].name = 'Phi'
            self.outputs[2].name = 'Theta'

    output_mode : EnumProperty(
        name = "Coordinates",
        items = coordinate_modes,
        default = 'XYZ',
        update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvVectorFieldSocket', "Field")
        self.outputs.new('SvScalarFieldSocket', "Field1")
        self.outputs.new('SvScalarFieldSocket', "Field2")
        self.outputs.new('SvScalarFieldSocket', "Field3")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        #layout.label(text="Output:")
        layout.prop(self, "output_mode", expand=True)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        fields_s = self.inputs['Field'].sv_get()
        fields_1_out = []
        fields_2_out = []
        fields_3_out = []
        for fields in fields_s:
            if not isinstance(fields, (list, tuple)):
                fields = [fields]
            for field in fields:
                field1 = SvVectorFieldDecomposed(field, self.output_mode, 0)
                field2 = SvVectorFieldDecomposed(field, self.output_mode, 1)
                field3 = SvVectorFieldDecomposed(field, self.output_mode, 2)
                fields_1_out.append(field1)
                fields_2_out.append(field2)
                fields_3_out.append(field3)
        self.outputs[0].sv_set(fields_1_out)
        self.outputs[1].sv_set(fields_2_out)
        self.outputs[2].sv_set(fields_3_out)

def register():
    bpy.utils.register_class(SvDecomposeVectorFieldNode)

def unregister():
    bpy.utils.unregister_class(SvDecomposeVectorFieldNode)

