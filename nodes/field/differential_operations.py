
import bpy
from bpy.props import FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

from sverchok.utils.field.differential import (
        SvVectorFieldDivergence, SvScalarFieldLaplacian,
        SvScalarFieldGradient, SvVectorFieldRotor)
from sverchok.utils.modules.sockets import SvDynamicSocketsHandler, SocketInfo

sockets_handler = SvDynamicSocketsHandler()

S_FIELD_A, V_FIELD_A = sockets_handler.register_inputs(
        SocketInfo("SvScalarFieldSocket", "SFieldA", "CIRCLE_DOT"),
        SocketInfo("SvVectorFieldSocket", "VFieldA", "CIRCLE_DOT")
    )

S_FIELD_B, V_FIELD_B = sockets_handler.register_outputs(
        SocketInfo("SvScalarFieldSocket", "SFieldB", "CIRCLE_DOT"),
        SocketInfo("SvVectorFieldSocket", "VFieldB", "CIRCLE_DOT")
    )

operations = [
    ('GRAD', "Gradient", [("SFieldA", "SField")], [("VFieldB", "Gradient")], "Calculate the gradient of the scalar field. The result is a vector field"),
    ('DIV', "Divergence", [("VFieldA", "VField")], [("SFieldB", "Divergence")], "Calculate the divergence of the vector field. The result is a scalar field"),
    ('LAPLACE', "Laplacian", [("SFieldA", "SField")], [("SFieldB", "Laplacian")], "Calculate the Laplace operator on the scalar field. The result is a scalar field"),
    ('ROTOR', "Rotor", [("VFieldA", "VField")], [("VFieldB", "Rotor")], "Calculate the rotor operator on the vector field. The result is a vector field")
]

operation_modes = [ (id, name, description, i) for i, (id, name, _, _, description) in enumerate(operations) ]

def get_sockets(op_id):
    actual_inputs = None
    actual_outputs = None
    for id, _, inputs, outputs, _ in operations:
        if id == op_id:
            return inputs, outputs
    raise Exception("unsupported operation")

class SvFieldDiffOpsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Field Differential Operations
    Tooltip: Field differential operations
    """
    bl_idname = 'SvExFieldDiffOpsNode'
    bl_label = 'Field Differential Operations'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_NABLA'

    step : FloatProperty(
            name = "Step",
            description = "Derivatives calculation step. Bigger values give smoother fields",
            default = 0.001,
            precision = 4,
            update = updateNode)

    def sv_init(self, context):
        sockets_handler.init_sockets(self)
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', text='')
        layout.prop(self, 'step')

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
        updateNode(self, context)

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
                    vfield = SvScalarFieldGradient(sfield, self.step)
                    vfields_out.append(vfield)
                elif self.operation == 'DIV':
                    sfield = SvVectorFieldDivergence(vfield, self.step)
                    sfields_out.append(sfield)
                elif self.operation == 'LAPLACE':
                    sfield = SvScalarFieldLaplacian(sfield, self.step)
                    sfields_out.append(sfield)
                elif self.operation == 'ROTOR':
                    vfield = SvVectorFieldRotor(vfield, self.step)
                    vfields_out.append(vfield)
                else:
                    raise Exception("Unsupported operation")

        self.outputs[V_FIELD_B.idx].sv_set(vfields_out)
        self.outputs[S_FIELD_B.idx].sv_set(sfields_out)

def register():
    bpy.utils.register_class(SvFieldDiffOpsNode)

def unregister():
    bpy.utils.unregister_class(SvFieldDiffOpsNode)

