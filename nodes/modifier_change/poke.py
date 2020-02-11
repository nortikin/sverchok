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

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvPokeFacesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Poke Faces (Alt-P)
    Tooltip: Poke selected faces
    """
    bl_idname = 'SvPokeFacesNode'
    bl_label = 'Poke Faces'
    bl_icon = 'MOD_BEVEL'

    modes = [
        ('MEAN_WEIGHTED', "Weighted Mean", "Using the mean average weighted by edge length", 0),
        ('MEAN', "Mean", "Using the mean average", 1),
        ('BOUNDS', "Bounds", "Uses center of bounding box", 2)
    ]

    mode : EnumProperty(
        name = "Poke Center",
        description = "Defines how to compute the center of a face",
        items = modes,
        default = 'MEAN_WEIGHTED',
        update = updateNode)

    offset_relative : BoolProperty(
        name = "Offset Relative",
        description = "Multiply the Offset by the average length from the center to the face vertices",
        default = False,
        update = updateNode)

    offset : FloatProperty(
        name = "Poke Offset",
        description = "Offset the new center vertex along the face normal",
        default = 0.0,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Offset').prop_name = 'offset'
        self.inputs.new('SvStringsSocket', 'FaceMask')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'FaceData')

    def draw_buttons(self, context, layout):
        layout.label(text="Poke Center:")
        layout.prop(self, "mode", text="")
        layout.prop(self, "offset_relative"),

    def process(self):
        if not any (socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        masks_s = self.inputs['FaceMask'].sv_get(default=[[1]])
        face_data_s = self.inputs['FaceData'].sv_get(default=[[]])
        offset_s = self.inputs['Offset'].sv_get()

        verts_out = []
        edges_out = []
        faces_out = []
        face_data_out = []

        meshes = zip_long_repeat(vertices_s, edges_s, faces_s, offset_s, masks_s, face_data_s)
        for vertices, edges, faces, offset, masks, face_data in meshes:
            if isinstance(offset, (list, tuple)):
                offset = offset[0]
            masks = repeat_last_for_length(masks, len(faces))
            if face_data:
                face_data = repeat_last_for_length(face_data, len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
            bm_faces = [face for mask, face in zip(masks, bm.faces[:]) if mask]

            bmesh.ops.poke(bm, faces=bm_faces, offset=offset,
                        center_mode = self.mode,
                        use_relative_offset = self.offset_relative)

            new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
            if not face_data:
                new_face_data = []
            else:
                new_face_data = face_data_from_bmesh_faces(bm, face_data)
            bm.free()

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)
            face_data_out.append(new_face_data)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['FaceData'].sv_set(face_data_out)

def register():
    bpy.utils.register_class(SvPokeFacesNode)

def unregister():
    bpy.utils.unregister_class(SvPokeFacesNode)

