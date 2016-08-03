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
from sverchok.core.update_system import make_tree_from_nodes, do_update

from sverchok.utils.sv_monad_tools import (
    socket_types, reverse_lookup, find_node, 
    average_of_selected, propose_io_locations,
    group_make, SvSocketAquisition,
    set_multiple_attrs,
    SvMoveSocketOpExp,
    SvRenameSocketOpExp,
    SvEditSocketOpExp,
    SvGroupEdit,
    SvTreePathParent
)


class SvGroupNodeExp(Node, SverchCustomTreeNode):
    bl_idname = 'SvGroupNodeExp'
    bl_label = 'Group Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    group_name = StringProperty()

    def sv_init(self, context):
        self.use_custom_color = True
        self.color = (1,1,1)
 
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

        self.use_custom_color = True
        self.color = (1,1,1)

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

        self.use_custom_color = True
        self.color = (1,1,1)


    def get_sockets(self):
        yield self.inputs, "inputs"


class SvCustomGroupInterface(Panel):
    bl_idname = "SvCustomGroupInterface"
    bl_label = "Sv Custom Group Interface"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    # bl_options = {'DEFAULT_CLOSED'}
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


class SvMonadCreateFromSelected(bpy.types.Operator):

    bl_idname = "node.sv_monad_from_selected"
    bl_label = "Create monad from selected nodes (sub graph)"

    group_name = StringProperty(default="Monad")

    def execute(self, context):

        ng = context.space_data.edit_tree
        nodes = [n for n in ng.nodes if n.select]

        if not nodes:
            self.report({"CANCELLED"}, "No nodes selected")
            return {'CANCELLED'}

        parent_node = ng.nodes.new('SvGroupNodeExp')
        parent_node.select = False
        parent_tree = parent_node.id_data
        parent_node.location = average_of_selected(nodes)
        bpy.ops.node.clipboard_copy()

        monad = group_make(parent_node, self.group_name)
        bpy.ops.node.sv_switch_layout(layout_name=monad.name)
        
        # by switching, space_data is now different
        path = context.space_data.path
        path.clear()
        path.append(parent_tree) # below the green opacity layer
        path.append(monad)  # top level

        bpy.ops.node.clipboard_paste()

        # remove nodes from parent_tree
        for n in reversed(nodes):
            parent_tree.nodes.remove(n)

        # move monad IO nodes to bounding box of pasted nodes, and beyond.
        # propose_io_locations(nodes)

        return {'FINISHED'}



classes = [
    SvMoveSocketOpExp,
    SvRenameSocketOpExp,
    SvEditSocketOpExp,
    SvGroupEdit,
    SvTreePathParent,
    SvGroupNodeExp,
    SvGroupInputsNodeExp,
    SvGroupOutputsNodeExp,
    SvCustomGroupInterface,
    SvMonadCreateFromSelected
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
 
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
 