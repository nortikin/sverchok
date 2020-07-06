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

import os
from os.path import dirname
from collections import OrderedDict

import bpy
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
import nodeitems_utils
import bl_operators

import sverchok
from sverchok.utils import get_node_class_reference
from sverchok.utils.logging import info, error, exception
from sverchok.utils.sv_help import build_help_remap
from sverchok.ui.sv_icons import node_icon, icon
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.extra_categories import get_extra_categories
from sverchok.core.update_system import set_first_run

class SverchNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'

    def __repr__(self):
        return f"<SverchNodeCategory {self.identifier}>"

def make_node_cats():
    '''
    this loads the index.md file and converts it to an OrderedDict of node categories.

    '''

    index_path = os.path.join(dirname(__file__), 'index.md')

    node_cats = OrderedDict()
    with open(index_path) as md:
        category = None
        temp_list = []
        for line in md:
            if not line.strip():
                continue
            if line.strip().startswith('>'):
                continue
            elif line.startswith('##'):
                if category:
                    node_cats[category] = temp_list
                category = line[2:].strip()
                temp_list = []

            elif line.strip() == '---':
                temp_list.append(['separator'])
            else:
                bl_idname = line.strip()
                temp_list.append([bl_idname])

        # final append
        node_cats[category] = temp_list

    return node_cats

def juggle_and_join(node_cats):
    '''
    this step post processes the extended catagorization used
    by ctrl+space dynamic menu, and attempts to merge previously
    joined catagories. Why? Because the default menu gets very
    long if there are too many categories.

    The only real alternative to this approach is to write a
    replacement for nodeitems_utils which respects categories
    and submenus.

    '''
    node_cats = node_cats.copy()

    # join beta and alpha node cats
    alpha = node_cats.pop('Alpha Nodes')
    node_cats['Beta Nodes'].extend(alpha)

    # put masks into list main
    for ltype in ["List Masks", "List Mutators"]:
        node_refs = node_cats.pop(ltype)
        node_cats["List Main"].extend(node_refs)

    objects_cat = node_cats.pop('Objects')
    node_cats['BPY Data'].extend(objects_cat)

    # add extended gens to Gens menu
    gen_ext = node_cats.pop("Generators Extended")
    node_cats["Generator"].extend(gen_ext)

    return node_cats

class SvResetNodeSearchOperator(bpy.types.Operator):
    """
    Reset node search string and return to selection of node by category
    """
    bl_idname = "node.sv_reset_node_search"
    bl_label = "Reset search"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.scene.sv_node_search = ""
        return {'FINISHED'}

# We are creating and registering node adding operators dynamically.
# So, we have to remember them in order to unregister them when needed.
node_add_operators = {}

node_panels = []

class SverchNodeItem(object):
    """
    A local replacement of nodeitems_utils.NodeItem.
    This calls our custom operator (see make_add_operator) instead of
    standard node.add_node. Having this replacement item class allows us to:
    * Have icons in the T panel
    * Have arbitrary tooltips in the T panel.
    """
    def __init__(self, nodetype, label=None, settings=None, poll=None):
        self.nodetype = nodetype
        self._label = label
        if settings is None:
            self.settings = {}
        else:
            self.settings = settings
        self.poll = poll

        self.make_add_operator()

    @staticmethod
    def new(name):
        if name == 'separator':
            return SverchSeparator()
        else:
            return SverchNodeItem(name)

    @property
    def label(self):
        if self._label:
            return self._label
        else:
            return self.get_node_class().bl_rna.name

    def get_node_class(self):
        return get_node_class_reference(self.nodetype)

    def get_node_strings(self):
        node_class = self.get_node_class()
        if hasattr(node_class, 'get_shorthand'):
            shorthand = node_class.get_shorthand()
        else:
            shorthand = ""

        if hasattr(node_class, 'get_tooltip'):
            tooltip = node_class.get_tooltip()
        else:
            tooltip = ""

        if hasattr(node_class, "bl_label"):
            label = node_class.bl_label
        else:
            label = ""

        return label, shorthand, tooltip

    def search_match(self, needle):
        needle = needle.upper()
        label, shorthand, tooltip = self.get_node_strings()
        #info("shorthand: %s, tooltip: %s, label: %s, needle: %s", shorthand, tooltip, label, needle)
        return (needle in label.upper()) or (needle in shorthand.upper()) or (needle in tooltip.upper())

    def get_idname(self):
        return get_node_idname_for_operator(self.nodetype)

    def make_add_operator(self):
        """
        Create operator class which adds specific type of node.
        Tooltip (docstring) for that operator is copied from
        node class docstring.
        """

        global node_add_operators

        class SverchNodeAddOperator(bl_operators.node.NodeAddOperator, bpy.types.Operator):
            """Wrapper for node.add_node operator to add specific node"""

            bl_idname = "node.sv_add_" + self.get_idname()
            bl_label = "Add {} node".format(self.label)
            bl_options = {'REGISTER', 'UNDO'}

            def execute(operator, context):
                # please not be confused: "operator" here references to
                # SverchNodeAddOperator instance, and "self" references to
                # SverchNodeItem instance.
                operator.use_transform = True
                operator.type = self.nodetype
                operator.create_node(context)
                return {'FINISHED'}

        node_class = self.get_node_class()
        SverchNodeAddOperator.__name__ = node_class.__name__

        if hasattr(node_class, "get_tooltip"):
            SverchNodeAddOperator.__doc__ = node_class.get_tooltip()
        else:
            SverchNodeAddOperator.__doc__ = node_class.__doc__

        node_add_operators[self.get_idname()] = SverchNodeAddOperator
        bpy.utils.register_class(SverchNodeAddOperator)

    def get_icon(self):
        rna = self.get_node_class().bl_rna
        if hasattr(rna, "bl_icon"):
            return rna.bl_icon
        else:
            return "RNA"

    @staticmethod
    def draw(self, layout, context):
        add = draw_add_node_operator(layout, self.nodetype, label=self._label)
        if add is None:
            return

        for setting in self.settings.items():
            ops = add.settings.add()
            ops.name = setting[0]
            ops.value = setting[1]

class SverchSeparator(object):
    @staticmethod
    def draw(self, layout, context):
        layout.separator()

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'

    def search_match(self, needle):
        return True

class SvOperatorLayout(object):
    """
    Abstract layout class for operator buttons.
    Wraps standard Blender's UILayout.
    """
    def __init__(self, parent):
        self.parent = parent
        self._prev_is_separator = False

    def label(self, text):
        self.parent.label(text=text)

    def separator(self):
        if not self._prev_is_separator:
            self.parent.separator()
        self._prev_is_separator = True

    @staticmethod
    def get(icons_only, parent, columns):
        if icons_only:
            return SvIconsLayout(parent, columns)
        else:
            return SvNamedButtonsLayout(parent)

class SvIconsLayout(SvOperatorLayout):
    """
    Layout class that shows operator buttons
    with icons only (or with text if the operator does not have icon),
    in the specified number of columns.
    """
    def __init__(self, parent, columns=4):
        super().__init__(parent)
        self.columns = columns
        self._column = 0
        self._row = None

    def _tick_column(self):
        self._column = (self._column + 1) % self.columns
        if self._column == 0:
            self._row = None

    def separator(self):
        if not self._prev_is_separator:
            self._row = None
            self._column = 0
            self.parent.separator()
        self._prev_is_separator = True

    def operator(self, operator_name, **params):
        self._prev_is_separator = False
        if 'icon_value' in params or 'icon' in params:
            if self._row is None:
                self._row = self.parent.row(align=True)
                self._row.scale_x = self._row.scale_y = 1.5
            params['text'] = ""
            op = self._row.operator(operator_name, **params)
            self._tick_column()
            return op
        else:
            self._row = None
            self._column = 0
            return self.parent.operator(operator_name, **params)

class SvNamedButtonsLayout(SvOperatorLayout):
    """
    Layout class that shows operator buttons in a standard way
    (icon and text).
    """
    def operator(self, operator_name, **params):
        self._prev_is_separator = False
        return self.parent.operator(operator_name, **params)

def get_node_idname_for_operator(nodetype):
    """Select valid bl_idname for node to create node adding operator bl_idname."""
    rna = get_node_class_reference(nodetype)
    if not rna:
        raise Exception("Can't find registered node {}".format(nodetype))
    if hasattr(rna, 'bl_idname'):
        return rna.bl_idname.lower()
    elif nodetype == "NodeReroute":
        return "node_reroute"
    else:
        return rna.name.lower()

def draw_add_node_operator(layout, nodetype, label=None, icon_name=None, params=None):
    """
    Draw node adding operator button.
    This is to be used both in Shift-A menu and in T panel.
    """

    default_context = bpy.app.translations.contexts.default
    node_class = get_node_class_reference(nodetype)
    if node_class is None:
        info("cannot locate node class: %s", nodetype)
        return
    node_rna = node_class.bl_rna

    if label is None:
        if hasattr(node_rna, 'bl_label'):
            label = node_rna.bl_label
        elif nodetype == "NodeReroute":
            label = "Reroute"
        else:
            label = node_rna.name

    if params is None:
        params = dict(text=label)
    params['text_ctxt'] = default_context
    if icon_name is not None:
        params.update(**icon(icon_name))
    else:
        params.update(**node_icon(node_rna))

    add = layout.operator("node.sv_add_" + get_node_idname_for_operator(nodetype), **params)

    add.type = nodetype
    add.use_transform = True

    return add

def sv_group_items(context):
    """
    Based on the built in node_group_items in the blender distrubution
    somewhat edited to fit.
    """
    if context is None:
        return
    space = context.space_data
    if not space:
        return
    ntree = space.edit_tree
    if not ntree:
        return

    yield NodeItemCustom(draw=draw_node_ops)

    def contains_group(nodetree, group):
        if nodetree == group:
            return True
        else:
            for node in nodetree.nodes:
                if node.bl_idname in node_tree_group_type.values() and node.node_tree is not None:
                    if contains_group(node.node_tree, group):
                        return True
        return False

    if ntree.bl_idname == "SverchGroupTreeType":
        yield NodeItem("SvMonadInfoNode", "Monad Info")

    for monad in context.blend_data.node_groups:
        if monad.bl_idname != "SverchGroupTreeType":
            continue
        # make sure class exists
        cls_ref = get_node_class_reference(monad.cls_bl_idname)

        if cls_ref and monad.cls_bl_idname:
            yield NodeItem(monad.cls_bl_idname, monad.name)
        elif monad.cls_bl_idname:
            monad_cls_template_dict = {"cls_bl_idname": "str('{}')".format(monad.cls_bl_idname)}
            yield NodeItem("SvMonadGenericNode", monad.name, monad_cls_template_dict)

def draw_node_ops(self,layout, context):

    make_monad = "node.sv_monad_from_selected"
    ungroup_monad = "node.sv_monad_expand"
    update_import = "node.sv_monad_class_update"
    layout.operator(make_monad, text='make group (+relink)', icon='RNA')
    layout.operator(make_monad, text='make group', icon='RNA').use_relinking = False
    layout.operator(ungroup_monad, text='ungroup', icon='RNA')
    layout.operator(update_import, text='update appended/linked', icon='RNA')
    layout.separator()

def make_categories():
    original_categories = make_node_cats()

    node_cats = juggle_and_join(original_categories)
    node_categories = []
    node_count = 0
    for category, nodes in node_cats.items():
        name_big = "SVERCHOK_" + category.replace(' ', '_')
        node_items = []
        for item in nodes:
            nodetype = item[0]
            rna = get_node_class_reference(nodetype)
            if not rna and not nodetype == 'separator':
                info("Node `%s' is not available (probably due to missing dependencies).", nodetype)
            else:
                node_item = SverchNodeItem.new(nodetype)
                node_items.append(node_item)

        if node_items:
            node_categories.append(
                SverchNodeCategory(
                    name_big,
                    category,
                    items=node_items))
            node_count += len(nodes)
    node_categories.append(SverchNodeCategory("SVERCHOK_GROUPS", "Groups", items=sv_group_items))

    return node_categories, node_count, original_categories

def register_node_panels(identifier, std_menu):
    global node_panels

    def get_cat_list():
        extra_categories = get_extra_categories()
        cat_list = std_menu[:]
        cat_list.extend(extra_categories)
        return cat_list

    with sv_preferences() as prefs:
        if prefs.node_panels == "N":

            def draw_node_item(self, context):
                layout = self.layout
                col = SvOperatorLayout.get(prefs.node_panels_icons_only, layout.column(align=True), prefs.node_panels_columns)
                for item in self.category.items(context):
                    item.draw(item, col, context)

            for category in get_cat_list():
                panel_type = type("NODE_PT_category_sv_" + category.identifier, (bpy.types.Panel,), {
                        "bl_space_type": "NODE_EDITOR",
                        "bl_region_type": "UI",
                        "bl_label": category.name,
                        "bl_category": category.name,
                        "category": category,
                        "poll": category.poll,
                        "draw": draw_node_item,
                    })
                node_panels.append(panel_type)
                bpy.utils.register_class(panel_type)

        elif prefs.node_panels == "T":

            class SV_PT_NodesTPanel(bpy.types.Panel):
                """Nodes panel under the T panel"""

                bl_space_type = "NODE_EDITOR"
                bl_region_type = "TOOLS"
                bl_label = "Sverchok Nodes"

                @classmethod
                def poll(cls, context):
                    return context.space_data.tree_type == 'SverchCustomTreeType'

                def draw(self, context):
                    layout = self.layout
                    row = layout.row(align=True)
                    row.prop(context.scene, "sv_node_search", text="")
                    row.operator("node.sv_reset_node_search", icon="X", text="")
                    if not context.scene.sv_node_search:
                        layout.prop(context.scene, "sv_selected_category", text="")

                    col = SvOperatorLayout.get(prefs.node_panels_icons_only, layout.column(align=True), prefs.node_panels_columns)

                    needle = context.scene.sv_node_search
                    # We will search either by category selected in the popup menu,
                    # or by search term.
                    check_search = needle != ""
                    check_category = not check_search
                    category_is_first = True

                    for category in get_cat_list():
                        category_ok = category.identifier == context.scene.sv_selected_category
                        if check_category:
                            if not category_ok:
                                continue

                        items_to_draw = []
                        has_nodes = False
                        for item in category.items(context):
                            if check_search:
                                if not hasattr(item, 'search_match'):
                                    continue
                                if not item.search_match(needle):
                                    continue
                            if not isinstance(item, SverchSeparator):
                                has_nodes = True
                            # Do not show separators if we are searching by text -
                            # otherwise search results would take too much vertical space.
                            if not (check_search and isinstance(item, SverchSeparator)):
                                items_to_draw.append(item)

                        # Show category only if it has some nodes to display
                        # according to search terms.
                        if has_nodes:
                            if check_search:
                                if not category_is_first:
                                    col.separator()
                                col.label(category.name + ":")
                            for item in items_to_draw:
                                item.draw(item, col, context)

                        category_is_first = False

            node_panels.append(SV_PT_NodesTPanel)
            bpy.utils.register_class(SV_PT_NodesTPanel)

def unregister_node_panels():
    global node_panels
    for panel_type in reversed(node_panels):
        bpy.utils.unregister_class(panel_type)
    node_panels = []

def reload_menu():
    menu, node_count, original_categories = make_categories()
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        unregister_node_panels()
        nodeitems_utils.unregister_node_categories("SVERCHOK")
        unregister_node_add_operators()
    nodeitems_utils.register_node_categories("SVERCHOK", menu)
    register_node_panels("SVERCHOK", menu)
    register_node_add_operators()

    build_help_remap(original_categories)
    set_first_run(False)
    print("Reload complete, press update")

def register_node_add_operators():
    """Register all our custom node adding operators"""
    for idname in node_add_operators:
        bpy.utils.register_class(node_add_operators[idname])

def unregister_node_add_operators():
    """Unregister all our custom node adding operators"""
    for idname in node_add_operators:
        bpy.utils.unregister_class(node_add_operators[idname])

def get_all_categories(std_categories):

    def generate(self, context):
        nonlocal std_categories
        extra_categories = get_extra_categories()
        n = len(std_categories)
        all_categories = std_categories[:]
        for category in extra_categories:
            n += 1
            all_categories.append((category.identifier, category.name, category.name, n))
        return all_categories
    return generate

def register():
    menu, node_count, original_categories = make_categories()
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        unregister_node_panels()
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    nodeitems_utils.register_node_categories("SVERCHOK", menu)

    categories = [(category.identifier, category.name, category.name, i) for i, category in enumerate(menu)]
    bpy.types.Scene.sv_selected_category = bpy.props.EnumProperty(
                        name = "Category",
                        description = "Select nodes category",
                        items = get_all_categories(categories)
                    )
    bpy.types.Scene.sv_node_search = bpy.props.StringProperty(
                        name = "Search",
                        description = "Enter search term and press Enter to search; clear the field to return to selection of node category."
                    )

    bpy.utils.register_class(SvResetNodeSearchOperator)

    register_node_panels("SVERCHOK", menu)

    build_help_remap(original_categories)
    print(f"sv: {node_count} nodes.")

def unregister():
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        unregister_node_panels()
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    unregister_node_add_operators()
    bpy.utils.unregister_class(SvResetNodeSearchOperator)
    del bpy.types.Scene.sv_selected_category
    del bpy.types.Scene.sv_node_search
