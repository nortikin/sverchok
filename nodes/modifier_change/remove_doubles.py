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
from bpy.props import FloatProperty
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Vector_generate, repeat_last
from sverchok.utils.logging import info, debug

#
# Remove Doubles
# by Linus Yng

def remove_doubles(vertices, faces, d, face_data=None, find_doubles=False):

    if faces:
        EdgeMode = (len(faces[0]) == 2)

    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in vertices]

    if faces:
        if EdgeMode:
            for edge in faces:
                bm.edges.new([bm_verts[i] for i in edge])
        else:
            for face in faces:
                bm.faces.new([bm_verts[i] for i in face])

    if face_data:
        bm.faces.ensure_lookup_table()
        layer = bm.faces.layers.int.new("initial_index")
        for idx, face in enumerate(bm.faces):
            face[layer] = idx

    if find_doubles:
        res = bmesh.ops.find_doubles(bm, verts=bm_verts, dist=d)
        doubles = [vert.co[:] for vert in res['targetmap'].keys()]
    else:
        doubles = []

    bmesh.ops.remove_doubles(bm, verts=bm_verts, dist=d)
    edges = []
    faces = []
    face_data_out = []
    bm.verts.index_update()
    verts = [vert.co[:] for vert in bm.verts[:]]

    bm.edges.index_update()
    bm.faces.index_update()
    for edge in bm.edges[:]:
        edges.append([v.index for v in edge.verts[:]])
    for face in bm.faces:
        faces.append([v.index for v in face.verts[:]])
    if face_data:
        for face in bm.faces:
            initial_face_index = face[layer]
            if 0 <= initial_face_index < len(face_data):
                face_data_o = face_data[initial_face_index]
            else:
                info("No face data for face #%s", initial_face_index)
                face_data_o = None
            face_data_out.append(face_data_o)

    bm.clear()
    bm.free()
    return (verts, edges, faces, face_data_out, doubles)


class SvRemoveDoublesNode(bpy.types.Node, SverchCustomTreeNode):
    '''Remove doubles'''
    bl_idname = 'SvRemoveDoublesNode'
    bl_label = 'Remove Doubles'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_REMOVE_DOUBLES'

    distance: FloatProperty(
        name='Distance', description='Remove distance',
        default=0.001, precision=3, min=0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Distance').prop_name = 'distance'
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'PolyEdge')
        self.inputs.new('SvStringsSocket', 'FaceData')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')
        self.outputs.new('SvStringsSocket', 'FaceData')
        self.outputs.new('SvVerticesSocket', 'Doubles')

    def draw_buttons(self, context, layout):
        #layout.prop(self, 'distance', text="Distance")
        pass

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        if not self.inputs['Vertices'].is_linked:
            return

        verts = Vector_generate(self.inputs['Vertices'].sv_get())
        polys = self.inputs['PolyEdge'].sv_get(default=[[]])
        if 'FaceData' in self.inputs:
            face_data = self.inputs['FaceData'].sv_get(default=[[]])
        else:
            face_data = [[]]
        distance = self.inputs['Distance'].sv_get(default=[self.distance])[0]
        has_double_out = self.outputs['Doubles'].is_linked

        verts_out = []
        edges_out = []
        polys_out = []
        face_data_out = []
        d_out = []

        for v, p, ms, d in zip(verts, polys, face_data, repeat_last(distance)):
            res = remove_doubles(v, p, d, ms, has_double_out)
            if not res:
                return
            verts_out.append(res[0])
            edges_out.append(res[1])
            polys_out.append(res[2])
            face_data_out.append(res[3])
            d_out.append(res[4])

        self.outputs['Vertices'].sv_set(verts_out)

        # restrict setting this output when there is no such input
        if self.inputs['PolyEdge'].is_linked:
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Polygons'].sv_set(polys_out)

        if 'FaceData' in self.outputs:
            self.outputs['FaceData'].sv_set(face_data_out)
        self.outputs['Doubles'].sv_set(d_out)


def register():
    bpy.utils.register_class(SvRemoveDoublesNode)


def unregister():
    bpy.utils.unregister_class(SvRemoveDoublesNode)
