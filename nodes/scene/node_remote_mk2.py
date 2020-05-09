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
    BoolProperty, FloatVectorProperty, StringProperty, EnumProperty, IntProperty
)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode
from sverchok.nodes.object_nodes.getsetprop import assign_data, types
from sverchok.utils import register_multiple_classes, unregister_multiple_classes

# can't use a PointerProperty for type=bpy.data.node_group
# https://blender.stackexchange.com/questions/2075/assign-datablock-to-custom-property


class SvNodePickupMK2(bpy.types.Operator):

    bl_idname = "node.pickup_active_node_mk2"
    bl_label = "Node Pickup"
    
    nodegroup_name: bpy.props.StringProperty(default='')

    def execute(self, context):
        active = bpy.data.node_groups[self.nodegroup_name].nodes.active
        n = context.node
        n.node_name = active.name
        return {'FINISHED'}


class SvNodeRemoteNodeMK2(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvNodeRemoteNodeMK2'
    bl_label = 'Node Remote (Control)+'
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
    
    input_Sc: EnumProperty(
        items=(('prop_int','int','prop_int'),('prop_float','float','prop_float'),('prop_angle','angle','prop_angle')),
        default='prop_int',name='input_Sc',
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'auto_convert')


    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, "activate", text="Update")
        col.prop_search(self, 'nodegroup_name', bpy.data, 'node_groups', text='', icon='NODETREE')

        ng = self.get_bpy_data_from_name(self.nodegroup_name, bpy.data.node_groups)
        if not ng:
            return

        row = col.row(align=True)
        row.prop_search(self, 'node_name', ng, 'nodes', text='', icon='SETTINGS')
        row.operator('node.pickup_active_node_mk2', text='', icon='EYEDROPPER')

        node = self.get_bpy_data_from_name(self.node_name, ng.nodes)
        if not node:
            return

        if ng.bl_idname == "ScNodeTree":
            # [['int',1,1,'prop_int'],['float',2,2,'prop_float'],['angle',3,3,'prop_angle']]
            col.prop(self, 'input_Sc',text='') #, text='', icon='DRIVER')
        else:
            col.prop_search(self, 'input_idx', node, 'inputs', text='', icon='DRIVER')


    def process(self):

        # end early?

        if not self.activate:
            return
        ng = self.get_bpy_data_from_name(self.nodegroup_name, bpy.data.node_groups)
        if not ng:
            return
        node = self.get_bpy_data_from_name(self.node_name, ng.nodes)
        if not node:
            return

        named_input = node.inputs.get(self.input_idx)
        
        if ng.bl_idname == 'ScNodeTree':
            # sorcar node tree it needs pure number
            data = self.inputs[0].sv_get()[0][0]
            if self.input_Sc == 'prop_float':
                ng.set_value(node.name,'prop_float', data)
            elif self.input_Sc == 'prop_int':
                ng.set_value(node.name,'prop_int', data)
            elif self.input_Sc == 'prop_angle':
                ng.set_value(node.name,'prop_angle', radians(data))

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
def register(): register_multiple_classes(classes)
def unregister(): unregister_multiple_classes(classes)
