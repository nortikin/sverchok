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

import sverchok.ui.nodeview_space_menu as sm  # import other way breaks showing custom icons
from bpy.props import PointerProperty, EnumProperty, StringProperty, BoolProperty, IntProperty


class AddNodeToolPanel(bpy.types.Panel):
    """Nodes panel under the T panel"""
    bl_idname = 'SV_PT_AddNodeToolPanel'
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_label = "Sverchok Nodes"

    _items: list[sm.AddNode] = []
    _categories: dict[sm.Category, sm.AddNode] = dict()

    def node_search_update(self, context):
        request = context.scene.sv_add_node_panel_settings.node_search
        if not request:
            AddNodeToolPanel._categories = dict()
            return

        categories = defaultdict(list)
        for cat in sm.add_node_menu.walk_categories():
            for add_node in cat:
                if not isinstance(add_node, sm.AddNode):
                    continue
                if add_node.search_match(request):
                    categories[cat].append(add_node)

        AddNodeToolPanel._categories = categories

    def select_category_update(self, context):
        cat_name = context.scene.sv_add_node_panel_settings.selected_category
        for cat in sm.add_node_menu.walk_categories():
            if cat.menu_cls.__name__ == cat_name:
                items = [n for n in cat if isinstance(n, (sm.AddNode, sm.Separator))]
                AddNodeToolPanel._items = items
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
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(context.scene.sv_add_node_panel_settings, "node_search", text="")
        if context.scene.sv_add_node_panel_settings.node_search:
            for cat, add_nodes in self.categories.items():
                icon_prop = sm.icon(cat.icon) if cat.icon else {}
                layout.label(text=cat.name, **icon_prop)
                self.draw_add_node(context, add_nodes)
        else:
            layout.prop(context.scene.sv_add_node_panel_settings, "selected_category", text="")
            self.draw_add_node(context, self.items)

        col = layout.column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(context.scene.sv_add_node_panel_settings, 'icons_only')
        if context.scene.sv_add_node_panel_settings.icons_only:
            col.prop(context.scene.sv_add_node_panel_settings, 'columns_number')

    def draw_add_node(self, context, items):
        layout = self.layout
        if context.scene.sv_add_node_panel_settings.icons_only:
            num = context.scene.sv_add_node_panel_settings.columns_number
            grid = layout.grid_flow(row_major=True, align=True, columns=num)
            grid.scale_x = 1.5
            for add_node in items:
                if hasattr(add_node, 'draw_icon'):
                    add_node.draw_icon(grid)
                else:  # <- separator
                    grid = layout.grid_flow(row_major=True, align=True, columns=num)
                    grid.scale_x = 1.5
        else:
            col = layout.column(align=True)
            for add_node in items:
                add_node.draw(col)


class AddNodePanelSettings(bpy.types.PropertyGroup):
    def categories(self, context):
        # this should be a function because new categories can be added
        # by Sverchok's extensions after the registration
        for i, category in enumerate(sm.add_node_menu.walk_categories()):
            if any(isinstance(add_node, sm.AddNode) for add_node in category):
                identifier = category.menu_cls.__name__
                yield identifier, category.name, category.name, i

    selected_category: EnumProperty(
        name="Category",
        description="Select nodes category",
        items=categories,
        default=1,  # it through errors in console without this option
        update=AddNodeToolPanel.select_category_update,
    )

    node_search: StringProperty(
        name="Search",
        description="Enter search term and press Enter to search; clear the"
                    " field to return to selection of node category.",
        update=AddNodeToolPanel.node_search_update,
        options={'TEXTEDIT_UPDATE'},
    )

    icons_only: BoolProperty(
        name="Icons only",
        description="Show node icon only when icon has an icon, otherwise show it's name",
        default=True,
    )

    columns_number: IntProperty(
        name="Columns",
        description="Number of icon panels per row; Set to 0 for automatic selection",
        default=5,
        min=1,
        max=12,
    )


classes = [AddNodeToolPanel, AddNodePanelSettings]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sv_add_node_panel_settings = PointerProperty(
        type=AddNodePanelSettings)


def unregister():
    del bpy.types.Scene.sv_add_node_panel_settings
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)
