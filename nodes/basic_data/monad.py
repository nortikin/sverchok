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

# the concrete monad classes plus common base

import bpy
from bpy.types import Node
from bpy.props import StringProperty

from sverchok.data_structure import replace_socket
from sverchok.node_tree import SverchCustomTreeNode

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}


MONAD_COLOR = (0.4, 0.9, 1)


class SvSocketAquisition:

    socket_map = {'outputs': 'to_socket', 'inputs': 'from_socket'}
    node_kind = StringProperty()

    def update(self):
        kind = self.node_kind
        if not kind:
            return

        monad = self.id_data
        if monad.bl_idname == "SverchCustomTreeType":
            return

        socket_list = getattr(self, kind)
        _socket = self.socket_map.get(kind) # from_socket, to_socket

        if socket_list[-1].is_linked:

            # first switch socket type
            socket = socket_list[-1]

            cls = monad.update_cls()

            if kind == "outputs":
                new_name, new_type, prop_data = cls.input_template[-1]
            else:
                new_name, new_type = cls.output_template[-1]
                prop_data = {}

            # if no 'linked_socket.prop_name' then use 'linked_socket.name'
            replace_socket(socket, new_type, new_name=new_name)

            for instance in monad.instances:
                sockets = getattr(instance, reverse_lookup[kind])
                new_socket = sockets.new(new_type, new_name)
                for name, value in prop_data.items():
                    setattr(new_socket, name, value)

            # add new dangling dummy
            socket_list.new('SvDummySocket', 'connect me')



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
    SvGroupInputsNodeExp,
    SvGroupOutputsNodeExp,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
