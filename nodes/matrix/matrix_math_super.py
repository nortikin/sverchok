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

from contextlib import contextmanager
from functools import reduce
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty

from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.data_structure import (updateNode, list_match_func, numpy_list_match_modes, node_id)
from sverchok.utils.sv_itertools import (recurse_f_level_control)
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator


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

def draw_matrix(context, args):
    """ this takes one or more matrices packed into an iterable """
    matrices, scale, grid = args

    mdraw = MatrixDraw28()
    for matrix in matrices:
        mdraw.draw_matrix(matrix, grid=grid, scale=scale)

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

@contextmanager
def suspend_sv_update(node):
    node.sv_update_lock = getattr(node, "sv_update_lock", 0) + 1
    try:
        yield
    finally:
        node.sv_update_lock -= 1

class SvMatrixSocketAction(bpy.types.Operator, SvGenericNodeLocator):
    '''Add Matrix to diagonal ones'''
    bl_idname = "node.sverchok_sv_add_matrix_socket_above"
    bl_label = "Add Matrix socket above"
    bl_description = "Add Matrix socket above"

    socket_label: bpy.props.StringProperty()
    socket_action: bpy.props.EnumProperty(
        name = "socket action",
        description = "socket action",
        items = [
            ("ADD_ABOVE", "add above", "add above", 0),
            ("REMOVE_CURRENT", "remove current", "remove current", 1),
        ],
        default = "ADD_ABOVE"
    )
    
    def sv_execute(self, context, node):
        # if hasattr(node, 'matrix_list_items')==True:
        #     node.matrix_list_items[self.idx].MATRIX_UI = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
        print( f"{self.socket_action}: {self.socket_label}")

        if self.socket_action in ['ADD_ABOVE', 'REMOVE_CURRENT']:
            pass
        else:
            print( f"{self.socket_action}: no action")
            return
        
        with suspend_sv_update(node):
            nodeTree = node.id_data
            inputs = node.inputs
            len_inputs = len(inputs)

            if self.socket_action=='ADD_ABOVE':
                # Проверить количество запасных индексов (хотя такой поход не очень, но это нужно иначе переделать систему индексов)
                if len_inputs>=len(ABC):
                    # Больше индексов нет
                    return

            # Определить кто подключен от текущего сокета и ниже и попутно удалить их:
            reconnect_links = []
            for I in range(len_inputs-1, -1, -1):
                print(f"{I},", end='')
                socket = inputs[I]
                socket_name = socket.name
                if len(socket.links)==0:
                    reconnect_links.append(dict({"to_socket_name":socket_name}))
                    pass
                else:
                    from_socket = socket.links[0].from_socket
                    to_socket = socket.links[0].to_socket
                    reconnect_links.append(dict({"to_socket_name":to_socket.name, "from_socket":from_socket, }))
                
                is_top_socket = False
                if socket.label==self.socket_label:
                    is_top_socket = True
                if socket.is_linked==True:
                    from_socket = socket.links[0].from_socket
                    to_socket = socket.links[0].to_socket
                    for link in list(nodeTree.links):
                        if link.from_socket == from_socket and link.to_socket == to_socket:
                            nodeTree.links.remove(link)
                            break
                    else:
                        # Странно, что сокет не найден. Пока не знаю как обрабатывать
                        pass
                if socket_name in inputs:
                    inputs.remove(inputs[socket_name])
                if is_top_socket:
                    break
            
            if self.socket_action=='ADD_ABOVE':
                # Создать новые сокеты (на одного больше удалённых):
                for I in range(len(node.inputs), len_inputs+1):
                    name = ABC[I]  # pick the next letter A to Z
                    inputs.new("SvMatrixSocket", name)
                    inputs[name].label=name
                    inputs[name].custom_draw = 'draw_in_matrix_socket'
                name = ABC[len_inputs]
                reconnect_links.insert(0, dict({"to_socket_name":name}))

                # Переподключить сокеты на один ниже:
                for I in range(1, len(reconnect_links)):
                    if "from_socket" not in reconnect_links[I]:
                        # Если в списке сокетов только метка, то его не надо подключать никуда
                        continue
                    from_socket = reconnect_links[I]["from_socket"]
                    to_socket_name = reconnect_links[I-1]["to_socket_name"]
                    nodeTree.links.new(from_socket, inputs[to_socket_name])
            elif self.socket_action=='REMOVE_CURRENT':
                # Если ниже удаляемого сокета не было больше никаких подключенных сокетов, то не выполнять переподключения,
                # т.к. все пустые сокеты схлопнулись до предпоследнего сокета или до минимума из двух сокетов:
                len_reconnect_links = len(reconnect_links)
                link_exists = False
                for I in range( len_reconnect_links-1 ):
                    if "from_socket" in reconnect_links[I]:
                        link_exists=True
                        break
                    pass
                
                if link_exists:
                    # Если ниже удаляемого сокета были линки, то нужно пересоздать структуру с переподключением на 1 выше.
                    # Создать новые сокеты (на одного меньше, кроме удаляемого):
                    for I in range(len(node.inputs), len_inputs-1):
                        name = ABC[I]  # pick the next letter A to Z
                        inputs.new("SvMatrixSocket", name)
                        inputs[name].label=name
                        inputs[name].custom_draw = 'draw_in_matrix_socket'
                    # Сокетов должно быть не меньше 2-х:
                    while(len(inputs)<2):
                        name = ABC[len(inputs)]  # pick the next letter A to Z
                        inputs.new("SvMatrixSocket", name)
                        inputs[name].label=name
                        inputs[name].custom_draw = 'draw_in_matrix_socket'

                    # Переподключить сокеты на один выше:
                    for I in range( len_reconnect_links-1 ):
                        if "from_socket" not in reconnect_links[I]:
                            # Если в списке сокетов только метка, то его не надо подключать никуда
                            continue
                        from_socket = reconnect_links[I]["from_socket"]
                        to_socket_name = reconnect_links[I+1]["to_socket_name"]
                        nodeTree.links.new(from_socket, inputs[to_socket_name])
                    # проверить, если последний сокет не пустой, то добавить пустой сокет
                else:
                    pass
            else:
                print( f"{self.socket_action}: no action")
            pass
        node.sv_update()
        pass

class SvMatrixMathSuperNode(SverchCustomTreeNode, bpy.types.Node):
    '''Math operation on matrices.
    In: Matrixes A, B
    Params: Operation [Multiply (Pre/Post)]/Invert/Filter (T,R,S)/Basis
    Out: Matrix, (Basic: X, Y, Z)
    '''
    bl_idname = 'SvMatrixMathSuperNode'
    bl_label = 'Matrix Math Ext'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_MATH'

    def wrapper_MatrixSocket_op(self, layout_element, operator_idname, idx, soket_action, **keywords):
        """
        this wrapper allows you to track the origin of a clicked operator, by automatically passing
        the node_name and tree_name to the operator.

        example usage:

            row.separator()
            self.wrapper_tracked_ui_draw_op(row, "node.view3d_align_from", icon='CURSOR', text='')

        """
        op = layout_element.operator(operator_idname, **keywords)
        op.node_name = self.name
        op.tree_name = self.id_data.name
        op.socket_label = idx
        op.socket_action = soket_action
        return op


    def update_operation(self, context):
        #self.label = "Matrix " + self.operation.title()
        self.label = "Matrix Math Ext"
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

    post_result_matrix_view: BoolProperty(
        name="Show Matrix",
        description="Show Result Matrix on the scene",
        default=False, update=updateNode)
    
    post_result_matrix_scale_view: FloatProperty(
        name="Matrix View Scale",
        description="Matrix View Scale on the scene",
        min=0.0,
        default=1.0,
        update=updateNode)

    post_result_matrix_grid_view: BoolProperty(
        name="Grid",
        description="Matrix View Scale On/Off",
        default=True,
        update=updateNode)

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

    def draw_in_matrix_socket(self, socket, context, layout):
        if socket.is_linked: 
            socket_object_number = socket.objects_number
        else:
            socket_object_number = '-'

        grid0 = layout.grid_flow(row_major=False, columns=3, align=True, even_columns=False)
        if socket.is_linked==False:
            grid0.operator('node.sv_quicklink_new_node_input', text="", icon="PLUGIN")
        else:
            self.wrapper_MatrixSocket_op(grid0, SvMatrixSocketAction.bl_idname, socket.label, 'ADD_ABOVE', text="", icon='EMPTY_SINGLE_ARROW', emboss =True)
        grid0.label(text=f"{socket.label}. {socket_object_number}")
        self.wrapper_MatrixSocket_op(grid0, SvMatrixSocketAction.bl_idname, socket.label, 'REMOVE_CURRENT', text="", icon='PANEL_CLOSE', emboss =True)

        pass

    def draw_C_out_socket(self, socket, context, layout):
        #row1 = layout.row(align=True)
        grid0 = layout.grid_flow(row_major=False, columns=4)
        grid0.alignment = 'RIGHT'
        if socket.is_linked: 
            socket_object_number = socket.objects_number
        else:
            socket_object_number = '-'
        #row1.label(text=f"")

        # grid0.prop(self, 'post_result_enabled', text='')
        # grid1 = grid0.grid_flow(row_major=False, columns=5, align=True)
        # #grid1.prop(self, 'result_invert_1', toggle=True, icon="IMAGE_ALPHA", icon_only=True)
        # grid1.prop(self, 'result_invert_1', text="Inv", toggle=True)
        # grid2 = grid1.grid_flow(row_major=False, columns=3, align=True)
        # grid1.enabled = self.post_result_enabled

        # grid2.prop(self, 'result_filter_t', toggle=True, text="", icon_only=True, icon="ORIENTATION_VIEW")
        # grid2.prop(self, 'result_filter_r', toggle=True, text="", icon_only=True, icon="PHYSICS")
        # grid2.prop(self, 'result_filter_s', toggle=True, text="", icon_only=True, icon="FULLSCREEN_ENTER")
        # grid1.prop(self, 'result_invert_2', text="Inv", toggle=True)
        # #grid1.prop(self, 'result_invert_2', toggle=True, icon="IMAGE_ALPHA", icon_only=True)
        grid0.prop(self, 'post_result_basis', toggle=True)
        grid0.label(text=f"{socket.label}.{socket_object_number}") # Почему-то, если делать label под layout, то он выводится с минимальным приоритетом и занимает минимум места

    def sv_init(self, context):
        self.width = 250
        self.inputs.new('SvMatrixSocket', "A")
        self.inputs.new('SvMatrixSocket', "B")
        self.inputs["A"].label="A"
        self.inputs["B"].label="B"
        self.inputs["A"].custom_draw = 'draw_in_matrix_socket'
        self.inputs["B"].custom_draw = 'draw_in_matrix_socket'

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
        row = layout.row()
        grid0 = layout.grid_flow(row_major=False, columns=3, align=True)
        grid0.prop(self, 'post_result_matrix_view', text='')
        grid0.prop(self, 'post_result_matrix_scale_view', text='Scale')
        grid0.prop(self, 'post_result_matrix_grid_view')

        grid0 = layout.grid_flow(row_major=False, columns=4)
        grid0.alignment = 'RIGHT'
        grid0.prop(self, 'post_result_enabled', text='')
        grid1 = grid0.grid_flow(row_major=False, columns=5, align=False)
        grid1.prop(self, 'result_invert_1', text="Inv", toggle=True)
        grid2 = grid1.grid_flow(row_major=False, columns=3, align=True)
        grid1.enabled = self.post_result_enabled

        grid2.prop(self, 'result_filter_t', toggle=True, text="", icon_only=True, icon="ORIENTATION_VIEW")
        grid2.prop(self, 'result_filter_r', toggle=True, text="", icon_only=True, icon="PHYSICS")
        grid2.prop(self, 'result_filter_s', toggle=True, text="", icon_only=True, icon="FULLSCREEN_ENTER")
        grid1.prop(self, 'result_invert_2', text="Inv", toggle=True)


        row = layout.row()
        gf = row.grid_flow(row_major=False, columns=2, align=True)
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

    sv_update_lock: IntProperty(
        name="sv_update_lock",
        description="sv_update_lock",
        default=0,
        options={'SKIP_SAVE'}
    )

    def sv_update(self):
        if self.sv_update_lock==0:
            # add an empty last socket
            inputs = self.inputs
            if inputs[-1].links:
                name = ABC[len(inputs)]  # pick the next letter A to Z
                inputs.new("SvMatrixSocket", name)
                inputs[name].label=name
                inputs[name].custom_draw = 'draw_in_matrix_socket'
            else:  # last input disconnected ? => remove all but last unconnected extra inputs
                while len(inputs) > 2 and not inputs[-2].links:
                    inputs.remove(inputs[-1])
        else:
            pass

    def process(self):
        outputs = self.outputs
        # if not any(s.is_linked for s in outputs):
        #     return

        n_id = node_id(self)
        callback_disable(n_id)

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

        if self.post_result_matrix_view and mat_list:
            gl_instructions = {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_matrix,
                'args': (mat_list, self.post_result_matrix_scale_view, self.post_result_matrix_grid_view)}
            callback_enable(n_id, gl_instructions)
            
        outputs['C'].sv_set(mat_list)

classes = [SvMatrixSocketAction, SvMatrixMathSuperNode]
register, unregister = bpy.utils.register_classes_factory(classes)