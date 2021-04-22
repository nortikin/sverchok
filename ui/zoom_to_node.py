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

class ZoomToNodeOperator(bpy.types.Operator):
    """Zoom In and Out from node"""
    bl_idname = "node.zoom_to_node"
    bl_label = "Zoom To Node Operator"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR'

    def execute(self, context):
        if context.scene.zoomed_in:
            bpy.ops.node.view_all()
            for i in range(5):
                bpy.ops.view2d.zoom_in()
            context.scene.zoomed_in = False
        else:
            context.scene.zoomed_in = True
            bpy.ops.view2d.zoom_border()
            bpy.ops.node.view_selected()
            node_selected = context.selected_nodes
            if len(node_selected) > 1:
                for i in range(3):
                    bpy.ops.view2d.zoom_in()


        return {'FINISHED'}


def register():
    bpy.utils.register_class(ZoomToNodeOperator)
    bpy.types.Scene.zoomed_in = bpy.props.BoolProperty(
        name='Zoom In and out from node',
        default=False,
        description='Zoom to selected/ Zoom to all')


def unregister():
    bpy.utils.unregister_class(ZoomToNodeOperator)
    del bpy.types.Scene.zoomed_in
