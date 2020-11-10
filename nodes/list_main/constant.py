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
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, updateNode, ensure_nesting_level, throttle_and_update_node


class SvConstantListNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: constant list
    Tooltip: Make a list by repeating a constant value
    """
    bl_idname = 'SvConstantListNode'
    bl_label = 'Constant List'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CONST_LIST'

    modes = [
        ('INT', "Integer", "Integer number", 0),
        ('FLOAT', "Float", "Floating-point number", 1)
    ]

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['IntValue'].hide_safe = self.mode != 'INT'
        self.inputs['FloatValue'].hide_safe = self.mode != 'FLOAT'

    mode : EnumProperty(
        name = "Type",
        description = "Data type to use",
        items = modes,
        default = 'INT',
        update = update_sockets)

    int_value : IntProperty(
        name = "Value",
        default = 0,
        update = updateNode)
    
    float_value : FloatProperty(
        name = "Value",
        default = 0.0,
        update = updateNode)
    
    length : IntProperty(
        name = "Length",
        default = 3,
        update = updateNode)

    out_level : IntProperty(
        name = "Output level",
        description = "Resulting list nesting level",
        default = 2,
        min = 1, max = 3,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)
        layout.prop(self, 'out_level')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "IntValue").prop_name = 'int_value'
        self.inputs.new('SvStringsSocket', "FloatValue").prop_name = 'float_value'
        self.inputs.new('SvStringsSocket', "Length").prop_name = 'length'
        self.outputs.new('SvStringsSocket', "Data")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        
        int_value_s = self.inputs['IntValue'].sv_get()
        int_value_s = ensure_nesting_level(int_value_s, 2)
        float_value_s = self.inputs['FloatValue'].sv_get()
        float_value_s = ensure_nesting_level(float_value_s, 2)
        length_s = self.inputs['Length'].sv_get()
        length_s = ensure_nesting_level(length_s, 2)

        if self.mode == 'INT':
            value_s = int_value_s
        else:
            value_s = float_value_s

        data_out = []
        for values, lengths in zip_long_repeat(value_s, length_s):
            new_data = []
            for value, length in zip_long_repeat(values, lengths):
                data = [value] * length
                if self.out_level == 1:
                    new_data.extend(data)
                else:
                    new_data.append(data)
            if self.out_level < 3:
                data_out.extend(new_data)
            else:
                data_out.append(new_data)

        self.outputs['Data'].sv_set(data_out)

def register():
    bpy.utils.register_class(SvConstantListNode)

def unregister():
    bpy.utils.unregister_class(SvConstantListNode)

