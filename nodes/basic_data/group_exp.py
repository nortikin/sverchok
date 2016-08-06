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
from bpy.types import Node

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.core.update_system import make_tree_from_nodes, do_update

from sverchok.ui.sv_monad_panel import SvCustomGroupInterface
from sverchok.ui.nodeview_keymaps import add_keymap, remove_keymap

from sverchok.utils.sv_monad_tools import (
    find_node,
    SvSocketAquisition,
    SvMoveSocketOpExp,
    SvRenameSocketOpExp,
    SvEditSocketOpExp,
    SvGroupEdit,
    SvTreePathParent,
    SvMonadCreateFromSelected
)

MONAD_COLOR = (0.4, 0.9, 1)


class SvGroupNodeExp(Node, SverchCustomTreeNode):
    bl_idname = 'SvGroupNodeExp'
    bl_label = 'Group Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    group_name = StringProperty()

    def sv_init(self, context):
        self.use_custom_color = True
        self.color = MONAD_COLOR
 
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
        self.color = MONAD_COLOR

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
        self.color = MONAD_COLOR

    def get_sockets(self):
        yield self.inputs, "inputs"


def draw_node_ops(self, context):
    layout = self.layout
    layout.separator()
    # layout.operator("node.sv_group_edit")
    # layout.operator("node.group_ungroup")
    make_monad = "node.sv_monad_from_selected"
    layout.operator(make_monad, text='make group (+relink)', icon='RNA')
    layout.operator(make_monad, text='make group', icon='RNA').use_relinking = False
    # layout.operator("node.group_insert")
    layout.separator()    


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
    bpy.types.NODE_MT_add.prepend(draw_node_ops)
    # add_keymap()
 
def unregister():
    # remove_keymap()
    bpy.types.NODE_MT_add.remove(draw_node_ops)
    for cls in classes:
        bpy.utils.unregister_class(cls)
 