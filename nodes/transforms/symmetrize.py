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
from mathutils import Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


class SvSymmetrizeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Symmetrize mesh '''
    bl_idname = 'SvSymmetrizeNode'
    bl_label = 'Symmetrize Mesh'
    bl_icon = 'MOD_MIRROR'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Polygons')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.inputs.new('SvMatrixSocket', "Matrix")

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')
        self.outputs.new('SvStringsSocket', 'FaceData')

    directions = [
            ("-X+X", "-X to +X", "-X to +X", 0),
            ("+X-X", "+X to -X", "+X to -X", 1),
            ("-Y+Y", "-Y to +Y", "-Y to +Y", 2),
            ("+Y-Y", "+Y to -Y", "+Y to -Y", 3),
            ("-Z+Z", "-Z to +Z", "-Z to +Z", 4),
            ("+Z-Z", "+Z to -Z", "+Z to -Z", 5)
        ]

    direction : EnumProperty(
            name = "Direction",
            description = "Which sides to copy from and to",
            items = directions,
            default = "-X+X",
            update = updateNode)

    merge_dist : FloatProperty(
            name = "Merge Distance",
            description = "maximum distance for merging. does no merging if 0",
            default = 0.001, min = 0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "direction")
        layout.prop(self, "merge_dist")

    def get_symmetrize_direction(self):
        if self.direction in ("-X+X", "+X-X"):
            return 'X'
        if self.direction in ("-Y+Y", "+Y-Y"):
            return 'Y'
        if self.direction in ("-Z+Z", "+Z-Z"):
            return 'Z'

    def get_mirror_direction(self):
        if self.direction == '+X-X':
            return 'X'
        if self.direction == '+Y-Y':
            return 'Y'
        if self.direction == '+Z-Z':
            return 'Z'
        return None

    def mirror(self, verts, axis, matrix):
        def go_x(x, y, z):
            return -x, y, z
        def go_y(x, y, z):
            return x, -y, z
        def go_z(x, y, z):
            return x, y, -z

        def apply_matrix(verts, matrix):
            return [(matrix @ Vector(v))[:] for v in verts]

        has_matrix = matrix is not None and matrix != Matrix()
        if has_matrix:
            verts = apply_matrix(verts, matrix.inverted())

        if axis == 'X':
            verts = [go_x(*v) for v in verts]
        if axis == 'Y':
            verts = [go_y(*v) for v in verts]
        if axis == 'Z':
            verts = [go_z(*v) for v in verts]

        if has_matrix:
            verts = apply_matrix(verts, matrix)

        return verts

    def process(self):
        if not (self.inputs['Vertices'].is_linked):
            return
        if not (any(output.is_linked for output in self.outputs)):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])
        face_data_s = self.inputs['FaceData'].sv_get(default=[[]])
        matrixes_s = self.inputs['Matrix'].sv_get(default=[[Matrix()]])

        result_vertices = []
        result_edges = []
        result_faces = []
        result_face_data = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, face_data_s, matrixes_s])

        for vertices, edges, faces, face_data, matrixes in zip(*meshes):
            if face_data:
                fullList(face_data, len(faces))
            if isinstance(matrixes, list):
                matrix = matrixes[0]
            else:
                matrix = matrixes
            has_matrix = matrix is not None and matrix != Matrix()

            # TODO: this is actually a workaround for a known Blender bug
            # https://developer.blender.org/T59804
            mirror_axis = self.get_mirror_direction()
            if mirror_axis is not None:
                vertices = self.mirror(vertices, mirror_axis, matrix)
            bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True)

            if has_matrix:
                bmesh.ops.transform(bm, matrix = matrix.inverted(), verts = list(bm.verts))

            bmesh.ops.symmetrize(
                bm, input = list(bm.verts) + list(bm.edges) + list(bm.faces),
                direction = self.get_symmetrize_direction(),
                dist = self.merge_dist
            )

            if has_matrix:
                bmesh.ops.transform(bm, matrix = matrix, verts = list(bm.verts))

            if face_data:
                new_vertices, new_edges, new_faces, new_face_data = pydata_from_bmesh(bm, face_data)
            else:
                new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
                new_face_data = []
            if mirror_axis is not None:
                new_vertices = self.mirror(new_vertices, mirror_axis, matrix)
            bm.free()

            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_face_data.append(new_face_data)

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Polygons'].sv_set(result_faces)
        self.outputs['FaceData'].sv_set(result_face_data)


def register():
    bpy.utils.register_class(SvSymmetrizeNode)


def unregister():
    bpy.utils.unregister_class(SvSymmetrizeNode)

