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

import random

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, EnumProperty

from node_tree import SverchCustomTreeNode, MatrixSocket
from data_structure import dataCorrect, updateNode, SvGetSocketAnyType


class SvObjRemoteNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvObjRemoteNode'
    bl_label = 'Sv Obj Remote'
    bl_icon = 'OUTLINER_OB_EMPTY'

    activate = BoolProperty(
        default=True,
        name='Show', description='Activate node?',
        update=updateNode)

    obj_name = StringProperty(
        default='',
        description='stores the name of the obj this node references',
        update=updateNode)

    input_text = StringProperty(
        default='', update=updateNode)

    show_string_box = BoolProperty()

    def init(self, context):
        self.inputs.new('VerticesSocket', 'location')
        self.inputs.new('VerticesSocket', 'scale')
        self.inputs.new('VerticesSocket', 'rotation')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Update")
        row.prop_search(self, 'obj_name', bpy.data, 'objects', text='', icon='HAND')

        if self.show_string_box:
            row = layout.row(align=True)
            row.prop(self, 'input_text', text='')

    def update(self):
        if not self.activate:
            return

        inputs = self.inputs
        objects = bpy.data.objects

        if self.obj_name in objects:
            obj = objects[self.obj_name]
            obj.location = self.inputs['location'].sv_get()[0][0]
            obj.scale = self.inputs['scale'].sv_get()[0][0]
            obj.rotation_euler = self.inputs['rotation'].sv_get()[0][0]
            self.show_string_box = (obj.type == 'FONT')

            if self.show_string_box:
                print('herrree!!')
                obj.data.body = self.input_text

        else:
            self.show_string_box = 0


def register():
    bpy.utils.register_class(SvObjRemoteNode)
    #bpy.utils.register_class(SvInstancerOp)


def unregister():
    bpy.utils.unregister_class(SvObjRemoteNode)
    #bpy.utils.unregister_class(SvInstancerOp)
