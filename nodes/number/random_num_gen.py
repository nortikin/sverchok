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
from bpy.props import BoolProperty, FloatProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last


class SvRndNumGen(bpy.types.Node, SverchCustomTreeNode):
    ''' Generate a random number (int of float) thru a given range (inclusive) '''
    bl_idname = 'SvRndNumGen'
    bl_label = 'Random Num Gen'
    bl_icon = 'OUTLINER_OB_EMPTY'

    low_f = FloatProperty(
        name='Float Low', description='Minimum float value',
        default=1.0,
        options={'ANIMATABLE'}, update=updateNode)

    high_f = FloatProperty(
        name='Float High', description='Maximum float value',
        default=1,
        options={'ANIMATABLE'}, update=updateNode)

    low_i = IntProperty(
        name='Int Low', description='Minimum integer value',
        default=0,
        options={'ANIMATABLE'}, update=updateNode)

    high_i = IntProperty(
        name='Int High', description='Maximum integer value',
        default=10,
        options={'ANIMATABLE'}, update=updateNode)

    count = IntProperty(
        name='Count', description='number of values to output',
        default=10,
        options={'ANIMATABLE'}, update=updateNode)

    seed = IntProperty(
        name='Seed', description='seed, grow',
        default=0,
        options={'ANIMATABLE'}, update=updateNode)

    as_list = BoolProperty(
        name='As List', description='on means output list, off means output np.array 1d',
        default=True, 
        update=updateNode)

    mode_options = [
        ("Simple", "Simple", "", 0),
        ("Advanced", "Advanced", "", 1)
    ]
    
    selected_mode = bpy.props.EnumProperty(
        items=mode_options,
        description="offers....",
        default="Simple", update=updateNode
    )

    type_mode_options = [
        ("Int", "Int", "", 0),
        ("Float", "Float", "", 1)
    ]
    
    type_selected_mode = bpy.props.EnumProperty(
        items=type_mode_options,
        description="offers....",
        default="Int", update=updateNode
    )


    def sv_init(self, context):
        si = self.inputs
        si.new('StringsSocket', "Count").prop_name = 'count'
        si.new('StringsSocket', "Seed").prop_name = 'seed'
        si.new('StringsSocket', "Low").prop_name = 'low_i'
        si.new('StringsSocket', "High").prop_name = 'high_i'
        so = self.outputs
        so.new('StringsSocket', "Value")


    def draw_buttons(self, context, layout):
        
        row = layout.row()
        row.prop(self, 'type_selected_mode', expand=True)
        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)

        if self.selected_mode == 'Simple':
            ...
        else:
            ...
        
        layout.prop(self, "as_list")
    

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        # no outputs, end early.
        if not outputs['Value'].is_linked:
            return
        
        value_in = iter(inputs[0].sv_get())
        param = [repeat_last(inputs[i].sv_get()[0]) for i in range(1, 5)]
        out = [self.map_range(*args) for args in zip(value_in, *param)]
        
        outputs['Value'].sv_set(out)


def register():
    bpy.utils.register_class(SvRndNumGen)


def unregister():
    bpy.utils.unregister_class(SvRndNumGen)
