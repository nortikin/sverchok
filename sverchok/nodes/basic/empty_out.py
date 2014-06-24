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
from mathutils import Matrix
from bpy.props import StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvGetSocketAnyType, node_id, Matrix_generate


class SvEmptyOutNode(bpy.types.Node, SverchCustomTreeNode):
    '''Create a blender empty object'''
    bl_idname = 'SvEmptyOutNode'
    bl_label = 'Set Empty'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def rename_empty(self, context):
        empty = self.find_empty()
        if empty:
            empty.name = self.empty_name
            self.label = empty.name

    n_id = StringProperty(default='')
    empty_name = StringProperty(default='Sv empty', name="Base name",
                                description="Base name of empty",
                                update=rename_empty)
    obj_name = StringProperty(default='')

    def create_empty(self):
        n_id = node_id(self)
        scene = bpy.context.scene
        objects = bpy.data.objects
        empty = objects.new(self.empty_name, None)
        scene.objects.link(empty)
        scene.update()
        empty["SVERCHOK_REF"] = n_id
        return empty

    def init(self, context):
        self.create_empty()
        self.inputs.new('MatrixSocket', "Matrix")
        
    def find_empty(self):
        n_id = node_id(self)
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY':
                if "SVERCHOK_REF" in obj and obj["SVERCHOK_REF"] == n_id:
                    return obj
        return None

    def draw_buttons(self, context, layout):
        layout.label("Base name")
        row = layout.row()
        row.scale_y = 1.1
        row.prop(self, "empty_name", text="")

    def update(self):
        if not "Matrix" in self.inputs:
            return
        # startup safety net
        try:
            l = bpy.data.node_groups[self.id_data.name]
        except:
            print(self.name, "cannot run during startup, press update.")
            return

        empty = self.find_empty()
        if not empty:
            empty = self.create_empty()
            print("created new empty")

        if self.inputs['Matrix'].links:
            mats = SvGetSocketAnyType(self, self.inputs['Matrix'])
            mat = Matrix_generate(mats)[0]
        else:
            mat = Matrix()
        self.label = empty.name
        empty.matrix_world = mat

    def copy(self, node):
        self.n_id = ''
        empty = self.create_empty()
        self.label = empty.name

def register():
    bpy.utils.register_class(SvEmptyOutNode)


def unregister():
    bpy.utils.unregister_class(SvEmptyOutNode)
