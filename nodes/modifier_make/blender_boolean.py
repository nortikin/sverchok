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
import sys
from bpy.props import EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_cycle as mlr
from sverchok.utils.csg_core import CSG


class SvBlenderBoolean(bpy.types.Node, SverchCustomTreeNode):
    '''CSG Boolean Node MK2'''
    bl_idname = 'SvBlenderBoolean'
    bl_label = 'B3d Boolean'
    bl_icon = 'MOD_BOOLEAN'

    mode_options = [
        ("INTERSECT", "Intersect", "", 0),
        ("UNION", "Union", "", 1),
        ("DIFFERENCE", "Diff", "", 2)
    ]

    selected_mode: EnumProperty(
        items=mode_options,
        description="offers basic booleans using CSG",
        default="INTERSECT", update=updateNode)

    bool_name: bpy.props.StringProperty(name="bool name", update=updateNode)
    overlap_threshold: bpy.props.FloatProperty(
        step=0.00001, default=0.000001,
        name="overlap threshold", description="double threshold, epsilon", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Obj A')
        self.inputs.new('SvObjectSocket', 'Obj B')
        self.outputs.new('SvObjectSocket', 'Obj')
        

    def draw_buttons(self, context, layout):
        layout.row().prop(self, 'selected_mode', expand=True)
        layout.row().prop(self, 'bool_name', text="name")
        layout.row().prop(self, 'overlap_threshold', text="Eps")

    def process(self):
        """ off load boolean computation to Blender """

        start_obj = self.inputs[0].sv_get()[0]
        modifier_obj = self.inputs[1].sv_get()[0]

        with self.sv_throttle_tree_update():
        
            if not (self.bool_name in start_obj.modifiers):
                start_obj.modifiers.new(name=self.bool_name, type="BOOLEAN")
            
            modifier = start_obj.modifiers.get(self.bool_name)
            if not modifier.operation == self.selected_mode:
                 modifier.operation = self.selected_mode

            if not modifier.object or (not modifier.object == modifier_obj):
                modifier.object = modifier_obj

            modifier.double_threshold = self.overlap_threshold

        self.outputs[0].sv_set([start_obj])

classes = [SvBlenderBoolean]
register, unregister = bpy.utils.register_classes_factory(classes)