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

import bpy

import sverchok
from sverchok.utils.sv_help import build_help_remap
from sverchok.utils.extra_categories import get_extra_categories
import sverchok.ui.nodeview_space_menu as sm  # import other way breaks showing custom icons


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


class SV_PT_NodesTPanel(bpy.types.Panel):
    """Nodes panel under the T panel"""

    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_label = "Sverchok Nodes"

    _items: list[sm.AddNode] = []
    _categories: dict[sm.Category, sm.AddNode] = dict()

    def node_search_update(self, context):
        request = context.scene.sv_node_search
        if not request:
            SV_PT_NodesTPanel._categories = dict()
            return

        categories = defaultdict(list)
        for cat in sm.add_node_menu.walk_categories():
            for add_node in cat:
                if not hasattr(add_node, 'bl_idname'):
                    continue
                if add_node.search_match(request):
                    categories[cat].append(add_node)

        SV_PT_NodesTPanel._categories = categories

    def select_category_update(self, context):
        cat_name = context.scene.sv_selected_category
        for cat in sm.add_node_menu.walk_categories():
            if cat.menu_cls.__name__ == cat_name:
                items = [n for n in cat if hasattr(n, 'bl_idname')]
                SV_PT_NodesTPanel._items = items
                return

    @property
    def categories(self):
        if not self._categories:
            self.node_search_update(bpy.context)
        return self._categories

    @property
    def items(self):
        """After reloading the items will be none. They can't be updated from
        registration function. So do this on demand"""
        if not self._items:
            self.select_category_update(bpy.context)
        return self._items

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(context.scene, "sv_node_search", text="")
        row.operator("node.sv_reset_node_search", icon="X", text="")
        addon = bpy.context.preferences.addons.get(sverchok.__name__)
        prefs = addon.preferences
        if context.scene.sv_node_search:
            for cat, add_nodes in self.categories.items():
                icon_prop = sm.icon(cat.icon) if cat.icon else {}
                layout.label(text=cat.name, **icon_prop)
                if prefs.node_panels_icons_only:
                    grid = layout.grid_flow(row_major=True, align=True, columns=prefs.node_panels_columns)
                    grid.scale_x = 1.5
                    for add_node in add_nodes:
                        add_node.draw(grid, only_icon=True)
                else:
                    col = layout.column(align=True)
                    for add_node in add_nodes:
                        add_node.draw(col)
        else:
            layout.prop(context.scene, "sv_selected_category", text="")
            if prefs.node_panels_icons_only:
                grid = layout.grid_flow(row_major=True, align=True, columns=prefs.node_panels_columns)
                grid.scale_x = 1.5
                for add_node in self.items:
                    add_node.draw(grid, only_icon=True)
            else:
                col = layout.column(align=True)
                for add_node in self.items:
                    add_node.draw(col)


def reload_menu():
    build_help_remap(sm.add_node_menu.walk_categories())


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


classes = [SvResetNodeSearchOperator, SV_PT_NodesTPanel]


def register():
    def search_tooltip(self, context, edit_text):
        for cat in sm.add_node_menu.walk_categories():
            for add_node in cat:
                if not hasattr(add_node, 'search_match'):
                    continue
                if add_node.search_match(edit_text):
                    yield add_node.label, "Some editional text"

    categories = []
    for i, category in enumerate(sm.add_node_menu.walk_categories()):
        if any(hasattr(add_node, 'bl_idname') for add_node in category):
            identifier = category.menu_cls.__name__
            categories.append((identifier, category.name, category.name, i))
    bpy.types.Scene.sv_selected_category = bpy.props.EnumProperty(
        name="Category",
        description="Select nodes category",
        items=get_all_categories(categories),
        update=SV_PT_NodesTPanel.select_category_update,
    )

    search_prop = dict(search=search_tooltip) if bpy.app.version >= (3, 3) else {}
    bpy.types.Scene.sv_node_search = bpy.props.StringProperty(
        name="Search",
        description="Enter search term and press Enter to search; clear the"
                    " field to return to selection of node category.",
        update=SV_PT_NodesTPanel.node_search_update,
        **search_prop
    )

    for cls in classes:
        bpy.utils.register_class(cls)

    build_help_remap(sm.add_node_menu.walk_categories())


def unregister():
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.sv_selected_category
    del bpy.types.Scene.sv_node_search
