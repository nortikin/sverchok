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

from typing import List, Tuple

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.mesh_functions import apply_matrix_to_vertices_py
from sverchok.utils.vectorize import vectorize, devectorize, SvVerts, SvEdges, SvPolys
from sverchok.utils.modules.matrix_utils import matrix_apply_np


def apply_matrices(
        *,
        vertices: SvVerts,
        edges: SvEdges,
        polygons: SvPolys,
        matrices: List[Matrix],
        implementation: str = 'Python') -> Tuple[SvVerts, SvEdges, SvPolys]:
    """several matrices can be applied to a mesh
    in this case each matrix will populate geometry inside object"""

    if not matrices or (vertices is None or not len(vertices)):
        return vertices, edges, polygons

    if implementation == 'NumPy':
        vertices = np.asarray(vertices, dtype=np.float32)

    _apply_matrices = matrix_apply_np if isinstance(vertices, np.ndarray) else apply_matrix_to_vertices_py

    sub_vertices = []
    sub_edges = [edges] * len(matrices) if edges else None
    sub_polygons = [polygons] * len(matrices) if polygons else None
    for matrix in matrices:
        sub_vertices.append(_apply_matrices(vertices, matrix))

    out_vertices, out_edges, out_polygons = join_meshes(vertices=sub_vertices, edges=sub_edges, polygons=sub_polygons)
    return out_vertices, out_edges, out_polygons


def apply_matrix(
        *,
        vertices: SvVerts,
        edges: SvEdges,
        polygons: SvPolys,
        matrix: Matrix,
        implementation: str = 'Python') -> Tuple[SvVerts, SvEdges, SvPolys]:
    """several matrices can be applied to a mesh
    in this case each matrix will populate geometry inside object"""

    if not matrix or (vertices is None or not len(vertices)):
        return vertices, edges, polygons

    if implementation == 'NumPy':
        vertices = np.asarray(vertices, dtype=np.float32)

    _apply_matrices = matrix_apply_np if isinstance(vertices, np.ndarray) else apply_matrix_to_vertices_py

    new_vertices = _apply_matrices(vertices, matrix)

    return new_vertices, edges, polygons


def join_meshes(*, vertices: List[SvVerts], edges: List[SvEdges], polygons: List[SvPolys]):
    joined_vertices = []
    joined_edges = []
    joined_polygons = []

    if not vertices:
        return joined_vertices, joined_edges, joined_polygons
    else:
        if isinstance(vertices[0], np.ndarray):
            joined_vertices = np.concatenate(vertices)
        else:
            joined_vertices = [v for vs in vertices for v in vs]

    if edges:
        vertexes_number = 0
        for i, es in enumerate(edges):
            if es:
                if isinstance(es, np.ndarray):
                    joined_edges.extend((es + vertexes_number).tolist())
                else:
                    joined_edges.extend([(e[0] + vertexes_number, e[1] + vertexes_number) for e in es])
                vertexes_number += len(vertices[i])

    if polygons:
        vertexes_number = 0
        for i, ps in enumerate(polygons):
            if ps:
                if isinstance(ps, np.ndarray):
                    joined_polygons.extend((ps + vertexes_number).tolist())
                else:
                    joined_polygons.extend([[i + vertexes_number for i in p] for p in ps])
                vertexes_number += len(vertices[i])

    return joined_vertices, joined_edges, joined_polygons


class SvMatrixApplyJoinNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: matrix mesh join
    Tooltip: Multiply vectors on matrices with several objects in output, processes edges & faces too.
    It can also join the output meshes in to a single one
    """

    bl_idname = 'SvMatrixApplyJoinNode'
    bl_label = 'Matrix Apply'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_APPLY_JOIN'

    do_join: BoolProperty(name='Join', default=True, update=updateNode)

    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("Python", "Python", "Python", 1)]

    implementation: EnumProperty(
        name='Implementation', items=implementation_modes,
        description='Choose calculation method (See Documentation)',
        default="Python", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvMatrixSocket', "Matrices")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def draw_buttons(self, context, layout):
        layout.prop(self, "do_join")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "do_join")

        layout.label(text="Implementation:")
        layout.prop(self, "implementation", expand=True)

    def rclick_menu(self, context, layout):
        layout.prop(self, "do_join")
        layout.prop_menu_enum(self, "implementation", text="Implementation")

    def process(self):
        vertices = self.inputs['Vertices'].sv_get(default=[], deepcopy=False)
        edges = self.inputs['Edges'].sv_get(default=[], deepcopy=False)
        faces = self.inputs['Faces'].sv_get(default=[], deepcopy=False)
        matrices = self.inputs['Matrices'].sv_get(default=[], deepcopy=False)

        # fixing matrices nesting level if necessary, this is for back capability, can be removed later on
        if matrices:
            is_flat_list = not isinstance(matrices[0], (list, tuple))
            if is_flat_list:
                _apply_matrix = vectorize(apply_matrix, match_mode='REPEAT')
                out_vertices, out_edges, out_polygons = _apply_matrix(
                    vertices=vertices, edges=edges, polygons=faces, matrix=matrices, implementation=self.implementation)
            else:
                _apply_matrix = vectorize(apply_matrices, match_mode="REPEAT")
                out_vertices, out_edges, out_polygons = _apply_matrix(
                    vertices=vertices or None, edges=edges or None, polygons=faces or None, matrices=matrices or None,
                    implementation=self.implementation)
        else:
            out_vertices, out_edges, out_polygons = vertices, edges, faces

        if self.do_join:
            _join_mesh = devectorize(join_meshes, match_mode="REPEAT")
            out_vertices, out_edges, out_polygons = _join_mesh(
                vertices=out_vertices, edges=out_edges, polygons=out_polygons)
            out_vertices, out_edges, out_polygons = (
                [out_vertices] if out_vertices is not None and len(out_vertices) else out_vertices,
                [out_edges] if out_edges is not None and len(out_edges) else out_edges,
                [out_polygons] if out_polygons is not None and len(out_polygons) else out_polygons)

        self.outputs['Vertices'].sv_set(out_vertices)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_polygons)


def register():
    bpy.utils.register_class(SvMatrixApplyJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixApplyJoinNode)
