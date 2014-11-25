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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Vector_generate, SvSetSocketAnyType, SvGetSocketAnyType

#
# Convex Hull
# by Linus Yng


def make_hull(vertices):
    if not vertices:
        return False

    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in vertices]
    bmesh.ops.convex_hull(bm, input=bm_verts, use_existing_faces=False)

    edges = []
    faces = []
    bm.verts.index_update()
    bm.faces.index_update()
    verts = [vert.co[:] for vert in bm.verts[:]]
    for face in bm.faces:
        faces.append([v.index for v in face.verts[:]])
    bm.clear()
    bm.free()
    return (verts, faces)


class SvConvexHullNode(bpy.types.Node, SverchCustomTreeNode):
    '''Create convex hull'''
    bl_idname = 'SvConvexHullNode'
    bl_label = 'Convex Hull'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')

        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Polygons', 'Polygons')

    def draw_buttons(self, context, layout):
        pass

    def process(self):

        if 'Vertices' in self.inputs and self.inputs['Vertices'].is_linked:

            verts = Vector_generate(SvGetSocketAnyType(self, self.inputs['Vertices']))

            verts_out = []
            polys_out = []

            for v_obj in verts:
                res = make_hull(v_obj)
                if not res:
                    return
                verts_out.append(res[0])
                polys_out.append(res[1])

            if 'Vertices' in self.outputs and self.outputs['Vertices'].is_linked:
                SvSetSocketAnyType(self, 'Vertices', verts_out)

            if 'Polygons' in self.outputs and self.outputs['Polygons'].is_linked:
                SvSetSocketAnyType(self, 'Polygons', polys_out)


def register():
    bpy.utils.register_class(SvConvexHullNode)


def unregister():
    bpy.utils.unregister_class(SvConvexHullNode)
