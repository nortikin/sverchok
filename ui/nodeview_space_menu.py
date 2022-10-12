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
from collections import defaultdict
from pathlib import Path
from typing import Iterator, Union, TypeVar

import bl_operators
import bpy
from bpy.props import StringProperty

from sverchok.ui.sv_icons import node_icon, icon, get_icon_switch
from sverchok.ui import presets
from sverchok.ui.presets import apply_default_preset
from sverchok.utils import yaml_parser
from sverchok.utils.modules_inspection import iter_classes_from_module
from sverchok.utils.dummy_nodes import dummy_nodes_dict


CutSelf = TypeVar("CutSelf", bound="Category")
sv_tree_types = {'SverchCustomTreeType', }


class MenuItem:  # todo ABC
    def draw(self, layout):
        pass


class Separator(MenuItem):
    def draw(self, layout):
        layout.separator()


class AddNode(MenuItem):
    def __init__(self, id_name):
        self.bl_idname = id_name
        self._label = None
        self._icon_prop = None

    @property
    def label(self):
        """This and other properties of the class can't be accessed during
        module initialization and registration"""
        if self._label is None:
            node_cls = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
            if self.bl_idname == 'NodeReroute':
                self._label = "Reroute"
            # todo check labels of dependent classes after their refactoring
            elif node_cls is not None:
                self._label = node_cls.bl_label  # todo node_cls.bl_rna.name ?
            else:  # todo log missing nodes?
                self._label = f'{self.bl_idname} (not found)'
        return self._label

    @property
    def icon_prop(self):
        if self._icon_prop is None:
            node_cls = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
            if self.bl_idname == 'NodeReroute':
                self._icon_prop = icon('SV_REROUTE')
            elif self.dependency:
                self._icon_prop = {'icon': 'ERROR'}
            elif node_cls is not None:  # can be dummy class here
                self._icon_prop = node_icon(node_cls)
            else:  # todo log missing nodes?
                self._icon_prop = {'icon': 'ERROR'}
        return self._icon_prop

    @property
    def dependency(self):
        _, dep = dummy_nodes_dict.get(self.bl_idname, (None, ''))
        return dep

    def draw(self, layout, only_icon=False):
        node_cls = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
        icon_prop = self.icon_prop if only_icon or get_icon_switch() else {}

        if not self.dependency and node_cls is None:
            layout.label(text=self.label, **icon_prop)
            return

        op = ShowMissingDependsOperator if self.dependency else SvNodeAddOperator
        default_context = bpy.app.translations.contexts.default
        add = layout.operator(op.bl_idname,
                              text=self.label if not only_icon else '',
                              text_ctxt=default_context,
                              **icon_prop)
        add.type = self.bl_idname
        add.use_transform = True
        add.dependency = self.dependency

    def search_match(self, request):
        request = request.upper()
        if request in self.label.upper():
            return True
        node_class = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
        if not node_class or not hasattr(node_class, 'docstring'):
            return False
        if request in node_class.docstring.get_shorthand():
            return True
        if request in node_class.docstring.get_tooltip():
            return True
        return False


class Category(MenuItem):
    def __init__(self, name, menu_cls, icon_name='BLANK1', extra_menu=''):
        self.name = name
        self.icon = icon_name
        self.extra_menu = extra_menu
        self.menu_cls: CategoryMenuTemplate = menu_cls

    def draw(self, layout):
        icon_prop = icon(self.icon) if get_icon_switch() else {}
        layout.menu(self.menu_cls.__name__, **icon_prop)  # text=submenu_title)

    def draw_contents(self, layout):
        layout.menu_contents(self.menu_cls.__name__)

    def __iter__(self) -> Iterator[Union[Separator, AddNode, 'Category']]:
        return iter(e for e in self.menu_cls.draw_data)

    def walk_categories(self) -> 'Category':
        yield self
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'walk_categories'):
                yield from elem.walk_categories()

    def register(self):
        """Register itself and all its elements.
        Can be called several times by Sverchok's extensions"""
        if not self.is_registered:
            bpy.utils.register_class(self.menu_cls)
        for elem in self.walk_categories():
            if not elem.is_registered:
                elem.register()

    @property
    def is_registered(self):
        return hasattr(bpy.types, self.menu_cls.__name__)

    def unregister(self):
        """Register itself and all its elements"""
        bpy.utils.unregister_class(self.menu_cls)
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'unregister'):
                elem.unregister()

    def __repr__(self):
        return f'<NodeCategory "{self.name}">'

    @classmethod
    def from_config(cls, conf: list, menu_name, **extra_props) -> CutSelf:
        """Extra_props should have keys oly from the __init__ method"""
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
                parsed_items.append(cls.from_config(value, name, **props))

            else:  # some value, separator?
                if all('-' == ch for ch in elem):  # separator
                    parsed_items.append(Separator())
                else:
                    parsed_items.append(AddNode(elem))

        # generate menu of current list
        cls_name = 'NODEVIEW_MT_SvCategory' + menu_name.title().replace(' ', '')
        menu_cls = type(cls_name,
                   (CategoryMenuTemplate, bpy.types.Menu),
                   {'bl_label': menu_name, 'draw_data': parsed_items})

        return cls(menu_name, menu_cls, **extra_props)

    def append_from_config(self, config: list):
        """It should be called before registration functions"""
        new_categories = []
        for cat in config:
            cat_name = list(cat.keys())[0]
            items = list(cat.values())[0]
            new_categories.append(self.from_config(items, cat_name))
        self.menu_cls.draw_data.extend(new_categories)


class SverchokContext:
    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in sv_tree_types:
            return True


class CategoryMenuTemplate(SverchokContext):
    bl_label = ''
    draw_data = []  # items to draw

    def draw(self, context):
        for elem in self.draw_data:
            elem.draw(self.layout)


menu_file = Path(__file__).parents[1] / 'index.yaml'
add_node_menu = Category.from_config(yaml_parser.load(menu_file), 'AllCategories', icon_name='RNA')


class AddNodeOp(bl_operators.node.NodeAddOperator):
    dependency: StringProperty()

    _node_classes = dict()

    @classmethod
    def node_classes(cls) -> dict[str, type]:
        if not cls._node_classes:
            import sverchok  # not available during initialization of the module
            for cls_ in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
                cls._node_classes[cls_.bl_idname] = cls_
        return cls._node_classes

    @classmethod
    def description(cls, _context, properties):
        node_type = properties["type"]
        tooltip = ''
        if node_type in dummy_nodes_dict:
            if node_cls := cls.node_classes().get(node_type):
                tooltip = node_cls.docstring.get_tooltip()
            gap = "\n\n" if tooltip else ''
            tooltip = tooltip + f"{gap}Dependency: {properties.dependency}"
        else:
            if node_cls := bpy.types.Node.bl_rna_get_subclass_py(node_type):
                tooltip = node_cls.docstring.get_tooltip()
        return tooltip


class SvNodeAddOperator(AddNodeOp, bpy.types.Operator):
    """Wrapper for node.add_node operator to add specific node"""

    bl_idname = "node.sv_add_node"
    bl_label = "Add SV node"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = self.create_node(context)
        apply_default_preset(node)
        return {'FINISHED'}

    # todo add poll method


class ShowMissingDependsOperator(AddNodeOp, bpy.types.Operator):
    bl_idname = 'node.show_missing_dependencies'
    bl_label = 'Show missing dependencies'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # the message can be customized if to generate separate class for each node
        cls.poll_message_set('The library is not installed')
        return False


class NODEVIEW_MT_Dynamic_Menu(CategoryMenuTemplate, bpy.types.Menu):
    """Shift+A menu"""
    bl_label = "Sverchok Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("node.sv_extra_search", text="Search", icon='OUTLINER_DATA_FONT')

        add_node_menu.draw_contents(self.layout)

        layout.menu('NODE_MT_category_SVERCHOK_GROUP', icon='NODETREE')  # todo add these two lines to UiToolsPartialMenu
        layout.menu('NODEVIEW_MT_AddPresetOps', icon='SETTINGS')


class CallPartialMenu(SverchokContext, bpy.types.Operator):
    bl_idname = "node.call_partial_menu"
    bl_label = "Call partial menu"
    bl_options = {'REGISTER', 'UNDO'}

    menu_name: StringProperty()

    def execute(self, context):

        def draw(_self, context):
            _self.layout.prop_menu_enum(self, 'test')
            for cat in add_node_menu.walk_categories():
                if cat.extra_menu == self.menu_name:
                    cat.draw(_self.layout)

        context.window_manager.popup_menu(draw, title=self.menu_name, icon='BLANK1')
        return {'FINISHED'}


class NodeCategoryMenu(SverchokContext, bpy.types.Menu):
    """https://blender.stackexchange.com/a/269716"""
    bl_label = "Node Categories"
    bl_idname = "NODEVIEW_MT_node_category_menu"

    @property
    def categories(self):
        if not self._categories:
            import sverchok
            cats = defaultdict(list)
            for cls in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
                if name := getattr(cls, 'solid_catergory', None):
                    cats[name].append(AddNode(cls.bl_idname))
            self._categories = cats
        return self._categories

    _categories = dict()
    _layout_values = dict()

    def draw(self, context):
        layout = self.layout
        if not self.categories:
            layout.label(text='Nodes was not found')
            return

        parent_id = getattr(context, 'CONTEXT_ID', None)

        if parent_id is None:  # root
            NodeCategoryMenu._layout_values.clear()  # protect from overflow
            for cat_name in self.categories.keys():
                row = layout.row()
                row.context_pointer_set('CONTEXT_ID', row)
                NodeCategoryMenu._layout_values[row] = cat_name
                row.menu(NodeCategoryMenu.bl_idname, text=str(cat_name))
        else:
            for n in self._categories[NodeCategoryMenu._layout_values[parent_id]]:
                n.draw(layout)


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


classes = [
    NODEVIEW_MT_Dynamic_Menu,
    NODEVIEW_MT_AddPresetOps,
    NODE_MT_category_SVERCHOK_GROUP,
    SvNodeAddOperator,
    ShowMissingDependsOperator,
    CallPartialMenu,
    NodeCategoryMenu,
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
    add_node_menu.unregister()
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
    for category in presets.get_category_names():
        if category in preset_category_menus:
            bpy.utils.unregister_class(preset_category_menus[category])
    bpy.types.NODE_MT_add.remove(sv_draw_menu)
