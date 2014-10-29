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

from bpy.props import FloatProperty

from sv_node_tree import SverchCustomTreeNode
from sv_data_structure import Vector_generate, SvSetSocketAnyType, SvGetSocketAnyType, updateNode
from utils.sv_bmesh_utils import bmesh_from_pydata


def join_tris(verts, faces, limit):
    if not verts:
        return False

    bm = bmesh_from_pydata(verts, [], faces)

    bmesh.ops.join_triangles(bm, faces=bm.faces, limit=limit)
    bm.verts.index_update()
    bm.faces.index_update()

    faces_out = []
    verts_out = [vert.co[:] for vert in bm.verts]
    [faces_out.append([v.index for v in face.verts]) for face in bm.faces]

    bm.clear()
    bm.free()
    return (verts_out, faces_out)


class SvJoinTrianglesNode(bpy.types.Node, SverchCustomTreeNode):
    '''Join coplanar Triangles'''
    bl_idname = 'SvJoinTrianglesNode'
    bl_label = 'Join Triangles'
    bl_icon = 'OUTLINER_OB_EMPTY'

    limit = FloatProperty(
        min=0.0, max=5.0, step=0.01,
        name='limit', description='not sure',
        update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.inputs.new('StringsSocket', 'Polygons', 'Polygons')

        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Polygons', 'Polygons')

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'limit', text='limit')
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

        if not (len(verts) == len(faces)):
            return

        verts_out = []
        polys_out = []

        for v_obj, f_obj in zip(verts, faces):
            res = join_tris(v_obj, f_obj, self.limit)
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
    bpy.utils.register_class(SvJoinTrianglesNode)


def unregister():
    bpy.utils.unregister_class(SvJoinTrianglesNode)
