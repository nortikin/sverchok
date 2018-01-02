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

import os
from os.path import join
from glob import glob

import bpy
from bpy.props import StringProperty, BoolProperty

from sverchok.utils.sv_IO_panel_tools import write_json, create_dict_of_tree, import_tree
from sverchok.utils.logging import debug, info, error

def get_presets_directory():
    presets = join(bpy.utils.user_resource('DATAFILES', path='sverchok/presets', create=True))
    if not os.path.exists(presets):
        os.makedirs(presets)
    return presets

def get_preset_path(name):
    presets = get_presets_directory()
    return join(presets, name + ".json")

def get_preset_paths():
    presets = get_presets_directory()
    return list(sorted(glob(join(presets, "*.json"))))

class SvSaveSelected(bpy.types.Operator):
    """
    Save selected nodes as a preset
    """

    bl_idname = "node.sv_save_selected"
    bl_label = "Save selected tree part"
    bl_options = {'INTERNAL'}

    preset_name = StringProperty(name = "Name",
            description = "Preset name")

    id_tree = StringProperty()

    def execute(self, context):
        if not self.id_tree:
            msg = "Node tree is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        if not self.preset_name:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        ng = bpy.data.node_groups[self.id_tree]

        nodes = list(filter(lambda n: n.select, ng.nodes))
        if not len(nodes):
            msg = "There are no selected nodes to export"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        layout_dict = create_dict_of_tree(ng, selected=True)
        destination_path = get_preset_path(self.preset_name)
        write_json(layout_dict, destination_path)
        msg = 'exported to: ' + destination_path
        self.report({"INFO"}, msg)
        info(msg)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class SvRenamePreset(bpy.types.Operator):
    """
    Change the name of preset
    """

    bl_idname = "node.sv_preset_rename"
    bl_label = "Rename"
    bl_options = {'INTERNAL'}

    old_name = StringProperty(name = "Old name",
            description = "Preset name")

    new_name = StringProperty(name = "New name",
            description = "New preset name")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")

    def execute(self, context):
        if not self.old_name:
            msg = "Old preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        if not self.new_name:
            msg = "New preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        old_path = get_preset_path(self.old_name)
        new_path = get_preset_path(self.new_name)

        if os.path.exists(new_path):
            msg = "Preset named `{}' already exists. Refusing to rewrite existing preset.".format(self.new_name)
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        
        os.rename(old_path, new_path)
        info("Renamed `%s' to `%s'", old_path, new_path)
        self.report({'INFO'}, "Renamed `{}' to `{}'".format(self.old_name, self.new_name))

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        self.new_name = self.old_name
        return wm.invoke_props_dialog(self)

class SvDeletePreset(bpy.types.Operator):
    """
    Delete existing preset
    """

    bl_idname = "node.sv_preset_delete"
    bl_label = "Do you really want to delete this preset? This action cannot be undone."
    bl_options = {'INTERNAL'}

    preset_name = StringProperty(name = "Preset name",
            description = "Preset name")

    def execute(self, context):
        if not self.preset_name:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        path = get_preset_path(self.preset_name)

        os.remove(path)
        info("Removed `%s'", path)
        self.report({'INFO'}, "Removed `{}'".format(self.preset_name))

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

class SvUserPresetsPanel(bpy.types.Panel):
    bl_idname = "SvUserPresetsPanel"
    bl_label = "Presets"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'Presets'
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False

    def draw(self, context):
        layout = self.layout
        ntree = context.space_data.node_tree
        panel_props = ntree.preset_panel_properties

        if any(node.select for node in ntree.nodes):
            layout.operator('node.sv_save_selected', text="Save Preset", icon='SAVE_PREFS').id_tree = ntree.name
            layout.separator()

        presets = get_preset_paths()
        if len(presets):
            layout.prop(panel_props, 'manage_mode', toggle=True)
            layout.separator()

        if panel_props.manage_mode:
            layout.label("Manage presets:")
            for path in presets:
                name = os.path.basename(path)
                name,_ = os.path.splitext(name)

                row = layout.row(align=True)
                row.label(text=name)

                rename = row.operator('node.sv_preset_rename', text="Rename")
                rename.old_name = name

                delete = row.operator('node.sv_preset_delete', text="", icon='CANCEL')
                delete.preset_name = name

        else:
            layout.label("Use preset:")
            for path in presets:
                name = os.path.basename(path)
                name,_ = os.path.splitext(name)
                op = layout.operator("node.tree_importer_silent", text=name)
                op.id_tree = ntree.name
                op.filepath = path

class SvUserPresetsPanelProps(bpy.types.PropertyGroup):
    manage_mode = BoolProperty(name = "Manage",
            description = "Presets management mode",
            default = False)

classes = [SvSaveSelected, SvUserPresetsPanelProps, SvRenamePreset, SvDeletePreset, SvUserPresetsPanel]

def register():
    for clazz in classes:
        bpy.utils.register_class(clazz)

    bpy.types.NodeTree.preset_panel_properties = bpy.props.PointerProperty(
        name="preset_panel_properties", type=SvUserPresetsPanelProps)

def unregister():
    del bpy.types.NodeTree.preset_panel_properties

    for clazz in reversed(classes):
        bpy.utils.unregister_class(clazz)

