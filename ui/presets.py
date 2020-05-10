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
from os.path import join, isdir, basename, dirname
import shutil
from glob import glob
import json
from urllib.parse import quote_plus
import inspect
import hashlib

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty

from sverchok.utils.sv_IO_panel_tools import write_json, create_dict_of_tree, import_tree, import_node_settings
from sverchok.utils.logging import debug, info, error, exception
from sverchok.utils import sv_gist_tools
from sverchok.utils import sv_IO_panel_tools
from sverchok.utils import get_node_class_reference
import sverchok

# To be moved somewhere under core/
def get_sverchok_directory():
    filename = inspect.getfile(sverchok)
    return dirname(filename)

GENERAL = "General"

def get_presets_directory(category=None, mkdir=True, standard=False):
    if category is None or category == GENERAL:
        if standard:
            path_partial = 'presets'
        else:
            path_partial = os.path.join('sverchok', 'presets')
    else:
        if standard:
            path_partial = join('presets', category)
        else:
            path_partial = os.path.join('sverchok', 'presets', category)
    if standard:
        presets = join(get_sverchok_directory(), path_partial)
    else:
        presets = join(bpy.utils.user_resource('DATAFILES', path=path_partial, create=mkdir))
    if not os.path.exists(presets) and mkdir and not standard:
        os.makedirs(presets)
    return presets

def get_category_names(mkdir=True):
    standard = get_presets_directory(standard=True)
    user = get_presets_directory(standard=False, mkdir=mkdir)
    categories = []
    for base in [standard, user]:
        for path in sorted(glob(join(base, "*"))):
            if isdir(path):
                name = basename(path)
                if name not in categories:
                    categories.append(name)
    return categories

def get_category_items(self, context):
    category_items = None
    category_items = [(GENERAL, "General", "Uncategorized presets", 0)]
    node_category_items = []
    for idx, category in enumerate(get_category_names()):
        node_class = get_node_class_reference(category)
        if node_class:
            title = "/Node/ {}".format(node_class.bl_label)
            node_category_items.append((category, title, category, idx+1))
        else:
            title = category
            category_items.append((category, title, category, idx+1))
    include_node_categories = not hasattr(self, 'include_node_categories') or self.include_node_categories
    if node_category_items and include_node_categories:
        category_items = category_items + [None] + node_category_items
    return category_items

def get_preset_path(name, category=None, standard=False, mkdir=True):
    presets = get_presets_directory(category, standard=standard, mkdir=mkdir)
    return join(presets, name + ".json")

def get_preset_paths(category=None, mkdir=True):
    standard = get_presets_directory(category, standard=True)
    user = get_presets_directory(category, standard=False, mkdir=mkdir)
    standard_presets = glob(join(standard, "*.json"))
    user_presets = glob(join(user, "*.json"))
    standard_presets.sort()
    user_presets.sort()
    return [(True, path) for path in standard_presets] + [(False, path) for path in user_presets]

def replace_bad_chars(s):
    return quote_plus(s).replace('+', '_').replace('%', '_').replace('-','_').lower()

def get_preset_idname_for_operator(name, category=None):
    name = replace_bad_chars(name)
    if category:
        category = replace_bad_chars(category)
        name = category + "__" + name
    if len(name) > 45:
        name = name[:38] + "_" + hashlib.sha1(name.encode('utf-8')).hexdigest()[:5]
    return name

# We are creating and registering preset adding operators dynamically.
# So, we have to remember them in order to unregister them when needed.
preset_add_operators = {}

class SvPreset(object):
    def __init__(self, name=None, path=None, category=None, standard=False):
        if name is None and path is None:
            raise Exception("Either name or path must be specified when initializing SvPreset")
        self._name = name
        self._path = path
        self._data = None
        self.category = category
        self.standard = standard

    def get_name(self):
        if self._name is not None:
            return self._name
        else:
            name = os.path.basename(self._path)
            name,_ = os.path.splitext(name)
            self._name = name
            return name

    def set_name(self, new_name):
        self._name = new_name
        self._path = get_preset_path(new_name, standard=False)
        self.standard = False

    name = property(get_name, set_name)

    def get_path(self):
        if self._path is not None:
            return self._path
        else:
            path = get_preset_path(self._name, self.category, standard=self.standard)
            self._path = path
            return path

    def set_path(self, new_path):
        name = basename(new_path)
        dir = dirname(new_path)
        if dir == get_presets_directory():
            self.category = None
        else:
            self.category = basename(dir)
        name,_ = os.path.splitext(name)
        self._name = name
        self._path = new_path

    path = property(get_path, set_path)

    def get_search_terms(self):
        terms = []
        if self.name:
            terms.append(self.name.upper())
        if self.category:
            terms.append(self.category.upper())
        if self.keywords:
            terms.append(self.keywords.upper())
        return terms

    def matches(self, needle):
        if not needle:
            return True
        needle = needle.upper()
        return any(needle in term for term in self.get_search_terms() if term)

    @property
    def data(self):
        if self._data is not None:
            return self._data
        else:
            if os.path.exists(self.path):
                with open(self.path, 'rb') as jsonfile:
                    data = jsonfile.read().decode('utf8')
                    data = json.loads(data)
                    self._data = data
                    return self._data
            else:
                return dict()

    @property
    def meta(self):
        data = self.data
        if 'metainfo' in data:
            return data['metainfo']
        else:
            meta = dict()
            data['metainfo'] = meta
            return meta

    @property
    def description(self):
        return self.meta.get("description", None)

    @property
    def keywords(self):
        return self.meta.get("keywords", None)

    def save(self):
        if self._data is None:
            debug("Preset `%s': no data was loaded, nothing to save.", self.name)
            return

        data = json.dumps(self.data, sort_keys=True, indent=2).encode('utf8')
        with open(self.path, 'wb') as jsonfile:
            jsonfile.write(data)

        info("Saved preset `%s'", self.name)

    @staticmethod
    def get_target_location(node_tree):
        """
        Calculate average location of selected nodes in the tree,
        or all nodes if there are no nodes selected.
        """
        selection = [node for node in node_tree.nodes if node.select]
        if not len(selection):
            debug("No selection, using all nodes")
            selection = node_tree.nodes[:]
        n = len(selection)
        if not n:
            return [0,0]
        locations = [node.location for node in selection]
        location_sum = [sum(x) for x in zip(*locations)]
        average_location = [x / float(n) for x in location_sum]
        return average_location

    def make_add_operator(self):
        """
        Create operator class which adds specific preset nodes to current node tree.
        Tooltip (docstring) for that operator is copied from metainfo/description field.
        """

        global preset_add_operators
        if self.category is None:
            self.category = GENERAL

        if (self.category, self.name) not in preset_add_operators:

            class SverchPresetAddOperator(bpy.types.Operator):
                bl_idname = "node.sv_preset_" + get_preset_idname_for_operator(self.name, self.category)
                bl_label = "Add {} preset ({} category)".format(self.name, self.category)
                bl_options = {'REGISTER', 'UNDO'}

                cursor_x: bpy.props.IntProperty()
                cursor_y: bpy.props.IntProperty()

                @classmethod
                def poll(cls, context):
                    try:
                        return context.space_data.node_tree.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}
                    except:
                        return False

                def execute(operator, context):
                    # please not be confused: "operator" here references to
                    # SverchPresetAddOperator instance, and "self" references to
                    # SvPreset instance.  
                    ntree = context.space_data.node_tree
                    id_tree = ntree.name
                    ng = bpy.data.node_groups[id_tree]

                    center = SvPreset.get_target_location(ng)
                    # Deselect everything, so as a result only imported nodes
                    # will be selected
                    bpy.ops.node.select_all(action='DESELECT')
                    import_tree(ng, self.path, center = center)
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
                    return {'FINISHED'}

                def invoke(self, context, event):
                    self.cursor_x = event.mouse_region_x
                    self.cursor_y = event.mouse_region_y
                    return self.execute(context)

            SverchPresetAddOperator.__name__ = self.name
            SverchPresetAddOperator.__doc__ = self.meta.get("description", self.name)
            if self.standard:
                SverchPresetAddOperator.__doc__ += " [standard]"

            preset_add_operators[(self.category, self.name)] = SverchPresetAddOperator
            bpy.utils.register_class(SverchPresetAddOperator)
            debug("Registered: %s",
                "node.sv_preset_" + get_preset_idname_for_operator(self.name, self.category))

    def draw_operator(self, layout, id_tree, category=None):
        if not category:
            category = self.category
        op = layout.operator("node.sv_preset_"+get_preset_idname_for_operator(self.name, category), text=self.name)

class SverchPresetReplaceOperator(bpy.types.Operator):
    """Load node settings from preset"""
    bl_idname = "node.sv_preset_replace_node"
    bl_label = "Load node settings from preset"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    node_name : StringProperty()
    preset_path : StringProperty()
    preset_name : StringProperty()

    @classmethod
    def description(cls, context, properties):
        return "Load node settings from the preset `{}' (overwrite current settings)".format(properties.preset_name)

    def execute(self, context):
        ntree = context.space_data.node_tree
        node = ntree.nodes[self.node_name]
        id_tree = ntree.name
        ng = bpy.data.node_groups[id_tree]

        preset = SvPreset(path = self.preset_path, category = node.bl_idname)
        node_json = list(preset.data['nodes'].values())[0]
        import_node_settings(node, node_json, overwrite_presentation_props = False)
        return {'FINISHED'}

def get_presets(category=None, search=None, mkdir=True):
    result = []
    if search:
        categories = [GENERAL] + get_category_names(mkdir=mkdir)
    else:
        categories = [category]
    for category in categories:
        for is_standard, path in get_preset_paths(category, mkdir=mkdir):
            preset = SvPreset(path=path, category=category, standard=is_standard)
            if preset.matches(search):
                result.append(preset)
    return result

class SvUserPresetsPanelProps(bpy.types.PropertyGroup):
    manage_mode: BoolProperty(
        name="Manage Presets",
        description="Presets management mode", default=False)

    category : EnumProperty(
        name = "Category",
        description = "Select presets category",
        items = get_category_items)
    
    search_text : StringProperty(
        name = "Search",
        description = "Enter search term and press Enter to search; clear the field to return to selection of preset category.")


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
    save_defaults : BoolProperty(default = False)

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

        layout_dict = create_dict_of_tree(ng, selected=True, save_defaults = self.save_defaults)
        preset = SvPreset(name=self.preset_name, category = self.category)
        preset.make_add_operator()
        destination_path = preset.path
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

class SvPresetProps(bpy.types.Operator):
    """
    Edit preset properties
    """

    bl_idname = "node.sv_preset_props"
    bl_label = "Preset properties"
    bl_options = {'INTERNAL'}

    old_category: StringProperty(name="Old category", description="Preset category")
    new_category: EnumProperty(name="Category", description="New preset category", items = get_category_items)
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
                msg = "Preset named `{}' already exists. Refusing to rewrite existing preset.".format(self.new_name)
                error(msg)
                self.report({'ERROR'}, msg)
                return {'CANCELLED'}
            
            os.rename(old_path, new_path)
            preset.name = self.new_name
            preset.category = self.new_category
            info("Renamed `%s' to `%s'", old_path, new_path)
            self.report({'INFO'}, "Renamed `{}' to `{}'".format(self.old_name, self.new_name))

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

class SvDeletePreset(bpy.types.Operator):
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
        info("Removed `%s'", path)
        self.report({'INFO'}, "Removed `{} / {}'".format(self.category, self.preset_name))

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
        msg = "Saved `{} / {}' as `{}'".format(self.category, self.preset_name, self.filepath)
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
        msg = "Imported `{}' as `{} / {}'".format(self.filepath, self.category, self.preset_name)
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
        items = get_category_items)

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
            msg = "Preset named `{}' already exists. Refusing to rewrite existing preset.".format(self.preset_name)
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        
        with open(target_path, 'wb') as jsonfile:
            gist_data = json.dumps(gist_data, sort_keys=True, indent=2).encode('utf8')
            jsonfile.write(gist_data)

        preset = SvPreset(name = self.preset_name, category = self.category)
        preset.make_add_operator()

        msg = "Imported `{}' as `{}'".format(self.gist_id, self.preset_name)
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
            msg = "Category named `{}' already exists; refusing to overwrite existing category"
            error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        path = get_presets_directory(category = self.category, mkdir=True)
        info("Created new category `%s' at %s", self.category, path)
        self.report({'INFO'}, "Created new category {}".format(self.category))
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
            msg = "Category `{}' is not empty; refusing to delete non-empty category.".format(self.category)
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

class SvResetPresetSearchOperator(bpy.types.Operator):
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

def draw_presets_ops(layout, category=None, id_tree=None, presets=None, context=None):
    if category is None:
        category = GENERAL
    if presets is None:
        presets = get_presets(category)

    if id_tree is None:
        if context is None:
            raise Exception("Either id_tree or context must be provided for draw_presets_ops()")
        ntree = context.space_data.node_tree
        id_tree = ntree.name

    col = layout.column(align=True)
    for preset in presets:
        preset.draw_operator(col, id_tree) #, category=category)

class SV_PT_UserPresetsPanel(bpy.types.Panel):
    bl_idname = "SV_PT_UserPresetsPanel"
    bl_label = "Presets"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    # bl_category = 'Presets'
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

        layout.prop(panel_props, 'manage_mode', toggle=True, icon='PREFERENCES')

        needle = None
        if not panel_props.manage_mode:
            row = layout.row(align=True)
            row.prop(panel_props, "search_text", text="")
            row.operator("node.sv_reset_preset_search", icon="X", text="")
            needle = panel_props.search_text

        if not panel_props.search_text:
            layout.prop(panel_props, 'category', text='')

        row = layout.row()
        op = row.operator('node.sv_save_selected', text="Save Preset", icon='SOLO_ON')
        op.id_tree = ntree.name
        op.category = panel_props.category

        selected_nodes = [node for node in ntree.nodes if node.select]
        can_save_preset = len(selected_nodes) > 0
        category_node_class = get_node_class_reference(op.category)
        if category_node_class is not None:
            if len(selected_nodes) == 1:
                selected_node = selected_nodes[0]
                can_save_preset = can_save_preset and hasattr(selected_node, 'bl_idname') and selected_node.bl_idname == op.category
            else:
                can_save_preset = False
        row.enabled = can_save_preset

        layout.separator()

        presets = get_presets(panel_props.category, search=needle)
        layout.separator()

        if panel_props.manage_mode:
            col = layout.column(align=True)
            col.operator("node.sv_preset_from_gist", icon='URL').category = panel_props.category
            col.operator("node.sv_preset_from_file", icon='IMPORT').category = panel_props.category

            col.operator('node.sv_preset_category_new', icon='NEWFOLDER')
            if panel_props.category != GENERAL:
                remove = col.operator('node.sv_preset_category_remove', text="Delete category {}".format(panel_props.category), icon='CANCEL')
                remove.category = panel_props.category

            if len(presets):
                layout.label(text="Manage presets:")
                for preset in presets:
                    name = preset.name

                    row = layout.row(align=True)
                    row.label(text=name)

                    gist = row.operator('node.sv_preset_to_gist', text="", icon='URL')
                    gist.preset_name = name
                    gist.category = panel_props.category

                    export = row.operator('node.sv_preset_to_file', text="", icon="EXPORT")
                    export.preset_name = name
                    export.category = panel_props.category

                    if not preset.standard:
                        rename = row.operator('node.sv_preset_props', text="", icon="GREASEPENCIL")
                        rename.old_name = name
                        rename.old_category = panel_props.category
                        rename.allow_change_category = (category_node_class is None)
                        if rename.allow_change_category:
                            rename.new_category = rename.old_category

                        delete = row.operator('node.sv_preset_delete', text="", icon='CANCEL')
                        delete.preset_name = name
                        delete.category = panel_props.category
            else:
                layout.label(text="You do not have any presets")
                layout.label(text="under `{}` category.".format(panel_props.category))
                layout.label(text="You can import some presets")
                layout.label(text="from Gist or from file.")

        else:
            if len(presets):
                layout.label(text="Use preset:")
                draw_presets_ops(layout, panel_props.category, ntree.name, presets)
            elif needle:
                layout.label(text="There are no presets matching")
                layout.label(text="the search terms.")
            else:
                layout.label(text="You do not have any presets")
                layout.label(text="under `{}` category.".format(panel_props.category))
                layout.label(text="Select some nodes and")
                layout.label(text="Use the `Save Preset' button.")

classes = [
    SvSaveSelected,
    SvUserPresetsPanelProps,
    SvPresetFromFile,
    SvPresetFromGist,
    SvPresetProps,
    SvDeletePreset,
    SvPresetCategoryNew,
    SvPresetCategoryDelete,
    SvPresetToGist,
    SvPresetToFile,
    SverchPresetReplaceOperator,
    SV_PT_UserPresetsPanel
]

def register():
    for clazz in classes:
        bpy.utils.register_class(clazz)

    for preset in get_presets():
        preset.make_add_operator()
    for category_name in get_category_names():
        for preset in get_presets(category_name):
            preset.make_add_operator()

    bpy.types.NodeTree.preset_panel_properties = bpy.props.PointerProperty(
        name="preset_panel_properties", type=SvUserPresetsPanelProps)

    bpy.utils.register_class(SvResetPresetSearchOperator)

def unregister():
    bpy.utils.unregister_class(SvResetPresetSearchOperator)
    del bpy.types.NodeTree.preset_panel_properties

    for clazz in reversed(classes):
        bpy.utils.unregister_class(clazz)

    for category, name in preset_add_operators:
        bpy.utils.unregister_class(preset_add_operators[(category, name)])

