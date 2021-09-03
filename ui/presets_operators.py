# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import os
import json
import shutil
from glob import glob
from os.path import join, isdir, basename, dirname

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty

from sverchok.utils import sv_gist_tools
from sverchok.utils import sv_IO_panel_tools
from sverchok.utils.sv_json_import import JSONImporter
from sverchok.utils.sv_json_export import JSONExporter
from sverchok.utils.logging import debug, info, error, exception
from sverchok.ui.presets import (
	SvPreset, 
	get_category_items_all,
	get_category_names,
	get_preset_path,
	get_presets_directory,
	GENERAL
)

class SvPresetReplace(bpy.types.Operator):
    """Load node settings from preset"""
    bl_idname = "node.sv_preset_replace_node"
    bl_label = "Load node settings from preset"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    node_name : StringProperty()
    preset_path : StringProperty()
    preset_name : StringProperty()

    @classmethod
    def description(cls, context, properties):
        return f"Load node settings from the preset '{properties.preset_name}' (overwrite current settings)"

    def execute(self, context):
        ntree = context.space_data.path[-1].node_tree  # in case if the node in a node group
        node = ntree.nodes[self.node_name]
        id_tree = ntree.name
        ng = bpy.data.node_groups[id_tree]

        preset = SvPreset(path = self.preset_path, category = node.bl_idname)
        JSONImporter(preset.data).import_node_settings(node)
        return {'FINISHED'}

class SvSaveSelected(bpy.types.Operator):
    """
    Save selected nodes as a preset
    """
    bl_idname = "node.sv_save_selected"
    bl_label = "Save selected tree part"
    bl_options = {'INTERNAL'}

    preset_name: StringProperty(name="Name", description="Preset name")
    id_tree: StringProperty()
    category: StringProperty()
    is_node_preset: BoolProperty()

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

        # the operator can be used for both preset importing of a node and preset from a bunch of selected nodes
        if self.is_node_preset:
            layout_dict = JSONExporter.get_node_structure(nodes[0])
        else:
            layout_dict = JSONExporter.get_tree_structure(ng, True)

        preset = SvPreset(name=self.preset_name, category = self.category)
        preset.make_add_operator()
        destination_path = preset.path
        json.dump(layout_dict, open(destination_path, 'w'), indent=2)  # sort keys is not expected by the exporter

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

class SvPresetProps(bpy.types.Operator):
    """
    Edit preset properties
    """

    bl_idname = "node.sv_preset_props"
    bl_label = "Preset properties"
    bl_options = {'INTERNAL'}

    old_category: StringProperty(name="Old category", description="Preset category")
    new_category: EnumProperty(name="Category", description="New preset category", items = get_category_items_all)
    allow_change_category : BoolProperty(default = True)
    include_node_categories : BoolProperty(default = False)

    old_name: StringProperty(name="Old name", description="Preset name")
    new_name: StringProperty(name="Name", description="New preset name")

    description: StringProperty(name="Description", description="Preset description")
    keywords: StringProperty(name="Keywords", description="Search keywords")
    author: StringProperty(name="Author", description="Preset author name")
    license: StringProperty(
        name="License", description="Preset license (short name)", default="CC-BY-SA")

    def draw(self, context):
        layout = self.layout
        if self.allow_change_category:
            layout.prop(self, "new_category")
        else:
            layout.label(text="Category: " + self.old_category)
        layout.prop(self, "new_name")
        layout.prop(self, "description")
        layout.prop(self, "keywords")
        layout.prop(self, "author")
        layout.prop(self, "license")

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

        preset = SvPreset(name = self.old_name, category = self.old_category)
        preset.meta['description'] = self.description
        preset.meta['keywords'] = self.keywords
        preset.meta['author'] = self.author
        preset.meta['license'] = self.license
        preset.save()

        category_changed = self.allow_change_category and (self.new_category != self.old_category)
        if self.new_name != self.old_name or category_changed:
            old_path = get_preset_path(self.old_name, category=self.old_category)
            new_path = get_preset_path(self.new_name, category=self.new_category)

            if os.path.exists(new_path):
                msg = f"Preset named '{self.new_name}' already exists. Refusing to rewrite existing preset."
                error(msg)
                self.report({'ERROR'}, msg)
                return {'CANCELLED'}
            
            os.rename(old_path, new_path)
            preset.name = self.new_name
            preset.category = self.new_category

            info(f"Renamed '{old_path}' to '{new_path}'")
            self.report({'INFO'}, f"Renamed '{self.old_name}' to '{self.new_name}'")

        bpy.utils.unregister_class(preset_add_operators[(self.old_category, self.old_name)])
        del preset_add_operators[(self.old_category, self.old_name)]
        preset.make_add_operator()

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        self.new_name = self.old_name
        preset = SvPreset(name=self.old_name, category=self.old_category)
        self.description = preset.meta.get('description', "")
        self.keywords = preset.meta.get("keywords", "")
        self.author = preset.meta.get('author', "")
        self.license = preset.meta.get('license', "CC-BY-SA")
        return wm.invoke_props_dialog(self)

class SvPresetDelete(bpy.types.Operator):
    """
    Delete existing preset
    """

    bl_idname = "node.sv_preset_delete"
    bl_label = "Do you really want to delete this preset? This action cannot be undone."
    bl_options = {'INTERNAL'}

    preset_name: StringProperty(name="Preset name", description="Preset name")
    category : StringProperty(name = "Category")

    def execute(self, context):
        if not self.preset_name:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        path = get_preset_path(self.preset_name, category=self.category)

        os.remove(path)
        info(f"Removed '{path}'")
        self.report({'INFO'}, f"Removed '{self.category} / {self.preset_name}'")

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

class SvPresetToGist(bpy.types.Operator):
    """
    Export preset to Gist
    """

    bl_idname = "node.sv_preset_to_gist"
    bl_label = "Export preset to Gist"
    bl_options = {'INTERNAL'}

    preset_name: StringProperty(name="Preset name", description="Preset name")
    category : StringProperty(name = "Category")

    def execute(self, context):
        if not self.preset_name:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        path = get_preset_path(self.preset_name, category=self.category)

        gist_filename = self.preset_name + ".json"
        gist_description = self.preset_name
        with open(path, 'rb') as jsonfile:
            gist_body = jsonfile.read().decode('utf8')

        try:
            gist_url = sv_gist_tools.main_upload_function(gist_filename, gist_description, gist_body, show_browser=False)
            context.window_manager.clipboard = gist_url   # full destination url
            info(gist_url)
            self.report({'WARNING'}, "Copied gist URL to clipboad")
            sv_gist_tools.write_or_append_datafiles(gist_url, gist_filename)
        except Exception as err:
            exception(err)
            self.report({'ERROR'}, "Error 222: net connection or github login failed!")
            return {'CANCELLED'}
            
        finally:
            return {'FINISHED'}

class SvPresetToFile(bpy.types.Operator):
    """
    Export preset to outer file
    """

    bl_idname = "node.sv_preset_to_file"
    bl_label = "Export preset to file"
    bl_options = {'INTERNAL'}

    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})
    preset_name: StringProperty(name="Preset name", description="Preset name")
    category : StringProperty(name = "Category")

    filepath: StringProperty(
        name="File Path",
        description="Path where preset should be saved to",
        maxlen=1024, default="", subtype='FILE_PATH')


    def execute(self, context):
        if not self.preset_name:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        if not self.filepath:
            msg = "Target file path is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        existing_path = get_preset_path(self.preset_name, category=self.category)
        shutil.copy(existing_path, self.filepath)

        msg = f"Saved '{self.category} / {self.preset_name}' as '{self.filepath}'"
        info(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

class SvPresetFromFile(bpy.types.Operator):
    """
    Import preset from JSON file
    """

    bl_idname = "node.sv_preset_from_file"
    bl_label = "Import preset from file"
    bl_options = {'INTERNAL'}

    preset_name: StringProperty(name="Preset name", description="Preset name")
    category : StringProperty(name = "Category")

    filepath: StringProperty(
        name="File Path",
        description="Path where preset should be saved to",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        if not self.preset_name:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        if not self.filepath:
            msg = "Source file path is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        target_path = get_preset_path(self.preset_name, category=self.category)
        shutil.copy(self.filepath, target_path)

        msg = f"Imported '{self.filepath}' as '{self.category} / {self.preset_name}'"
        info(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

class SvPresetFromGist(bpy.types.Operator):
    """
    Import preset from Gist
    """

    bl_idname = "node.sv_preset_from_gist"
    bl_label = "Import preset from Gist"
    bl_options = {'INTERNAL'}

    gist_id: StringProperty(
        name="Gist ID", description="Gist identifier (or full URL)")

    preset_name: StringProperty(
        name="Preset name", description="Preset name")
    category : EnumProperty(
        name = "Category",
        description = "Select presets category",
        items = get_category_items_all)

    def execute(self, context):
        if not self.preset_name:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        if not self.gist_id:
            msg = "Gist ID is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        gist_data = sv_IO_panel_tools.load_json_from_gist(self.gist_id, self)
        target_path = get_preset_path(self.preset_name, category=self.category)
        if os.path.exists(target_path):
            msg = f"Preset named '{self.preset_name}' already exists. Refusing to rewrite existing preset."
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        
        with open(target_path, 'wb') as jsonfile:
            gist_data = json.dumps(gist_data, sort_keys=True, indent=2).encode('utf8')
            jsonfile.write(gist_data)

        preset = SvPreset(name = self.preset_name, category = self.category)
        preset.make_add_operator()

        msg = f"Imported '{self.gist_id}' as '{self.preset_name}'"
        info(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        self.gist_id = context.window_manager.clipboard
        return wm.invoke_props_dialog(self)

class SvPresetCategoryNew(bpy.types.Operator):
    """
    Create new presets category
    """
    bl_idname = "node.sv_preset_category_new"
    bl_label = "Create new category"
    bl_options = {'INTERNAL'}

    category : StringProperty(name = "Category name")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "category")

    def execute(self, context):
        if not self.category:
            msg = "Category name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        if self.category == GENERAL or self.category in get_category_names():
            msg = f"Category named '{self.category}' already exists; refusing to overwrite existing category"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        path = get_presets_directory(category = self.category, mkdir=True)
        info(f"Created new category '{self.category}' at {path}")
        self.report({'INFO'}, f"Created new category {self.category}")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class SvPresetCategoryDelete(bpy.types.Operator):
    """
    Delete existing presets category
    """
    bl_idname = "node.sv_preset_category_remove"
    bl_label = "Do you really want to delete this presets category? This action cannot be undone."
    bl_options = {'INTERNAL'}

    category : StringProperty(name = "Category")

    def execute(self, context):
        if not self.category:
            msg = "Preset name is not specified"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        if self.category == GENERAL:
            msg = "General category can not be deleted"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        path = get_presets_directory(category = self.category)
        files = glob(join(path, "*"))
        if files:
            msg = f"Category '{self.category}' is not empty; refusing to delete non-empty category."
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        os.rmdir(path)

        ntree = context.space_data.node_tree
        panel_props = ntree.preset_panel_properties
        panel_props.category = GENERAL

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

class SvResetPresetSearch(bpy.types.Operator):
    """
    Reset preset search string and return to selection of preset by category
    """
    bl_idname = "node.sv_reset_preset_search"
    bl_label = "Reset search"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        ntree = context.space_data.node_tree
        panel_props = ntree.preset_panel_properties
        panel_props.search_text = ""
        return {'FINISHED'}

classes = [
    SvSaveSelected,
    SvPresetFromFile,
    SvPresetFromGist,
    SvPresetProps,
    SvPresetCategoryNew,
    SvPresetCategoryDelete,
    SvPresetToGist,
    SvPresetToFile,
    SvPresetReplace
    SvPresetDelete,
    SvResetPresetSearch
]

register, unregister = bpy.utils.register_classes_factory(classes)
