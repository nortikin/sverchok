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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode
from sverchok.nodes.object_nodes.getsetprop import assign_data, types


class SvNodePickup(bpy.types.Operator):

    bl_idname = "node.pickup_active_node"
    bl_label = "Node Pickup"
    
    # bl_options = {'REGISTER', 'UNDO'}

    nodegroup_name: bpy.props.StringProperty(default='')

    def execute(self, context):
        active = bpy.data.node_groups[self.nodegroup_name].nodes.active
        n = context.node
        n.node_name = active.name
        return {'FINISHED'}


class SvNodeRemoteNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvNodeRemoteNode'
    bl_label = 'Node Remote (Control)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_REMOTE_NODE'

    activate: BoolProperty(
        default=True,
        name='Show', description='Activate node?',
        update=updateNode)

    nodegroup_name: StringProperty(
        default='',
        description='stores the name of the nodegroup referenced by this node',
        update=updateNode)

    node_name: StringProperty(
        default='',
        description='stores the name of the node referenced by this node',
        update=updateNode)

    input_idx: StringProperty()
    execstr: StringProperty(default='', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'auto_convert')

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, "activate", text="Update")
        col.prop_search(self, 'nodegroup_name', bpy.data, 'node_groups', text='', icon='NODETREE')
        node_group = bpy.data.node_groups.get(self.nodegroup_name)
        if node_group:

            row = col.row(align=True)
            row.prop_search(self, 'node_name', node_group, 'nodes', text='', icon='SETTINGS')
            row.operator('node.pickup_active_node', text='', icon='EYEDROPPER')

            if self.node_name:
                node = node_group.nodes[self.node_name]
                col.prop_search(self, 'input_idx', node, 'inputs', text='', icon='DRIVER')

    def process(self):
        if not self.activate:
            return

        node_group = bpy.data.node_groups.get(self.nodegroup_name)
        if not node_group:
            return
        node = node_group.nodes.get(self.node_name)
        if not node:
            return

        named_input = node.inputs.get(self.input_idx)
        if named_input:
            data = self.inputs[0].sv_get()
            if 'value' in named_input:
                # [ ] switch socket type if needed
                assign_data(named_input.value, data)
            elif 'value_prop' in named_input:
                # for audio nodes for example
                # https://github.com/nomelif/Audionodes
                named_input.value_prop = data[0][0]
                        


def register():
    bpy.utils.register_class(SvNodePickup)
    bpy.utils.register_class(SvNodeRemoteNode)


def unregister():
    bpy.utils.unregister_class(SvNodeRemoteNode)
    bpy.utils.unregister_class(SvNodePickup)
