
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat
from sverchok.utils.logging import info, exception

from sverchok.utils.field.scalar import (SvScalarField,
            SvVectorFieldsScalarProduct,
            SvVectorFieldNorm,
            SvVectorScalarFieldComposition)
from sverchok.utils.field.vector import (SvVectorField,
            SvVectorFieldBinOp, SvVectorFieldMultipliedByScalar,
            SvVectorFieldsLerp, SvVectorFieldCrossProduct, 
            SvVectorFieldTangent, SvVectorFieldCotangent,
            SvAbsoluteVectorField, SvRelativeVectorField,
            SvVectorFieldComposition)
from sverchok.utils.modules.sockets import SvDynamicSocketsHandler, SocketInfo

sockets_handler = SvDynamicSocketsHandler()

V_FIELD_A, V_FIELD_B, S_FIELD_B = sockets_handler.register_inputs(
        SocketInfo("SvVectorFieldSocket", "VFieldA", "CIRCLE_DOT"),
        SocketInfo("SvVectorFieldSocket", "VFieldB", "CIRCLE_DOT"),
        SocketInfo("SvScalarFieldSocket", "SFieldB", "CIRCLE_DOT")
    )

V_FIELD_C, S_FIELD_C, V_FIELD_D = sockets_handler.register_outputs(
        SocketInfo("SvVectorFieldSocket", "VFieldC", "CIRCLE_DOT"),
        SocketInfo("SvScalarFieldSocket", "SFieldC", "CIRCLE_DOT"),
        SocketInfo("SvVectorFieldSocket", "VFieldD", "CIRCLE_DOT")
    )

operations = [
    ('ADD', "Add", lambda x,y : x+y, [("VFieldA", "A"), ("VFieldB", "B")], [("VFieldC", "Sum")]),
    ('SUB', "Sub", lambda x, y : x-y, [("VFieldA", "A"), ('VFieldB', "B")], [("VFieldC", "Difference")]),
    ('AVG', "Average", lambda x, y : (x+y)/2, [("VFieldA", "A"), ("VFieldB", "B")], [("VFieldC", "Average")]),
    ('DOT', "Scalar Product", None, [("VFieldA", "A"), ("VFieldB", "B")], [("SFieldC", "Product")]),
    ('CROSS', "Vector Product", None, [("VFieldA", "A"), ("VFieldB","B")], [("VFieldC", "Product")]),
    ('MUL', "Multiply Scalar", None, [("VFieldA", "VField"), ("SFieldB", "Scalar")], [("VFieldC", "Product")]),
    ('TANG', "Projection decomposition", None, [("VFieldA", "VField"), ("VFieldB","Basis")], [("VFieldC", "Projection"), ("VFieldD", "Coprojection")]),
    ('COMPOSE', "Composition VB(VA(x))", None, [("VFieldA", "VA"), ("VFieldB", "VB")], [("VFieldC", "VC")]),
    ('COMPOSES', "Composition SB(VA(x))", None, [("VFieldA", "VA"), ("SFieldB", "SB")], [("SFieldC", "SC")]),
    ('NORM', "Norm", None, [("VFieldA", "VField")], [("SFieldC", "Norm")]),
    ('LERP', "Lerp A -> B", None, [("VFieldA", "A"), ("VFieldB", "B"), ("SFieldB", "Coefficient")], [("VFieldC", "VField")]),
    ('ABS', "Relative -> Absolute", None, [("VFieldA", "Relative")], [("VFieldC", "Absolute")]),
    ('REL', "Absolute -> Relative", None, [("VFieldA", "Absolute")], [("VFieldC", "Relative")]),
]

operation_modes = [ (id, name, name, i) for i, (id, name, fn, _, _) in enumerate(operations) ]

def get_operation(op_id):
    for id, _, function, _, _ in operations:
        if id == op_id:
            return function
    raise Exception("Unsupported operation: " + op_id)

def get_sockets(op_id):
    actual_inputs = None
    actual_outputs = None
    for id, _, _, inputs, outputs in operations:
        if id == op_id:
            return inputs, outputs
    raise Exception("unsupported operation")

class SvVectorFieldMathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Field Math
    Tooltip: Vector Field Math
    """
    bl_idname = 'SvExVectorFieldMathNode'
    bl_label = 'Vector Field Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VECTOR_FIELD_MATH'

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
        default = 'ADD',
        update = update_sockets)

    def sv_init(self, context):
        sockets_handler.init_sockets(self)
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vfield_a_s = self.inputs[V_FIELD_A.idx].sv_get()
        vfield_b_s = self.inputs[V_FIELD_B.idx].sv_get(default=[[None]])
        sfield_b_s = self.inputs[S_FIELD_B.idx].sv_get(default=[[None]])

        vfields_c_out = []
        vfields_d_out = []
        sfields_out = []
        for vfields_a, vfields_b, sfields_b in zip_long_repeat(vfield_a_s, vfield_b_s, sfield_b_s):

            if not isinstance(vfields_a, (list, tuple)):
                vfields_a = [vfields_a]
            if not isinstance(vfields_b, (list, tuple)):
                vfields_b = [vfields_b]
            if not isinstance(sfields_b, (list, tuple)):
                sfields_b = [sfields_b]

            for vfield_a, vfield_b, sfield_b in zip_long_repeat(vfields_a, vfields_b, sfields_b):

                inputs = dict(VFieldA = vfield_a, VFieldB = vfield_b, SFieldB = sfield_b)

                if self.operation == 'MUL':
                    field_c = SvVectorFieldMultipliedByScalar(vfield_a, sfield_b)
                    vfields_c_out.append(field_c)
                elif self.operation == 'DOT':
                    field_c = SvVectorFieldsScalarProduct(vfield_a, vfield_b)
                    sfields_out.append(field_c)
                elif self.operation == 'CROSS':
                    field_c = SvVectorFieldCrossProduct(vfield_a, vfield_b)
                    vfields_c_out.append(field_c)
                elif self.operation == 'NORM':
                    field_c = SvVectorFieldNorm(vfield_a)
                    sfields_out.append(field_c)
                elif self.operation == 'TANG':
                    field_c = SvVectorFieldTangent(vfield_a, vfield_b)
                    field_d = SvVectorFieldCotangent(vfield_a, vfield_b)
                    vfields_c_out.append(field_c)
                    vfields_d_out.append(field_d)
                elif self.operation == 'COMPOSE':
                    field_c = SvVectorFieldComposition(vfield_a, vfield_b)
                    vfields_c_out.append(field_c)
                elif self.operation == 'COMPOSES':
                    field_c = SvVectorScalarFieldComposition(vfield_a, sfield_b)
                    sfields_out.append(field_c)
                elif self.operation == 'LERP':
                    field_c = SvVectorFieldsLerp(vfield_a, vfield_b, sfield_b)
                    vfields_c_out.append(field_c)
                elif self.operation == 'ABS':
                    field_c = SvAbsoluteVectorField(vfield_a)
                    vfields_c_out.append(field_c)
                elif self.operation == 'REL':
                    field_c = SvRelativeVectorField(vfield_a)
                    vfields_c_out.append(field_c)
                else:
                    operation = get_operation(self.operation)
                    field_c = SvVectorFieldBinOp(vfield_a, vfield_b, operation)
                    vfields_c_out.append(field_c)

        self.outputs[V_FIELD_C.idx].sv_set(vfields_c_out)
        self.outputs[V_FIELD_D.idx].sv_set(vfields_d_out)
        self.outputs[S_FIELD_C.idx].sv_set(sfields_out)

def register():
    bpy.utils.register_class(SvVectorFieldMathNode)

def unregister():
    bpy.utils.unregister_class(SvVectorFieldMathNode)

