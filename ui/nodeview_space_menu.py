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
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Iterator, Union, TypeVar, Optional
import shutil

import bl_operators
import bpy
from bpy.props import StringProperty

from sverchok.ui.sv_icons import node_icon, icon, get_icon_switch
from sverchok.ui import presets
from sverchok.ui.presets import apply_default_preset
from sverchok.ui.utils import get_menu_preset_path
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils import yaml_parser
from sverchok.utils.modules_inspection import iter_classes_from_module


"""
The module is used for generating Shift+A / Add(Node) menu.
The structure of the menu also used for searching nodes and Add Node Tool panel.
`add_node_menu` is instance of the panel which can be used to access its data.

Sverchok's extensions can use this module to add their nodes to the menu.
For this two steps should be done:

- Pass config file to `Category.append_from_config` method of `add_node_menu`
  object.
- Call `Category.register` method during registration of an extension.

Registration is needed because menus which were added in Sverchok are already
registered. And un-registration is not needed because they will be reloaded
during reloading Sverchok add-on (extensions can't be reloaded without reloading
Sverchok)

The module parses `index.yaml` file and creates a tree-like data structure `Category`
which is used for adding nodes in different areas of user interface. Also it
contains `CallPartialMenu` which shows alternative menus by pressing 1, 2, 3, 4, 5.
It's possible to add categories to the menus by adding `- extra_menu: menu_name`
attribute to a category in `index.yaml` file where menu_name is one of possible
menu names:

- BasicDataPartialMenu
- MeshPartialMenu
- AdvancedObjectsPartialMenu
- ConnectionPartialMenu
- UiToolsPartialMenu
"""

logger = logging.getLogger('sverchok')
CutSelf = TypeVar("CutSelf", bound="Category")
sv_tree_types = {'SverchCustomTreeType', }


class MenuItem(ABC):
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
    def __init__(self, name, custom_menu, icon_name='', extra_menu=''):
        self.name = name
        self.bl_idname = custom_menu
        self.icon = icon_name
        self.extra_menu = extra_menu

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
                self._label = node_cls.bl_label
            else:  # todo log missing nodes?
                self._label = f'{self.bl_idname} (not found)'
        return self._label

    @property
    def icon_prop(self):
        if self._icon_prop is None:
            node_cls = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
            if node_cls is None:
                self._icon_prop = {'icon': 'ERROR'}
            elif self.bl_idname == 'NodeReroute':
                self._icon_prop = icon('SV_REROUTE')
            elif node_cls is not None:
                self._icon_prop = node_icon(node_cls)
            elif node_cls.missing_dependency:
                self._icon_prop = node_icon(node_cls)
            else:
                self._icon_prop = {'icon': 'ERROR'}
        return self._icon_prop

    def draw(self, layout):
        node_cls = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
        icon_prop = self.icon_prop if get_icon_switch() else {}

        if node_cls is None:
            layout.label(text=self.label, **icon_prop)
            return

        if getattr(node_cls, 'missing_dependency', False):  # reroutes do not have
            op = ShowMissingDependsOperator
        else:
            op = SvNodeAddOperator
        default_context = bpy.app.translations.contexts.default
        add = layout.operator(op.bl_idname,
                              text=self.label,
                              text_ctxt=default_context,
                              **icon_prop)
        add.type = self.bl_idname
        add.use_transform = True

    def draw_icon(self, layout):
        """Only icon will be drawn"""
        node_cls = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
        icon_prop = self.icon_prop or {'icon': 'OUTLINER_OB_EMPTY'}

        if node_cls is None:
            layout.label(text=self.label, **icon_prop)
            return

        if getattr(node_cls, 'missing_dependency', False):
            op = ShowMissingDependsOperator
        else:
            op = SvNodeAddOperator
        default_context = bpy.app.translations.contexts.default
        add = layout.operator(op.bl_idname,
                              text='',
                              text_ctxt=default_context,
                              **icon_prop)
        add.type = self.bl_idname
        add.use_transform = True
        add.extra_description = f'Add {self.label} node'

    def search_match(self, request: str) -> bool:
        """Return True if the request satisfies to node search tags"""
        request = request.upper()
        words = [w for w in request.split(' ') if w]
        label = self.label.upper()
        if all(w in label for w in words):
            return True

        node_class = bpy.types.Node.bl_rna_get_subclass_py(self.bl_idname)
        if not node_class or not hasattr(node_class, 'docstring'):
            return False
        shorthand = node_class.docstring.get_shorthand()
        if all(w in shorthand for w in words):
            return True
        tooltip = node_class.docstring.get_tooltip()
        if all(w in tooltip for w in words):
            return True
        return False


class Category(MenuItem):
    """It keeps the whole structure of Add Node menu. Instancing the class with
    `Category.from_config` method generates menu classes. They should be
     registered by calling `Category.register`
     """
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
        """Iterate over all nested categories. The current category is also included."""
        yield self
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'walk_categories'):
                yield from elem.walk_categories()

    def get_submenus_for_extra_menu(self, extra_menu_name):
        if getattr(self, 'extra_menu', '') == extra_menu_name:
            yield self
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'get_submenus_for_extra_menu'):
                yield from elem.get_submenus_for_extra_menu(extra_menu_name)
            elif isinstance(elem, CustomMenu):
                if getattr(elem, 'extra_menu', '') == extra_menu_name:
                    yield elem

    def get_category(self, node_idname) -> Optional['Category']:
        """The search is O(len(sverchok_nodes))"""
        for cat in self.walk_categories():
            for elem in cat:
                if isinstance(elem, AddNode):
                    if elem.bl_idname == node_idname:
                        return cat

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
        """Register itself and all its elements. Should be called only once by
        Sverchok's unregister function."""
        bpy.utils.unregister_class(self.menu_cls)
        for elem in self.menu_cls.draw_data:
            if hasattr(elem, 'unregister'):
                elem.unregister()

    def __repr__(self):
        return f'<NodeCategory "{self.name}">'

    @classmethod
    def from_config(cls, conf: list, menu_name, **extra_props) -> CutSelf:
        """
        It creates category from given config of category items. The format
        of config is next:

            [option, option, ..., menu item, menu item, ...]

        Menu item can be one of next elements:

        - `'---'` - String of a dotted line to define separator.
        - `'SomeNode'` - String of node `bl_idname` to define Add Node operator.
        - `{'Sub category name': [option, menu_item, ...]}` - Dictionary of
          a subcategory.
        - `{'Operator name': [option, ...]}` - Dictionary of a custom operator
          to call. Options for operator call are not supported currently.
        - `{'Menu name': [option, ...]}` - Custom menu to show.

        Options have such format - `{'option_name': value}`. They can be added
        to sub categories, operators and custom menus.

        Categories can have next options:

        - `{'icon_name': 'SOME_ICON'}` - Value can be a string of standard Blender
          icons or Sverchok icon.
        - `{'extra_menu': 'menu_name'}`  - Values is a name of one of extra menus.
          Possible values:

          - "BasicDataPartialMenu"
          - "MeshPartialMenu"
          - "AdvancedObjectsPartialMenu"
          - "ConnectionPartialMenu"
          - "UiToolsPartialMenu"

        Operators options:

        - `{"icon_name": "SOME_ICON"}` - Icon to show in the menu.
        - `{"operator": "operator id name"}` - `bl_idname` of operator to call.

        Custom menus options:

        - `{"icon_name": "SOME_CION"}` - Icon to show in menu.
        - `{"custom_menu": "menu id name"}` - `bl_idname` of menu to show.

        The example of format can be found in the `sverchok/index.yaml` file.

        Extra_props should have keys only from the __init__ method of `MenuItem`
        subclasses.
        """
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
                elif isinstance(value, str):
                    extra_props.update(elem) # to use for properties of root element in addons (like {'icon_name': 'MESH_CUBE'}). Non root element work good. Without this "elif" root menu icon of sverchok addons cannot be created.
                    continue
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
        """
        This method is expected to be used by Sverchok's extensions to add
        extra items to the Add Node menu. See the format of config in
        `Category.from_config` documentation. Example:

            import sverchok.ui.nodeview_space_menu as sm
            sm.add_node_menu.append_from_config(config)

            def register():
                sm.add_node_menu.register()

        It should be called before registration functions
        """
        new_categories = []
        top_menu_names = {c.name for c in self if getattr(c, 'name', None)}
        for cat in config:
            cat_name = list(cat.keys())[0]

            # if extension is reloaded before Sverchok it can add the same menu
            # twice, this condition should prevent it
            if cat_name in top_menu_names:
                continue

            items = list(cat.values())[0]
            new_categories.append(self.from_config(items, cat_name))
        self.menu_cls.draw_data.extend(new_categories)


class SverchokContext:
    @classmethod
    def poll(cls, context):
        tree_type = getattr(context.space_data, 'tree_type', None)
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

add_node_menu = None

def setup_add_menu():
    global add_node_menu
    datafiles = Path(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))

    default_menu_file = Path(__file__).parents[1] / 'index.yaml'

    with sv_preferences() as prefs:
        if prefs is None:
            raise Exception("Internal error: Sverchok preferences are not initialized yet at the moment of loading the menu")
        if prefs.menu_preset_usage == 'COPY':
            default_menu_file = get_menu_preset_path(prefs.menu_preset)
            menu_file = datafiles / 'index.yaml'
            use_preset_copy = True
        else:
            menu_file = get_menu_preset_path(prefs.menu_preset)
            use_preset_copy = False

    if use_preset_copy and not menu_file.exists():
        logger.info(f"Applying menu preset {default_menu_file} at startup")
        shutil.copy(default_menu_file, menu_file)
    logger.debug(f"Using menu preset file: {menu_file}")
    add_node_menu = Category.from_config(yaml_parser.load(menu_file), 'All Categories', icon_name='RNA')

def get_add_node_menu():
    global add_node_menu
    if add_node_menu is None:
        setup_add_menu()
    return add_node_menu


class AddNodeOp(bl_operators.node.NodeAddOperator):
    extra_description: StringProperty()

    # this option was moved from NodeAddOperator to NODE_OT_add_node
    if bpy.app.version >= (3, 6):
        type: StringProperty(name="Node Type", description="Node type")

    @classmethod
    def description(cls, _context, properties):
        node_type = properties["type"]
        extra = properties.get("extra_description", "")
        tooltip = extra + ("\n" if extra else "")
        node_cls = bpy.types.Node.bl_rna_get_subclass_py(node_type)
        if node_cls is None:
            return f'"{node_type}" node is not found'
        tooltip += node_cls.docstring.get_tooltip()
        if node_cls.missing_dependency:
            gap = "\n\n" if tooltip else ''
            tooltip += f"{gap}Dependency: {node_cls.sv_dependencies}"
        return tooltip


class SvNodeAddOperator(AddNodeOp, bpy.types.Operator):
    """Operator to show as menu item to add available node"""
    bl_idname = "node.sv_add_node"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        # it seems some logic from create_node was moved to new deselect_node method
        if bpy.app.version >= (3, 6):
            self.deselect_nodes(context)

        node = self.create_node(context, self.type)
        apply_default_preset(node)
        return {'FINISHED'}

    # if node is not available the operator is now used - there is no need in poll


class ShowMissingDependsOperator(AddNodeOp, bpy.types.Operator):
    """Operator as menu item to show that a node is not available"""
    bl_idname = 'node.show_missing_dependencies'
    bl_label = 'Missing dependencies'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # the message can be customized if to generate separate class for each node
        if hasattr(cls, 'poll_message_set'):  # Bl 2.93 does not have the method
            cls.poll_message_set('The library is not installed')
        return False


class CallPartialMenu(SverchokContext, bpy.types.Operator):
    """It calls dynamic menus to show alternative set of node categories."""
    bl_idname = "node.call_partial_menu"
    bl_label = "Call partial menu"
    bl_options = {'REGISTER', 'UNDO'}

    menu_name: StringProperty()

    def execute(self, context):

        def draw(_self, context):
            for cat in add_node_menu.get_submenus_for_extra_menu(self.menu_name):
                cat.draw(_self.layout)

        context.window_manager.popup_menu(draw, title=self.menu_name, icon='BLANK1')
        return {'FINISHED'}


class NodeCategoryMenu(SverchokContext, bpy.types.Menu):
    """ It's a dynamic menu with submenus - https://blender.stackexchange.com/a/269716
    It scans `sv_category` attribute of all nodes and builds categories according
    the collected data.
    """
    bl_label = "Node Categories"
    bl_idname = "NODEVIEW_MT_node_category_menu"

    @property
    def categories(self):
        if not self._categories:
            import sverchok
            cats = defaultdict(list)
            # todo replace with `bpy.types.Node.bl_rna_get_subclass_py` after dummy nodes refactoring
            for cls in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
                if name := getattr(cls, 'sv_category', None):
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
    get_add_node_menu().register()


def unregister():
    add_node_menu.unregister()
    for class_name in reversed(classes):
        bpy.utils.unregister_class(class_name)
    for category in reversed(presets.get_category_names()):
        if category in preset_category_menus:
            bpy.utils.unregister_class(preset_category_menus[category])
            # call of unregister not only on close Blender. So it is important to remove this category:
            del preset_category_menus[category]
    bpy.types.NODE_MT_add.remove(sv_draw_menu)
