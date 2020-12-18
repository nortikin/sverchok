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
from bpy.props import BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.data_structure import repeat_last
from sverchok.utils.mesh_functions import join_meshes, apply_matrix, meshes_py, to_elements, repeat_meshes, \
    apply_matrices, meshes_np


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

        object_number = max([len(vertices), len(matrices)]) if vertices else 0
        meshes = (meshes_py if self.implementation == 'Python' else meshes_np)(vertices, edges, faces)
        meshes = repeat_meshes(meshes, object_number)

        if matrices:
            is_flat_list = not isinstance(matrices[0], (list, tuple))
            meshes = (apply_matrix if is_flat_list else apply_matrices)(meshes, repeat_last(matrices))

        if self.do_join:
            meshes = join_meshes(meshes)

        out_vertices, out_edges, out_polygons = to_elements(meshes)
        self.outputs['Vertices'].sv_set(out_vertices)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_polygons)


def register():
    bpy.utils.register_class(SvMatrixApplyJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixApplyJoinNode)
