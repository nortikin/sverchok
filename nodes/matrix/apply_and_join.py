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

from functools import reduce

import bpy
from bpy.props import BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.data_structure import repeat_last
import sverchok.utils.meshes as me


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
        meshes = []
        for i, *elements, matrix in zip(
                range(object_number),
                repeat_last(vertices),
                repeat_last(edges or [[]]),
                repeat_last(faces or [[]]),
                repeat_last(matrices or [[]])):

            if matrix:
                if not isinstance(matrix, (list, tuple)):
                    # most likely it is Matrix or np.ndarray
                    # but the node expects list of list of matrices as input
                    matrix = [matrix]

                sub_meshes = []
                for mat in matrix:
                    mesh = me.to_mesh(*elements) if self.implementation != 'NumPy' else me.NpMesh(*elements)
                    mesh.apply_matrix(mat)
                    sub_meshes.append(mesh)

                sub_mesh = reduce(lambda m1, m2: m1.add_mesh(m2), sub_meshes)
            else:
                sub_mesh = me.to_mesh(*elements) if self.implementation != 'NumPy' else me.NpMesh(*elements)
            meshes.append(sub_mesh)

        if self.do_join and meshes:
            meshes = [reduce(lambda m1, m2: m1.add_mesh(m2), meshes)]

        self.outputs['Vertices'].sv_set([m.vertices.data for m in meshes])
        self.outputs['Edges'].sv_set([m.edges.data for m in meshes])
        self.outputs['Faces'].sv_set([m.polygons.data for m in meshes])


def register():
    bpy.utils.register_class(SvMatrixApplyJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixApplyJoinNode)
