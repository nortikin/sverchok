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
from sverchok.utils.bvh_tree import bvh_tree_from_polygons

# zeffii 2017 8 okt
# airlifted from Kosvor's Raycast nodes..

class SvRaycasterLiteNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Raycast on Mesh
    Tooltip: Cast rays from arbitrary points on to a mesh a determine hiting location, normal at hitpoint, ray legngth and index of the hitted face.
    """
    bl_idname = 'SvRaycasterLiteNode'
    bl_label = 'Raycaster'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_RAYCASTER'

    start: bpy.props.FloatVectorProperty(default=(0,0,0), size=3, update=updateNode)
    direction: bpy.props.FloatVectorProperty(default=(0,0,-1), size=3, update=updateNode)
    all_triangles: bpy.props.BoolProperty(
        name='All Triangles',
        description='Enable to improve node performance if all inputted polygons are triangles',
        default=False,
        update=updateNode)
    safe_check: bpy.props.BoolProperty(
        name='Safe Check',
        description='When disabled polygon indices referring to unexisting points will crash Blender but makes node faster',
        default=True)
    epsilon: bpy.props.FloatProperty(
        name="epsilon",
        description="Float threshold for cut weak results",
        default=0.0,
        min=0.0,
        max=10.0,
        update=updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'all_triangles')
        layout.prop(self, 'safe_check')
        layout.prop(self, "epsilon")
    def sv_init(self, context):
        si = self.inputs.new
        so = self.outputs.new

        si('SvVerticesSocket', 'Verts')
        si('SvStringsSocket', 'Faces')
        si('SvVerticesSocket', 'Start').prop_name = 'start'
        si('SvVerticesSocket', 'Direction').prop_name = 'direction'

        so('SvVerticesSocket', 'Location')
        so('SvVerticesSocket', 'Normal')
        so('SvStringsSocket', 'Index')
        so('SvStringsSocket', 'Distance')
        so('SvStringsSocket', 'Success')

    @staticmethod
    def svmesh_to_bvh_lists(v, f, all_tris, epsilon, safe_check):
        for vertices, polygons in zip(*C([v, f])):
            yield bvh_tree_from_polygons(vertices, polygons, all_triangles=all_tris, epsilon=epsilon, safe_check=safe_check)

    def process(self):
        L, N, I, D, S = self.outputs
        RL = []
        if not any([s.is_linked for s in self.outputs]):
            return
        vert_in, face_in, start_in, direction_in = C([sock.sv_get(deepcopy=False) for sock in self.inputs])

        for bvh, st, di in zip(*[self.svmesh_to_bvh_lists(vert_in, face_in, self.all_triangles, self.epsilon, self.safe_check), start_in, direction_in]):
            st, di = C([st, di])
            RL.append([bvh.ray_cast(i, i2) for i, i2 in zip(st, di)])

        if L.is_linked:
            L.sv_set([[r[0][:] if (r[0] is not None) else (0, 0, 0) for r in L] for L in RL])
        if N.is_linked:
            N.sv_set([[r[1][:] if (r[1] is not None) else (0, 0, 0) for r in L] for L in RL])
        if I.is_linked:
            I.sv_set([[r[2] if (r[2] is not None) else -1 for r in L] for L in RL])
        if D.is_linked:
            D.sv_set([[r[3] if (r[3] is not None) else 0 for r in L] for L in RL])
        if S.is_linked:
            S.sv_set([[(r[2] is not None) for r in L] for L in RL])



def register():
    bpy.utils.register_class(SvRaycasterLiteNode)


def unregister():
    bpy.utils.unregister_class(SvRaycasterLiteNode)
