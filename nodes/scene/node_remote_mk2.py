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
from math import radians
from bpy.props import (
    BoolProperty, FloatVectorProperty, StringProperty, EnumProperty, IntProperty, PointerProperty
)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode
from sverchok.nodes.object_nodes.getsetprop import assign_data, types
from sverchok.utils import register_multiple_classes, unregister_multiple_classes

class SvNodePickupMK2(bpy.types.Operator):

    bl_idname = "node.pickup_active_node_MK2"
    bl_label = "Node Pickup"
    
    # bl_options = {'REGISTER', 'UNDO'}

    nodegroup_name: bpy.props.StringProperty(default='')

    def execute(self, context):
        active = bpy.data.node_groups[self.nodegroup_name].nodes.active
        n = context.node
        n.node_name = active.name
        return {'FINISHED'}



class SvNodeRemoteNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: remote rv
    Tooltip: remote control mk2
        
    This node lets you control the nodes of other nodegorups, in theory
    """
        

    bl_idname = 'SvNodeRemoteNodeMK2'
    bl_label = 'Node Remote (Control)+'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_REMOTE_NODE'

    activate: BoolProperty(
        default=True, name='Show', description='Activate node?',
        update=updateNode)

    nodegroup_pointer: PointerProperty(
        type=bpy.types.NodeGroup, poll=lambda s, o: True, update=updateNode,
        description='stores the name of the nodegroup referenced by this node')

    node_pointer: .PointerProperty(
        type=bpy.types.Node, poll=lambda s, o: True, update=updateNode,
        description='stores the name of the node referenced by this node')

    property_types = (('prop_int','int','prop_int'),('prop_float','float','prop_float'),('prop_angle','angle','prop_angle'))

    input_idx: StringProperty()
    execstr: StringProperty(default='', update=updateNode)
    input_Sc: EnumProperty(items=property, default='prop_int',name='input_Sc', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'auto_convert')

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, "activate", text="Update")
        col.prop_search(self, 'nodegroup_pointer', bpy.data, 'node_groups', text='', icon='NODETREE')
        
        if self.node_group_pointer:

            row = col.row(align=True)
            row.prop_search(self, 'node_pointer', self.node_group_pointer, 'nodes', text='', icon='SETTINGS')
            row.operator('node.pickup_active_node_MK2', text='', icon='EYEDROPPER')

            if self.node_pointer:
                if node_group.bl_idname == "ScNodeTree":
                    col.prop(self, 'input_Sc',text='')
                else:
                    col.prop_search(self, 'input_idx', self.node_pointer, 'inputs', text='', icon='DRIVER')

    def process(self):
        if not all(self.activate, self.node_group_pointer):
            return

        if self.node_pointer:
            
            named_input = self.node_pointer.inputs.get(self.input_idx)
            
            if self.node_group_pointer.bl_idname == 'ScNodeTree':

                # sorcar node tree, it needs pure number
                ng = self.node_group_pointer
                node = self.node_pointer
                data = self.inputs[0].sv_get()[0][0]

                if self.input_Sc == 'prop_float':
                    ng.set_value(node.name,'prop_float', data)
                elif self.input_Sc == 'prop_int':
                    ng.set_value(node.name,'prop_int', data)
                elif self.input_Sc == 'prop_angle':
                    ng.set_value(node.name, 'prop_angle', radians(data))

            elif named_input:
                data = self.inputs[0].sv_get()
                if 'value' in named_input:
                    # [ ] switch socket type if needed (AN)
                    assign_data(named_input.value, data)
                elif 'value_prop' in named_input:
                    # for audio nodes for example
                    # https://github.com/nomelif/Audionodes
                    named_input.value_prop = data[0][0]


classes = [SvNodePickupMK2, SvNodeRemoteNodeMK2]

def register():
    register_multiple_classes(classes)

def unregister():
    unregister_multiple_classes(classes)
