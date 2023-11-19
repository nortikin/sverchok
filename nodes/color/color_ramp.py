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

import json
import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import updateNode
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_color_ramp_utils import (
    get_valid_evaluate_function as get_evaluator,
    set_color_ramp,
    get_color_ramp)


node_group_name = 'sverchok_helper_group'

def color_ramp_mapper(params, constant, matching_f):
    result = []
    evaluate, use_alpha = constant
    if use_alpha:
        for flist in params[0]:
            result.append([evaluate(v) for v in flist])
    else:
        for flist in params[0]:
            result.append([evaluate(v)[:-1] for v in flist])
    return result

class SvColorRampNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Color Gradient
    Tooltip:  Map input list to a defined color.\n\tIn: Value\n\tParams: Color Stops, Use Alpha [On]/Off, Update Node (Btn)\n\tOut: Color

    """
    bl_idname = 'SvColorRampNode'
    bl_label = 'Color Ramp'
    bl_icon = 'COLOR'
    sv_icon = 'SV_COLOR_RAMP'
    is_scene_dependent = True

    value: FloatProperty(
        name='Value', description='Input value(s)',
        default=.5, update=updateNode)

    use_alpha: BoolProperty(name="Use Alpha", default=True, update=updateNode)


    def sv_init(self, context):
        self.width = 250
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'value'

        self.outputs.new('SvColorSocket', "Color")
        _ = get_evaluator(node_group_name, self._get_color_ramp_node_name())

    def sv_draw_buttons(self, context, layout):
        m = bpy.data.node_groups.get(node_group_name)
        if not m:
            layout.label(text="Connect input to activate")
            return
        try:
            layout.prop(self, 'use_alpha')
            tnode = m.nodes[self._get_color_ramp_node_name()]
            if not tnode:
                layout.label(text="Connect input to activate")
                return
            layout.template_color_ramp(tnode, "color_ramp", expand=True)

        except AttributeError:
            layout.label(text="Connect input to activate")
            return

    def sv_copy(self, node):
        self.n_id = ''

    def free(self):
        m = bpy.data.node_groups.get(node_group_name)
        node = m.nodes[self._get_color_ramp_node_name()]
        m.nodes.remove(node)

    def _get_color_ramp_node_name(self):
        n_id = self.node_id
        return 'Color Ramp'+n_id

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        color_ramp_node_name = self._get_color_ramp_node_name()
        evaluate = get_evaluator(node_group_name, color_ramp_node_name)

        # no outputs, end early.
        if not outputs['Color'].is_linked:
            return
        result = []
        floats_in = inputs[0].sv_get(default=[[]], deepcopy=False)

        desired_levels = [2]
        result = recurse_f_level_control([floats_in], [evaluate, self.use_alpha], color_ramp_mapper, None, desired_levels)

        self.outputs[0].sv_set(result)

    def load_from_json(self, node_data: dict, import_version: float):
        '''function to get data when importing from json'''
        data_list = node_data.get('color_ramp_data')
        data_dict = json.loads(data_list)
        color_ramp_node_name = self._get_color_ramp_node_name()
        set_color_ramp(data_dict, color_ramp_node_name)

    def save_to_json(self, node_data: dict):
        '''function to set data for exporting json'''
        color_ramp_node_name = self._get_color_ramp_node_name()
        data = get_color_ramp(node_group_name, color_ramp_node_name)
        data_json_str = json.dumps(data)
        node_data['color_ramp_data'] = data_json_str


    def sv_copy(self, other):  # like curve mapper
        '''
        self: is the new node, other: is the old node
        by the time this function is called the new node has a new empty n_id
        a new n_id will be generated as a side effect of _get_curve_node_name
        '''
        color_ramp_node_name = self._get_color_ramp_node_name()
        _ = get_evaluator(node_group_name, color_ramp_node_name)

        old_color_node_name = other._get_color_ramp_node_name()
        data = get_color_ramp(node_group_name, old_color_node_name)
        set_color_ramp(data, color_ramp_node_name)

        self.refresh_node(None)



def register():
    bpy.utils.register_class(SvColorRampNode)


def unregister():
    bpy.utils.unregister_class(SvColorRampNode)
