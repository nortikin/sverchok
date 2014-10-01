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

from node_tree import SverchCustomTreeNode
from data_structure import Vector_generate, SvSetSocketAnyType, SvGetSocketAnyType


def join_tris(verts, faces):
    if not vertices:
        return False

    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in verts]
    bm_faces = [bm.faces.new(f) for f in faces]
    # join_triangles(bm, faces, cmp_sharp, cmp_uvs, cmp_vcols, cmp_materials, limit)
    # bmesh.ops.convex_hull(bm, input=bm_verts, use_existing_faces=False)
    bmesh.ops.join_triangles(bm, input=bm_faces, limit=0.001)
    bm.verts.index_update()
    bm.faces.index_update()

    verts_out = []
    faces_out = []
    verts = [vert.co[:] for vert in bm.verts[:]]
    for face in bm.faces:
        faces.append([v.index for v in face.verts[:]])
    bm.clear()
    bm.free()
    return (verts, faces)


class SvJoinTriangles(bpy.types.Node, SverchCustomTreeNode):
    '''Join coplanar Triangles'''
    bl_idname = 'SvJoinTriangles'
    bl_label = 'Join Triangles'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.inputs.new('StringsSocket', 'Polygons', 'Polygons')

        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Polygons', 'Polygons')

    def draw_buttons(self, context, layout):
        pass

    def update(self):

        if not len(self.outputs) == 2:
            return

        if not (self.inputs['Vertices'].links and self.inputs['Polygons'].links):
            return

        if not self.outputs['Polygons'].links:
            return

        self.process()

    def process(self):

        verts = Vector_generate(SvGetSocketAnyType(self, self.inputs['Vertices']))
        faces = self.inputs['Polygons'].sv_get()

        if not len(verts) == len(faces):
            return

        verts_out = []
        polys_out = []

        for v_obj, f_obj in zip(verts, faces):
            res = join_tris(v_obj, f_obj)
            if not res:
                return
            verts_out.append(res[0])
            polys_out.append(res[1])

        if self.outputs['Vertices'].links:
            SvSetSocketAnyType(self, 'Vertices', verts_out)

        SvSetSocketAnyType(self, 'Polygons', polys_out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvJoinTriangles)


def unregister():
    bpy.utils.unregister_class(SvJoinTriangles)
