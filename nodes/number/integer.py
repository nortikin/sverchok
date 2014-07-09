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
from bpy.props import IntProperty
from node_tree import SverchCustomTreeNode
from data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType


class IntegerNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Integer '''
    bl_idname = 'IntegerNode'
    bl_label = 'Integer'
    bl_icon = 'OUTLINER_OB_EMPTY'

    int_ = IntProperty(name='Int', description='integer number',
                       default=1,
                       options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Integer", "Integer").prop_name = 'int_'
        self.outputs.new('StringsSocket', "Integer", "Integer")

    def update(self):
        # inputs
        if 'Integer' in self.inputs and self.inputs['Integer'].links:
            tmp = SvGetSocketAnyType(self, self.inputs['Integer'])
            Integer = tmp[0][0]
        else:
            Integer = self.int_

        # outputs
        if 'Integer' in self.outputs and self.outputs['Integer'].links:
            SvSetSocketAnyType(self, 'Integer', [[Integer]])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(IntegerNode)


def unregister():
    bpy.utils.unregister_class(IntegerNode)
