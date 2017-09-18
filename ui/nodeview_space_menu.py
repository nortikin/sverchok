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
from sverchok.utils import get_node_class_reference
from sverchok.ui.sv_icons import custom_icon
# from nodeitems_utils import _node_categories

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
node_cats = make_node_cats()
addon_name = sverchok.__name__
menu_prefs = {}

# _items_to_remove = {}

def get_icon_switch():
    addon = bpy.context.user_preferences.addons.get(addon_name)

    if addon and hasattr(addon, "preferences"):
        return addon.preferences.show_icons


def icon(display_icon):
    '''returns empty dict if show_icons is False, else the icon passed'''
    kws = {}
    if menu_prefs.get('show_icons'):
        if display_icon.startswith('SV_'):
            kws = {'icon_value': custom_icon(display_icon)}
        else: 
            kws = {'icon': display_icon}
    return kws


def node_icon(node_ref):
    '''returns empty dict if show_icons is False, else the icon passed'''
    if not menu_prefs.get('show_icons'):
        return {}
    else:
        if hasattr(node_ref, 'sv_icon'):
            iconID = custom_icon(node_ref.sv_icon)
            return {'icon_value': iconID} if iconID else {}
        elif hasattr(node_ref, 'bl_icon') and node_ref.bl_icon != 'OUTLINER_OB_EMPTY':
            iconID = node_ref.bl_icon
            return {'icon': iconID} if iconID else {}
        else:
            return {}


def layout_draw_categories(layout, node_details):

    add_n_grab = 'node.add_node'
    for node_info in node_details:

        if node_info[0] == 'separator':
            layout.separator()
            continue

        if not node_info:
            print(repr(node_info), 'is incomplete, or unparsable')
            continue

        bl_idname = node_info[0]
        node_ref = get_node_class_reference(bl_idname)

        if hasattr(node_ref, "bl_label"):
            layout_params = dict(text=node_ref.bl_label, **node_icon(node_ref))
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
        # prop_menu_enum(data, property, text="", text_ctxt="", icon='NONE')


# quick class factory.
def make_class(name, bl_label):
    name = 'NODEVIEW_MT_Add' + name
    return type(name, (NodeViewMenuTemplate,), {'bl_label': bl_label})


class NODEVIEW_MT_Dynamic_Menu(bpy.types.Menu):
    bl_label = "Sverchok Nodes"

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in sv_tree_types:
            menu_prefs['show_icons'] = get_icon_switch()
            # print('showing', menu_prefs['show_icons'])
            return True

    def draw(self, context):

        # dont show up in other tree menu (needed because we bypassed poll by appending manually)
        tree_type = context.space_data.tree_type
        if not tree_type in sv_tree_types:
            return

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        if self.bl_idname == 'NODEVIEW_MT_Dynamic_Menu':
            layout.operator("node.sv_extra_search", text="Search", icon='OUTLINER_DATA_FONT')


        layout.separator()
        layout.menu("NODEVIEW_MT_AddGenerators", **icon('OBJECT_DATAMODE'))
        layout.menu("NODEVIEW_MT_AddTransforms", **icon('MANIPUL'))
        layout.menu("NODEVIEW_MT_AddAnalyzers", **icon('VIEWZOOM'))
        layout.menu("NODEVIEW_MT_AddModifiers", **icon('MODIFIER'))
        layout.separator()
        layout.menu("NODEVIEW_MT_AddNumber")
        layout.menu("NODEVIEW_MT_AddVector")
        layout.menu("NODEVIEW_MT_AddMatrix")
        layout.menu("NODEVIEW_MT_AddLogic", **icon("SV_LOGIC"))
        layout.menu("NODEVIEW_MT_AddListOps", **icon('NLA'))
        layout.separator()
        layout.menu("NODEVIEW_MT_AddViz", **icon('RESTRICT_VIEW_OFF'))
        layout.menu("NODEVIEW_MT_AddText")
        layout.menu("NODEVIEW_MT_AddScene", **icon('SCENE_DATA'))
        layout.menu("NODEVIEW_MT_AddLayout", **icon("SV_LAYOUT"))
        layout.menu("NODE_MT_category_SVERCHOK_BPY_Data", icon="BLENDER")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddNetwork", **icon("OOPS"))
        layout.menu("NODEVIEW_MT_AddBetas", **icon("SV_BETA"))
        layout.menu("NODEVIEW_MT_AddAlphas", **icon("SV_ALPHA"))
        layout.separator() 
        layout.menu("NODE_MT_category_SVERCHOK_GROUPS", icon="RNA")


class NODEVIEW_MT_AddGenerators(bpy.types.Menu):
    bl_label = "Generators"

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, node_cats[self.bl_label])
        layout.menu("NODEVIEW_MT_AddGeneratorsExt", **icon('PLUGIN'))


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


# def ff_unregister_node_categories():
#     """
#     Below (in the register function) we remove the SVERCHOK group from _node_categories collection, by doing:

#         _items_to_remove['sverchok_popped'] = _node_categories.pop("SVERCHOK")

#     this allows us to populate the NODE_MT_add menu as we want. In doing so we lose the automatic unregistration of 
#     various menu and category classes. This function behaves as a dedicated removal of those classes (for F8 and disable add-on),
#     """

#     def ff_unregister_node_cat_types(cats):
#         for mt in cats[2]:
#             bpy.utils.unregister_class(mt)
#         for pt in cats[3]:
#             bpy.utils.unregister_class(pt)

#     cat_types = _items_to_remove['sverchok_popped']
#     if cat_types:
#         ff_unregister_node_cat_types(cat_types)

#     del _items_to_remove['sverchok_popped']



def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)

    # we pop sverchok from the standard nodecat collection to avoid the menu items appearing in the default Add node menu.
    # _items_to_remove['sverchok_popped'] = _node_categories.pop("SVERCHOK")

    # bpy.types.NODE_MT_add.append(bpy.types.NODEVIEW_MT_Dynamic_Menu.draw)


def unregister():
    # bpy.types.NODE_MT_add.remove(bpy.types.NODEVIEW_MT_Dynamic_Menu.draw)

    for class_name in classes:
        bpy.utils.unregister_class(class_name)

    # because we popped sverchok off the nodecat collection in register, we have to do our own class unregistration here.
    # ff_unregister_node_categories()
