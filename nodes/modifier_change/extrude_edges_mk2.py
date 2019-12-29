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

from mathutils import Matrix, Vector

import bpy
from bpy.props import IntProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList, Matrix_generate
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh, bmesh_edges_from_edge_mask

def is_matrix(lst):
    return len(lst) == 4 and len(lst[0]) == 4

class SvExtrudeEdgesNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Extrude edges
    Tooltip: Extrude some edges of the mesh
    '''
    bl_idname = 'SvExtrudeEdgesNodeMk2'
    bl_label = 'Extrude Edges Mk2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTRUDE_EDGES'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'EdgeMask')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.inputs.new('SvMatrixSocket', "Matrices")

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvVerticesSocket', 'NewVertices')
        self.outputs.new('SvStringsSocket', 'NewEdges')
        self.outputs.new('SvStringsSocket', 'NewFaces')
        self.outputs.new('SvStringsSocket', 'FaceData')

    def process(self):
        if not (self.inputs['Vertices'].is_linked):
            return

        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        matrices_s = self.inputs['Matrices'].sv_get(default=[[]])
        if is_matrix(matrices_s[0]):
            matrices_s = [Matrix_generate(matrices_s)]
        else:
            matrices_s = [Matrix_generate(matrices) for matrices in matrices_s]
        edge_masks_s = self.inputs['EdgeMask'].sv_get(default=[[]])
        face_data_s = self.inputs['FaceData'].sv_get(default=[[]])

        result_vertices = []
        result_edges = []
        result_faces = []
        result_face_data = []
        result_ext_vertices = []
        result_ext_edges = []
        result_ext_faces = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, edge_masks_s, face_data_s, matrices_s])

        for vertices, edges, faces, edge_mask, face_data, matrices in zip(*meshes):
            if not matrices:
                matrices = [Matrix()]
            if face_data:
                fullList(face_data, len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True, markup_edge_data=True)
            if edge_mask:
                b_edges = bmesh_edges_from_edge_mask(bm, edge_mask)
            else:
                b_edges = bm.edges

            new_geom = bmesh.ops.extrude_edge_only(bm, edges=b_edges, use_select_history=False)['geom']

            extruded_verts = [v for v in new_geom if isinstance(v, bmesh.types.BMVert)]

            for vertex, matrix in zip(*match_long_repeat([extruded_verts, matrices])):
                bmesh.ops.transform(bm, verts=[vertex], matrix=matrix, space=Matrix())

            extruded_verts = [tuple(v.co) for v in extruded_verts]

            extruded_edges = [e for e in new_geom if isinstance(e, bmesh.types.BMEdge)]
            extruded_edges = [tuple(v.index for v in edge.verts) for edge in extruded_edges]

            extruded_faces = [f for f in new_geom if isinstance(f, bmesh.types.BMFace)]
            extruded_faces = [[v.index for v in edge.verts] for edge in extruded_faces]

            if face_data:
                new_vertices, new_edges, new_faces, new_face_data = pydata_from_bmesh(bm, face_data)
            else:
                new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
                new_face_data = []
            bm.free()

            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_face_data.append(new_face_data)
            result_ext_vertices.append(extruded_verts)
            result_ext_edges.append(extruded_edges)
            result_ext_faces.append(extruded_faces)

            self.outputs['Vertices'].sv_set(result_vertices)
            self.outputs['Edges'].sv_set(result_edges)
            self.outputs['Faces'].sv_set(result_faces)
            self.outputs['FaceData'].sv_set(result_face_data)
            self.outputs['NewVertices'].sv_set(result_ext_vertices)
            self.outputs['NewEdges'].sv_set(result_ext_edges)
            self.outputs['NewFaces'].sv_set(result_ext_faces)


def register():
    bpy.utils.register_class(SvExtrudeEdgesNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvExtrudeEdgesNodeMk2)

