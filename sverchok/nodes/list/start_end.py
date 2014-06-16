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
from bpy.props import BoolProperty, IntProperty, StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, changable_sockets,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class ListFLNode(bpy.types.Node, SverchCustomTreeNode):
    ''' List First and last item of list '''
    bl_idname = 'ListFLNode'
    bl_label = 'List First Last'
    bl_icon = 'OUTLINER_OB_EMPTY'

    level = IntProperty(name='level_to_count',
                        default=2, min=0,
                        update=updateNode)
    typ = StringProperty(name='typ',
                         default='')
    newsock = BoolProperty(name='newsock',
                           default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")

    def init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket', "First", "First")
        self.outputs.new('StringsSocket', "Last", "Last")

    def update(self):
        if 'Data' in self.inputs and len(self.inputs['Data'].links) > 0:
            # адаптивный сокет
            inputsocketname = 'Data'
            outputsocketname = ['First', 'Last']
            changable_sockets(self, inputsocketname, outputsocketname)

        if 'First' in self.outputs and self.outputs['First'].links or \
                'Last' in self.outputs and self.outputs['Last'].links:
            data = SvGetSocketAnyType(self, self.inputs['Data'])

            if 'First' in self.outputs and self.outputs['First'].links:
                out = self.count(data, self.level, True)
                SvSetSocketAnyType(self, 'First', out)
            if 'Last' in self.outputs and self.outputs['Last'].links:
                out = self.count(data, self.level, False)
                SvSetSocketAnyType(self, 'Last', out)

    def count(self, data, level, First):
        if level:
            out = []
            for obj in data:
                out.append(self.count(obj, level-1, First))
        elif type(data) not in [int, float]:
            if First:
                out = [data[0]]
            else:
                out = [data[-1]]
        return out

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ListFLNode)


def unregister():
    bpy.utils.unregister_class(ListFLNode)
