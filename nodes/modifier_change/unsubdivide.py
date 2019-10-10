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
import bmesh
from bmesh.ops import unsubdivide
import numpy as np
from bpy.props import IntProperty
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)


class SvUnsubdivideNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Unsubdivide vertices if possible '''
    bl_idname = 'SvUnsubdivideNode'
    bl_label = 'Unsubdivide'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_UNSUBDIVIDE'

    iter: IntProperty(name='itr', default=1, min=1, update=updateNode)

    def sv_init(self, context):
        si, so = self.inputs.new, self.outputs.new
        si('SvStringsSocket', 'bmesh_list')
        si('SvVerticesSocket', 'Vert')
        si('SvStringsSocket', 'Poly')
        si('SvStringsSocket', 'Verts Index')
        si('SvStringsSocket', 'iteration').prop_name = 'iter'
        so('SvVerticesSocket', 'Verts')
        so('SvStringsSocket', 'Edges')
        so('SvStringsSocket', 'Faces')
        so('SvStringsSocket', 'bmesh_list')

    def process(self):
        bmL, V, P, mask, Iterate = self.inputs
        Val = bmL.sv_get([])
        out2 = []
        o1,o2,o3,o4 = self.outputs
        if V.is_linked:
            for v, f in zip(V.sv_get(), P.sv_get()):
                Val.append(bmesh_from_pydata(v, [], f))
        if mask.is_linked:
            seleg = [np.array(bm.verts[:])[ma] for bm,ma in zip(Val,mask.sv_get())]
        else:
            seleg = [bm.verts for bm in Val]
        for bm,se,itera in zip(Val, seleg, safc(Val, Iterate.sv_get()[0])):
            unsubdivide(bm, verts=se, iterations=itera)
        if o1.is_linked:
            o1.sv_set([[v.co[:] for v in bm.verts]for bm in Val])
        if o2.is_linked:
            o2.sv_set([[[i.index for i in e.verts] for e in bm.edges]for bm in Val])
        if o3.is_linked:
            o3.sv_set([[[i.index for i in p.verts] for p in bm.faces]for bm in Val])
        if o4.is_linked:
            o4.sv_set(Val)


def register():
    bpy.utils.register_class(SvUnsubdivideNode)


def unregister():
    bpy.utils.unregister_class(SvUnsubdivideNode)
