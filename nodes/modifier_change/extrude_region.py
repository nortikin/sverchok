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
#from math import copysign

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList, Matrix_generate
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

def is_matrix(lst):
    return len(lst) == 4 and len(lst[0]) == 4

class SvExtrudeRegionNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Extrude region of faces '''
    bl_idname = 'SvExtrudeRegionNode'
    bl_label = 'Extrude Region'
    bl_icon = 'OUTLINER_OB_EMPTY'

    keep_original = BoolProperty(name="Keep original",
        description="Keep original geometry",
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', 'Edges', 'Edges')
        self.inputs.new('StringsSocket', 'Polygons', 'Polygons')
        self.inputs.new('StringsSocket', 'Mask')
        self.inputs.new('MatrixSocket', 'Matrices')

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polygons')
        self.outputs.new('VerticesSocket', 'NewVertices')
        self.outputs.new('StringsSocket', 'NewEdges')
        self.outputs.new('StringsSocket', 'NewFaces')

    def draw_buttons(self, context, layout):
        layout.prop(self, "keep_original")
  
    def process(self):
        # inputs
        if not (self.inputs['Vertices'].is_linked and self.inputs['Polygons'].is_linked):
            return
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])
        masks_s = self.inputs['Mask'].sv_get(default=[[1]])
        matrices_s = self.inputs['Matrices'].sv_get(default=[[]])
        if is_matrix(matrices_s[0]):
            matrices_s = [Matrix_generate(matrices_s)]
        else:
            matrices_s = [Matrix_generate(matrices) for matrices in matrices_s]

        result_vertices = []
        result_edges = []
        result_faces = []
        result_ext_vertices = []
        result_ext_edges = []
        result_ext_faces = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, matrices_s])

        for vertices, edges, faces, masks, matrices in zip(*meshes):
            if not matrices:
                matrices = [Matrix()]
            fullList(masks,  len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces)

            b_faces = []
            b_edges = set()
            b_verts = set()
            for mask, face in zip(masks, bm.faces):
                if mask:
                    b_faces.append(face)
                    for edge in face.edges:
                        b_edges.add(edge)
                    for vert in face.verts:
                        b_verts.add(vert)

            new_geom = bmesh.ops.extrude_face_region(bm,
                            geom=b_faces+list(b_edges)+list(b_verts),
                            edges_exclude=set(),
                            use_keep_orig=self.keep_original)['geom']

            extruded_verts = [v for v in new_geom if isinstance(v, bmesh.types.BMVert)]

            for vertex, matrix in zip(*match_long_repeat([extruded_verts, matrices])):
                bmesh.ops.transform(bm, verts=[vertex], matrix=matrix, space=Matrix())

            extruded_verts = [tuple(v.co) for v in extruded_verts]

            extruded_edges = [e for e in new_geom if isinstance(e, bmesh.types.BMEdge)]
            extruded_edges = [tuple(v.index for v in edge.verts) for edge in extruded_edges]

            extruded_faces = [f for f in new_geom if isinstance(f, bmesh.types.BMFace)]
            extruded_faces = [[v.index for v in edge.verts] for edge in extruded_faces]

            new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()

            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_ext_vertices.append(extruded_verts)
            result_ext_edges.append(extruded_edges)
            result_ext_faces.append(extruded_faces)

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Polygons'].sv_set(result_faces)
        self.outputs['NewVertices'].sv_set(result_ext_vertices)
        self.outputs['NewEdges'].sv_set(result_ext_edges)
        self.outputs['NewFaces'].sv_set(result_ext_faces)

def register():
    bpy.utils.register_class(SvExtrudeRegionNode)


def unregister():
    bpy.utils.unregister_class(SvExtrudeRegionNode)

if __name__ == '__main__':
    register()

