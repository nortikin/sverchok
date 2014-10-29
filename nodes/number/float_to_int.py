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

from sv_node_tree import SverchCustomTreeNode, StringsSocket
from sv_data_structure import SvSetSocketAnyType, SvGetSocketAnyType


class Float2IntNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Float2Int '''
    bl_idname = 'Float2IntNode'
    bl_label = 'Float2int'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('StringsSocket', "float", "float")
        self.outputs.new('StringsSocket', "int", "int")

    def update(self):
        # inputs
        if 'float' in self.inputs and self.inputs['float'].links and \
           type(self.inputs['float'].links[0].from_socket) == StringsSocket:

            Number = SvGetSocketAnyType(self, self.inputs['float'])
        else:
            Number = []

        # outputs
        if 'int' in self.outputs and self.outputs['int'].links:
            result = self.inte(Number)
            SvSetSocketAnyType(self, 'int', result)

    def update_socket(self, context):
        self.update()

    def inte(self, l):
        if type(l) == int or type(l) == float:
            return round(l)
        else:
            return [self.inte(i) for i in l]

    def levels(self, list):
        level = 1
        for n in list:
            if type(n) == list:
                level += self.levels(n)
            return level


def register():
    bpy.utils.register_class(Float2IntNode)


def unregister():
    bpy.utils.unregister_class(Float2IntNode)
