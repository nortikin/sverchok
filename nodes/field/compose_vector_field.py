
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat
from sverchok.utils.logging import info, exception

from sverchok.utils.math import coordinate_modes
from sverchok.utils.field.vector import SvExComposedVectorField

class SvExComposeVectorFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Compose Vector Field
    Tooltip: Generate vector field from three scalar fields
    """
    bl_idname = 'SvExComposeVectorFieldNode'
    bl_label = 'Compose Vector Field'
    bl_icon = 'OUTLINER_OB_EMPTY'

    @throttled
    def update_sockets(self, context):
        if self.input_mode == 'XYZ':
            self.inputs[0].name = 'X'
            self.inputs[1].name = 'Y'
            self.inputs[2].name = 'Z'
        elif self.input_mode == 'CYL':
            self.inputs[0].name = 'Rho'
            self.inputs[1].name = 'Phi'
            self.inputs[2].name = 'Z'
        else: # SPH
            self.inputs[0].name = 'Rho'
            self.inputs[1].name = 'Phi'
            self.inputs[2].name = 'Theta'

    input_mode : EnumProperty(
        name = "Coordinates",
        items = coordinate_modes,
        default = 'XYZ',
        update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvExScalarFieldSocket', "Field1").display_shape = 'CIRCLE_DOT'
        self.inputs.new('SvExScalarFieldSocket', "Field2").display_shape = 'CIRCLE_DOT'
        self.inputs.new('SvExScalarFieldSocket', "Field3").display_shape = 'CIRCLE_DOT'
        self.outputs.new('SvExVectorFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        #layout.label(text="Input:")
        layout.prop(self, "input_mode", expand=True)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        fields_1_s = self.inputs[0].sv_get()
        fields_2_s = self.inputs[1].sv_get()
        fields_3_s = self.inputs[2].sv_get()

        fields_out = []
        for field1s, field2s, field3s in zip_long_repeat(fields_1_s, fields_2_s, fields_3_s):
            if not isinstance(field1s, (list, tuple)):
                field1s = [field1s]
            if not isinstance(field2s, (list, tuple)):
                field2s = [field2s]
            if not isinstance(field3s, (list, tuple)):
                field3s = [field3s]
            for field1, field2, field3 in zip_long_repeat(field1s, field2s, field3s):
                field = SvExComposedVectorField(self.input_mode, field1, field2, field3)
                fields_out.append(field)
        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExComposeVectorFieldNode)

def unregister():
    bpy.utils.unregister_class(SvExComposeVectorFieldNode)

