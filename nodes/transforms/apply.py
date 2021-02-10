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
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.mesh_functions import meshes_np, meshes_py, apply_matrix, apply_matrices, to_elements, repeat_meshes


class MatrixApplyNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Multiply vectors on matrixes with several objects in output '''
    bl_idname = 'MatrixApplyNode'
    bl_label = 'Matrix Apply (verts)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_APPLY'

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vectors")
        self.inputs.new('SvMatrixSocket', "Matrixes")
        self.outputs.new('SvVerticesSocket', "Vectors")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, 'output_numpy')

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop(self, "output_numpy", expand=False)

    def process(self):
        if not self.inputs['Vectors'].is_linked:
            return

        vertices = self.inputs['Vectors'].sv_get(deepcopy=False)
        matrices = self.inputs['Matrixes'].sv_get(deepcopy=False, default=[])

        is_py_input = isinstance(vertices[0], (list, tuple))
        meshes = (meshes_py if is_py_input or not self.output_numpy else meshes_np)(vertices)
        object_number = max([len(vertices), len(matrices)]) if vertices else 0
        meshes = repeat_meshes(meshes, object_number)
        if matrices:
            is_flat = not isinstance(matrices[0], (list, tuple))
            meshes = (apply_matrix if is_flat else apply_matrices)(meshes, repeat_last(matrices))
        out_vertices, *_ = to_elements(meshes)

        self.outputs['Vectors'].sv_set(out_vertices)


register, unregister = bpy.utils.register_classes_factory([MatrixApplyNode])
