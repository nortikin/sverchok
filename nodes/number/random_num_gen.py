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

    count = FloatProperty(
        name='Count', description='number of values to output',
        default=10,
        options={'ANIMATABLE'}, update=updateNode)

    as_list = BoolProperty(
        name='As List', description='on means output list, off means output np.array 1d',
        default=True, 
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Value").prop_name = 'value'
        self.inputs.new('StringsSocket', "Old Min").prop_name = 'old_min'
        self.inputs.new('StringsSocket', "Old Max").prop_name = 'old_max'
        self.inputs.new('StringsSocket', "New Min").prop_name = 'new_min'
        self.inputs.new('StringsSocket', "New Max").prop_name = 'new_max'

        self.outputs.new('StringsSocket', "Value")

    def draw_buttons(self, context, layout):
        layout.prop(self, "clamp")
    
    def map_range(self, x_list, old_min, old_max, new_min, new_max):
        old_d = old_max - old_min
        new_d = new_max - new_min
        scale = new_d/old_d

        def f(x):
            return new_min + (x-old_min)*scale

        if self.clamp:
            return [min(new_max, max(new_min, f(x))) for x in x_list]
        else:
            return [f(x) for x in x_list]

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        # no outputs, end early.
        if not outputs['Value'].is_linked:
            return
        value_in = iter(inputs[0].sv_get())
        param = [repeat_last(inputs[i].sv_get()[0]) for i in range(1, 5)]
        out = [self.map_range(*args) for args in zip(value_in, *param)]
        self.outputs['Value'].sv_set(out)


def register():
    bpy.utils.register_class(SvRndNumGen)


def unregister():
    bpy.utils.unregister_class(SvRndNumGen)
