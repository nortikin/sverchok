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

    def icon(display_icon):
        '''returns empty dict if show_icons is False, else the icon passed'''
        return {'icon': display_icon for i in [1] if show_icons and display_icon}

    def get_icon(node_ref):
        # some nodes don't declare a bl_icon, but most do so try/except is fine.
        try:
            _icon = getattr(node_ref, 'bl_icon')
            if _icon == 'OUTLINER_OB_EMPTY':
                _icon = None
        except:
            _icon = None
        return _icon

    add_n_grab = 'node.add_node'
    for node_info in node_details:

        if not node_info:
            print(repr(node_info), 'is incomplete, or unparsable')
            continue

        bl_idname = node_info[0]
        node_ref = getattr(bpy.types, bl_idname)

        display_icon = get_icon(node_ref)
        if hasattr(node_ref, "bl_label"):
            layout_params = dict(text=node_ref.bl_label, **icon(display_icon))
        elif bl_idname == 'NodeReroute':
            layout_params = dict(text='Reroute')
        else:
            continue

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
        if tree_type == 'SverchCustomTreeType':
            menu_prefs['show_icons'] = get_icon_switch()
            # print('showing', menu_prefs['show_icons'])
            return True

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        s = layout.operator("node.add_search", text="Search", icon='OUTLINER_DATA_FONT')
        s.use_transform = True

        show_icons = menu_prefs.get('show_icons')

        def icon(display_icon):
            '''returns empty dict if show_icons is False, else the icon passed'''
            return {'icon': display_icon for i in [1] if show_icons}

        layout.separator()

        layout.menu("NODEVIEW_MT_AddGenerators", **icon('OBJECT_DATAMODE'))
        layout.menu("NODEVIEW_MT_AddTransforms", **icon('MANIPUL'))
        layout.menu("NODEVIEW_MT_AddAnalyzers", **icon('VIEWZOOM'))
        layout.menu("NODEVIEW_MT_AddModifiers", **icon('MODIFIER'))

        layout.separator()
        layout.menu("NODEVIEW_MT_AddNumber")
        layout.menu("NODEVIEW_MT_AddVector")
        layout.menu("NODEVIEW_MT_AddMatrix")
        layout.menu("NODEVIEW_MT_AddLogic")
        layout.menu("NODEVIEW_MT_AddListOps", **icon('NLA'))
        layout.separator()
        layout.menu("NODEVIEW_MT_AddViz", **icon('RESTRICT_VIEW_OFF'))
        layout.menu("NODEVIEW_MT_AddText")
        layout.menu("NODEVIEW_MT_AddScene")
        layout.menu("NODEVIEW_MT_AddLayout")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddNetwork")
        layout.menu("NODEVIEW_MT_AddBetas", **icon('OUTLINER_DATA_POSE'))
        layout.menu("NODEVIEW_MT_AddAlphas", **icon('ERROR'))


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
        layout_draw_categories(self.layout, node_cats["List Mutators"])


classes = [
    NODEVIEW_MT_Dynamic_Menu,
    NODEVIEW_MT_AddListOps,
    NODEVIEW_MT_AddModifiers,
    NODEVIEW_MT_AddGenerators,
    # like magic.
    # make | NODEVIEW_MT_Add + class name , menu name
    make_class('GeneratorsExt', "Generators Extended"),
    make_class('Transforms', "Transforms"),
    make_class('Analyzers', "Analyzers"),
    make_class('Viz', "Viz"),
    make_class('Text', "Text"),
    make_class('Scene', "Scene"),
    make_class('Layout', "Layout"),
    make_class('Listmain', "List Main"),
    make_class('Liststruct', "List Struct"),
    make_class('Number', "Number"),
    make_class('Vector', "Vector"),
    make_class('Matrix', "Matrix"),
    make_class('ModifierChange', "Modifier Change"),
    make_class('ModifierMake', "Modifier Make"),
    make_class('Logic', "Logic"),
    make_class('Network', "Network"),
    make_class('Betas', "Beta Nodes"),
    make_class('Alphas', "Alpha Nodes"),
]

nodeview_keymaps = []

def add_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS', ctrl=True)
        kmi.properties.name = "NODEVIEW_MT_Dynamic_Menu"
        nodeview_keymaps.append((km, kmi))
    
def remove_keymap():
    for km, kmi in nodeview_keymaps:
        km.keymap_items.remove(kmi)
    nodeview_keymaps.clear()

def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)
    add_keymap()


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
    remove_keymap()
