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
from bpy.props import BoolProperty
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat)


class SvBManalyzinNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh In and props two in one '''
    bl_idname = 'SvBManalyzinNode'
    bl_label = 'BMesh Analyze In'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode1 = BoolProperty(name='normal_update', default=True, update=updateNode)

    def sv_init(self, context):
        si, so = self.inputs.new, self.outputs.new
        si('StringsSocket', 'bmesh_list')
        si('VerticesSocket', 'Vert')
        si('StringsSocket', 'Edge')
        si('StringsSocket', 'Poly')

        so('StringsSocket', 'mesh-volume')
        so('StringsSocket', 'vert-edge angle')
        so('StringsSocket', 'vert-shell factor')
        so('StringsSocket', 'vert-is boundary')
        so('StringsSocket', 'vert-is manifold')
        so('StringsSocket', 'vert-is wire')
        so('VerticesSocket', 'vert-normal')

        so('StringsSocket', 'edge-face angle signed')
        so('StringsSocket', 'edge-length')
        so('StringsSocket', 'edge-is boundary')
        so('StringsSocket', 'edge-is contiguous')
        so('StringsSocket', 'edge-is convex')
        so('StringsSocket', 'edge-is manifold')
        so('StringsSocket', 'edge-is wire')

        so('StringsSocket', 'face-area')
        so('VerticesSocket', 'face-center bounds')
        so('VerticesSocket', 'face-center median')
        so('VerticesSocket', 'face-center median weighted')
        so('StringsSocket', 'face-perimeter')
        so('VerticesSocket', 'face-tangent edge')
        so('VerticesSocket', 'face-tangent edge diagonal')
        so('VerticesSocket', 'face-tangent edge pair')
        so('VerticesSocket', 'face-tangent vert diagonal')
        so('VerticesSocket', 'face-normal')

        so('StringsSocket', 'bmesh_list')

        self.width = 230

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "mode1",   text="Update normals")

    def process(self):
        bmL, V, E, P = self.inputs
        Val = bmL.sv_get() if bmL.is_linked else []
        o1,o2,o3,o4,o5,o6,o7,o8,o9,o10,o11,o12,o13,o14,o15,o16,o17,o18,o19,o20,o21,o22,o23,o24,o25 = self.outputs
        if V.is_linked:
            for v, e, f in zip(*match_long_repeat([V.sv_get(), E.sv_get([[]]), P.sv_get([[]])])):
                bm = bmesh_from_pydata(v, e, f)
                Val.append(bm)

        if self.mode1:
            for bm in Val:
                bm.normal_update()

        if o1.is_linked:
            o1.sv_set([[bm.calc_volume(signed=False) for bm in Val]])

        if o2.is_linked:
            o2.sv_set([[vert.calc_edge_angle(-1) for vert in bm.verts] for bm in Val])
        if o3.is_linked:
            o3.sv_set([[vert.calc_shell_factor() for vert in bm.verts] for bm in Val])
        if o4.is_linked:
            o4.sv_set([[vert.is_boundary for vert in bm.verts] for bm in Val])
        if o5.is_linked:
            o5.sv_set([[vert.is_manifold for vert in bm.verts] for bm in Val])
        if o6.is_linked:
            o6.sv_set([[vert.is_wire for vert in bm.verts] for bm in Val])
        if o7.is_linked:
            o7.sv_set([[vert.normal[:] for vert in bm.verts] for bm in Val])

        if o8.is_linked:
            o8.sv_set([[edge.calc_face_angle_signed(0) for edge in bm.edges] for bm in Val])
        if o9.is_linked:
            o9.sv_set([[edge.calc_length() for edge in bm.edges] for bm in Val])
        if o10.is_linked:
            o10.sv_set([[edge.is_boundary for edge in bm.edges] for bm in Val])
        if o11.is_linked:
            o11.sv_set([[edge.is_contiguous for edge in bm.edges] for bm in Val])
        if o12.is_linked:
            o12.sv_set([[edge.is_convex for edge in bm.edges] for bm in Val])
        if o13.is_linked:
            o13.sv_set([[edge.is_manifold for edge in bm.edges] for bm in Val])
        if o14.is_linked:
            o14.sv_set([[edge.is_wire for edge in bm.edges] for bm in Val])

        if o15.is_linked:
            o15.sv_set([[face.calc_area() for face in bm.faces] for bm in Val])
        if o16.is_linked:
            o16.sv_set([[face.calc_center_bounds()[:] for face in bm.faces] for bm in Val])
        if o17.is_linked:
            o17.sv_set([[face.calc_center_median()[:] for face in bm.faces] for bm in Val])
        if o18.is_linked:
            o18.sv_set([[face.calc_center_median_weighted()[:] for face in bm.faces] for bm in Val])
        if o19.is_linked:
            o19.sv_set([[face.calc_perimeter() for face in bm.faces] for bm in Val])
        if o20.is_linked:
            o20.sv_set([[face.calc_tangent_edge()[:] for face in bm.faces] for bm in Val])
        if o21.is_linked:
            o21.sv_set([[face.calc_tangent_edge_diagonal()[:] for face in bm.faces] for bm in Val])
        if o22.is_linked:
            o22.sv_set([[face.calc_tangent_edge_pair()[:] for face in bm.faces] for bm in Val])
        if o23.is_linked:
            o23.sv_set([[face.calc_tangent_vert_diagonal()[:] for face in bm.faces] for bm in Val])
        if o24.is_linked:
            o24.sv_set([[face.normal[:] for face in bm.faces] for bm in Val])

        if o25.is_linked:
            o25.sv_set(Val)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBManalyzinNode)


def unregister():
    bpy.utils.unregister_class(SvBManalyzinNode)
