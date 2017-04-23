# -*- coding: utf-8 -*-
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
from bpy.props import StringProperty, BoolProperty

import re
import os
import json
import glob
from collections import OrderedDict

import sverchok
from sverchok.menu import make_node_cats
from sverchok.utils.context_managers import sv_preferences

DEBUG = False

_category_node_list = {}
_theme_collection = OrderedDict()
_current_theme_id = "default"
_hardcoded_theme_ids = []
_theme_preset_list = []

# theme dictionary sections/groups
THEME_NAME = "Name"
NODE_COLORS = "Node Colors"
ERROR_COLORS = "Error Colors"
HEATMAP_COLORS = "Heat Map Colors"

_theme_default = {
    THEME_NAME: "Default",
    NODE_COLORS: {
        "Visualizer": [1.0, 0.3, 0.0],
        "Text": [0.5, 0.5, 1.0],
        "Scene": [0.0, 0.5, 0.2],
        "Layout": [0.674, 0.242, 0.363],
        "Generators": [0.0, 0.5, 0.5],
        "Generators Extended": [0.4, 0.7, 0.7],
        # "Monad": [0.830, 0.91, 0.75],
    },
    ERROR_COLORS: {
        "Exception": [0.8, 0.0, 0.0],  # When node has an exception
        "No Data": [1.0, 0.3, 0.0],  # When a node can not get data
    },
    HEATMAP_COLORS: {
        "Heat Map Cold": [1.0, 1.0, 1.0],
        "Heat Map Hot": [0.8, 0.0, 0.0],
    }
}

_theme_nipon_blossom = {
    THEME_NAME: "Nipon Blossom",
    NODE_COLORS: {
        "Visualizer": [0.628488, 0.931008, 1.000000],
        "Text": [1.000000, 0.899344, 0.974251],
        "Scene": [0.904933, 1.000000, 0.883421],
        "Layout": [0.602957, 0.674000, 0.564277],
        "Generators": [0.92, 0.92, 0.92],
        "Generators Extended": [0.95, 0.95, 0.95],
    },
    ERROR_COLORS: {
        "Exception": [0.8, 0.0, 0.0],  # When node has an exception
        "No Data": [1.0, 0.3, 0.0]  # When a node can not get data
    },
    HEATMAP_COLORS: {
        "Heat Map Cold": [1.0, 1.0, 1.0],
        "Heat Map Hot": [0.8, 0.0, 0.0],
    }
}


_theme_color_attributes = {}  # cached values


def debugPrint(*args):
    if DEBUG:
        print(*args)


def theme_color_attrs():
    """ Convert default theme template to a dict of color attributes names """
    if not _theme_color_attributes:  # not cached ? => cache it!
        for group in _theme_default.keys():
            if group == THEME_NAME:  # skip the theme name section
                continue
            attrs = {}
            for category in _theme_default[group]:
                attrs[category] = theme_color_attr(category)
            _theme_color_attributes[group] = attrs

    return _theme_color_attributes


def theme_color_attr(category):
    attr = re.sub(r'[ ]', '_', category.lower()) + "_color"
    return attr


def get_theme_preset_list():
    """ Get the theme preset list (used by settings enum property) """
    return _theme_preset_list


def cache_theme_preset_list():
    """ Cache the theme preset list (triggered after add/remove theme preset) """
    _theme_preset_list.clear()
    for themeID, theme in _theme_collection.items():
        themeName = theme[THEME_NAME]
        debugPrint("file name = ", themeID)
        debugPrint("theme name = ", themeName)
        themeItem = (themeID, themeName, themeName)
        _theme_preset_list.append(themeItem)


def set_current_themeID(themeID):
    global _current_theme_id
    debugPrint("selecting current theme to:", themeID)
    _current_theme_id = themeID


def get_current_themeID():
    return _current_theme_id


def cache_category_node_list():
    """ Cache the category-node mapping (used for color access) """
    if not _category_node_list:
        node_category_list = make_node_cats()

        for category, nodes in node_category_list.items():
            for node in nodes:
                _category_node_list[node[0]] = category


def get_node_category(nodeID):
    """ Get the node category for the given node ID """
    cache_category_node_list()  # make sure the category-node list is cached
    return _category_node_list[nodeID]  # @todo check if nodeID is in list


def get_themes_path():
    """ Get the themes path. Create one first if it doesn't exist """
    dirPath = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    themePath = os.path.join(dirPath, 'themes')

    # create theme path if it doesn't exist
    if not os.path.exists(themePath):
        os.mkdir(themePath)

    return themePath


def get_theme_files():
    """ Get the theme files for all the themes present at the themes path """
    themePath = get_themes_path()
    themeFilePattern = os.path.join(themePath, "*.json")
    themeFiles = glob.glob(themeFilePattern)

    return themeFiles


def theme_id(themeName):
    """ Convert theme NAME into a theme ID (Nipon Blossom => nipon_blossom) """
    themeID = re.sub(r'[ ]', '_', themeName.lower())
    return themeID


def load_theme(filePath):
    """ Load a theme from the given file path """
    debugPrint("loading theme: ", filePath)
    theme = {}
    with open(filePath, 'r') as infile:
        theme = json.load(infile, object_pairs_hook=OrderedDict)

    return theme


def load_themes(reload=False):
    """ Load all the themes from disk into a cache """
    if _theme_collection and not reload:  # skip if already loaded and not reloading
        return

    _theme_collection.clear()  # clear in case of reloading

    debugPrint("Loading the themes...")

    themeFiles = get_theme_files()
    for f in themeFiles:
        # debugPrint("filepath: ", filePath)
        theme = load_theme(f)
        themeID = theme_id(theme[THEME_NAME])
        debugPrint("theme ID : ", themeID)
        _theme_collection[themeID] = theme

    # for themeID, theme in _theme_collection.items():
    #     debugPrint("Theme : ", themeID, " is called: ", theme[THEME_NAME])

    # debugPrint("Loaded theme collection: ", _theme_collection)


def save_theme(theme, fileName):
    """ Save the given theme to disk """
    debugPrint("save theme to:", fileName)

    themePath = get_themes_path()
    themeFile = os.path.join(themePath, fileName)
    debugPrint("filepath: ", themeFile)
    with open(themeFile, 'w') as outfile:
        json.dump(theme, outfile, indent=4, separators=(',', ':'))


def save_default_themes():
    """ Save the hardcoded default themes to disk """
    for theme in [_theme_default, _theme_nipon_blossom]:
        themeID = theme_id(theme[THEME_NAME])
        save_theme(theme, themeID + ".json")
        _hardcoded_theme_ids.append(themeID)  # keep track of the default themes IDs


def remove_theme(themeName):
    """ Remove theme with given name from theme collection and disk """
    themeID = theme_id(themeName)

    if themeID in _hardcoded_theme_ids:
        debugPrint("Cannot remove the default themes")
        return

    debugPrint("Removing the theme with name: ", themeName)
    if themeID in _theme_collection:
        debugPrint("Found theme <", themeID, "> to remove")
        del _theme_collection[themeID]
    else:
        debugPrint("NOT Found theme <", themeID, "> to remove")

    themePath = get_themes_path()
    themeFile = os.path.join(themePath, themeID + ".json")
    try:
        os.remove(themeFile)
    except OSError:
        debugPrint("failed to remove theme file: ", themeFile)
        pass


def get_current_theme():
    """ Get the currently selected theme """
    load_themes()  # make sure the themes are loaded
    debugPrint("getting the current theme for: ", _current_theme_id)
    return _theme_collection[_current_theme_id]  # @todo check if name exists


def theme_color(group, category):
    """
    Return the color in the current theme for the given group & category
    Groups : NODE_COLORS, ERROR_COLORS, HEATMAP_COLORS etc
    Category : "Visualizer", "Text", "Generators" etc
    """
    theme = get_current_theme()
    return theme[group][category]


def get_node_color(nodeID):
    """ Return the theme color of a node given its node ID """
    nodeCategory = get_node_category(nodeID)
    debugPrint("NodeID: ", nodeID, " is in category:", nodeCategory)
    nodeCategory = "Visualizer" if nodeCategory == "Viz" else nodeCategory

    theme = get_current_theme()
    debugPrint("Get node color for current theme name: ", theme[THEME_NAME])
    if nodeCategory in theme[NODE_COLORS]:
        debugPrint("Category: ", nodeCategory, " found in the theme")
        # return theme_color(NODE_COLORS, nodeCategory)
        with sv_preferences() as prefs:
            # print("node color category: ", nodeCategory)
            attr = theme_color_attr(nodeCategory)
            color = getattr(prefs, attr)
            debugPrint("get node color for attribute: ", attr, " : ", color)
            return color
    else:
        debugPrint("Category: ", nodeCategory, " NOT found in the theme")


def update_prefs_colors():
    with sv_preferences() as prefs:
        for group, categories in theme_color_attrs().items():
            for category, attr in categories.items():
                setattr(prefs, attr, theme_color(group, category))


def sverchok_trees():
    for ng in bpy.data.node_groups:
        if ng.bl_idname == "SverchCustomTreeType":
            yield ng


def apply_theme(ng=None):
    """ Apply theme colors """
    debugPrint("apply theme called")
    if not ng:
        for ng in sverchok_trees():
            apply_theme(ng)
    else:
        for n in filter(lambda n: hasattr(n, "set_color"), ng.nodes):
            n.set_color()


class SvApplyTheme(bpy.types.Operator):
    """
    Apply Sverchok theme
    """
    bl_idname = "node.sverchok_apply_theme2"
    bl_label = "Sverchok Apply theme"
    bl_options = {'REGISTER', 'UNDO'}

    tree_name = StringProperty()

    def execute(self, context):
        global _current_theme_id
        with sv_preferences() as prefs:
            _current_theme_id = prefs.theme_preset

        debugPrint("applying sverchok theme: ", _current_theme_id)
        if self.tree_name:
            ng = bpy.data.node_groups.get(self.tree_name)
            if ng:
                apply_theme(ng)
            else:
                return {'CANCELLED'}
        else:
            apply_theme()
        return {'FINISHED'}


class SvAddTheme(bpy.types.Operator):
    """
    Add current settings as new theme.
    Note: it will not update the hardcoded themes.
    """
    bl_idname = "node.sv_add_theme"
    bl_label = "Add Theme"

    themeName = StringProperty(name="Name:")
    overwrite = BoolProperty(name="Overwrite")

    def add_theme(self, themeName):
        debugPrint("add_theme in action: ", themeName)

        with sv_preferences() as prefs:
            theme = OrderedDict()
            theme[THEME_NAME] = themeName
            for group, categories in theme_color_attrs().items():
                groupColors = OrderedDict()
                for category, attr in categories.items():
                    groupColors[category] = getattr(prefs, attr)[:]
                theme[group] = groupColors

            debugPrint("theme: ", theme)

            themeID = theme_id(theme[THEME_NAME])
            save_theme(theme, themeID + ".json")

            load_themes(True)  # force reload themes
            cache_theme_preset_list()  # update theme ID list (for settings preset enum)

    def execute(self, context):
        debugPrint("EXECUTE the ADD preset operator")
        themeName = self.themeName
        themeID = theme_id(themeName)
        with sv_preferences() as prefs:
            if prefs.theme_preset == themeID and not self.overwrite:
                self.report({'ERROR'}, "A theme with given name already exists!")
            else:  # OK to add/update the theme
                self.add_theme(themeName)
                prefs.theme_preset = themeID  # select the newly added theme

        return {'FINISHED'}

    def invoke(self, context, event):
        debugPrint("INVOKE the ADD preset operator")
        with sv_preferences() as prefs:
            # themeID = get_current_themeID()
            themeID = prefs.theme_preset
            if themeID in _hardcoded_theme_ids:  # populate with generic theme name
                self.themeName = "Unamed Theme"
            else:  # populate with current theme's name (anticipating an update)
                theme = get_current_theme()
                self.themeName = theme[THEME_NAME]
        self.overwrite = False  # assume no overwrite by default
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'themeName')
        layout.prop(self, 'overwrite')


class SvRemoveTheme(bpy.types.Operator):
    """
    Remove currently selected theme.
    Note: it doesn't work on hardcoded themes.
    """
    bl_idname = "node.sv_remove_theme"
    bl_label = "Remove Theme"

    remove_confirm = BoolProperty(name="Confirm Remove")

    def remove_theme(self, themeName):
        debugPrint("remove_theme in action")
        remove_theme(themeName)
        load_themes(True)  # force reload themes
        cache_theme_preset_list()  # update theme ID list (for settings preset enum)

    def execute(self, context):
        debugPrint("EXECUTE the REMOVE preset operator")
        with sv_preferences() as prefs:
            themeID = prefs.theme_preset
            if themeID in _hardcoded_theme_ids:
                self.report({'ERROR'}, "Cannot remove default themes!")
            else:  # OK to remove (if confirmed)
                if self.remove_confirm:
                    theme = get_current_theme()
                    self.remove_theme(theme[THEME_NAME])
                    prefs.theme_preset = "default"  # select the default theme
                else:
                    self.report({'ERROR'}, "Must confirm to remove!")

        return {'FINISHED'}

    def invoke(self, context, event):
        debugPrint("INVOKE the REMOVE preset operator")
        with sv_preferences() as prefs:
            # themeID = get_current_themeID()
            themeID = prefs.theme_preset
            if themeID in _hardcoded_theme_ids:
                self.report({'ERROR'}, "Cannot remove default themes!")
                return {'FINISHED'}
            else:  # not a default theme ? => can be removed (if confirmed)
                self.remove_confirm = False
                return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label('Are you sure you want to remove current theme?')
        layout.prop(self, 'remove_confirm')


classes = [SvAddTheme, SvRemoveTheme, SvApplyTheme]


def register():
    save_default_themes()
    load_themes()
    cache_theme_preset_list()

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    register()
