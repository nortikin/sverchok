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
zeffii 2020.
'''

import bpy
import nodeitems_utils
from bpy.app.translations import contexts as i18n_contexts

def is_sverchok_editor(context):
    sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
    tree_type = context.space_data.tree_type
    if tree_type in sv_tree_types:
        return True

class SVNODE_MT_add(bpy.types.Menu):
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, context):
        layout = self.layout

        if is_sverchok_editor(context):
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("node.sv_extra_search", text="Search", icon='OUTLINER_DATA_FONT')
        else:
            layout.operator_context = 'INVOKE_DEFAULT'
            props = layout.operator("node.add_search", text="Search...", icon='VIEWZOOM')
            props.use_transform = True

        layout.separator()

        # actual node submenus are defined by draw functions from node categories
        nodeitems_utils.draw_node_categories_menu(self, context)

def perform_menu_monkey_patch():
    # replace the default Add menu, and update it with sverchok specific search
    bpy.types.NODE_MT_add.draw = SVNODE_MT_add.draw

    # replace the default Node Categories menu with our implementation
    NC = nodeitems_utils._node_categories
    SV = NC['SVERCHOK']
    SVcatlist, sv_draw, SvCats = SV
    NC['SVERCHOK'] = (SVcatlist, bpy.types.NODEVIEW_MT_Dynamic_Menu.draw, SvCats)
