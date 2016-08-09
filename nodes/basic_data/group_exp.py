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
from sverchok.data_structure import get_other_socket

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


class SvGroupInputsNodeExp(Node, SverchCustomTreeNode, SvSocketAquisition):
    bl_idname = 'SvGroupInputsNodeExp'
    bl_label = 'Group Inputs Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

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

    def sv_init(self, context):
        si = self.inputs.new
        si('SvDummySocket', 'connect me')
        self.node_kind = 'inputs'

        self.use_custom_color = True
        self.color = MONAD_COLOR

    def get_sockets(self):
        yield self.inputs, "inputs"


def draw_node_ops(self, context):

    tree_type = context.space_data.tree_type
    if not (tree_type == 'SverchCustomTreeType'):
        return

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
    SvGroupInputsNodeExp,
    SvGroupOutputsNodeExp,
    SvCustomGroupInterface,
    SvMonadCreateFromSelected
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_add.prepend(draw_node_ops)
    add_keymap()

def unregister():
    remove_keymap()
    bpy.types.NODE_MT_add.remove(draw_node_ops)
    for cls in classes:
        bpy.utils.unregister_class(cls)
