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

import random

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from bpy.props import (
    BoolProperty, FloatVectorProperty, StringProperty, EnumProperty, IntProperty
)

from sverchok.node_tree import SverchCustomTreeNode, MatrixSocket
from sverchok.data_structure import dataCorrect, updateNode, SvGetSocketAnyType


class SvNodePickup(bpy.types.Operator):

    bl_idname = "node.pickup_active_node"
    bl_label = "Node Pickup"
    # bl_options = {'REGISTER', 'UNDO'}

    nodegroup_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        active = bpy.data.node_groups[self.nodegroup_name].nodes.active
        n = context.node
        n.node_name = active.name
        return {'FINISHED'}


class SvNodeRemoteNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvNodeRemoteNode'
    bl_label = 'Sv Node Remote'
    bl_icon = 'OUTLINER_OB_EMPTY'

    activate = BoolProperty(
        default=True,
        name='Show', description='Activate node?',
        update=updateNode)

    nodegroup_name = StringProperty(
        default='',
        description='stores the name of the nodegroup referenced by this node',
        update=updateNode)

    node_name = StringProperty(
        default='',
        description='stores the name of the node referenced by this node',
        update=updateNode)

    input_idx = StringProperty()
    execstr = StringProperty(default='', update=updateNode)

    def sv_init(self, context):
        # self.inputs.new('VerticesSocket', 'location')
        # self.inputs.new('VerticesSocket', 'scale')
        # self.inputs.new('VerticesSocket', 'rotation')
        ...

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, "activate", text="Update")
        col.prop_search(self, 'nodegroup_name', bpy.data, 'node_groups', text='', icon='NODETREE')
        if self.nodegroup_name and (self.nodegroup_name in bpy.data.node_groups):
            node_group = bpy.data.node_groups[self.nodegroup_name]
            row = col.row(align=True)
            row.prop_search(self, 'node_name', node_group, 'nodes', text='', icon='SETTINGS')
            eyedropper = row.operator('node.pickup_active_node', text='', icon='EYEDROPPER')
            eyedropper.nodegroup_name = self.nodegroup_name

            if self.node_name:
                node = node_group.nodes[self.node_name]
                col.prop_search(self, 'input_idx', node, 'inputs', text='', icon='DRIVER')

    def process(self):
        # if not self.activate:
        #     return

        # inputs = self.inputs
        # objects = bpy.data.objects

        # def get_if_valid(sockname, fallback):
        #     s = self.inputs[sockname].sv_get()
        #     if s and s[0] and s[0][0]:
        #         return s[0][0]
        #     else:
        #         return fallback

        # if self.obj_name in objects:
        #     obj = objects[self.obj_name]

        #     sockets = ['location', 'scale', 'rotation']
        #     fallbacks = [(0, 0, 0), (1, 1, 1), (0, 0, 0)]
        #     for socket, fb in zip(sockets, fallbacks):
        #         if inputs[socket].is_linked:
        #             attribute = socket.replace('rotation', 'rotation_euler')
        #             if hasattr(obj, attribute):
        #                 new_val = get_if_valid(socket, fallback=fb)
        #                 setattr(obj, attribute, new_val)

        #     self.show_string_box = (obj.type == 'FONT')

        #     if self.show_string_box:
        #         obj.data.body = self.input_text

        # else:
        #     self.show_string_box = 0
        ...


def register():
    bpy.utils.register_class(SvNodePickup)
    bpy.utils.register_class(SvNodeRemoteNode)


def unregister():
    bpy.utils.unregister_class(SvNodeRemoteNode)
    bpy.utils.unregister_class(SvNodePickup)
