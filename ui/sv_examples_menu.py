# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import chain
from os.path import basename
from pathlib import Path

import bpy
from bpy.types import Operator

import sverchok
from sverchok.ui.utils import datafiles
from sverchok.utils.sv_json_import import JSONImporter
from sverchok.ui.sv_icons import icon
from sverchok.ui.sv_3d_panel import plugin_icons


def node_examples_pulldown(self, context):
    if context.space_data.tree_type == 'SverchCustomTreeType':
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        #row.alert = True
        row.menu("SV_MT_layouts_examples", icon="RNA")


def node_settings_pulldown(self, context):
    if context.space_data.tree_type == 'SverchCustomTreeType':
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        row.operator(
                "preferences.addon_show", icon="SETTINGS" #, text="Settings"
            ).module = __package__.split('.')[0]
        row.operator("switcher.console", icon="CONSOLE", text="")
        if bpy.context.preferences.inputs.use_rotate_around_active==True:
            row.operator("sv.orbit_around_selection", icon="PROP_CON",text="",)
        else:
            row.operator("sv.orbit_around_selection", icon="SNAP_NORMAL", text="")
        row.menu("SV_MT_layouts_Splash", text='👈☝ ( ͡° ͜ʖ ͡°)', icon_value=plugin_icons['sverchock_icon_b.png'].icon_id)
        

class SV_MT_LayoutsSplash(bpy.types.Menu):
    """Node tree examples"""
    bl_idname = 'SV_MT_layouts_Splash'
    bl_space_type = 'NODE_EDITOR'
    bl_label = ""
    bl_description = "Quick help can be downloaded from github repo and used inside node tree as popup splash screen"

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except Exception as err:
            return False


    def draw(self, context):
        if bpy.app.version <= (3,6,18): return
        layout = self.layout
        col = layout.column(align=True)
        col.operator('sv.download_splash_images', text='Download helps', icon='URL')
        for path, category_name in sv_helps_categories_names():
            op = col.operator('sv.splash_screen_simple', text=category_name, icon='HIDE_OFF')
            op.group = category_name

class SW_OT_Console(Operator):
    """Show/hide console"""
    bl_label = "Open Blender system console"
    bl_idname = "switcher.console"
    def execute(self, context):
        bpy.ops.wm.console_toggle()
        return {'FINISHED'}

class SW_OT_Orbit_Around_Selection(Operator):
    '''Orbit Around Selection [On/Off]'''
    bl_label = "Edit->Preferences->Navigation->Orbit Around Selection"
    bl_idname = "sv.orbit_around_selection"
    @classmethod
    def poll(self, context):
        # Activate always
        res = True
        return res

    def execute(self, context):
        bpy.context.preferences.inputs.use_rotate_around_active = not(bpy.context.preferences.inputs.use_rotate_around_active)
        if bpy.context.preferences.inputs.use_rotate_around_active:
            bpy.context.preferences.inputs.use_mouse_depth_navigate = bpy.context.preferences.inputs.use_rotate_around_active
        return {'FINISHED'}

class SV_MT_LayoutsExamples(bpy.types.Menu):
    """Node tree examples"""
    bl_idname = 'SV_MT_layouts_examples'
    bl_space_type = 'NODE_EDITOR'
    bl_label = "E X A M P L E S"
    bl_description = "List of Sverchok Examples"

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except Exception as err:
            return False


    def draw(self, context):
        layout = self.layout

        # Search field всегда visible
        row = layout.row()
        row.prop(context.window_manager, "sv_examples_search_string", icon='VIEWZOOM', text="")

        search_string = context.window_manager.sv_examples_search_string.lower().strip()

        if search_string:
            # Показать результаты поиска
            found_files = self.search_examples(search_string)
            if found_files:
                categorized = self.categorize_files(found_files)
                for category_name, files in categorized.items():
                    if category_name:
                        layout.label(text=category_name)
                    for file_path, display_name in files:
                        op = layout.operator("node.tree_importer_silent", text=display_name)
                        op.filepath = file_path
            else:
                layout.label(text="No examples found")
        else:
            # Показать категории как раньше
            for path, category_name in example_categories_names():
                self.layout.menu("SV_MT_PyMenu_" + category_name.replace(' ', '_'))

    def search_examples(self, search_string):
        """Search through all example files"""
        found_files = []

        # Search in main examples
        examples_path = Path(sverchok.__file__).parent / 'json_examples'
        found_files.extend(self.search_in_directory(examples_path, search_string))

        # Search in extra examples
        for provider, path in extra_examples.items():
            found_files.extend(self.search_in_directory(path, search_string))

        return found_files

    def search_in_directory(self, directory_path, search_string):
        """Search for files in a directory matching search string"""
        found = []
        directory = Path(directory_path)

        if not directory.exists():
            return found

        for category_path in directory.iterdir():
            if category_path.is_dir():
                for file_path in category_path.glob("*.json"):
                    # Search in filename without extension
                    file_stem = file_path.stem.lower()
                    category_name = category_path.name.lower()

                    if (search_string in file_stem or
                        search_string in category_name or
                        search_string in f"{category_name} {file_stem}"):

                        # Create nice display name
                        display_name = f"{file_path.stem} ({category_path.name})"
                        found.append((str(file_path), display_name))

        return found

    def categorize_files(self, file_list):
        """Categorize files by their parent directory"""
        categories = {}
        for file_path, display_name in file_list:
            category = Path(file_path).parent.name
            if category not in categories:
                categories[category] = []
            categories[category].append((file_path, display_name))

        # Sort categories and files within categories
        for category in categories:
            categories[category].sort(key=lambda x: x[1])

        return dict(sorted(categories.items()))

    def draw_all_examples(self, layout):
        """Draw all examples without categorization"""
        all_files = []

        # Collect all files
        examples_path = Path(sverchok.__file__).parent / 'json_examples'
        all_files.extend(self.get_all_example_files(examples_path))

        for provider, path in extra_examples.items():
            all_files.extend(self.get_all_example_files(path))

        # Sort alphabetically
        all_files.sort(key=lambda x: x[1])

        # Draw all files
        for file_path, display_name in all_files:
            op = layout.operator("node.tree_importer_silent", text=display_name)
            op.filepath = file_path

    def get_all_example_files(self, directory_path):
        """Get all example files from a directory"""
        files = []
        directory = Path(directory_path)

        if not directory.exists():
            return files

        for category_path in directory.iterdir():
            if category_path.is_dir():
                for file_path in category_path.glob("*.json"):
                    display_name = f"{file_path.stem} ({category_path.name})"
                    files.append((str(file_path), display_name))

        return files


def make_submenu_classes(path, category_name):
    """Generator of submenus classes"""
    def draw_submenu(self, context):
        """Draw Svershok template submenu"""
        category_path = path / category_name
        self.path_menu(searchpaths=[str(category_path)], operator='node.tree_importer_silent')

    class_name = "SV_MT_PyMenu_" + category_name.replace(' ', '_')

    return type(class_name, (bpy.types.Menu,), {'bl_label': category_name, 'draw': draw_submenu,
                                               'bl_idname': class_name})

extra_examples= dict()
def add_extra_examples(provider, path):
    global extra_examples
    extra_examples[provider] = path

def example_categories_names():
    examples_path = Path(sverchok.__file__).parent / 'json_examples'
    names = []
    for category_path in examples_path.iterdir():
        if category_path.is_dir():
            names.append((examples_path, category_path.name))
    for c in extra_examples:
        for category_path in extra_examples[c].iterdir():
            if category_path.is_dir():
                names.append((extra_examples[c], category_path.name))
    for name in names:
        yield name


def sv_helps_categories_names():
    splash_path = Path(datafiles) / 'splash_images'
    names = []
    for category_path in splash_path.iterdir():
        if category_path.is_dir():
            names.append((splash_path, category_path.name))
    for name in names:
        yield name

class SvNodeTreeImporterSilent(bpy.types.Operator):
    """Importing template tree"""
    bl_idname = "node.tree_importer_silent"
    bl_label = "sv NodeTree Import Silent"

    filepath: bpy.props.StringProperty(  # path to template file got from path_menu
        name="File Path",
        description="File path used to import from",
        maxlen=1024, default="", subtype='FILE_PATH')

    def execute(self, context):
        # if triggered from a non-initialized tree, we first make a tree
        tree = context.space_data.node_tree
        if tree is None:
            tree = bpy.data.node_groups.new(basename(self.filepath), 'SverchCustomTreeType')
            context.space_data.node_tree = tree  # pass this tree to the active node view

        # Deselect everything, so as a result only imported nodes will be selected
        bpy.ops.node.select_all(action='DESELECT')
        JSONImporter.init_from_path(self.filepath).import_into_tree(tree)
        return {'FINISHED'}


# Operators for search functionality
class SV_OT_ToggleExamplesSearch(bpy.types.Operator):
    """Toggle between search and categories view"""
    bl_idname = "wm.sv_examples_toggle_search"
    bl_label = "Toggle Examples Search"

    def execute(self, context):
        wm = context.window_manager
        wm.sv_examples_show_search = not wm.sv_examples_show_search
        if not wm.sv_examples_show_search:
            wm.sv_examples_search_string = ""  # Clear search when switching to categories
        return {'FINISHED'}


class SV_OT_ClearExamplesSearch(bpy.types.Operator):
    """Clear search string"""
    bl_idname = "wm.sv_examples_clear_search"
    bl_label = "Clear Examples Search"

    def execute(self, context):
        context.window_manager.sv_examples_search_string = ""
        return {'FINISHED'}

classes = [
    SW_OT_Orbit_Around_Selection,
    SW_OT_Console,
    SV_MT_LayoutsExamples,
    SV_MT_LayoutsSplash,
    SvNodeTreeImporterSilent,
    SV_OT_ToggleExamplesSearch,
    SV_OT_ClearExamplesSearch
]



def register():
    global submenu_classes
    bpy.types.WindowManager.sv_examples_search_string = bpy.props.StringProperty(
        name="Search Examples",
        description="Search through Sverchok examples",
        default=""
    )

    bpy.types.WindowManager.sv_examples_show_search = bpy.props.BoolProperty(
        name="Show Search",
        description="Show search field instead of categories",
        default=False
    )
    submenu_classes = [make_submenu_classes(path, category_name) for path, category_name in example_categories_names()]
    _ = [bpy.utils.register_class(cls) for cls in chain(classes, submenu_classes)]
    bpy.types.NODE_HT_header.append(node_examples_pulldown)
    bpy.types.NODE_HT_header.append(node_settings_pulldown)


def unregister():
    bpy.types.NODE_HT_header.remove(node_settings_pulldown)
    bpy.types.NODE_HT_header.remove(node_examples_pulldown)
    _ = [bpy.utils.unregister_class(cls) for cls in reversed(list(chain(classes, submenu_classes)))]
    del bpy.types.WindowManager.sv_examples_search_string
    del bpy.types.WindowManager.sv_examples_show_search
