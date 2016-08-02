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
from bpy.props import StringProperty, EnumProperty, IntProperty
from bpy.types import Operator, Node, Panel

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import multi_socket, node_id, replace_socket
from sverchok.core.update_system import make_tree_from_nodes, do_update
import ast


socket_types = [
    ("StringsSocket", "s", "Numbers, polygon data, generic"),
    ("VerticesSocket", "v", "Vertices, point and vector data"),
    ("MatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}


def find_node(id_name, ng):
    for n in ng.nodes:
        if n.bl_idname == id_name:
            return n
    raise NotFoundErr


def set_multiple_attrs(cls_ref, **kwargs):
    for arg_name, value in kwargs.items():
        setattr(cls_ref, arg_name, value)


def get_data(self, context):
    """ expects:
            - self.node_name
            - and self.pos
            - space_data.path to have 2 members, ([1] being the upper visible)
    """
    node = context.space_data.path[1].node_tree.nodes[self.node_name]
    kind = node.node_kind
    socket = getattr(node, kind)[self.pos]
    return node, kind, socket


def get_parent_data(node, kind):
    """
        gets the correct set of sockets on the external (parent) node
    """
    ntree = bpy.data.node_groups[node.parent_tree_name]
    parent_node = ntree.nodes[node.parent_node_name]
    sockets = getattr(parent_node, reverse_lookup.get(kind))
    return sockets


def group_make(self, new_group_name):
    self.node_tree = bpy.data.node_groups.new(new_group_name, 'SverchGroupTreeType')
    self.node_tree['sub_group'] = True
    self.group_name = self.node_tree.name
    nodes = self.node_tree.nodes

    inputnode = nodes.new('SvGroupInputsNodeExp')
    inputnode.location = (-200, 0)
    inputnode.parent_node_name = self.name
    inputnode.parent_tree_name = self.id_data.name

    outputnode = nodes.new('SvGroupOutputsNodeExp')
    outputnode.location = (200, 0)
    outputnode.parent_node_name = self.name
    outputnode.parent_tree_name = self.id_data.name

    return self.node_tree


class SvMoveSocketOpExp(Operator):
    """Move a socket in the direction of the arrow, will wrap around"""
    bl_idname = "node.sverchok_move_socket_exp"
    bl_label = "Move Socket"

    pos = IntProperty()
    direction = IntProperty()
    node_name = StringProperty()

    def execute(self, context):
        node, kind, socket = get_data(self, context)
        parent_sockets = get_parent_data(node, kind)
        IO_node_sockets = getattr(node, kind)
        pos = self.pos

        if self.direction == 0:
            IO_node_sockets.remove(socket)     # I/O interface (subgroup)
            parent_sockets.remove(parent_sockets[pos])
        else:
            def wrap_around(current_idx, direction, member_count):
                return (current_idx + direction) % member_count

            # -1 because subgroup IO interface has a dummysocket appendix
            IO_new_pos = wrap_around(pos, self.direction, len(IO_node_sockets)-1)
            IO_node_sockets.move(pos, IO_new_pos)

            parent_new_pos = wrap_around(pos, self.direction, len(parent_sockets))
            parent_sockets.move(pos, parent_new_pos)

        return {"FINISHED"}


class SvRenameSocketOpExp(Operator):
    """Rename a socket"""
    bl_idname = "node.sverchok_rename_socket_exp"
    bl_label = "Rename Socket"

    pos = IntProperty()
    node_name = StringProperty()
    new_name = StringProperty()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'new_name', text='(new) name')

    def execute(self, context):
        # make changes to this node's socket name
        node, kind, socket = get_data(self, context)
        socket.name = self.new_name

        # make changes to parent node's socket name in parent tree
        sockets = get_parent_data(node, kind)
        sockets[self.pos].name = self.new_name
        return {"FINISHED"}
 
    def invoke(self, context, event):
        _, _, socket = get_data(self, context)
        self.new_name = socket.name
        return context.window_manager.invoke_props_dialog(self)


class SvEditSocketOpExp(Operator):
    """Edit a socket signature"""
    bl_idname = "node.sverchok_edit_socket_exp"
    bl_label = "Edit Socket"

    node_name = StringProperty()
    pos = IntProperty()
    socket_type = EnumProperty(
        items=socket_types, default="StringsSocket")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'socket_type', text='Socket Type')

    def execute(self, context):
        # make changes to this node's socket name
        node, kind, socket = get_data(self, context)

        # make changes to parent node's socket name in parent tree
        parent_sockets = get_parent_data(node, kind)
        parent_socket = parent_sockets[self.pos]

        # replace socket types of subgroup IO and parent node
        for s in [socket, parent_socket]:
            replace_socket(s, self.socket_type)

        return {"FINISHED"}

    def invoke(self, context, event):
        _, _, socket = get_data(self, context)
        self.socket_type = socket.bl_idname
        return context.window_manager.invoke_props_dialog(self)

class SvGroupEdit(Operator):
    bl_idname = "node.sv_group_edit"
    bl_label = "edits an sv group"
    
    group_name = StringProperty()
    
    def execute(self, context):
        node = context.node
        parent_tree_name = node.id_data.name
        ng = bpy.data.node_groups

        group_node = ng.get(self.group_name)
        if not group_node:
            group_node = group_make(node, new_group_name=self.group_name)
        
        bpy.ops.node.sv_switch_layout(layout_name=self.group_name)
        
        # by switching, space_data is now different
        path = context.space_data.path
        path.clear()
        path.append(ng[parent_tree_name]) # below the green opacity layer
        path.append(ng[self.group_name])  # top level

        return {"FINISHED"}


class SvTreePathParent(Operator):
    '''Go to parent node tree'''
    bl_idname = "node.sv_tree_path_parent"
    bl_label = "Parent Sv Node Tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and len(space.path) > 1

    def execute(self, context):
        space = context.space_data
        space.path.pop()
        context.space_data.node_tree = space.path[0].node_tree
        return {'FINISHED'}


class SvSocketAquisition:

    socket_map = {'outputs': 'to_socket', 'inputs': 'from_socket'}
    node_kind = StringProperty()

    def update(self):
        kind = self.node_kind
        if not kind:
            return

        socket_list = getattr(self, kind)
        _socket = self.socket_map.get(kind) # from_socket, to_socket
        _puts = reverse_lookup.get(kind) # inputs, outputs

        if socket_list[-1].is_linked:

            # first switch socket type
            socket = socket_list[-1]
            links = socket.links[0]
            linked_socket = getattr(links, _socket)
            new_type = linked_socket.bl_idname

            # if no 'linked_socket.prop_name' then use 'linked_socket.name'
            socket_prop_name = getattr(linked_socket, 'prop_name')
            
            no_prop_name = (not socket_prop_name or len(socket_prop_name) == 0)
            if no_prop_name:
                new_name = linked_socket.name
            else:
                new_name = socket_prop_name

            new_name = new_name.replace('_', ' ').strip() # more elaborate sanitizing needed?
            replace_socket(socket, new_type, new_name=new_name)

            # add new input socket to parent node
            parent_tree = bpy.data.node_groups[self.parent_tree_name].nodes
            parent_node = parent_tree[self.parent_node_name]
            sok = getattr(parent_node, _puts).new(new_type, new_name)


            # add new dangling dummy
            socket_list.new('SvDummySocket', 'connect me')


class SvGroupNodeExp(Node, SverchCustomTreeNode):
    bl_idname = 'SvGroupNodeExp'
    bl_label = 'Group Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    group_name = StringProperty()
 
    def update(self):
        ''' Override inherited '''
        pass
        
    def draw_buttons_ext(self, context, layout):
        pass
            
    def draw_buttons(self, context, layout):
        c = layout.column()
        c.prop(self, 'group_name', text='name')

        d = layout.column()
        d.active = bool(self.group_name)
        f = d.operator('node.sv_group_edit', text='edit!')
        f.group_name = self.group_name

    def process(self):
        if not self.group_name:
            return

        group_ng = bpy.data.node_groups[self.group_name]
        in_node = find_node("SvGroupInputsNodeExp", group_ng)
        out_node = find_node("SvGroupOutputsNodeExp", group_ng)
        for index, socket in enumerate(self.inputs):
            if socket.is_linked:
                data = socket.sv_get(deepcopy=False)
                in_node.outputs[index].sv_set(data)
        #  get update list
        #  could be cached
        ul = make_tree_from_nodes([out_node.name], group_ng, down=False)
        do_update(ul, group_ng.nodes)
        # set output sockets correctly
        for index, socket in enumerate(self.outputs):
            if socket.is_linked:
                data = out_node.inputs[index].sv_get(deepcopy=False)
                socket.sv_set(data)
    
    def load(self):
        pass
    

class SvGroupInputsNodeExp(Node, SverchCustomTreeNode, SvSocketAquisition):
    bl_idname = 'SvGroupInputsNodeExp'
    bl_label = 'Group Inputs Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    parent_node_name = bpy.props.StringProperty()
    parent_tree_name = bpy.props.StringProperty()

    def sv_init(self, context):
        si = self.outputs.new
        si('SvDummySocket', 'connect me')
        self.node_kind = 'outputs'

    def get_sockets(self):
        yield self.outputs, "outputs"


class SvGroupOutputsNodeExp(Node, SverchCustomTreeNode, SvSocketAquisition):
    bl_idname = 'SvGroupOutputsNodeExp'
    bl_label = 'Group Outputs Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    parent_node_name = bpy.props.StringProperty()
    parent_tree_name = bpy.props.StringProperty()

    def sv_init(self, context):
        si = self.inputs.new
        si('SvDummySocket', 'connect me')
        self.node_kind = 'inputs'

    def get_sockets(self):
        yield self.inputs, "inputs"


class SvCustomGroupInterface(Panel):
    bl_idname = "SvCustomGroupInterface"
    bl_label = "Sv Custom Group Interface"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    bl_options = {'DEFAULT_CLOSED'}
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            path = context.space_data.path
            return len(path) == 2 and path[1].node_tree.get('sub_group')
        except:
            return False

    def draw(self, context):
        ntree = context.space_data.edit_tree
        nodes = ntree.nodes

        layout = self.layout
        row = layout.row()

        # draw left and right columns corresponding to sockets_types, display_name, move_operator
        in_node = nodes.get('Group Inputs Exp')
        out_node = nodes.get('Group Outputs Exp')
        
        if not (in_node and out_node):
            return

        width = context.region.width
        # should ideally take dpi into account, 
        if width > 310:
            row = layout.row()
            split = row.split(percentage=0.5)
            column1 = split.box().column()
            split = split.split()
            column2 = split.box().column()
        else:
            column1 = layout.row().box().column()
            layout.separator()
            column2 = layout.row().box().column()

        move = 'node.sverchok_move_socket_exp'
        rename = 'node.sverchok_rename_socket_exp'
        edit = 'node.sverchok_edit_socket_exp'

        def draw_socket_row(_column, s, index):
            if s.bl_idname == 'SvDummySocket':
                return

            """ type | (re)name     | /\  \/  X  """
            
            # lots of repetition here...
            socket_ref = dict(pos=index, node_name=s.node.name)

            r = _column.row(align=True)
            r.template_node_socket(color=s.draw_color(s.node, context))

            m = r.operator(edit, icon='PLUGIN', text='')
            set_multiple_attrs(m, **socket_ref)

            m = r.operator(rename, text=s.name)
            set_multiple_attrs(m, **socket_ref)

            m = r.operator(move, icon='TRIA_UP', text='')
            set_multiple_attrs(m, **socket_ref, direction=-1)
            
            m = r.operator(move, icon='TRIA_DOWN', text='')
            set_multiple_attrs(m, **socket_ref, direction=1)

            m = r.operator(move, icon='X', text='')
            set_multiple_attrs(m, **socket_ref, direction=0)


        column1.label('inputs')
        for i, s in enumerate(in_node.outputs):
            draw_socket_row(column1, s, i)

        column2.label('outputs')
        for i, s in enumerate(out_node.inputs):
            draw_socket_row(column2, s, i)


classes = [
    SvMoveSocketOpExp,
    SvRenameSocketOpExp,
    SvEditSocketOpExp,
    SvGroupEdit,
    SvTreePathParent,
    SvGroupNodeExp,
    SvGroupInputsNodeExp,
    SvGroupOutputsNodeExp,
    SvCustomGroupInterface
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
 
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
 