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
from itertools import chain, repeat
import bpy
from bpy.props import FloatProperty
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Vector_generate, repeat_last, zip_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, face_data_from_bmesh_faces, vert_data_from_bmesh_verts
from sverchok.utils.logging import info, debug


def remove_doubles(vertices, faces, d, face_data=None, find_doubles=False, mask=[], output_mask=False):

    if faces:
        EdgeMode = (len(faces[0]) == 2)
    if face_data:
        mark_face_data = True
    else:
        mark_face_data = False

    bm = bmesh_from_pydata(
        vertices,
        faces if EdgeMode else [],
        [] if EdgeMode else faces,
        markup_face_data=mark_face_data,
        markup_vert_data=output_mask)
    bm_verts = bm.verts

    if mask:
        mask_full = chain(mask, repeat(mask[-1]))
        bm_verts = [v for v, m in zip(bm_verts, mask_full) if m]

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
        face_data_out = face_data_from_bmesh_faces(bm, face_data)
    if output_mask:
        mask_out = vert_data_from_bmesh_verts(bm, mask)
    else:
        mask_out = []

    bm.clear()
    bm.free()
    return (verts, edges, faces, face_data_out, doubles, mask_out)


class SvRemoveDoublesNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Merge by Distance
    Tooltip: Merge Vertices that are closer than a distance.
    """
    bl_idname = 'SvRemoveDoublesNodeMk2'
    bl_label = 'Remove Doubles2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_REMOVE_DOUBLES'

    distance: FloatProperty(
        name='Distance', description='Remove distance',
        default=0.001, precision=3, min=0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'PolyEdge')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.inputs.new('SvStringsSocket', 'Mask')
        self.inputs.new('SvStringsSocket', 'Distance').prop_name = 'distance'

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')
        self.outputs.new('SvStringsSocket', 'FaceData')
        self.outputs.new('SvVerticesSocket', 'Doubles')
        self.outputs.new('SvStringsSocket', 'Mask')

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
        face_data = self.inputs['FaceData'].sv_get(default=[[]])
        distance = self.inputs['Distance'].sv_get(default=[self.distance])[0]
        has_double_out = self.outputs['Doubles'].is_linked
        mask_s = self.inputs['Mask'].sv_get(default=[[]], deepcopy=False)
        has_mask_out = self.outputs['Mask'].is_linked
        verts_out = []
        edges_out = []
        polys_out = []
        face_data_out = []
        d_out = []
        mask_out = []

        for v, p, ms, d, mask in zip_long_repeat(verts, polys, face_data, distance, mask_s):
            res = remove_doubles(v, p, d, ms, has_double_out, mask=mask, output_mask=has_mask_out)
            if not res:
                return
            verts_out.append(res[0])
            edges_out.append(res[1])
            polys_out.append(res[2])
            face_data_out.append(res[3])
            d_out.append(res[4])
            mask_out.append(res[5])

        self.outputs['Vertices'].sv_set(verts_out)

        # restrict setting this output when there is no such input
        if self.inputs['PolyEdge'].is_linked:
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Polygons'].sv_set(polys_out)

        self.outputs['FaceData'].sv_set(face_data_out)
        self.outputs['Doubles'].sv_set(d_out)

        self.outputs['Mask'].sv_set(mask_out)


def register():
    bpy.utils.register_class(SvRemoveDoublesNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvRemoveDoublesNodeMk2)
