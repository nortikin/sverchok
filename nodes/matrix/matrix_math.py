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

from functools import reduce
import bpy
from bpy.props import BoolProperty, EnumProperty

from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, list_match_func, numpy_list_match_modes)
from sverchok.utils.sv_itertools import (recurse_f_level_control)

OPERATION_ITEMS = [
    ("MULTIPLY", "Multiply", "Multiply two matrices", 0),
    ("INVERT", "Invert", "Invert matrix", 1),
    ("FILTER", "Filter", "Filter matrix components", 2),
    ("BASIS", "Basis", "Extract Basis vectors", 3)
]

PRE_POST_ITEMS = [
    ("PRE", "Pre", "Calculate A op B", 0),
    ("POST", "Post", "Calculate B op A", 1)
]

id_mat = [Matrix.Identity(4)]
ABC = tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

def matrix_multiply(params, constant, matching_f):
    operation, pre_post = constant
    if pre_post == "PRE":  # A op B : keep input order
        parameters = matching_f(params)
    else:  # B op A : reverse input order
        parameters = matching_f(params[::-1])

    return [operation(params) for params in zip(*parameters)]

def operation_basis(matrix):
    _, rotation, _ = matrix.decompose()

    rot_mat = rotation.to_matrix().to_4x4()
    x_axis = (rot_mat[0][0], rot_mat[1][0], rot_mat[2][0])
    y_axis = (rot_mat[0][1], rot_mat[1][1], rot_mat[2][1])
    z_axis = (rot_mat[0][2], rot_mat[1][2], rot_mat[2][2])

    return x_axis, y_axis, z_axis

def recursive_basis_op(mat_list):
    x_list = []
    y_list = []
    z_list = []
    if isinstance(mat_list[0], Matrix):

        for mat in mat_list:
            x_axis, y_axis, z_axis = operation_basis(mat)
            x_list.append(x_axis)
            y_list.append(y_axis)
            z_list.append(z_axis)
    else:
        for sublist in mat_list:
            sub_x_list, sub_y_list, sub_z_list = recursive_basis_op(sublist)
            x_list.append(sub_x_list)
            y_list.append(sub_y_list)
            z_list.append(sub_z_list)

    return x_list, y_list, z_list


def general_op(mat_list, operation):

    if isinstance(mat_list[0], Matrix):

        out_matrix_list = [operation(a) for a in mat_list]

    else:
        out_matrix_list = []
        for sublist in mat_list:
            out_matrix_list.append(general_op(sublist, operation))

    return out_matrix_list

class SvMatrixMathNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Math operation on matrices '''
    bl_idname = 'SvMatrixMathNode'
    bl_label = 'Matrix Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_MATH'

    def update_operation(self, context):
        self.label = "Matrix " + self.operation.title()
        self.update_sockets()
        updateNode(self, context)

    prePost: EnumProperty(
        name='Pre Post',
        description='Order of operations PRE = A op B vs POST = B op A)',
        items=PRE_POST_ITEMS, default="PRE", update=updateNode)

    operation: EnumProperty(
        name="Operation",
        description="Operation to apply on the given matrices",
        items=OPERATION_ITEMS, default="MULTIPLY", update=update_operation)

    filter_t: BoolProperty(
        name="Filter Translation",
        description="Filter out the translation component of the matrix",
        default=False, update=updateNode)

    filter_r: BoolProperty(
        name="Filter Rotation",
        description="Filter out the rotation component of the matrix",
        default=False, update=updateNode)

    filter_s: BoolProperty(
        name="Filter Scale",
        description="Filter out the scale component of the matrix",
        default=False, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', "A")
        self.inputs.new('SvMatrixSocket', "B")

        self.outputs.new('SvMatrixSocket', "C")
        self.outputs.new('SvVerticesSocket', "X")
        self.outputs.new('SvVerticesSocket', "Y")
        self.outputs.new('SvVerticesSocket', "Z")

        self.operation = "MULTIPLY"

    def update_sockets(self):
        # update inputs
        inputs = self.inputs
        if self.operation in {"MULTIPLY"}:  # multiple input operations
            if len(inputs) < 2:  # at least two matrix inputs are available
                if not "B" in inputs:
                    inputs.new("SvMatrixSocket", "B")
        else:  # single input operations (remove all inputs except the first one)
            ss = [s for s in inputs]
            for s in ss:
                if s != inputs["A"]:
                    inputs.remove(s)

        # update outputs
        outputs = self.outputs
        if self.operation == "BASIS":
            for name in list("XYZ"):
                if name not in outputs:
                    outputs.new("SvVerticesSocket", name)
        else:  # remove basis output sockets for all other operations
            for name in list("XYZ"):
                if name in outputs:
                    outputs.remove(outputs[name])

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")
        if self.operation == "MULTIPLY":
            layout.prop(self, "prePost", expand=True)
        elif self.operation == "FILTER":
            row = layout.row(align=True)
            row.prop(self, "filter_t", toggle=True, text="T")
            row.prop(self, "filter_r", toggle=True, text="R")
            row.prop(self, "filter_s", toggle=True, text="S")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "list_match")

    def operation_filter(self, matix_in):
        T, R, S = matix_in.decompose()

        if self.filter_t:
            mat_t = Matrix().Identity(4)
        else:
            mat_t = Matrix().Translation(T)

        if self.filter_r:
            mat_r = Matrix().Identity(4)
        else:
            mat_r = R.to_matrix().to_4x4()

        if self.filter_s:
            mat_s = Matrix().Identity(4)
        else:
            mat_s = Matrix().Identity(4)
            mat_s[0][0] = S[0]
            mat_s[1][1] = S[1]
            mat_s[2][2] = S[2]

        mat_out = mat_t @ mat_r @ mat_s

        return mat_out

    def get_operation(self):
        if self.operation == "MULTIPLY":
            return lambda l: reduce((lambda a, b: a @ b), l)
        if self.operation == "FILTER":
            return self.operation_filter
        if self.operation == "INVERT":
            return lambda a: a.inverted()

        return operation_basis

    def sv_update(self):
        # single input operation ? => no need to update sockets
        if self.operation not in {"MULTIPLY"}:
            return

        # multiple input operation ? => add an empty last socket
        inputs = self.inputs
        if inputs[-1].links:
            name = ABC[len(inputs)]  # pick the next letter A to Z
            inputs.new("SvMatrixSocket", name)
        else:  # last input disconnected ? => remove all but last unconnected extra inputs
            while len(inputs) > 2 and not inputs[-2].links:
                inputs.remove(inputs[-1])

    def process(self):
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        data_in = []  # collect the inputs from the connected sockets
        for s in filter(lambda s: s.is_linked, self.inputs):
            data_in.append(s.sv_get(default=id_mat))

        operation = self.get_operation()

        if self.operation in {"MULTIPLY"}:  # multiple input operations
            desired_levels = [1 for i in data_in]
            ops = [operation, self.prePost]
            list_match_f = list_match_func[self.list_match]
            result = recurse_f_level_control(data_in, ops, matrix_multiply, list_match_f, desired_levels)

            outputs['C'].sv_set(result)

        else:  # single input operations
            mat_list = data_in[0]

            if self.operation == "BASIS":
                x_list, y_list, z_list = recursive_basis_op(mat_list)

                wrap = isinstance(x_list[0][0], (list, tuple))
                outputs['X'].sv_set(x_list if wrap else [x_list])
                outputs['Y'].sv_set(y_list if wrap else [y_list])
                outputs['Z'].sv_set(z_list if wrap else [z_list])
                outputs['C'].sv_set(mat_list)

            else:  # INVERSE / FILTER
                outputs['C'].sv_set(general_op(mat_list, operation))


def register():
    bpy.utils.register_class(SvMatrixMathNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixMathNode)
