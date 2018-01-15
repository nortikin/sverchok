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
import numpy as np
from bpy.props import IntProperty
from bmesh.ops import unsubdivide
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat as mlr
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata as bfp, pydata_from_bmesh as pfb


class SvUnsubdivideNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Unsubdivide vertices if possible '''
    bl_idname = 'SvUnsubdivideNode'
    bl_label = 'Unsubdivide'
    bl_icon = 'OUTLINER_OB_EMPTY'

    iteration = IntProperty(default=1, min=1, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Verts')
        self.inputs.new('StringsSocket', 'Edges')
        self.inputs.new('StringsSocket', 'Polys')
        self.inputs.new('StringsSocket', 'Verts Index')
        self.outputs.new('VerticesSocket', 'Verts')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polys')

    def draw_buttons(self, context, layout):
        layout.prop(self, "iteration")

    def process(self):
        V, E, F, ind = self.inputs
        Ov, Oe, Op = self.outputs
        if Ov.is_linked:
            r_v = []
            r_e = []
            r_f = []
            bmlist = [bfp(v, e, f, normal_update=True) for v, e, f in zip(*mlr([V.sv_get(), E.sv_get([[]]), F.sv_get([[]])]))]
            if ind.is_linked:
                usev = [np.array(bm.verts[:])[ind] for bm, ind in zip(bmlist, ind.sv_get())]
            else:
                usev = [bm.verts for bm in bmlist]
            for bm, usind in zip(bmlist, usev):
                unsubdivide(bm, verts=usind, iterations=self.iteration)
                new_verts, new_edges, new_faces = pfb(bm)
                bm.free()
                r_v.append(new_verts)
                r_e.append(new_edges)
                r_f.append(new_faces)
            Ov.sv_set(r_v)
            Oe.sv_set(r_e)
            Op.sv_set(r_f)


def register():
    bpy.utils.register_class(SvUnsubdivideNode)


def unregister():
    bpy.utils.unregister_class(SvUnsubdivideNode)
