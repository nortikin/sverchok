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
from bpy.props import IntProperty, FloatProperty, EnumProperty
import mathutils
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, enum_item_4, list_match_func, list_match_modes
from sverchok.utils.sv_KDT_utils import kdt_closest_edges, scipy_kdt_closest_edges_fast, scipy_kdt_closest_max_queried, scipy_kdt_closest_edges_no_skip
from sverchok.dependencies import scipy

def fast_mode():
    return scipy is not None

class SvKDTreeEdgesNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Create Edges by distance
    Tooltip: Join verts pairs by defining distance range and number of connections
    '''
    bl_idname = 'SvKDTreeEdgesNodeMK2'
    bl_label = 'KDT Closest Edges MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_KDT_EDGES'

    mindist: FloatProperty(
        name='mindist', description='Minimum dist', min=0.0,
        default=0.1, update=updateNode)

    maxdist: FloatProperty(
        name='maxdist', description='Maximum dist', min=0.0,
        default=2.0, update=updateNode)

    maxNum: IntProperty(
        name='maxNum', description='max edge count',
        default=4, min=1, update=updateNode)

    skip: IntProperty(
        name='skip', description='skip first n',
        default=0, min=0, update=updateNode)

    def update_sockets(self, context):
        self.inputs['maxNum'].hide_safe = self.mode == 'Fast'
        self.inputs['skip'].hide_safe = self.mode in ['Fast', 'No_Skip']

        updateNode(self, context)
    mode: EnumProperty(
        name='Mode', description='Implementation used',
        items=enum_item_4(['Fast', 'Max Queried', 'No Skip', 'Complete']),
        default='Fast', update=update_sockets)
    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'mindist').prop_name = 'mindist'
        self.inputs.new('SvStringsSocket', 'maxdist').prop_name = 'maxdist'
        self.inputs.new('SvStringsSocket', 'maxNum').prop_name = 'maxNum'
        self.inputs.new('SvStringsSocket', 'skip').prop_name = 'skip'
        self.inputs['maxNum'].hide_safe = True
        self.inputs['skip'].hide_safe = True
        self.outputs.new('SvStringsSocket', 'Edges')

    def draw_buttons(self, context, layout):
        if fast_mode():
            layout.prop(self, 'mode')
    def draw_buttons_ext(self, context, layout):
        if fast_mode():
            layout.prop(self, 'mode')
        layout.prop(self, 'list_match')

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        if not inputs['Verts'].is_linked or not outputs['Edges'].is_linked:
            return
        params = [inputs['Verts'].sv_get(deepcopy=False)]
        match = list_match_func[self.list_match]
        if fast_mode() and self.mode != 'Complete':
            if self.mode == 'Fast':
                params.extend([sk.sv_get(deepcopy=False)[0] for sk in self.inputs[1:3]])
                result = [scipy_kdt_closest_edges_fast(vs, min_d, max_d) for vs, min_d, max_d  in zip(*match(params))]
            elif self.mode == 'Max_Queried':
                params.extend([sk.sv_get(deepcopy=False)[0] for sk in self.inputs[1:]])
                result = [scipy_kdt_closest_max_queried(vs, min_d, max_d, max_num, skip) for vs, min_d, max_d, max_num, skip  in zip(*match(params))]
            elif self.mode == 'No_Skip':
                params.extend([sk.sv_get(deepcopy=False)[0] for sk in self.inputs[1:]])
                result = [scipy_kdt_closest_edges_no_skip(vs, min_d, max_d, max_num, skip) for vs, min_d, max_d, max_num, skip  in zip(*match(params))]

        else:
            params.extend([sk.sv_get(deepcopy=False)[0] for sk in self.inputs[1:]])
            result = [kdt_closest_edges(p[0], p[1:]) for p in zip(*match(params))]
        outputs['Edges'].sv_set(result)

def register():
    bpy.utils.register_class(SvKDTreeEdgesNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvKDTreeEdgesNodeMK2)
