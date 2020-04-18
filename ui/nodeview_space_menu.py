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

from sverchok.menu import make_node_cats, draw_add_node_operator
from sverchok.utils import get_node_class_reference
from sverchok.utils.extra_categories import get_extra_categories
from sverchok.ui.sv_icons import node_icon, icon, get_icon_switch, custom_icon
from sverchok.ui import presets
# from nodeitems_utils import _node_categories

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
node_cats = make_node_cats()
#menu_prefs = {}

# _items_to_remove = {}

def layout_draw_categories(layout, node_details):

    for node_info in node_details:

        if node_info[0] == 'separator':
            layout.separator()
            continue

        if not node_info:
            print(repr(node_info), 'is incomplete, or unparsable')
            continue

        bl_idname = node_info[0]

        # this is a node bl_idname that can be registered but shift+A can drop it from showing.
        if bl_idname == 'ScalarMathNode':
            continue

        node_ref = get_node_class_reference(bl_idname)

        if hasattr(node_ref, "bl_label"):
            layout_params = dict(text=node_ref.bl_label, **node_icon(node_ref))
        elif bl_idname == 'NodeReroute':
            layout_params = dict(text='Reroute',icon_value=custom_icon('SV_REROUTE'))
        else:
            continue

        node_op = draw_add_node_operator(layout, bl_idname, params=layout_params)

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
            #menu_prefs['show_icons'] = get_icon_switch()
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
        layout.menu("NODEVIEW_MT_AddCurves", **icon('OUTLINER_OB_CURVE'))
        layout.menu("NODEVIEW_MT_AddSurfaces", **icon('SURFACE_DATA'))
        layout.menu("NODEVIEW_MT_AddFields", **icon('OUTLINER_OB_FORCE_FIELD'))
        layout.menu("NODEVIEW_MT_AddTransforms", **icon('ORIENTATION_LOCAL'))
        layout.menu("NODEVIEW_MT_AddAnalyzers", **icon('VIEWZOOM'))
        layout.menu("NODEVIEW_MT_AddModifiers", **icon('MODIFIER'))
        layout.menu("NODEVIEW_MT_AddCAD", **icon('TOOL_SETTINGS'))
        layout.separator()
        layout.menu("NODEVIEW_MT_AddNumber", **icon("SV_NUMBER"))
        layout.menu("NODEVIEW_MT_AddVector", **icon("SV_VECTOR"))
        layout.menu("NODEVIEW_MT_AddMatrix", **icon('EMPTY_AXIS'))
        layout.menu("NODEVIEW_MT_AddQuaternion", **icon('SV_QUATERNION'))
        layout.menu("NODEVIEW_MT_AddLogic", **icon("SV_LOGIC"))
        layout.menu("NODEVIEW_MT_AddListOps", **icon('NLA'))
        layout.menu("NODEVIEW_MT_AddDictionary", icon='OUTLINER_OB_FONT')
        layout.separator()
        layout.menu("NODEVIEW_MT_AddViz", **icon('RESTRICT_VIEW_OFF'))
        layout.menu("NODEVIEW_MT_AddText", icon='TEXT')
        layout.menu("NODEVIEW_MT_AddScene", **icon('SCENE_DATA'))
        layout.menu("NODEVIEW_MT_AddLayout", icon='NODETREE')
        layout.menu("NODE_MT_category_SVERCHOK_BPY_Data", icon="BLENDER")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddNetwork", **icon("SYSTEM"))
        layout.menu("NODEVIEW_MT_AddBetas", **icon("SV_BETA"))
        layout.menu("NODEVIEW_MT_AddAlphas", **icon("SV_ALPHA"))
        layout.separator()
        layout.menu("NODE_MT_category_SVERCHOK_GROUPS", icon="RNA")
        layout.menu("NODEVIEW_MT_AddPresetOps", icon="SETTINGS")

        extra_categories = get_extra_categories()
        if extra_categories:
            layout.separator()
            for category in extra_categories:
                layout.menu("NODEVIEW_MT_EX_" + category.identifier)


class NODEVIEW_MT_AddGenerators(bpy.types.Menu):
    bl_label = "Generator"

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

preset_category_menus = dict()

def make_preset_category_menu(category):
    global preset_category_menus
    if category in preset_category_menus:
        return preset_category_menus[category]

    class SvPresetCategorySubmenu(bpy.types.Menu):
        bl_label = category

        def draw(self, context):
            layout = self.layout
            presets.draw_presets_ops(layout, category=category, context=context)

    category_id = presets.replace_bad_chars(category)
    class_name = "NODEVIEW_MT_PresetCategory__" + category_id
    SvPresetCategorySubmenu.__name__ = class_name
    bpy.utils.register_class(SvPresetCategorySubmenu)
    preset_category_menus[category] = SvPresetCategorySubmenu
    return SvPresetCategorySubmenu

class NODEVIEW_MT_AddPresetOps(bpy.types.Menu):
    bl_label = "Presets"

    def draw(self, context):
        layout = self.layout
        presets.draw_presets_ops(layout, context=context)
        for category in presets.get_category_names():
            class_name = preset_category_menus[category].__name__
            layout.menu(class_name)

extra_category_menu_classes = dict()

def make_extra_category_menus():
    global extra_category_menu_classes
    extra_categories = get_extra_categories()
    menu_classes = []
    for category in extra_categories:
        if category.identifier in extra_category_menu_classes:
            clazz = extra_category_menu_classes[category.identifier]
            menu_classes.append(clazz)
        else:
            class NODEVIEW_MT_ExtraCategoryMenu(bpy.types.Menu):
                bl_label = category.name

                def draw(self, context):
                    nodes = [[item.nodetype] for item in self.category_items] 
                    layout_draw_categories(self.layout, nodes)

            class_name = "NODEVIEW_MT_EX_" + category.identifier
            items = list(category.items(None))
            menu_class = type(class_name, (NODEVIEW_MT_ExtraCategoryMenu,), {'category_items': items})
            menu_classes.append(menu_class)
            extra_category_menu_classes[category.identifier] = menu_class
            bpy.utils.register_class(menu_class)
    return menu_classes

classes = [
    NODEVIEW_MT_Dynamic_Menu,
    NODEVIEW_MT_AddListOps,
    NODEVIEW_MT_AddModifiers,
    NODEVIEW_MT_AddGenerators,
    NODEVIEW_MT_AddPresetOps,
    # like magic.
    # make | NODEVIEW_MT_Add + class name , menu name
    make_class('GeneratorsExt', "Generators Extended"),
    make_class('Curves', "Curves"),
    make_class('Surfaces', "Surfaces"),
    make_class('Fields', "Fields"),
    make_class('Transforms', "Transforms"),
    make_class('Analyzers', "Analyzers"),
    make_class('Viz', "Viz"),
    make_class('Text', "Text"),
    make_class('Scene', "Scene"),
    make_class('Layout', "Layout"),
    make_class('Listmain', "List Main"),
    make_class('Liststruct', "List Struct"),
    make_class('Dictionary', "Dictionary"),
    make_class('Number', "Number"),
    make_class('Vector', "Vector"),
    make_class('Matrix', "Matrix"),
    make_class('Quaternion', "Quaternion"),
    make_class('CAD', "CAD"),
    make_class('ModifierChange', "Modifier Change"),
    make_class('ModifierMake', "Modifier Make"),
    make_class('Logic', "Logic"),
    make_class('Network', "Network"),
    make_class('Betas', "Beta Nodes"),
    make_class('Alphas', "Alpha Nodes"),
]

def register():
    for category in presets.get_category_names():
        make_preset_category_menu(category)
    for class_name in classes:
        bpy.utils.register_class(class_name)

def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
    for category in presets.get_category_names():
        bpy.utils.unregister_class(preset_category_menus[category])

