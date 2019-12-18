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

from math import radians

import bpy
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh, face_data_from_bmesh_faces

def get_bm_geom(geom):
    bm_edges = geom['edges']
    edges = [(edge.verts[0].index, edge.verts[1].index) for edge in bm_edges]
    bm_faces = geom['faces']
    faces = [[vert.index for vert in face.verts] for face in bm_faces]
    return edges, faces

class SvSplitFacesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: split nonplanar concave faces
    Tooltip: Split non-planar / concave faces
    """
    bl_idname = 'SvSplitFacesNode'
    bl_label = 'Split Faces'
    bl_icon = 'MOD_BEVEL'

    modes = [
            ('NONPLANAR', "Non-planar", "Split faces by connecting edges along non planer faces", 0),
            ('CONCAVE', "Concave", "Ensures all faces are convex faces", 1)
        ]

    def mode_change(self, context):
        self.inputs['MaxAngle'].hide_safe = self.split_mode != 'NONPLANAR'
        updateNode(self, context)

    split_mode : EnumProperty(
        name = "Mode",
        description = "Which faces to split",
        items = modes,
        default = 'NONPLANAR',
        update = mode_change)

    max_angle : FloatProperty(
        name = "Max. angle",
        description = "total rotation angle (degrees)",
        default = 5,
        min = 0, max = 180,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'FaceMask')
        self.inputs.new('SvStringsSocket', 'MaxAngle').prop_name = 'max_angle'
        self.inputs.new('SvStringsSocket', 'FaceData')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'FaceData')

        self.mode_change(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "split_mode")

    def process(self):
        if not any (socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        masks_s = self.inputs['FaceMask'].sv_get(default=[[1]])
        max_angle_s = self.inputs['MaxAngle'].sv_get()
        face_data_s = self.inputs['FaceData'].sv_get(default=[[]])

        verts_out = []
        edges_out = []
        faces_out = []
        face_data_out = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, max_angle_s, face_data_s])
        for vertices, edges, faces, masks, max_angle, face_data in zip(*meshes):
            if self.split_mode == 'NONPLANAR':
                if isinstance(max_angle, (list, tuple)):
                    max_angle = max_angle[0]

            fullList(masks, len(faces))
            if face_data:
                fullList(face_data, len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True, markup_face_data=True)
            bm_faces = [face for mask, face in zip(masks, bm.faces[:]) if mask]

            if self.split_mode == 'NONPLANAR':
                new_geom = bmesh.ops.connect_verts_nonplanar(bm,
                        angle_limit = radians(max_angle),
                        faces = bm_faces)
            else:
                new_geom = bmesh.ops.connect_verts_concave(bm,
                        faces = bm_faces)

            new_verts, _, _ = pydata_from_bmesh(bm)
            new_edges, new_faces = get_bm_geom(new_geom)
            if not face_data:
                new_face_data = []
            else:
                new_face_data = face_data_from_bmesh_faces(bm, face_data)

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)
            face_data_out.append(new_face_data)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['FaceData'].sv_set(face_data_out)

def register():
    bpy.utils.register_class(SvSplitFacesNode)


def unregister():
    bpy.utils.unregister_class(SvSplitFacesNode)

