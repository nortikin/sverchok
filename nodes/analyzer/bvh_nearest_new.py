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
from bpy.props import EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_cycle as C)
from mathutils.bvhtree import BVHTree


class SvBVHnearNewNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BVH Find Nearest '''
    bl_idname = 'SvBVHnearNewNode'
    bl_label = 'bvh_nearest'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POINT_ON_MESH'

    modes = [
            ("find_nearest", "nearest", "", 0),
            ("find_nearest_range", "nearest in range", "", 1),
        ]

    mode: EnumProperty(name="Mode", items=modes, default='find_nearest', update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')

    def sv_init(self, context):
        si = self.inputs.new
        so = self.outputs.new
        si('SvVerticesSocket', 'Verts')
        si('SvStringsSocket', 'Faces')
        si('SvVerticesSocket', 'Points').use_prop = True
        so('SvVerticesSocket', 'Location')
        so('SvVerticesSocket', 'Normal')
        so('SvStringsSocket', 'Index')
        so('SvStringsSocket', 'Distance')

    @staticmethod
    def svmesh_to_bvh_lists(vsock, fsock):
        for vertices, polygons in zip(*C([vsock.sv_get(), fsock.sv_get()])):
            yield BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=0.0)

    def process(self):
        vert_sock, face_sock, point_sock = self.inputs
        L, N, I, D = self.outputs
        RL = []
        PT = point_sock.sv_get()
        if self.mode == 'find_nearest':
            for bvh, pt in zip(self.svmesh_to_bvh_lists(vert_sock, face_sock), PT):
                RL.append([bvh.find_nearest(P) for P in pt])
        else:  # find_nearest_range
            for bvh, pt in zip(self.svmesh_to_bvh_lists(vert_sock, face_sock), PT):
                RL.extend([bvh.find_nearest_range(P) for P in pt])
        if L.is_linked:
            L.sv_set([[r[0][:] for r in L] for L in RL])
        if N.is_linked:
            N.sv_set([[r[1][:] for r in L] for L in RL])
        if I.is_linked:
            I.sv_set([[r[2] for r in L] for L in RL])
        if D.is_linked:
            D.sv_set([[r[3] for r in L] for L in RL])


def register():
    bpy.utils.register_class(SvBVHnearNewNode)


def unregister():
    bpy.utils.unregister_class(SvBVHnearNewNode)
