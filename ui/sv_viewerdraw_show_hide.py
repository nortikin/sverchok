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

import bpy


def viewerdraw_showhide(operator, context):
    space = context.space_data
    node_tree = space.node_tree

    links = node_tree.links
    selected_nodes = context.selected_nodes

    if not selected_nodes:
        operator.report({"ERROR_INVALID_INPUT"}, 'No selected nodes to join')
        return  {'CANCELLED'}

    for node in selected_nodes:
        res = any([i in node.name for i in ['Viewer','Stethoscope']])
        if  res:
            node.activate = not node.activate


class SvNodeVDShowHideOperator(bpy.types.Operator):
    """Viewer Draw Node Show Hide Toggle"""
    bl_idname = "node.sv_node_vd_toggle"
    bl_label = "Sverchok VD Node Hide Toggle"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):

        space = context.space_data
        tree_type = getattr(space, 'tree_type', None)
        return space.type == 'NODE_EDITOR' and tree_type in {'SverchCustomTreeType', }

    def execute(self, context):
        viewerdraw_showhide(self, context)
        return {'FINISHED'}



def register():
    bpy.utils.register_class(SvNodeVDShowHideOperator)


def unregister():
    bpy.utils.unregister_class(SvNodeVDShowHideOperator)
