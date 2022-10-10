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
from pathlib import Path

import bl_operators
import bpy

from sverchok.utils import get_node_class_reference
from sverchok.utils.extra_categories import get_extra_categories, extra_category_providers
from sverchok.ui.sv_icons import node_icon, icon, custom_icon
from sverchok.ui import presets
from sverchok.ui.presets import apply_default_preset
from sverchok.utils import yaml_parser


class MenuItem:  # todo ABC
    def draw(self, layout):
        pass


class Separator(MenuItem):
    def draw(self, layout):
        layout.separator()


class AddNode(MenuItem):
    def __init__(self, id_name):
        self.bl_idname = id_name
        # bpy.types.Node.bl_rna_get_subclass_py(self.id_name) - does not work during registration

    def draw(self, layout):
        node_cls = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
        if node_cls is not None:
            label = node_cls.bl_label  # todo node_cls.bl_rna.name ?
            icon_prop = node_icon(node_cls)
        elif self.bl_idname == 'NodeReroute':
            label = "Reroute"
            icon_prop = icon('SV_REROUTE')
        else:  # todo log missing nodes?
            label = f'{self.bl_idname} (not found)'
            icon_prop = {'icon': 'ERROR'}

        if node_cls is None:
            layout.label(text=label, **icon_prop)
            return
        default_context = bpy.app.translations.contexts.default
        add = layout.operator(SvNodeAddOperator.bl_idname,
                              text=label,
                              text_ctxt=default_context,
                              **icon_prop)
        add.type = self.bl_idname
        add.use_transform = True


class Category(MenuItem):
    def __init__(self, name, menu_cls, icon_name):
        self.name = name
        self.icon = icon_name
        self.menu_cls: CategoryMenuTemplate = menu_cls

    def draw(self, layout):
        layout.menu(self.menu_cls.__name__, **icon(self.icon))  # text=submenu_title)

    def draw_contents(self, layout):
        layout.menu_contents(self.menu_cls.__name__)

    def __iter__(self):
        return iter(e for e in self.menu_cls.draw_data)

    def walk_categories(self) -> 'Category':
        yield self
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'walk_categories'):
                yield from elem.walk_categories()

    def register(self):
        """Register itself and all its elements"""
        bpy.utils.register_class(self.menu_cls)
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'register'):
                elem.register()

    def unregister(self):
        """Register itself and all its elements"""
        bpy.utils.unregister_class(self.menu_cls)
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'unregister'):
                elem.unregister()

    def __repr__(self):
        return f'<NodeCategory "{self.name}">'


def pars_config(conf: list, menu_name, icon_name='BLANK1'):
    menu_name = menu_name.title().replace(' ', '')
    parsed_items = []

    # parsing menu elements
    for elem in conf:
        if isinstance(elem, dict):
            name = list(elem.keys())[0]
            value = list(elem.values())[0]
            props = dict()
            if isinstance(value, list):  # sub menu

                # pars sub menu properties
                for prop in value:
                    if not isinstance(prop, dict):  # some node or separator
                        continue
                    prop_value = list(prop.values())[0]
                    if isinstance(prop_value, list):  # some sub menu
                        continue
                    props.update(prop)

            elif value is None:  # empty category
                value = []
            else:  # menu property
                continue  # was already handled
            parsed_items.append(pars_config(value, name, **props))

        else:  # some value, separator?
            if all('-' == ch for ch in elem):  # separator
                parsed_items.append(Separator())
            else:
                parsed_items.append(AddNode(elem))

    # generate menu of current list
    cls_name = 'NODEVIEW_MT_SvCategory' + menu_name
    cls = type(cls_name,
               (CategoryMenuTemplate, bpy.types.Menu),
               {'bl_label': menu_name, 'draw_data': parsed_items})

    return Category(menu_name, cls, icon_name)


class CategoryMenuTemplate:
    bl_label = ''
    draw_data: list[MenuItem] = []  # items to draw

    def draw(self, context):
        for elem in self.draw_data:
            elem.draw(self.layout)

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in sv_tree_types:
            return True


menu_file = Path(__file__).parents[1] / 'index.yaml'
add_node_menu = pars_config(yaml_parser.load(menu_file), 'AllCategories', 'RNA')


class SvNodeAddOperator(bl_operators.node.NodeAddOperator, bpy.types.Operator):
    """Wrapper for node.add_node operator to add specific node"""

    bl_idname = "node.sv_add_node"
    bl_label = "Add SV node"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = self.create_node(context)
        apply_default_preset(node)
        return {'FINISHED'}

    @classmethod
    def description(cls, _context, properties):
        nodetype = properties["type"]
        node_cls = bpy.types.Node.bl_rna_get_subclass_py(nodetype)
        if node_cls is not None:
            return node_cls.docstring.get_tooltip()
        else:
            return ""

    # todo add poll method


sv_tree_types = {'SverchCustomTreeType', }
node_cats = dict()  # make_node_cats()

menu_class_by_title = dict()


# _items_to_remove = {}
menu_structure = [
    ["separator"],
    ["NODEVIEW_MT_AddGenerators", 'OBJECT_DATAMODE'],
    ["NODEVIEW_MT_AddCurves", 'OUTLINER_OB_CURVE'],
    ["NODEVIEW_MT_AddSurfaces", 'SURFACE_DATA'],
    ["NODEVIEW_MT_AddFields", 'OUTLINER_OB_FORCE_FIELD'],
    ["NODEVIEW_MT_AddSolids", 'MESH_CUBE'],
    ["NODEVIEW_MT_AddSpatial", 'POINTCLOUD_DATA'],
    ["NODEVIEW_MT_AddTransforms", 'ORIENTATION_LOCAL'],
    ["NODEVIEW_MT_AddAnalyzers", 'VIEWZOOM'],
    ["NODEVIEW_MT_AddModifiers", 'MODIFIER'],
    ["NODEVIEW_MT_AddCAD", 'TOOL_SETTINGS'],
    ["separator"],
    ["NODEVIEW_MT_AddNumber", "SV_NUMBER"],
    ["NODEVIEW_MT_AddVector", "SV_VECTOR"],
    ["NODEVIEW_MT_AddMatrix", 'EMPTY_AXIS'],
    ["NODEVIEW_MT_AddQuaternion", 'SV_QUATERNION'],
    ["NODEVIEW_MT_AddColor", 'COLOR'],
    ["NODEVIEW_MT_AddLogic", "SV_LOGIC"],
    ["NODEVIEW_MT_AddListOps", 'NLA'],
    ["NODEVIEW_MT_AddDictionary", 'OUTLINER_OB_FONT'],
    ["separator"],
    ["NODEVIEW_MT_AddViz", 'RESTRICT_VIEW_OFF'],
    ["NODEVIEW_MT_AddText", 'TEXT'],
    ["NODEVIEW_MT_AddScene", 'SCENE_DATA'],
    ["NODEVIEW_MT_AddExchange", 'ARROW_LEFTRIGHT'],
    ["NODEVIEW_MT_AddLayout", 'NODETREE'],
    ["NODEVIEW_MT_AddBPYData", "BLENDER"],
    ["separator"],
    ["NODEVIEW_MT_AddScript", "WORDWRAP_ON"],
    ["NODEVIEW_MT_AddNetwork", "SYSTEM"],
    ["NODEVIEW_MT_AddPulgaPhysics", "MOD_PHYSICS"],
    ["NODEVIEW_MT_AddSVG", "SV_SVG"],
    ["NODEVIEW_MT_AddBetas", "SV_BETA"],
    ["NODEVIEW_MT_AddAlphas", "SV_ALPHA"],
    ["separator"],
    ["NODE_MT_category_SVERCHOK_GROUP", "NODETREE"],
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


class SV_NodeTree_Poll():
    """
    mixin to detect if the current nodetree is a Sverchok type nodetree, if not poll returns False
    """
    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in sv_tree_types:
            return True


# quick class factory.
def make_class(name, bl_label):
    global menu_class_by_title
    name = 'NODEVIEW_MT_Add' + name
    clazz = type(name, (NodeViewMenuTemplate,), {'bl_label': bl_label})
    menu_class_by_title[bl_label] = clazz
    return clazz


class NODEVIEW_MT_Dynamic_Menu(CategoryMenuTemplate, bpy.types.Menu):
    """Shift+A menu"""
    bl_label = "Sverchok Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("node.sv_extra_search", text="Search", icon='OUTLINER_DATA_FONT')

        add_node_menu.draw_contents(self.layout)

        layout.menu('NODE_MT_category_SVERCHOK_GROUP', icon='NODETREE')
        layout.menu('NODEVIEW_MT_AddPresetOps', icon='SETTINGS')

        if extra_category_providers:
            for provider in extra_category_providers:
                if hasattr(provider, 'use_custom_menu') and provider.use_custom_menu:
                    layout.menu(provider.custom_menu)
                else:
                    for category in provider.get_categories():
                        layout.menu("NODEVIEW_MT_EX_" + category.identifier)


class NodePatialMenuTemplate(bpy.types.Menu, SV_NodeTree_Poll):
    bl_label = ""
    items = []

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        for i in self.items:
            item = menu_structure[i]
            layout.menu(item[0], **icon(item[1]))

# quick class factory.
def make_partial_menu_class(name, bl_label, items):
    name = f'NODEVIEW_MT_{name}_Partial_Menu'
    clazz = type(name, (NodePatialMenuTemplate,), {'bl_label': bl_label, 'items':items})
    return clazz

class NODEVIEW_MT_AddGenerators(bpy.types.Menu):
    bl_label = "Generator"

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, node_cats[self.bl_label])
        layout.menu("NODEVIEW_MT_AddGeneratorsExt", **icon('PLUGIN'))

class NODEVIEW_MT_AddBPYData(bpy.types.Menu):
    bl_label = "BPY Data"

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, node_cats['BPY Data'])
        layout_draw_categories(self.layout, self.bl_label, node_cats['Objects'])

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
    if not presets.check_category(category):
        return None

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
            if category in preset_category_menus:
                if category in preset_category_menus:
                    class_name = preset_category_menus[category].__name__
                    layout.menu(class_name)


class NODE_MT_category_SVERCHOK_GROUP(bpy.types.Menu):
    bl_label = "Group"

    def draw(self, context):
        layout = self.layout
        layout.operator('node.add_group_node')
        layout.operator('node.add_node_output_input', text="Group input").node_type = 'input'
        layout.operator('node.add_node_output_input', text="Group output").node_type = 'output'
        layout.operator('node.add_group_tree_from_selected')


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
    NODEVIEW_MT_AddBPYData,
    NODEVIEW_MT_AddPresetOps,
    NODE_MT_category_SVERCHOK_GROUP,
    SvNodeAddOperator,
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
    make_class('Spatial', "Spatial"),
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
    make_class('Color', "Color"),
    make_class('CAD', "CAD"),
    make_class('ModifierChange', "Modifier Change"),
    make_class('ModifierMake', "Modifier Make"),
    make_class('Logic', "Logic"),
    make_class('Script', "Script"),
    make_class('Network', "Network"),
    make_class('Exchange', "Exchange"),
    make_class('PulgaPhysics', "Pulga Physics"),
    make_class('SVG', "SVG"),
    make_class('Betas', "Beta Nodes"),
    make_class('Alphas', "Alpha Nodes"),

    # make | NODEVIEW_MT_ + class name +_Partial_Menu , menu name, menu items
    make_partial_menu_class('Basic_Data', 'Basic Data Types (1)', range(12, 20)),
    make_partial_menu_class('Mesh', 'Mesh (2)', [1, 7, 8, 9, 10]),
    make_partial_menu_class('Advanced_Objects', 'Advanced Objects (3)', [2, 3, 4, 5, 6, 28, 30, 32, 33]),
    make_partial_menu_class('Connection', 'Connection (4)', [21, 22, 23, 24, 26, 29, 31]),
    make_partial_menu_class('UI_tools', 'SV Interface (5)', [25, 35, 36])

]
def sv_draw_menu(self, context):
    """This is drawn in ADD menu of the header of a tree editor"""
    tree_type = context.space_data.tree_type
    if not tree_type in sv_tree_types:
        return
    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"

    if not any([(g.bl_idname in sv_tree_types) for g in bpy.data.node_groups]):
        layout.operator("node.new_node_tree", text="New Sverchok Node Tree", icon="RNA_ADD")
        return

    layout.menu_contents(NODEVIEW_MT_Dynamic_Menu.__name__)

def register():

    for category in presets.get_category_names():
        make_preset_category_menu(category)
    for class_name in classes:
        bpy.utils.register_class(class_name)
    bpy.types.NODE_MT_add.append(sv_draw_menu)
    add_node_menu.register()


def unregister():
    global menu_class_by_title

    add_node_menu.unregister()
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
    for category in presets.get_category_names():
        if category in preset_category_menus:
            bpy.utils.unregister_class(preset_category_menus[category])
    bpy.types.NODE_MT_add.remove(sv_draw_menu)
    menu_class_by_title = dict()
