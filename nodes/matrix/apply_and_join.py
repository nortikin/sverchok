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
from sverchok.utils.mesh_functions import join_meshes, meshes_py, to_elements, meshes_np, \
    apply_matrix_to_vertices_py
from sverchok.utils.vectorize import vectorize
from sverchok.utils.modules.matrix_utils import matrix_apply_np


# todo move to another module?
SvVerts = List[Tuple[float, float, float]]
SvEdges = List[Tuple[int, int]]
SvPolys = List[List[int]]


def apply_matrices(
        *,
        vertices: SvVerts,
        edges: SvEdges,
        polygons: SvPolys,
        matrices: List[Matrix],
        implementation: str = 'Python') -> Tuple[SvVerts, SvEdges, SvPolys]:
    """several matrices can be applied to a mesh
    in this case each matrix will populate geometry inside object"""

    if not matrices:
        return vertices, edges, polygons

    if implementation == 'NumPy':
        vertices = np.asarray(vertices, dtype=np.float32)

    _apply_matrices = matrix_apply_np if implementation == 'NumPy' else apply_matrix_to_vertices_py

    sub_vertices = []
    sub_edges = [edges] * len(matrices) if edges else None
    sub_polygons = [polygons] * len(matrices) if polygons else None
    for matrix in matrices:
        sub_vertices.append(_apply_matrices(vertices, matrix))

    new_meshes = (meshes_py if implementation == 'Python' else meshes_np)(sub_vertices, sub_edges, sub_polygons)
    new_meshes = join_meshes(new_meshes)
    out_vertices, out_edges, out_polygons = to_elements(new_meshes)

    return out_vertices[0], out_edges[0], out_polygons[0]  # todo is using 0 index not ugly?


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

        # fixing matrices nesting level if necessary
        if matrices:
            is_flat_list = not isinstance(matrices[0], (list, tuple))
            if is_flat_list:
                matrices = [[m] for m in matrices]

        _apply_matrix = vectorize(apply_matrices, match_mode="REPEAT")
        out_vertices, out_edges, out_polygons = _apply_matrix(
            vertices=vertices, edges=edges, polygons=faces, matrices=matrices, implementation=self.implementation)

        # todo add separate implementations for applying single matrix?
        # todo join meshes

        self.outputs['Vertices'].sv_set(out_vertices)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_polygons)


def register():
    bpy.utils.register_class(SvMatrixApplyJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixApplyJoinNode)
