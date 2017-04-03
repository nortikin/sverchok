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

import sverchok
from sverchok.menu import make_node_cats
from sverchok.ui.sv_icons import custom_icon

node_cats = make_node_cats()
addon_name = sverchok.__name__
menu_prefs = {}

def make_flat_nodecats():
    flat_node_list = []
    for cat in node_cats:
        for node_ref in cat:
            if not node_ref[0] == 'separator':
                flat_node_list.append(node_ref)  # maybe return lookups too
    return flat_node_list

flat_node_cats = make_flat_nodecats()

def filter_items(self, context):
    return [(n[0], n[0], '', idx) for n, idx in enumerate(flat_node_cats)]


class SvFuzzySearchOne(bpy.types.Operator):
    """Implementing Search fuzzyness"""
    bl_idname = "node.sv_fuzzy_node_search"
    bl_label = "Fuzzy Search"
    bl_property = "search_responses"

    search_responses = bpy.props.EnumProperty(items=filter_items)
    use_transform = bpy.props.BoolProperty()

    def execute(self, context):
        self.report({'INFO'}, "Selected: %s" % self.search_responses)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


classes = [SvFuzzySearchOne,]


def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]


def unregister():
    _ = [bpy.utils.unregister_class(cls) for cls in classes]
