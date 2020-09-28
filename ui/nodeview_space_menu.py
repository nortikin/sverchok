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

from sverchok.menu import make_node_cats, draw_add_node_operator, is_submenu_call, get_submenu_call_name, compose_submenu_name
from sverchok.utils import get_node_class_reference
from sverchok.utils.extra_categories import get_extra_categories
from sverchok.ui.sv_icons import node_icon, icon, get_icon_switch, custom_icon
from sverchok.ui import presets
# from nodeitems_utils import _node_categories

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
node_cats = make_node_cats()

menu_class_by_title = dict()

def category_has_nodes(cat_name):
    cat = node_cats[cat_name]
    for item in cat:
        rna = get_node_class_reference(item[0])
        if rna and not item[0] == 'separator':
            return True
    return False
#menu_prefs = {}

# _items_to_remove = {}
menu_structure = [
    ["separator"],
    ["NODEVIEW_MT_AddGenerators", 'OBJECT_DATAMODE'],
    ["NODEVIEW_MT_AddCurves", 'OUTLINER_OB_CURVE'],
    ["NODEVIEW_MT_AddSurfaces", 'SURFACE_DATA'],
    ["NODEVIEW_MT_AddFields", 'OUTLINER_OB_FORCE_FIELD'],
    ["NODEVIEW_MT_AddSolids", 'MESH_CUBE'],
    ["NODEVIEW_MT_AddTransforms", 'ORIENTATION_LOCAL'],
    ["NODEVIEW_MT_AddAnalyzers", 'VIEWZOOM'],
    ["NODEVIEW_MT_AddModifiers", 'MODIFIER'],
    ["NODEVIEW_MT_AddCAD", 'TOOL_SETTINGS'],
    ["separator"],
    ["NODEVIEW_MT_AddNumber", "SV_NUMBER"],
    ["NODEVIEW_MT_AddVector", "SV_VECTOR"],
    ["NODEVIEW_MT_AddMatrix", 'EMPTY_AXIS'],
    ["NODEVIEW_MT_AddQuaternion", 'SV_QUATERNION'],
    ["NODEVIEW_MT_AddLogic", "SV_LOGIC"],
    ["NODEVIEW_MT_AddListOps", 'NLA'],
    ["NODEVIEW_MT_AddDictionary", 'OUTLINER_OB_FONT'],
    ["NODEVIEW_MT_AddLadybug", 'LIGHT_SUN'],
    ["separator"],
    ["NODEVIEW_MT_AddViz", 'RESTRICT_VIEW_OFF'],
    ["NODEVIEW_MT_AddText", 'TEXT'],
    ["NODEVIEW_MT_AddScene", 'SCENE_DATA'],
    ["NODEVIEW_MT_AddExchange", 'SCENE_DATA'],
    ["NODEVIEW_MT_AddLayout", 'NODETREE'],
    ["NODE_MT_category_SVERCHOK_BPY_Data", "BLENDER"],
    ["separator"],
    ["NODEVIEW_MT_AddNetwork", "SYSTEM"],
    ["NODEVIEW_MT_AddSVG", "SV_SVG"],
    ["NODEVIEW_MT_AddBetas", "SV_BETA"],
    ["NODEVIEW_MT_AddAlphas", "SV_ALPHA"],
    ["separator"],
    ["NODE_MT_category_SVERCHOK_GROUPS", "RNA"],
    ["NODEVIEW_MT_AddPresetOps", "SETTINGS"],
]
def layout_draw_categories(layout, category_name, node_details):
    
    global menu_class_by_title

    for node_info in node_details:

        if node_info[0] == 'separator':
            layout.separator()
            continue

        if not node_info:
            print(repr(node_info), 'is incomplete, or unparsable')
            continue

        bl_idname = node_info[0]

        if is_submenu_call(bl_idname):
            submenu_title = get_submenu_call_name(bl_idname)
            menu_title = compose_submenu_name(category_name, bl_idname)
            menu_class = menu_class_by_title[menu_title]
            layout.menu(menu_class.__name__, text=submenu_title)
            continue

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
        layout_draw_categories(self.layout, self.bl_label, node_cats[self.bl_label])
        # prop_menu_enum(data, property, text="", text_ctxt="", icon='NONE')

# quick class factory.
def make_class(name, bl_label):
    global menu_class_by_title
    name = 'NODEVIEW_MT_Add' + name
    clazz = type(name, (NodeViewMenuTemplate,), {'bl_label': bl_label})
    menu_class_by_title[bl_label] = clazz
    return clazz

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

        for item in menu_structure:
            if item[0] == 'separator':
                layout.separator()
            else:
                if "Add" in item[0]:
                    name = item[0].split("Add")[1]
                    if name in node_cats:
                        if category_has_nodes(name):
                            layout.menu(item[0], **icon(item[1]))

                    else:
                        layout.menu(item[0], **icon(item[1]))
                else:
                # print('AA', globals()[item[0]].bl_label)
                    layout.menu(item[0], **icon(item[1]))

        extra_categories = get_extra_categories()
        if extra_categories:
            layout.separator()
            for category in extra_categories:
                layout.menu("NODEVIEW_MT_EX_" + category.identifier)

class NODEVIEW_MT_Solids_Special_Menu(bpy.types.Menu):
    bl_label = "Solids"
    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in sv_tree_types:
            #menu_prefs['show_icons'] = get_icon_switch()
            # print('showing', menu_prefs['show_icons'])
            return True
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout_draw_categories(self.layout, self.bl_label, node_cats[self.bl_label])


class NODEVIEW_MT_AddGenerators(bpy.types.Menu):
    bl_label = "Generator"

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, node_cats[self.bl_label])
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
        layout_draw_categories(self.layout, "List Masks", node_cats["List Masks"])
        layout_draw_categories(self.layout, "List Mutators", node_cats["List Mutators"])

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
                    layout_draw_categories(self.layout, category.name, nodes)

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
    make_class('CurvePrimitives', "Curves @ Primitives"),
    make_class('BezierCurves', "Curves @ Bezier"),
    make_class('NurbsCurves', "Curves @ NURBS"),
    make_class('Curves', "Curves"),
    make_class('NurbsSurfaces', "Surfaces @ NURBS"),
    make_class('Surfaces', "Surfaces"),
    make_class('Fields', "Fields"),
    make_class('MakeSolidFace', "Solids @ Make Face"),
    make_class('AnalyzeSolid', "Solids @ Analyze"),
    make_class('Solids', "Solids"),
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
    make_class('Ladybug', "Ladybug"),
    make_class('Logic', "Logic"),
    make_class('Network', "Network"),
    make_class('Exchange', "Exchange"),
    make_class('SVG', "SVG"),
    make_class('Betas', "Beta Nodes"),
    make_class('Alphas', "Alpha Nodes"),
    # NODEVIEW_MT_Solids_Special_Menu
]

def register():
    #global menu_class_by_title
    #menu_class_by_title = dict()

    for category in presets.get_category_names():
        make_preset_category_menu(category)
    for class_name in classes:
        bpy.utils.register_class(class_name)

def unregister():
    global menu_class_by_title

    for class_name in classes:
        bpy.utils.unregister_class(class_name)
    for category in presets.get_category_names():
        bpy.utils.unregister_class(preset_category_menus[category])

    menu_class_by_title = dict()

