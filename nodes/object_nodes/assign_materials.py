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

import numpy as np

import bpy
from bpy.props import StringProperty, IntProperty, CollectionProperty, PointerProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList

class SvMaterialEntry(bpy.types.PropertyGroup):

    def update_material(self, context):
        updateNode(context.node, context)

    material : PointerProperty(type = bpy.types.Material, update=update_material)

class SvMaterialList(bpy.types.PropertyGroup):
    materials : CollectionProperty(type=SvMaterialEntry)
    index : IntProperty()

class SvMaterialUiList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop_search(item, "material", bpy.data, 'materials', text='', icon='MATERIAL_DATA')

class SvAddMaterial(bpy.types.Operator):
    bl_label = "Add material"
    bl_idname = "sverchok.material_index_add"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.materials.add()
        updateNode(node, context)
        return {'FINISHED'}

class SvRemoveMaterial(bpy.types.Operator):
    bl_label = "Remove material"
    bl_idname = "sverchok.material_index_remove"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        idx = node.selected
        node.materials.remove(idx)
        updateNode(node, context)
        return {'FINISHED'}

class SvAssignMaterialListNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: material list
    Tooltip: Assign the list of materials to the object
    """

    bl_idname = 'SvAssignMaterialListNode'
    bl_label = "Assign Materials List"
    bl_icon = 'MATERIAL'

    materials : CollectionProperty(type=SvMaterialEntry)
    selected : IntProperty()

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('SvObjectSocket', 'Object')

    def draw_buttons(self, context, layout):
        layout.template_list("SvMaterialUiList", "materials", self, "materials", self, "selected")
        row = layout.row(align=True)

        add = row.operator('sverchok.material_index_add', text='', icon='ADD')
        add.nodename = self.name
        add.treename = self.id_data.name

        remove = row.operator('sverchok.material_index_remove', text='', icon='REMOVE')
        remove.nodename = self.name
        remove.treename = self.id_data.name

    def assign_materials(self, obj):
        n_existing = len(obj.data.materials)
        for i, material_entry in enumerate(self.materials):
            material = material_entry.material
            if i >= n_existing:
                obj.data.materials.append(material)
            else:
                obj.data.materials[i] = material

    def process(self):
        objects = self.inputs['Object'].sv_get()

        for obj in objects:
            self.assign_materials(obj)
            obj.data.update()

        self.outputs['Object'].sv_set(objects)

classes = [SvMaterialEntry, SvMaterialList, SvMaterialUiList, SvAddMaterial, SvRemoveMaterial, SvAssignMaterialListNode]

def register():
    for name in classes:
        bpy.utils.register_class(name)


def unregister():
    for name in reversed(classes):
        bpy.utils.unregister_class(name)

