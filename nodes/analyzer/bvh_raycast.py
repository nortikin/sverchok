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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as C)


class SvBVHRaycastNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BVH Tree Raycast '''
    bl_idname = 'SvBVHRaycastNode'
    bl_label = 'bvh_raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'BVH_tree_list')
        self.inputs.new('VerticesSocket', 'Start').use_prop=True
        self.inputs.new('VerticesSocket', 'Direction').use_prop=True
        self.outputs.new('VerticesSocket', 'Location')
        self.outputs.new('VerticesSocket', 'Normal')
        self.outputs.new('StringsSocket', 'Index')
        self.outputs.new('StringsSocket', 'Distance')

    def process(self):
        outL,outN,outI,outD = [],[],[],[]
        bvhl, st, di = self.inputs
        st,di = C(st.sv_get()[0], di.sv_get()[0])
        for bvh in bvhl.sv_get():
            L,N,I,D = [],[],[],[]
            for i,i2 in zip(st,di):
                r = bvh.ray_cast(i, i2)
                L.append(r[0])
                N.append(r[1])
                I.append(r[2])
                D.append(r[3])
            outL.append(L)
            outN.append(N)
            outI.append(I)
            outD.append(D)
        for i, i2 in zip([outL,outN,outI,outD], self.outputs):
            i2.sv_set(i)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBVHRaycastNode)


def unregister():
    bpy.utils.unregister_class(SvBVHRaycastNode)
