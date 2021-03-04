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
from sverchok.data_structure import (updateNode, match_long_cycle as C)
from mathutils.bvhtree import BVHTree

# zeffii 2017 8 okt
# airlifted from Kosvor's Raycast nodes..

class SvRaycasterLiteNode(bpy.types.Node, SverchCustomTreeNode):
    ''' svmesh to Raycast '''
    bl_idname = 'SvRaycasterLiteNode'
    bl_label = 'Raycaster'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_RAYCASTER'
    
    MaxDistance: bpy.props.FloatProperty(name='MaxDistance', description='MaxDistance', default=1.0, update=updateNode)
    start: bpy.props.FloatVectorProperty(default=(0,0,0), size=3, update=updateNode)
    direction: bpy.props.FloatVectorProperty(default=(0,0,-1), size=3, update=updateNode)

    def sv_init(self, context):
        si = self.inputs.new
        so = self.outputs.new

        si('SvVerticesSocket', 'Verts')
        si('SvStringsSocket', 'Faces')
        si('SvStringsSocket', 'MaxDistance').prop_name = 'MaxDistance' #添加输入最大距离接口
        si('SvVerticesSocket', 'Start').prop_name = 'start'
        si('SvVerticesSocket', 'Direction').prop_name = 'direction'

        so('SvVerticesSocket', 'Location')
        so('SvVerticesSocket', 'Normal')
        so('SvStringsSocket', 'Index')
        so('SvStringsSocket', 'Distance')
        so('SvStringsSocket', 'Success')

    @staticmethod
    def svmesh_to_bvh_lists(v, f):
        for vertices, polygons in zip(*C([v, f])):
            yield BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=0.0)

    def process(self):
        L, N, I, D, S = self.outputs
        RL = []
        # 添加max_distance-md-m
        vert_in, face_in, max_distance ,start_in, direction_in = C([sock.sv_get() for sock in self.inputs])

        for bvh, st, di ,md in zip(*[self.svmesh_to_bvh_lists(vert_in, face_in), start_in, direction_in,max_distance]):
            st, di, md = C([st, di,md])
            RL.append([bvh.ray_cast(i, i2,m) for i, i2,m in zip(st, di , md)])

        if L.is_linked:
            L.sv_set([[r[0][:] if r[0] else (0, 0, 0) for r in L] for L in RL])
        if N.is_linked:
            N.sv_set([[r[1][:] if r[1] else (0, 0, 0) for r in L] for L in RL])
        if I.is_linked:
            I.sv_set([[r[2] if r[2] else -1 for r in L] for L in RL])
        if D.is_linked:
            D.sv_set([[r[3] if r[3] else 0 for r in L] for L in RL])
        if S.is_linked:
            S.sv_set([[r[2] != None for r in L] for L in RL])


def register():
    bpy.utils.register_class(SvRaycasterLiteNode)


def unregister():
    bpy.utils.unregister_class(SvRaycasterLiteNode)
