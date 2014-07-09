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
from bpy.props import FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType


class FloatNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Float '''
    bl_idname = 'FloatNode'
    bl_label = 'Float'
    bl_icon = 'OUTLINER_OB_EMPTY'

    float_ = FloatProperty(name='Float', description='float number',
                           default=1.0,
                           options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'float_'
        self.outputs.new('StringsSocket', "Float")

    def update(self):
        # inputs
        if 'Float' in self.inputs and self.inputs['Float'].links:
            tmp = SvGetSocketAnyType(self, self.inputs['Float'])
            Float = tmp[0][0]
        else:
            Float = self.float_
        # outputs
        if 'Float' in self.outputs and self.outputs['Float'].links:
            SvSetSocketAnyType(self, 'Float', [[Float]])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(FloatNode)


def unregister():
    bpy.utils.unregister_class(FloatNode)
