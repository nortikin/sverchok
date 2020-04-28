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
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode

from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.logging import info, debug

class SvMaterialEntry(bpy.types.PropertyGroup):

    def update_material(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            info("Node is not defined in this context, so will not update the node.")

    material : PointerProperty(type = bpy.types.Material, update=update_material)

class SvMaterialList(bpy.types.PropertyGroup):
    materials : CollectionProperty(type=SvMaterialEntry)
    index : IntProperty()

class UI_UL_SvMaterialUiList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        row.prop_search(item, "material", bpy.data, 'materials', text='', icon='MATERIAL_DATA')

        up = row.operator(SvMoveMaterial.bl_idname, text='', icon='TRIA_UP')
        up.nodename = data.name
        up.treename = data.id_data.name
        up.item_index = index
        up.shift = -1

        down = row.operator(SvMoveMaterial.bl_idname, text='', icon='TRIA_DOWN')
        down.nodename = data.name
        down.treename = data.id_data.name
        down.item_index = index
        down.shift = 1

        remove = row.operator(SvRemoveMaterial.bl_idname, text='', icon='REMOVE')
        remove.nodename = data.name
        remove.treename = data.id_data.name
        remove.item_index = index
    
    def draw_filter(self, context, layout):
        pass

class SvAddMaterial(bpy.types.Operator):
    bl_label = "Add material slot"
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
    bl_label = "Remove material slot"
    bl_idname = "sverchok.material_index_remove"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        idx = self.item_index
        node.materials.remove(idx)
        updateNode(node, context)
        return {'FINISHED'}

class SvMoveMaterial(bpy.types.Operator):
    "Move material in the list"

    bl_label = "Move material"
    bl_idname = "sverchok.material_index_shift"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')
    shift : IntProperty(name='shift')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        selected_index = self.item_index
        next_index = selected_index + self.shift
        if (0 <= selected_index < len(node.materials)) and (0 <= next_index < len(node.materials)):
            selected_material = node.materials[selected_index].material
            next_material = node.materials[next_index].material
            node.materials[selected_index].material = next_material
            node.materials[next_index].material = selected_material
            updateNode(node, context)
        return {'FINISHED'}

class SvAssignMaterialListNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    """
    Triggers: material list
    Tooltip: Assign the list of materials to the object
    """

    bl_idname = 'SvAssignMaterialListNode'
    bl_label = "Assign Materials List"
    bl_icon = 'MATERIAL'

    materials : CollectionProperty(type=SvMaterialEntry)
    selected : IntProperty()

    properties_to_skip_iojson = ['materials']

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('SvObjectSocket', 'Object')

    def draw_buttons(self, context, layout):
        self.animatable_buttons(layout, icon_only=True)
        layout.template_list("UI_UL_SvMaterialUiList", "materials", self, "materials", self, "selected")
        row = layout.row(align=True)

        add = row.operator('sverchok.material_index_add', text='', icon='ADD')
        add.nodename = self.name
        add.treename = self.id_data.name


    def assign_materials(self, obj):
        n_existing = len(obj.data.materials)
        if n_existing > len(self.materials):
            obj.data.materials.clear()
            n_existing = 0
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

    def storage_get_data(self, storage):
        materials = [entry.material.name for entry in self.materials]
        storage['materials'] = materials

    def storage_set_data(self, storage):
        for material_name in storage.get('materials', []):
            material = bpy.data.materials.get(material_name)
            if material is None:
                material = bpy.data.materials.new(material_name)
            self.materials.add().material = material

classes = [SvMaterialEntry, SvMaterialList, UI_UL_SvMaterialUiList, SvAddMaterial, SvRemoveMaterial, SvMoveMaterial, SvAssignMaterialListNode]

def register():
    for name in classes:
        bpy.utils.register_class(name)


def unregister():
    for name in reversed(classes):
        bpy.utils.unregister_class(name)

