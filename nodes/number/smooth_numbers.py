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

from math import pi
import bpy
from bpy.props import IntProperty, EnumProperty, FloatProperty, BoolProperty

from sverchok.ui.sv_icons import custom_icon
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes, numpy_list_match_modes, numpy_list_match_func
from sverchok.utils.sv_itertools import (recurse_f_level_control)
from sverchok.utils.geom import LinearSpline, CubicSpline
import numpy as np

def smooth_list(data_out, iteration, factor, cyclic):
    data_out[1:] += (data_out[:-1] - data_out[1:]) * (0.5 * factor)
    data_out[:-1] += (data_out[1:] - data_out[:-1]) * (0.5 * factor)
    if cyclic:
        data_out[0] += (data_out[-1] - data_out[0]) * (0.5 * factor)
        data_out[-1] += (data_out[0] - data_out[-1]) * (0.5 * factor)
    if iteration > 1:
        smooth_list(data_out, iteration-1, factor, cyclic)

def smooth_numbers(params, constants, matching_f):
    result = []
    cyclic, out_numpy = constants
    params = matching_f(params)

    for props in zip(*params):
        data = np.array(props[0])
        iterations = max(props[1][0], 0)
        factor = max(min(props[2][0], 1),-1)
        if iterations:
            smooth_list(data, iterations, factor, cyclic)

        result.append(data if out_numpy else data.tolist())

    return result

class SvSmoothNumbersNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ease values
    Tooltip: Smooth the values of a numerical list.
    """
    bl_idname = 'SvSmoothNumbersNode'
    bl_label = 'Smooth Numbers'
    sv_icon = 'SV_OSCILLATOR'

    def mode_change(self, context):
        self.update_sockets()
        updateNode(self, context)



    factor: FloatProperty(default=1.0, min=-1, max=1, name='Factor', update=updateNode)
    iterations: IntProperty(default=1, min=0, name='Iterations', update=updateNode)
    cyclic: BoolProperty(
        name='Cyclic',
        description='Smooth first value with last value',
        default=False, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_buttons(self, ctx, layout):
        layout.prop(self, "cyclic", expand=False)

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "cyclic", expand=False)
        layout.prop(self, "list_match", expand=False)
        layout.prop(self, "output_numpy", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop(self, "cyclic", expand=False)
        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "output_numpy", expand=False)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Values")
        self.inputs.new('SvStringsSocket', "Iterations").prop_name = 'iterations'
        self.inputs.new('SvStringsSocket', "Factor").prop_name = 'factor'

        self.outputs.new('SvStringsSocket', "Out")


    def process(self):

        if self.outputs[0].is_linked:

            params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]
            matching_f = list_match_func[self.list_match]

            desired_levels = [2, 2, 2]
            ops = [self.cyclic, self.output_numpy]
            result = recurse_f_level_control(params, ops, smooth_numbers, matching_f, desired_levels)

            self.outputs[0].sv_set(result)


classes = [SvSmoothNumbersNode]
register, unregister = bpy.utils.register_classes_factory(classes)
