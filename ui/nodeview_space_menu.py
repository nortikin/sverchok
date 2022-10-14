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
from abc import ABC, abstractmethod
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


class MenuItem(ABC):
    _node_classes = dict()

    @property
    def node_classes(self) -> dict[str, type]:
        if not self._node_classes:
            import sverchok  # not available during initialization of the module
            for cls_ in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
                self._node_classes[cls_.bl_idname] = cls_
        return self._node_classes

    @property
    def icon_prop(self):
        if hasattr(self, 'icon'):
            return icon(self.icon)
        return {}

    @abstractmethod
    def draw(self, layout):
        pass

    def __repr__(self):
        name = getattr(self, 'name', '')
        name = f' "{name}"' if name else ''
        return f"<{type(self).__name__}{name}>"


class Separator(MenuItem):
    def draw(self, layout):
        layout.separator()


class Operator(MenuItem):
    def __init__(self, name, operator, icon_name=''):  # it's possible to add extra options for operator call
        self.name = name
        self.bl_idname = operator
        self.icon = icon_name

    def draw(self, layout):
        layout.operator_context = 'INVOKE_REGION_WIN'  # I'm not sure that all operators need this
        layout.operator(self.bl_idname, text=self.name, **self.icon_prop)

    @classmethod
    def from_config(cls, config: dict):
        name = list(config.keys())[0]
        values = list(config.values())[0]
        props = dict()
        for prop in values:
            key = list(prop.keys())[0]
            value = list(prop.values())[0]
            props[key] = value
        return cls(name, **props)

    @classmethod
    def is_operator_config(cls, config: dict):
        for prop in list(config.values())[0]:
            if isinstance(prop, dict):
                prop_name = list(prop.keys())[0]
                if prop_name.lower() == 'operator':
                    return True
        return False


class CustomMenu(MenuItem):
    def __init__(self, name, custom_menu, icon_name=''):
        self.name = name
        self.bl_idname = custom_menu
        self.icon = icon_name

    def draw(self, layout):
        layout.menu(self.bl_idname, text=self.name, **self.icon_prop)

    @classmethod
    def from_config(cls, config: dict):
        name = list(config.keys())[0]
        values = list(config.values())[0]
        props = dict()
        for prop in values:
            key = list(prop.keys())[0]
            value = list(prop.values())[0]
            props[key] = value
        return cls(name, **props)

    @classmethod
    def is_custom_menu_config(cls, config: dict):
        for prop in list(config.values())[0]:
            if isinstance(prop, dict):
                prop_name = list(prop.keys())[0]
                if prop_name.lower() == 'custom_menu':
                    return True
        return False


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
                if cls := self.node_classes.get(self.bl_idname):
                    self._icon_prop = node_icon(cls)
                else:
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
        if only_icon:
            icon_prop = self.icon_prop or {'icon': 'OUTLINER_OB_EMPTY'}
        else:
            icon_prop = self.icon_prop if get_icon_switch() else {}

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
                if Operator.is_operator_config(elem):
                    parsed_items.append(Operator.from_config(elem))
                    continue
                if CustomMenu.is_custom_menu_config(elem):
                    parsed_items.append(CustomMenu.from_config(elem))
                    continue

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
        # it would be better to have the condition only for the root menu
        if not getattr(context.space_data, 'edit_tree', None):
            # todo also it's possible to give choice of picking one of existing node trees
            self.layout.operator("node.new_node_tree",
                                 text="New Sverchok Node Tree",
                                 icon="RNA_ADD")
            return
        for elem in self.draw_data:
            elem.draw(self.layout)


menu_file = Path(__file__).parents[1] / 'index.yaml'
add_node_menu = Category.from_config(yaml_parser.load(menu_file), 'All Categories', icon_name='RNA')


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
        if hasattr(cls, 'poll_message_set'):  # Bl 2.93 does not have the method
            cls.poll_message_set('The library is not installed')
        return False


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


class AddPresetMenu(bpy.types.Menu):
    bl_idname = 'NODEVIEW_MT_AddPresetMenu'
    bl_label = "Presets"

    def draw(self, context):
        layout = self.layout
        presets.draw_presets_ops(layout, context=context)
        for category in presets.get_category_names():
            if category in preset_category_menus:
                if category in preset_category_menus:
                    class_name = preset_category_menus[category].__name__
                    layout.menu(class_name)


class SverchokGroupMenu(bpy.types.Menu):
    bl_idname = 'NODE_MT_SverchokGroupMenu'
    bl_label = "Group"

    def draw(self, context):
        layout = self.layout
        layout.operator('node.add_group_node')
        layout.operator('node.add_node_output_input', text="Group input").node_type = 'input'
        layout.operator('node.add_node_output_input', text="Group output").node_type = 'output'
        layout.operator('node.add_group_tree_from_selected')


classes = [
    AddPresetMenu,
    SverchokGroupMenu,
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

    self.layout.menu_contents(add_node_menu.menu_cls.__name__)


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
