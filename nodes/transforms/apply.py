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
from mathutils import Matrix, Vector
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Vector_generate, Vector_degenerate,
                                     Matrix_generate, updateNode)
from sverchok.utils.modules.matrix_utils import matrix_apply_np

import numpy as np

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
        if not self.outputs['Vectors'].is_linked:
            return

        vecs_ = self.inputs['Vectors'].sv_get(deepcopy=False)
        mats = self.inputs['Matrixes'].sv_get(deepcopy=False)

        out = []
        s_len = max(map(len, [vecs_, mats]))
        vecs = [np.array(vs) for vs in vecs_]
        v_l = len(vecs_) - 1
        m_l = len(mats) - 1
        func = matrix_apply_np
        if self.output_numpy:
            out = [func(vecs[min(i, v_l)], mats[min(i, m_l)]) for i in range(s_len)]
        else:
            out = [func(vecs[min(i, v_l)], mats[min(i, m_l)]).tolist() for i in range(s_len)]

        self.outputs['Vectors'].sv_set(out)


def register():
    bpy.utils.register_class(MatrixApplyNode)


def unregister():
    bpy.utils.unregister_class(MatrixApplyNode)
