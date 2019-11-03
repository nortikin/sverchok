# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       BoolVectorProperty,
                       EnumProperty)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

from mathutils import Matrix, Quaternion
from functools import reduce

# list of operations [name: id, input, output, description ]
operations = {
    # multiple quaternions => quaternion (NQ or QQ => Q)
    "ADD":       (10, "NQ", "Q", "Add multiple quaternions"),
    "SUB":       (11, "QQ", "Q", "Subtract two quaternions"),
    "MULTIPLY":  (12, "NQ", "Q", "Multiply multiple quaternions"),
    "DIVIDE":    (13, "QQ", "Q", "Divide two quaternions"),
    "ROTATE":    (14, "QQ", "Q", "Rotate a quaternion around another"),
    # two quaternions => scalar value (QQ => Q)
    "DOT":       (20, "QQ", "S", "Dot product two quaternions"),
    "DISTANCE":  (21, "QQ", "S", "Distance between two quaternions"),
    # one quaternion => quaternion (Q => Q)
    "NEGATE":    (30, "Q", "Q", "Negate a quaternion"),
    "CONJUGATE": (31, "Q", "Q", "Conjugate a quaternion"),
    "INVERT":    (32, "Q", "Q", "Invert a quaternion"),
    "NORMALIZE": (33, "Q", "Q", "Normalize a quaternion"),
    # one quaternion + scalar => quaternion (QS => Q)
    "SCALE":     (40, "QS", "Q", "Scale a quaternion by given factor"),
    # one quaternion => scalar value (Q => S)
    "QUADRANCE": (50, "Q", "S", "Quadrance of a quaternion"),
    "MAGNITUDE": (51, "Q", "S", "Magnitude of a quaternion"),
}

operation_items = [(k, k.title(), s[3], "", s[0]) for k, s in sorted(operations.items(), key=lambda k: k[1][0])]

# cache various operation categories
NQ_operations = [n for n in operations if operations[n][1] == "NQ"]
QQ_operations = [n for n in operations if operations[n][1] == "QQ"]
Q_operations = [n for n in operations if operations[n][1] in {"Q", "QS"}]
QS_operations = [n for n in operations if operations[n][1] == "QS"]
output_S_operations = [n for n in operations if operations[n][2] == "S"]
pre_post_operations = {"SUB", "MULTIPLY", "DIVIDE", "ROTATE"}

pre_post_items = [
    ("PRE", "Pre", "Calculate A op B", 0),
    ("POST", "Post", "Calculate B op A", 1)
]

id_quat = [Quaternion([1, 0, 0, 0])]
ABC = tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class SvQuaternionMathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Quaternions, Math
    Tooltip: Compute various arithmetic operations on quaternions
    """
    bl_idname = 'SvQuaternionMathNode'
    bl_label = 'Quaternion Math'
    sv_icon = 'SV_QUATERNION_MATH'

    def update_operation(self, context):
        self.label = "Quaternion " + self.operation.title()
        self.update_sockets()
        updateNode(self, context)

    pre_post : EnumProperty(
        name='Pre Post',
        description='Order of operations PRE = A op B vs POST = B op A)',
        items=pre_post_items, default="PRE", update=updateNode)

    operation : EnumProperty(
        name="Operation",
        description="Operation to apply on the given quaternions",
        items=operation_items, default="MULTIPLY", update=update_operation)

    scale : FloatProperty(
        name="Scale",
        description="Scale quaternion components by this factor",
        default=1.0, update=updateNode)

    scales : BoolVectorProperty(
        name="Scales", description="Which individual components to scale",
        size=4, subtype="QUATERNION",
        default=(True, True, True, True), update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Scale").prop_name = "scale"
        self.inputs.new('SvQuaternionSocket', "A")
        self.inputs.new('SvQuaternionSocket', "B")

        self.outputs.new('SvQuaternionSocket', "Quaternion")
        self.outputs.new('SvStringsSocket', "Value")

        self.update_operation(context)

    def update(self):
        ''' Add/remove sockets as A-Z sockets are connected/disconnected '''

        # not a multiple quaternion operation ? => no need to update sockets
        if self.operation not in NQ_operations:
            return

        inputs = self.inputs

        # get all existing A-Z sockets (connected or not)
        inputs_AZ = list(filter(lambda s: s.name in ABC, inputs))

        # last A-Z socket connected ? => add an empty A-Z socket at the end
        if inputs_AZ and inputs_AZ[-1].links:
            name = ABC[len(inputs_AZ)]  # pick the next letter A to Z
            inputs.new("SvQuaternionSocket", name)
        else:  # last input disconnected ? => remove all but last unconnected
            while len(inputs_AZ) > 2 and not inputs_AZ[-2].links:
                s = inputs_AZ[-1]
                inputs.remove(s)
                inputs_AZ.remove(s)

    def update_sockets(self):
        ''' Upate sockets based on selected operation '''
        inputs = self.inputs

        if self.operation in Q_operations:  # Q or Q+S operations
            for a in ABC[1:]:  # remove all B-Z inputs (keep A)
                if a in inputs:
                    inputs.remove(inputs[a])
        elif self.operation in QQ_operations:  # Q + Q operations
            for a in ABC[2:]:  # remove all C-Z inputs (keep A & B)
                if a in inputs:
                    inputs.remove(inputs[a])
            if not "B" in inputs:
                inputs.new("SvQuaternionSocket", "B")
        else:  # multiple Q operations
            if not "B" in inputs:
                inputs.new("SvQuaternionSocket", "B")

        inputs["Scale"].hide_safe = self.operation != "SCALE"

        outputs = self.outputs
        if self.operation in output_S_operations:
            outputs["Quaternion"].hide_safe = True
            if outputs["Value"].hide:
                outputs["Value"].hide_safe = False
        else:
            if outputs["Quaternion"].hide:
                outputs["Quaternion"].hide_safe = False
            outputs["Value"].hide_safe = True

        self.update()

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")
        if self.operation in pre_post_operations:
            layout.prop(self, "pre_post", expand=True)
        if self.operation == "SCALE":
            row = layout.row(align=True)
            row.prop(self, "scales", text="", toggle=True)

    def operation_negate(self, q):
        qn = Quaternion(q)
        qn.negate()
        return qn

    def operation_rotate(self, q, p):
        qr = Quaternion(q)
        qr.rotate(p)
        return qr

    def get_operation(self):
        if self.operation == "ADD":
            return lambda l: reduce((lambda q, p: q + p), l)
        elif self.operation == "SUB":
            return lambda q, p: q - p
        elif self.operation == "MULTIPLY":
            return lambda l: reduce((lambda q, p: q.cross(p)), l)
        elif self.operation == "DIVIDE":
            return lambda q, p: q.cross(p.inverted())
        elif self.operation == "ROTATE":
            return self.operation_rotate
        elif self.operation == "DOT":
            return lambda q, p: q.dot(p)
        elif self.operation == "DISTANCE":
            return lambda q, p: (p - q).magnitude
        elif self.operation == "NEGATE":
            return self.operation_negate
        elif self.operation == "CONJUGATE":
            return lambda q: q.conjugated()
        elif self.operation == "INVERT":
            return lambda q: q.inverted()
        elif self.operation == "NORMALIZE":
            return lambda q: q.normalized()
        elif self.operation == "SCALE":
            return lambda q, s: Quaternion([q[i] * s[i] for i in range(4)])
        elif self.operation == "QUADRANCE":
            return lambda q: q.dot(q)
        elif self.operation == "MAGNITUDE":
            return lambda q: q.magnitude

    def process(self):
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs

        all_AZ_sockets = list(filter(lambda s: s.name in ABC, inputs))
        connected_AZ_sockets = list(filter(lambda s: s.is_linked, all_AZ_sockets))

        if len(connected_AZ_sockets) == 0:
            return

        # collect the quaternion inputs from all connected AZ sockets
        I = [s.sv_get(default=id_quat) for s in connected_AZ_sockets]

        if self.operation in pre_post_operations:
            if self.pre_post == "POST":  # A op B : keep input order
                I = I[::-1]

        other_sockets = list(filter(lambda s: s.name not in ABC and not s.hide, inputs))

        # collect the remaning visible inputs
        for socket in other_sockets:
            values = socket.sv_get()[0]
            if socket.name == "Scale":
                qs = []
                for s in values:
                    swxyz = [s if self.scales[i] else 1.0 for i in range(4)]
                    qs.append(Quaternion(swxyz))
                values = qs
            I.append(values)

        operation = self.get_operation()

        if self.operation in NQ_operations:
            parameters = match_long_repeat(I)
            quaternion_list = [operation(params) for params in zip(*parameters)]

        elif self.operation in QQ_operations:
            parameters = match_long_repeat(I)
            quaternion_list = [operation(*params) for params in zip(*parameters)]

        elif self.operation == "SCALE":
            parameters = match_long_repeat(I)
            quaternion_list = [operation(*params) for params in zip(*parameters)]

        else:  # single input operations
            parameters = I[0]  # just quaternion values
            quaternion_list = [operation(a) for a in parameters]

        if self.operation in output_S_operations:
            if outputs['Value'].is_linked:
                outputs['Value'].sv_set([quaternion_list])
        else:  # output quaternions
            if outputs['Quaternion'].is_linked:
                outputs['Quaternion'].sv_set(quaternion_list)


def register():
    bpy.utils.register_class(SvQuaternionMathNode)


def unregister():
    bpy.utils.unregister_class(SvQuaternionMathNode)
