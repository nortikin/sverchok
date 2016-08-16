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
    SvSocketAquisition,
    SvMoveSocketOpExp,
    SvRenameSocketOpExp,
    SvEditSocketOpExp,
    SvGroupEdit,
    SvMonadEnter,
    SvTreePathParent,
    SvMonadCreateFromSelected,
    SverchGroupTree,
    SvMonadExpand
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


classes = [
    SvMoveSocketOpExp,
    SvRenameSocketOpExp,
    SvEditSocketOpExp,
    SvGroupEdit,
    SvMonadEnter,
    SvMonadExpand,
    SvTreePathParent,
    SvGroupInputsNodeExp,
    SvGroupOutputsNodeExp,
    SvCustomGroupInterface,
    SvMonadCreateFromSelected,
    SverchGroupTree
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    add_keymap()

def unregister():
    remove_keymap()
    for cls in classes:
        bpy.utils.unregister_class(cls)
