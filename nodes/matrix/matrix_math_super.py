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
    ("PRE" , "Pre" , "Calculate A op B", "SORT_ASC", 0),
    ("POST", "Post", "Calculate B op A", "SORT_DESC", 1)
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

class SvMatrixMathSuperNode(SverchCustomTreeNode, bpy.types.Node):
    '''Math operation on matrices.
    In: Matrixes A, B
    Params: Operation [Multiply (Pre/Post)]/Invert/Filter (T,R,S)/Basis
    Out: Matrix, (Basic: X, Y, Z)
    '''
    bl_idname = 'SvMatrixMathSuperNode'
    bl_label = 'Matrix Math Super'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_MATH'

    def update_operation(self, context):
        #self.label = "Matrix " + self.operation.title()
        self.label = "Matrix Super Node"
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

    post_result_basis: BoolProperty(
        name="Basis",
        description="Show result as Basis",
        default=False, update=update_operation)

    result_invert_1: BoolProperty(
        name="Invert",
        description="Invert restult before filter",
        default=False, update=updateNode)

    result_invert_2: BoolProperty(
        name="Invert",
        description="Invert restult post filter",
        default=False, update=updateNode)

    post_result_enabled: BoolProperty(
        name="Enabled",
        description="Do post operation on matrix",
        default=False, update=updateNode)

    result_filter_t: BoolProperty(
        name="Filter Translation",
        description="Filter out the translation component of the matrix",
        default=False, update=updateNode)

    result_filter_r: BoolProperty(
        name="Filter Rotation",
        description="Filter out the rotation component of the matrix",
        default=False, update=updateNode)

    result_filter_s: BoolProperty(
        name="Filter Scale",
        description="Filter out the scale component of the matrix",
        default=False, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)
    
    def draw_C_out_socket(self, socket, context, layout):
        #row1 = layout.row(align=True)
        grid0 = layout.grid_flow(row_major=False, columns=4)
        grid0.alignment = 'RIGHT'
        if socket.is_linked: 
            socket_label = 0
        else:
            socket_label = '-'
        #row1.label(text=f"")

        grid0.prop(self, 'post_result_enabled', text='')
        grid1 = grid0.grid_flow(row_major=False, columns=5, align=True)
        #grid1.prop(self, 'result_invert_1', toggle=True, icon="IMAGE_ALPHA", icon_only=True)
        grid1.prop(self, 'result_invert_1', text="Inv", toggle=True)
        grid2 = grid1.grid_flow(row_major=False, columns=3, align=True)
        grid1.enabled = self.post_result_enabled

        grid2.prop(self, 'result_filter_t', toggle=True, text="", icon_only=True, icon="ORIENTATION_VIEW")
        grid2.prop(self, 'result_filter_r', toggle=True, text="", icon_only=True, icon="PHYSICS")
        grid2.prop(self, 'result_filter_s', toggle=True, text="", icon_only=True, icon="FULLSCREEN_ENTER")
        grid1.prop(self, 'result_invert_2', text="Inv", toggle=True)
        #grid1.prop(self, 'result_invert_2', toggle=True, icon="IMAGE_ALPHA", icon_only=True)
        grid0.prop(self, 'post_result_basis', toggle=True)
        grid0.label(text=f"{socket.label}.{socket_label}") # Почему-то, если делать label под layout, то он выводится с минимальным приоритетом и занимает минимум места

    def sv_init(self, context):
        self.width = 250
        self.inputs.new('SvMatrixSocket', "A")
        self.inputs.new('SvMatrixSocket', "B")

        self.outputs.new('SvMatrixSocket', "C")
        self.outputs.new('SvVerticesSocket', "X")
        self.outputs.new('SvVerticesSocket', "Y")
        self.outputs.new('SvVerticesSocket', "Z")

        self.outputs['C'].custom_draw = 'draw_C_out_socket'
        self.outputs['C'].label = "C"

        self.operation = "MULTIPLY"
        self.result_operAation = "ASIS"

    def update_sockets(self):
        # update inputs
        inputs = self.inputs
        if len(inputs) < 2:  # at least two matrix inputs are available
            if not "B" in inputs:
                inputs.new("SvMatrixSocket", "B")

        # update outputs
        outputs = self.outputs
        if self.post_result_basis:
            for name in list("XYZ"):
                if name not in outputs:
                    outputs.new("SvVerticesSocket", name)
        else:  # remove basis output sockets for all other operations
            for name in list("XYZ"):
                if name in outputs:
                    outputs.remove(outputs[name])

    def draw_buttons(self, context, layout):
        #layout.prop(self, "operation", text="")
        col = layout.row()
        gf = col.grid_flow(row_major=False, columns=2, align=True)
        gf.alignment = 'LEFT'
        gf.prop(self, "prePost", expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "list_match")

    def operation_filter(self, matix_in):
        T, R, S = matix_in.decompose()

        if self.result_filter_t:
            mat_t = Matrix().Identity(4)
        else:
            mat_t = Matrix().Translation(T)

        if self.result_filter_r:
            mat_r = Matrix().Identity(4)
        else:
            mat_r = R.to_matrix().to_4x4()

        if self.result_filter_s:
            mat_s = Matrix().Identity(4)
        else:
            mat_s = Matrix().Identity(4)
            mat_s[0][0] = S[0]
            mat_s[1][1] = S[1]
            mat_s[2][2] = S[2]

        mat_out = mat_t @ mat_r @ mat_s

        return mat_out

    def sv_update(self):
        # add an empty last socket
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
            if s.links[0].is_muted:
                continue
            data_in.append(s.sv_get(default=id_mat))

        operation = lambda l: reduce((lambda a, b: a @ b), l)

        desired_levels = [1 for i in data_in]
        ops = [operation, self.prePost]
        list_match_f = list_match_func[self.list_match]
        result = recurse_f_level_control(data_in, ops, matrix_multiply, list_match_f, desired_levels)

        outputs['C'].sv_set(result)

        mat_list = result # data_in[0]

        # else:  # INVERSE / FILTER
        #     outputs['C'].sv_set(general_op(mat_list, operation))

        if self.post_result_enabled:
            if self.result_invert_1:
                mat_list = general_op(mat_list, lambda a: a.inverted() )
            
            if self.result_filter_t or self.result_filter_r or self.result_filter_s :
                mat_list = general_op(mat_list, self.operation_filter )

            if self.result_invert_2:
                mat_list = general_op(mat_list, lambda a: a.inverted() )


        if self.post_result_basis:
            x_list, y_list, z_list = recursive_basis_op([mat_list])

            wrap = isinstance(x_list[0][0], (list, tuple))
            outputs['X'].sv_set(x_list if wrap else [x_list])
            outputs['Y'].sv_set(y_list if wrap else [y_list])
            outputs['Z'].sv_set(z_list if wrap else [z_list])
            
        outputs['C'].sv_set(mat_list)

def register():
    bpy.utils.register_class(SvMatrixMathSuperNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixMathSuperNode)
