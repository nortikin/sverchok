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
import mathutils
from bpy.props import FloatProperty, EnumProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat as mlr)
from sverchok.utils.sv_KDT_utils import kdt_closest_verts_range, kdt_closest_verts_find_n

class SvKDTreeNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Find nearest verts
    Tooltip: Find nearest verts to another verts group
    '''

    bl_idname = 'SvKDTreeNodeMK2'
    bl_label = 'KDT Closest Verts MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_KDT_VERTS'

    modes = [
        ('find_n', 'find_n', 'find certain number of closest tree vectors', '', 0),
        ('find_range', 'find_range', 'find closest tree vectors in range', '', 1),
    ]

    func_dict = {
        'find_n': kdt_closest_verts_find_n,
        'find_range': kdt_closest_verts_range
        }

    number : IntProperty(
        min=1, default=1, name='Number',
        description="find this amount", update=updateNode)

    radius : FloatProperty(
        min=0, default=1, name='Radius',
        description="search in this radius", update=updateNode)

    def update_mode(self, context):
        self.inputs['number'].hide_safe = self.mode == "find_range"
        self.inputs['radius'].hide_safe = self.mode == "find_n"
        updateNode(self, context)

    mode : EnumProperty(
        items=modes, description="mathutils kdtree metods",
        default="find_n", update=update_mode)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'mode', expand=True)

    def sv_init(self, context):

        si = self.inputs
        so = self.outputs
        si.new('SvVerticesSocket', 'insert')
        si.new('SvVerticesSocket', 'find').use_prop = True
        si.new('SvStringsSocket', 'number').prop_name = "number"
        si.new('SvStringsSocket', 'radius').prop_name = "radius"
        si['radius'].hide_safe = True
        so.new('SvVerticesSocket', 'Co')
        so.new('SvStringsSocket', 'index')
        so.new('SvStringsSocket', 'distance')

    def process(self):
        '''main node function called every update'''
        si = self.inputs
        so = self.outputs
        if not (any(s.is_linked for s in so) and si[0].is_linked):
            return
        V1, V2, N, R = mlr([i.sv_get() for i in si])
        out = []
        Co, ind, dist = so
        find_n = self.mode == "find_n"
        func = self.func_dict[self.mode]
        for v, v2, k in zip(V1, V2, (N if find_n else R)):
            func(v, v2, k, out)

        if Co.is_linked:
            Co.sv_set([[i[0][:] for i in i2] for i2 in out])
        if ind.is_linked:
            ind.sv_set([[i[1] for i in i2] for i2 in out])
        if dist.is_linked:
            dist.sv_set([[i[2] for i in i2] for i2 in out])


def register():
    bpy.utils.register_class(SvKDTreeNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvKDTreeNodeMK2)
