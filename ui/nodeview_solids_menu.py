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

def category_has_nodes(cat_name):
    cat = node_cats[cat_name]
    for item in cat:
        rna = get_node_class_reference(item[0])
        if rna and not item[0] == 'separator':
            return True
    return False
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

def layout_draw_solid_categories(layout, node_details, sub_category):

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

        else:
            continue

        if hasattr(node_ref, "solid_catergory") and node_ref.solid_catergory == sub_category:
            node_op = draw_add_node_operator(layout, bl_idname, params=layout_params)

# does not get registered
class NodeViewMenuSolidTemplate(bpy.types.Menu):
    bl_label = ""

    def draw(self, context):
        layout_draw_solid_categories(self.layout, node_cats["Solids"], self.bl_label)
        # layout_draw_categories(self.layout, node_cats[self.bl_label])
        # prop_menu_enum(data, property, text="", text_ctxt="", icon='NONE')


# quick class factory.
def make_solids_class(name, bl_label):
    name = 'NODEVIEW_MT_Add_Solids' + name
    return type(name, (NodeViewMenuSolidTemplate,), {'bl_label': bl_label})


class NODEVIEW_MT_Solids_Input_Menu(bpy.types.Menu):
    bl_label = "Inputs"
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

        layout_draw_solid_categories(self.layout, node_cats["Solids"], self.bl_label)


class NODEVIEW_MT_Solids_Special_Menu(bpy.types.Menu):
    bl_label = "Solids"
    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in sv_tree_types:
            return True
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu('NODEVIEW_MT_Add_SolidsInputs')
        layout.menu('NODEVIEW_MT_Add_SolidsOperators')
        layout.menu('NODEVIEW_MT_Add_SolidsOutputs')


classes = [
    make_solids_class('Inputs', 'Inputs'),
    make_solids_class('Operators', 'Operators'),
    make_solids_class('Outputs', 'Outputs'),
    # NODEVIEW_MT_Solids_Input_Menu,
    NODEVIEW_MT_Solids_Special_Menu
]

def register():

    for class_name in classes:
        bpy.utils.register_class(class_name)

def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
