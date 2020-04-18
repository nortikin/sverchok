
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.modules.eval_formula import get_variables, safe_eval
from sverchok.utils.logging import info, exception

from sverchok.utils.field.scalar import SvScalarFieldBinOp, SvScalarField, SvNegatedScalarField

operations = [
    ('ADD', "Add", lambda x, y : x+y),
    ('SUB', "Sub", lambda x, y : x-y),
    ('MUL', "Multiply", lambda x, y : x * y),
    ('MIN', "Minimum", lambda x, y : np.min([x,y],axis=0)),
    ('MAX', "Maximum", lambda x, y : np.max([x,y],axis=0)),
    ('AVG', "Average", lambda x, y : (x+y)/2),
    ('NEG', "Negate", lambda x : -x)
]

operation_modes = [ (id, name, name, i) for i, (id, name, fn) in enumerate(operations) ]

def get_operation(op_id):
    for id, _, function in operations:
        if id == op_id:
            return function
    raise Exception("Unsupported operation: " + op_id)

class SvScalarFieldMathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Math
    Tooltip: Scalar Field Math
    """
    bl_idname = 'SvExScalarFieldMathNode'
    bl_label = 'Scalar Field Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SCALAR_FIELD_MATH'

    @throttled
    def update_sockets(self, context):
        self.inputs['FieldB'].hide_safe = self.operation == 'NEG'

    operation : EnumProperty(
        name = "Operation",
        items = operation_modes,
        default = 'ADD',
        update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "FieldA")
        self.inputs.new('SvScalarFieldSocket', "FieldB")
        self.outputs.new('SvScalarFieldSocket', "FieldC")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field_a_s = self.inputs['FieldA'].sv_get()
        field_b_s = self.inputs['FieldB'].sv_get(default=[[None]])

        fields_out = []
        for fields_a, fields_b in zip_long_repeat(field_a_s, field_b_s):
            if isinstance(fields_a, SvScalarField):
                fields_a = [fields_a]
            if isinstance(fields_b, SvScalarField):
                fields_b = [fields_b]
            for field_a, field_b in zip_long_repeat(fields_a, fields_b):
                operation = get_operation(self.operation)
                if self.operation == 'NEG':
                    field_c = SvNegatedScalarField(field_a)
                else:
                    field_c = SvScalarFieldBinOp(field_a, field_b, operation)
                fields_out.append(field_c)

        self.outputs['FieldC'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvScalarFieldMathNode)

def unregister():
    bpy.utils.unregister_class(SvScalarFieldMathNode)

