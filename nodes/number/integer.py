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
from bpy.props import IntProperty, BoolProperty
from sv_node_tree import SverchCustomTreeNode
from sv_data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType


class IntegerNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Integer '''
    bl_idname = 'IntegerNode'
    bl_label = 'Integer'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def update_value(self, context):
        if self.int_ < self.minim:
            self.int_ = self.minim
            return
        if self.int_ > self.maxim:
            self.int_ = self.maxim
            return
        updateNode(self, context)
        
    def update_max(self, context):
        if self.maxim < self.minim:
            self.maxim = self.minim + 1
            return
        if self.int_ > self.maxim:
            self.int_ = self.maxim
    
    def update_min(self, context):
        if self.minim > self.maxim:
            self.minim = self.maxim - 1
            return
        if self.int_ < self.minim:
            self.int_ = self.minim
        
    int_ = IntProperty(name='Int', description='integer number',
                       default=1,
                       options={'ANIMATABLE'}, update=update_value)
    maxim = IntProperty(name='max', description='maximum',
                       default=1000,
                       update=update_max)
    minim = IntProperty(name='min', description='minimum',
                       default=-1000,
                       update=update_min)
    to3d = BoolProperty(name='to3d', description='show in 3d panel',
                       default=True)

    def draw_label(self):
        if not self.inputs[0].links:
            return str(self.int_)
        else:
            return self.bl_label
    
    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'minim')
        row.prop(self, 'maxim')
        row = layout.row(align=True)
        row.prop(self, 'to3d')

    def init(self, context):
        self.inputs.new('StringsSocket', "Integer", "Integer").prop_name = 'int_'
        self.outputs.new('StringsSocket', "Integer", "Integer")

    def update(self):
        # inputs
        if 'Integer' in self.inputs and self.inputs['Integer'].links:
            tmp = SvGetSocketAnyType(self, self.inputs['Integer'])
            Integer = min(max(int(tmp[0][0]), self.minim), self.maxim)
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

if __name__ == '__main__':
    register()



