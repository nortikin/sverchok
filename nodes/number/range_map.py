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
from bpy.props import BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func
from sverchok.utils.sv_itertools import recurse_f_level_control
import numpy as np

def map_range(params, constant, matching_f):
    result = []
    clamp, auto_limits, match_mode, out_numpy = constant
    params = matching_f(params)
    numpy_match = numpy_list_match_func[match_mode]
    for props in zip(*params):
        np_props = [np.array(prop) for prop in props]
        val, old_min, old_max, new_min, new_max = numpy_match(np_props)
        if auto_limits:
            old_min = np.min(val)
            old_max = np.max(val)

        res = new_min + (val - old_min) * ((new_max - new_min)/(old_max - old_min))

        if clamp and not auto_limits:
            res = np.clip(res, new_min, new_max)
        result.append(res if out_numpy else res.tolist())

    return result

class SvMapRangeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' '''
    """
    Triggers: Map a range from one to another
    Tooltip:  Map input list setting setting input range limits and output range limits

    """
    bl_idname = 'SvMapRangeNode'
    bl_label = 'Map Range'
    bl_icon = 'MOD_OFFSET'

    def update_sockets(self, context):
        if not self.inputs["Old Min"].is_linked:
            self.inputs["Old Min"].hide_safe = self.auto_limits
        if not self.inputs["Old Max"].is_linked:
            self.inputs["Old Max"].hide_safe = self.auto_limits
        updateNode(self, context)

    old_min: FloatProperty(
        name='Old Min', description='Old Min',
        default=0, update=updateNode)

    old_max: FloatProperty(
        name='Old Max', description='Old Max',
        default=1, update=updateNode)

    new_min: FloatProperty(
        name='New Min', description='New Min',
        default=0, update=updateNode)

    new_max: FloatProperty(
        name='New Max', description='New Max',
        default=10, update=updateNode)

    value: FloatProperty(
        name='Value', description='New Max',
        default=.5, update=updateNode)

    clamp: BoolProperty(
        name='Clamp', description='clamp the values if they are outside the range',
        default=True, update=updateNode)

    auto_limits: BoolProperty(
        name='List limits', description='Use old min and old max from list',
        default=False, update=update_sockets)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'value'
        self.inputs.new('SvStringsSocket', "Old Min").prop_name = 'old_min'
        self.inputs.new('SvStringsSocket', "Old Max").prop_name = 'old_max'
        self.inputs.new('SvStringsSocket', "New Min").prop_name = 'new_min'
        self.inputs.new('SvStringsSocket', "New Max").prop_name = 'new_max'

        self.outputs.new('SvStringsSocket', "Value")

    def draw_buttons(self, context, layout):
        layout.prop(self, "auto_limits")
        if not self.auto_limits:
            layout.prop(self, "clamp")

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "auto_limits")
        if not self.auto_limits:
            layout.prop(self, "clamp")

        layout.prop(self, "list_match", expand=False)
        layout.prop(self, "output_numpy", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop(self, "auto_limits")
        if not self.auto_limits:
            layout.prop(self, "clamp")

        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "output_numpy", expand=False)

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        # no outputs, end early.
        if not outputs['Value'].is_linked:
            return

        params = [si.sv_get(default=[[]], deepcopy=False) for si in inputs]
        matching_f = list_match_func[self.list_match]
        desired_levels = [2 for p in params]
        ops = [self.clamp, self.auto_limits, self.list_match, self.output_numpy]
        result = recurse_f_level_control(params, ops, map_range, matching_f, desired_levels)

        self.outputs[0].sv_set(result)


def register():
    bpy.utils.register_class(SvMapRangeNode)


def unregister():
    bpy.utils.unregister_class(SvMapRangeNode)
