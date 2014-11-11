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

'''
zeffii 2014.

borrows heavily from insights provided by Dynamic Space Bar!
but massively condensed for sanity.
'''

import bpy
from bpy.props import (
    StringProperty,
)

import sverchok
from sverchok.menu import make_node_cats

node_cats = make_node_cats()

addon_name = sverchok.__name__

menu_prefs = {}


def get_icon_switch():
    addon = bpy.context.user_preferences.addons.get(addon_name)

    if addon and hasattr(addon, "preferences"):
        return addon.preferences.show_icons


def layout_draw_categories(layout, node_details):
    show_icons = menu_prefs.get('show_icons')

    add_n_grab = 'node.add_node'
    for node_info in node_details:
        num_items = len(node_info)
        if not num_items in {2, 3}:
            print(repr(node_info), 'is incomplete, or unparsable')
            continue

        if show_icons:
            if num_items == 3:
                bl_idname, shortname, icon = node_info
                layout_params = dict(text=shortname, icon=icon)
            else:
                bl_idname, shortname = node_info
                layout_params = dict(text=shortname)
        else:
            # explicit chop of icon data
            bl_idname, shortname = node_info[:2]
            layout_params = dict(text=shortname)

        node_op = layout.operator(add_n_grab, **layout_params)
        node_op.type = bl_idname
        node_op.use_transform = True


# does not get registered
class NodeViewMenuTemplate(bpy.types.Menu):
    bl_label = ""

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


# quick class factory.
def make_class(name, bl_label):
    name = 'NODEVIEW_MT_Add' + name
    return type(name, (NodeViewMenuTemplate,), {'bl_label': bl_label})


class NODEVIEW_MT_Dynamic_Menu(bpy.types.Menu):
    bl_label = "Sverchok Nodes"

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if (tree_type == 'SverchCustomTreeType'):
            menu_prefs['show_icons'] = get_icon_switch()
            # print('showing', menu_prefs['show_icons'])
            return True

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        s = layout.operator("node.add_search", text="Search", icon='VIEWZOOM')
        s.use_transform = True

        show_icons = menu_prefs.get('show_icons')

        layout.separator()
        if show_icons:
            layout.menu("NODEVIEW_MT_AddGenerators", icon='OBJECT_DATAMODE')
            layout.menu("NODEVIEW_MT_AddTransforms", icon='MANIPUL')
            layout.menu("NODEVIEW_MT_AddAnalyzers", icon='BORDERMOVE')
            layout.menu("NODEVIEW_MT_AddModifiers", icon='MODIFIER')
        else:
            layout.menu("NODEVIEW_MT_AddGenerators")
            layout.menu("NODEVIEW_MT_AddTransforms")
            layout.menu("NODEVIEW_MT_AddAnalyzers")
            layout.menu("NODEVIEW_MT_AddModifiers")

        layout.separator()
        layout.menu("NODEVIEW_MT_AddNumber")
        layout.menu("NODEVIEW_MT_AddVector")
        layout.menu("NODEVIEW_MT_AddMatrix")
        layout.menu("NODEVIEW_MT_AddLogic")
        layout.menu("NODEVIEW_MT_AddListOps")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddViz")
        layout.menu("NODEVIEW_MT_AddText")
        layout.menu("NODEVIEW_MT_AddScene")
        layout.menu("NODEVIEW_MT_AddLayout")
        layout.separator()
        if show_icons:
            layout.menu("NODEVIEW_MT_AddBetas", icon='OUTLINER_DATA_POSE')
            layout.menu("NODEVIEW_MT_AddAlphas", icon='ERROR')
        else:
            layout.menu("NODEVIEW_MT_AddBetas")
            layout.menu("NODEVIEW_MT_AddAlphas")


class NODEVIEW_MT_AddGenerators(bpy.types.Menu):
    bl_label = "Generators"

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, node_cats[self.bl_label])
        if menu_prefs.get('show_icons'):
            layout.menu("NODEVIEW_MT_AddGeneratorsExt", icon='PLUGIN')
        else:
            layout.menu("NODEVIEW_MT_AddGeneratorsExt")


class NODEVIEW_MT_AddModifiers(bpy.types.Menu):
    bl_label = "Modifiers"

    def draw(self, context):
        layout = self.layout
        layout.menu("NODEVIEW_MT_AddModifierChange")
        layout.menu("NODEVIEW_MT_AddModifierMake")


class NODEVIEW_MT_AddListOps(bpy.types.Menu):
    bl_label = "List"

    def draw(self, context):
        layout = self.layout
        layout.menu("NODEVIEW_MT_AddListmain")
        layout.menu("NODEVIEW_MT_AddListstruct")
        layout_draw_categories(self.layout, node_cats["List Masks"])


classes = [
    NODEVIEW_MT_Dynamic_Menu,
    NODEVIEW_MT_AddListOps,
    NODEVIEW_MT_AddModifiers,
    NODEVIEW_MT_AddGenerators,
    # like magic.
    # make | NODEVIEW_MT_Add + class name , menu name
    make_class('GeneratorsExt', "Extended Generators"),
    make_class('Transforms', "Transforms"),
    make_class('Analyzers', "Analyzers"),
    make_class('Viz', "Viz"),
    make_class('Text', "Text"),
    make_class('Scene', "Scene"),
    make_class('Layout', "Layout"),
    make_class('Listmain', "List main"),
    make_class('Liststruct', "List struct"),
    make_class('Number', "Number"),
    make_class('Vector', "Vector"),
    make_class('Matrix', "Matrix"),
    make_class('ModifierChange', "Modifier Change"),
    make_class('ModifierMake', "Modifier Make"),
    make_class('Logic', "Logic"),
    make_class('Betas', "Beta Nodes"),
    make_class('Alphas', "Alpha Nodes"),
]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS', ctrl=True)
        kmi.properties.name = "NODEVIEW_MT_Dynamic_Menu"


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Node Editor']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "NODEVIEW_MT_Dynamic_Menu":
                    km.keymap_items.remove(kmi)
                    break
