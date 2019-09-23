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
from bpy.props import IntProperty, BoolProperty, FloatProperty
from bmesh.ops import dissolve_limit
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat as mlr, second_as_first_cycle as safc
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


class SvLimitedDissolveMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Limited Dissolve MK2 '''
    bl_idname = 'SvLimitedDissolveMK2'
    bl_label = 'Limited Dissolve MK2'
    bl_icon = 'MOD_DECIM'

    angle: FloatProperty(default=5.0, min=0.0, update=updateNode)
    use_dissolve_boundaries: BoolProperty(update=updateNode)
    delimit: IntProperty(update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'bmesh_list')
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Polys')
        self.inputs.new('SvStringsSocket', 'Vert index')
        self.inputs.new('SvStringsSocket', 'Edge index')
        self.inputs.new('SvStringsSocket', 'Angle Limit').prop_name = 'angle'
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polys')
        self.outputs.new('SvStringsSocket', 'bm region')
        self.outputs.new('SvStringsSocket', 'bmesh_list')

    def draw_buttons(self, context, layout):
        layout.prop(self, "use_dissolve_boundaries")
        layout.prop(self, "delimit")

    def process(self):
        BML, Verts, Edges, Polys, vermask, edgmask, angllim = self.inputs
        o1,o2,o3,o4,o5 = self.outputs
        angle = angllim.sv_get()[0]
        ret = []
        bmlist = BML.sv_get([])
        if Verts.is_linked:
            bmlist.extend([bmesh_from_pydata(verts, edges, faces, normal_update=True) for verts, edges, faces in zip(*mlr([Verts.sv_get(), Edges.sv_get([[]]), Polys.sv_get([[]])]))])
        if vermask.is_linked:
            verm = [np.array(bm.verts[:])[ma] for bm,ma in zip(bmlist,vermask.sv_get())]
        else:
            verm = [bm.verts for bm in bmlist]
        if edgmask.is_linked:
            edgm = [np.array(bm.edges[:])[ma] for bm,ma in zip(bmlist,edgmask.sv_get())]
        else:
            edgm = [bm.edges for bm in bmlist]
        udb = self.use_dissolve_boundaries
        for bm, ang, vm, em in zip(bmlist, safc(bmlist, angle), verm, edgm):
            # it's a little undocumented..
            ret.append(dissolve_limit(bm, angle_limit=ang, use_dissolve_boundaries=udb, verts=vm, edges=em)['region'])
            # delimit is {'NORMAL', 'MATERIAL', 'SEAM', 'SHARP', 'UV'} set now. Not so useful in Sverchok.
        if o1.is_linked:
            o1.sv_set([[v.co[:] for v in bm.verts]for bm in bmlist])
        if o2.is_linked:
            o2.sv_set([[[i.index for i in e.verts] for e in bm.edges]for bm in bmlist])
        if o3.is_linked:
            o3.sv_set([[[i.index for i in p.verts] for p in bm.faces]for bm in bmlist])
        if o4.is_linked:
            o4.sv_set(ret)
        if o5.is_linked:
            o5.sv_set(bmlist)


def register():
    bpy.utils.register_class(SvLimitedDissolveMK2)


def unregister():
    bpy.utils.unregister_class(SvLimitedDissolveMK2)
