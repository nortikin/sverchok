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

from copy import copy
from functools import reduce
from itertools import cycle

import bpy
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import sverchok.utils.meshes as me


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

        out_vertices = []
        if matrices:
            if isinstance(matrices[0][0][0], (int, float)):  # one level nesting
                for v, m in zip(cycle(vertices), matrices):
                    v = copy(v)
                    mesh = me.to_mesh(v) if not self.output_numpy else me.NpMesh(v)
                    mesh.apply_matrix(m)
                    out_vertices.append(mesh.vertices)

            else:  # otherwise it expects two levels nesting
                for v, ms in zip(cycle(vertices), matrices):
                    meshes = []
                    for m in ms:
                        v = copy(v)
                        mesh = me.to_mesh(v) if not self.output_numpy else me.NpMesh(v)
                        mesh.apply_matrix(m)
                        meshes.append(mesh)
                    mesh = reduce(lambda m1, m2: m1.add_mesh(m2), meshes)
                    out_vertices.append(mesh.vertices)

        self.outputs['Vectors'].sv_set(out_vertices or vertices)


def register():
    bpy.utils.register_class(MatrixApplyNode)


def unregister():
    bpy.utils.unregister_class(MatrixApplyNode)
