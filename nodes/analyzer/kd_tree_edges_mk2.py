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
from bpy.props import IntProperty, FloatProperty
import mathutils

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_KDT_utils import kdt_closest_edges

class SvKDTreeEdgesNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Create Edges by distance
    Tooltip: Join verts pairs by defining distance range and number of connections
    '''
    bl_idname = 'SvKDTreeEdgesNodeMK2'
    bl_label = 'KDT Closest Edges MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_KDT_EDGES'

    mindist : FloatProperty(
        name='mindist', description='Minimum dist', min=0.0,
        default=0.1, update=updateNode)

    maxdist : FloatProperty(
        name='maxdist', description='Maximum dist', min=0.0,
        default=2.0, update=updateNode)

    maxNum : IntProperty(
        name='maxNum', description='max edge count',
        default=4, min=1, update=updateNode)

    skip : IntProperty(
        name='skip', description='skip first n',
        default=0, min=0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'mindist').prop_name = 'mindist'
        self.inputs.new('SvStringsSocket', 'maxdist').prop_name = 'maxdist'
        self.inputs.new('SvStringsSocket', 'maxNum').prop_name = 'maxNum'
        self.inputs.new('SvStringsSocket', 'skip').prop_name = 'skip'

        self.outputs.new('SvStringsSocket', 'Edges')

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        try:
            verts = inputs['Verts'].sv_get()[0]
            linked = outputs['Edges'].is_linked
            if not linked:
                return
        except (IndexError, KeyError) as e:
            return

        optional_sockets = [
            ['mindist', self.mindist, float],
            ['maxdist', self.maxdist, float],
            ['maxNum', self.maxNum, int],
            ['skip', self.skip, int]]

        socket_inputs = []
        for s, s_default_value, dtype in optional_sockets:
            if s in inputs and inputs[s].is_linked:
                sock_input = dtype(inputs[s].sv_get()[0][0])
            else:
                sock_input = s_default_value
            socket_inputs.append(sock_input)

        kdt_closest_edges(verts, socket_inputs, outputs['Edges'])


def register():
    bpy.utils.register_class(SvKDTreeEdgesNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvKDTreeEdgesNodeMK2)
