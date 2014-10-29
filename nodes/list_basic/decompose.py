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

from sv_node_tree import SverchCustomTreeNode
from sv_data_structure import (levelsOflist, multi_socket, changable_sockets,
                            get_socket_type_full, SvSetSocket, SvGetSocketAnyType,
                            updateNode)


class SvListDecomposeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' List devided to multiple sockets in some level '''
    bl_idname = 'SvListDecomposeNode'
    bl_label = 'List Decompose'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # two veriables for multi socket input
    base_name = 'data'
    multi_socket_type = 'StringsSocket'

    typ = StringProperty(name='typ',
                         default='')
    newsock = BoolProperty(name='newsock',
                           default=False)
                           
    level = IntProperty(name='level',
                        default=1, min=1, update=updateNode)

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'level')

    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('StringsSocket', "data", "data")

    def update(self):
        if 'data' in self.inputs and self.inputs['data'].links:
            data = SvGetSocketAnyType(self, self.inputs['data'])

            leve = levelsOflist(data)
            if leve+1 < self.level:
                self.level = leve+1
            result = self.beat(data, self.level)
            

            self.multi_socket_type = get_socket_type_full(self, 'data')
            multi_socket(self, min=1, start=2, breck=True, output=len(result))
            outputsocketname = [name.name for name in self.outputs]
            changable_sockets(self, 'data', outputsocketname)

            for i, out in enumerate(result):
                if i > 30:
                    break
                SvSetSocket(self.outputs[i], out)

    def beat(self, data, level, count=1):
        out = []
        if level > 1:
            for objects in data:
                out.extend(self.beat(objects, level-1, count+1))
        else:
            for i in range(count):
                data = [data]
            return data
        return out


def register():
    bpy.utils.register_class(SvListDecomposeNode)


def unregister():
    bpy.utils.unregister_class(SvListDecomposeNode)


if __name__ == '__main__':
    register()