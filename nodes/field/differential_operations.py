
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat
from sverchok.utils.logging import info, exception

from sverchok.utils.field.scalar import (SvExScalarField,
                SvExVectorFieldDivergence, SvExScalarFieldLaplacian)
from sverchok.utils.field.vector import ( SvExVectorField,
                SvExScalarFieldGradient, SvExVectorFieldRotor)
from sverchok.utils.modules.sockets import SvExDynamicSocketsHandler, SocketInfo

sockets_handler = SvExDynamicSocketsHandler()

S_FIELD_A, V_FIELD_A = sockets_handler.register_inputs(
        SocketInfo("SvExScalarFieldSocket", "SFieldA", "CIRCLE_DOT"),
        SocketInfo("SvExVectorFieldSocket", "VFieldA", "CIRCLE_DOT")
    )

S_FIELD_B, V_FIELD_B = sockets_handler.register_outputs(
        SocketInfo("SvExScalarFieldSocket", "SFieldB", "CIRCLE_DOT"),
        SocketInfo("SvExVectorFieldSocket", "VFieldB", "CIRCLE_DOT")
    )

operations = [
    ('GRAD', "Gradient", [("SFieldA", "SField")], [("VFieldB", "Gradient")]),
    ('DIV', "Divergence", [("VFieldA", "VField")], [("SFieldB", "Divergence")]),
    ('LAPLACE', "Laplacian", [("SFieldA", "SField")], [("SFieldB", "Laplacian")]),
    ('ROTOR', "Rotor", [("VFieldA", "VField")], [("VFieldB", "Rotor")])
]

operation_modes = [ (id, name, name, i) for i, (id, name, _, _) in enumerate(operations) ]

def get_sockets(op_id):
    actual_inputs = None
    actual_outputs = None
    for id, _, inputs, outputs in operations:
        if id == op_id:
            return inputs, outputs
    raise Exception("unsupported operation")

class SvExFieldDiffOpsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Field Differential Operations
    Tooltip: Field differential operations
    """
    bl_idname = 'SvExFieldDiffOpsNode'
    bl_label = 'Field Differential Operation'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_NABLA'

    step : FloatProperty(
            name = "Step",
            default = 0.001,
            precision = 4,
            update = updateNode)

    def sv_init(self, context):
        sockets_handler.init_sockets(self)
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', text='')
        layout.prop(self, 'step')

    @throttled
    def update_sockets(self, context):
        actual_inputs, actual_outputs = get_sockets(self.operation)
        actual_inputs = dict(actual_inputs)
        actual_outputs = dict(actual_outputs)
        for socket in self.inputs:
            registered = sockets_handler.get_input_by_idx(socket.index)
            socket.hide_safe = registered.id not in actual_inputs
            if not socket.hide_safe:
                socket.name = actual_inputs[registered.id]

        for socket in self.outputs:
            registered = sockets_handler.get_output_by_idx(socket.index)
            socket.hide_safe = registered.id not in actual_outputs
            if not socket.hide_safe:
                socket.name = actual_outputs[registered.id]

    operation : EnumProperty(
        name = "Operation",
        items = operation_modes,
        default = 'GRAD',
        update = update_sockets)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sfields_s = self.inputs[S_FIELD_A.idx].sv_get(default=[[None]])
        vfields_s = self.inputs[V_FIELD_A.idx].sv_get(default=[[None]])
        if not isinstance(sfields_s, (list, tuple)):
            sfields_s = [sfields_s]
        if not isinstance(vfields_s, (list, tuple)):
            vfields_s = [vfields_s]

        vfields_out = []
        sfields_out = []
        for sfields, vfields in zip_long_repeat(sfields_s, vfields_s):
            if not isinstance(sfields, (list, tuple)):
                sfields = [sfields]
            if not isinstance(vfields, (list, tuple)):
                vfields = [vfields]
            for sfield, vfield in zip_long_repeat(sfields, vfields):
                if self.operation == 'GRAD':
                    vfield = SvExScalarFieldGradient(sfield, self.step)
                    vfields_out.append(vfield)
                elif self.operation == 'DIV':
                    sfield = SvExVectorFieldDivergence(vfield, self.step)
                    sfields_out.append(sfield)
                elif self.operation == 'LAPLACE':
                    sfield = SvExScalarFieldLaplacian(sfield, self.step)
                    sfields_out.append(sfield)
                elif self.operation == 'ROTOR':
                    vfield = SvExVectorFieldRotor(vfield, self.step)
                    vfields_out.append(vfield)
                else:
                    raise Exception("Unsupported operation")

        self.outputs[V_FIELD_B.idx].sv_set(vfields_out)
        self.outputs[S_FIELD_B.idx].sv_set(sfields_out)

def register():
    bpy.utils.register_class(SvExFieldDiffOpsNode)

def unregister():
    bpy.utils.unregister_class(SvExFieldDiffOpsNode)

