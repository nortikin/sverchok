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
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList, checking_links, iterate_process, Input, Output, match_inputs, std_links_processing
from sverchok.utils.sv_bmesh_utils import with_bmesh

class SvTriangulateNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Triangulate mesh '''
    bl_idname = 'SvTriangulateNode'
    bl_label = 'Triangulate'
    bl_icon = 'OUTLINER_OB_EMPTY'

    quad_modes = [
            ("0", "Beauty", "Split the quads in nice triangles, slower method", 1),
            ("1", "Fixed", "Split the quads on the 1st and 3rd vertices", 2),
            ("2", "Fixed Alternate", "Split the quads on the 2nd and 4th vertices", 3),
            ("3", "Shortest Diagonal", "Split the quads based on the distance between the vertices", 4)
        ]

    ngon_modes = [
            ("0", "Beauty", "Arrange the new triangles nicely, slower method", 1),
            ("1", "Clip", "Split the ngons using a scanfill algorithm", 2)
        ]
    
    quad_mode = EnumProperty(name='Quads mode',
        description="Quads processing mode",
        items = quad_modes,
        default="0",
        update=updateNode)

    ngon_mode = EnumProperty(name="Polygons mode",
        description="Polygons processing mode",
        items = ngon_modes,
        default="0",
        update=updateNode)

    input_descriptors = [
         Input('VerticesSocket', 'Vertices', default=[[]]),
         Input('StringsSocket',  'Edges',    default=[[]], is_mandatory=False),
         Input('StringsSocket',  'Polygons', default=[[]]),
         Input('StringsSocket',  'Mask',     default=[[True]], is_mandatory=False)
        ]

    output_descriptors = [
         Output('VerticesSocket', 'Vertices'),
         Output('StringsSocket',  'Edges'),
         Output('StringsSocket',  'Polygons'),
         Output('StringsSocket',  'NewEdges'),
         Output('StringsSocket',  'NewPolys')
        ]

    def draw_buttons(self, context, layout):
        layout.prop(self, "quad_mode")
        layout.prop(self, "ngon_mode")

    @std_links_processing(match_long_repeat)
    @with_bmesh
    def process(self, bm, mask):
        fullList(mask, len(bm.faces))

        b_faces = []
        for m, face in zip(mask,bm.faces):
            if m:
                b_faces.append(face)

        res = bmesh.ops.triangulate(bm, faces=b_faces,
                        quad_method=int(self.quad_mode),
                        ngon_method=int(self.ngon_mode))

        b_new_edges = [tuple(v.index for v in edge.verts) for edge in res['edges']]
        b_new_faces = [[v.index for v in face.verts] for face in res['faces']]

        return bm, b_new_edges, b_new_faces

def register():
    bpy.utils.register_class(SvTriangulateNode)


def unregister():
    bpy.utils.unregister_class(SvTriangulateNode)

if __name__ == '__main__':
    register()



