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
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_manual_curves_utils import (
    get_valid_evaluate_function_legacy,
    get_valid_evaluate_function,
    get_valid_node,
    CURVE_NODE_TYPE,
    set_rgb_curve,
    get_rgb_curve)

from sverchok.utils.curve import SvScalarFunctionCurve

import numpy as np
node_group_name = 'sverchok_helper_group'
if (2, 82, 0) > bpy.app.version:
    get_evaluator = get_valid_evaluate_function_legacy
else:
    get_evaluator = get_valid_evaluate_function

def curve_mapper(params, constant, matching_f):
    result = []
    evaluate = constant
    for flist in params[0]:
        result.append([evaluate(v) for v in flist])

    return result

class SvCurveMapperNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Manual Curve remap
    Tooltip:  Map input list using a manually defined curve

    """
    bl_idname = 'SvCurveMapperNode'
    bl_label = 'Curve Mapper'
    bl_icon = 'NORMALIZE_FCURVES'

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

    def update_mapper(self, context):
        if self.update_curve:
            self.update_curve = False
            updateNode(self,context)

    update_curve: BoolProperty(
        name='Update', description='Update Node with updated curve',
        default=False, update=update_mapper)

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
    n_id: StringProperty(default='')

    def sv_init(self, context):
        self.width=200
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'value'

        self.outputs.new('SvStringsSocket', "Value")
        self.outputs.new('SvCurveSocket', "Curve")
        _ = get_evaluator(node_group_name, self._get_curve_node_name())


    def draw_buttons(self, context, layout):
        m = bpy.data.node_groups.get(node_group_name)
        if not m:
            layout.label(text="Connect input to activate")
            return
        try:
            tnode = m.nodes[self._get_curve_node_name()]
            if not tnode:
                layout.label(text="Connect input to activate")
                return
            layout.template_curve_mapping(tnode, "mapping", type="NONE")
            layout.prop(self, "update_curve", toggle=True)
        except AttributeError:
            layout.label(text="Connect input to activate")
            return

    def sv_copy(self, node):
        self.n_id = ''

    def free(self):
        m = bpy.data.node_groups.get(node_group_name)
        node = m.nodes[self._get_curve_node_name()]
        m.nodes.remove(node)

    def _get_curve_node_name(self):
        n_id = self.node_id
        return 'RGB Curves'+n_id

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        curve_node_name = self._get_curve_node_name()
        evaluate = get_evaluator(node_group_name, curve_node_name)
        curve_node = get_valid_node(node_group_name, curve_node_name, CURVE_NODE_TYPE)

        if 'Curve' in self.outputs:
            curve = SvScalarFunctionCurve(evaluate)
            curve.u_bounds = (curve_node.mapping.clip_min_x, curve_node.mapping.clip_max_x)
            self.outputs['Curve'].sv_set([curve])

        # no outputs, end early.
        if not outputs['Value'].is_linked:
            return
        result = []

        floats_in = inputs[0].sv_get(default=[[]], deepcopy=False)

        desired_levels = [2]
        result = recurse_f_level_control([floats_in], evaluate, curve_mapper, None, desired_levels)

        self.outputs[0].sv_set(result)

    def storage_set_data(self, node_ref):

        data_list = node_ref.get('curve_data')
        data_dict = json.loads(data_list)
        set_rgb_curve(data_dict, self.node_id)

    def storage_get_data(self, node_dict):

        node_name = 'RGB Curves'+ self.node_id
        data = get_rgb_curve(node_group_name, node_name)
        data_json_str = json.dumps(data)
        node_dict['curve_data'] = data_json_str



def register():
    bpy.utils.register_class(SvCurveMapperNode)


def unregister():
    bpy.utils.unregister_class(SvCurveMapperNode)
