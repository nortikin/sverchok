
import bpy
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, updateNode

from sverchok.utils.field.scalar import (
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
    ('ADD', "Add", lambda x,y : x+y, [("VFieldA", "A"), ("VFieldB", "B")], [("VFieldC", "Sum")], "Calculate vector (coordinate-wise) sum of two vector fields - VFieldA + VFieldB" ),
    ('SUB', "Sub", lambda x, y : x-y, [("VFieldA", "A"), ('VFieldB', "B")], [("VFieldC", "Difference")], "Calculate vector (coordinate-wise) difference between two vector fields - VFieldA - VFieldB" ),
    ('AVG', "Average", lambda x, y : (x+y)/2, [("VFieldA", "A"), ("VFieldB", "B")], [("VFieldC", "Average")], "Calculate the average between two vector fields - (VFieldA + VFieldB) / 2" ),
    ('DOT', "Scalar Product", None, [("VFieldA", "A"), ("VFieldB", "B")], [("SFieldC", "Product")], "Calculate scalar (dot) product of two vector fields" ),
    ('CROSS', "Vector Product", None, [("VFieldA", "A"), ("VFieldB","B")], [("VFieldC", "Product")], "Calculate vector (cross) product of two vector fields" ),
    ('MUL', "Multiply Scalar", None, [("VFieldA", "VField"), ("SFieldB", "Scalar")], [("VFieldC", "Product")], "Multiply the vectors of vector field by scalar values of scalar field" ),
    ('TANG', "Projection decomposition", None, [("VFieldA", "VField"), ("VFieldB","Basis")], [("VFieldC", "Projection"), ("VFieldD", "Coprojection")], "Project the vectors of the first vector field to the vectors of the second vector field ('basis');\nOutput the component of the first vector field which is colinear to the basis ('Projection') and the residual component ('Coprojection')" ),
    ('COMPOSE', "Composition VB(VA(x))", None, [("VFieldA", "VA"), ("VFieldB", "VB")], [("VFieldC", "VC")], "Functional composition of two vector fields;\nThe resulting vector is calculated by evaluating the first vector field, and then evaluating the second vector field at the resulting point of the first evaluation" ),
    ('COMPOSES', "Composition SB(VA(x))", None, [("VFieldA", "VA"), ("SFieldB", "SB")], [("SFieldC", "SC")], "Functional composition of vector field and a scalar field. The resulting scalar is calculated by first evaluating the vector field at original point, and then evaluating the scalar field at the resulting point.\nThe result is a scalar field" ),
    ('NORM', "Norm", None, [("VFieldA", "VField")], [("SFieldC", "Norm")], "Calculate the norm (length) of vector field vectors. The result is a scalar field" ),
    ('LERP', "Lerp A -> B", None, [("VFieldA", "A"), ("VFieldB", "B"), ("SFieldB", "Coefficient")], [("VFieldC", "VField")], "Linear interpolation between two vector fields. The interpolation coefficient is defined by a scalar field. The result is a vector field" ),
    ('ABS', "Relative -> Absolute", None, [("VFieldA", "Relative")], [("VFieldC", "Absolute")], "Given the vector field VF, return the vector field which maps point X to X + VF(X)" ),
    ('REL', "Absolute -> Relative", None, [("VFieldA", "Absolute")], [("VFieldC", "Relative")], "Given the vector field VF, return the vector field which maps point X to VF(X) - X" ),
]

operation_modes = [ (id, name, description, i) for i, (id, name, fn, _, _, description) in enumerate(operations) ]

def get_operation(op_id):
    for id, _, function, _, _, _ in operations:
        if id == op_id:
            return function
    raise Exception("Unsupported operation: " + op_id)

def get_sockets(op_id):
    actual_inputs = None
    actual_outputs = None
    for id, _, _, inputs, outputs, _ in operations:
        if id == op_id:
            return inputs, outputs
    raise Exception("unsupported operation")

class SvVectorFieldMathNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Vector Field Math
    Tooltip: Vector Field Math
    """
    bl_idname = 'SvExVectorFieldMathNode'
    bl_label = 'Vector Field Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VECTOR_FIELD_MATH'

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

