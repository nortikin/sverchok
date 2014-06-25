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
from mathutils import Matrix

from node_tree import SverchCustomTreeNode, VerticesSocket, MatrixSocket
from data_structure import (Vector_generate, Vector_degenerate,
                            Matrix_generate, updateNode,
                            SvGetSocketAnyType, SvSetSocketAnyType)


class MatrixApplyNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Multiply vectors on matrixes with several objects in output '''
    bl_idname = 'MatrixApplyNode'
    bl_label = 'Apply matrix for vectors'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vectors", "Vectors")
        self.inputs.new('MatrixSocket', "Matrixes", "Matrixes")
        self.outputs.new('VerticesSocket', "Vectors", "Vectors")

    def update(self):
        # inputs
        if 'Vectors' in self.outputs and self.outputs['Vectors'].links:
            if not ('Vectors' in self.inputs and self.inputs['Vectors'].links):
                return
            if not ('Matrixes' in self.inputs and self.inputs['Matrixes'].links):
                return
            if type(self.inputs['Vectors'].links[0].from_socket) == VerticesSocket and \
               type(self.inputs['Matrixes'].links[0].from_socket) == MatrixSocket:

                vecs_ = SvGetSocketAnyType(self, self.inputs['Vectors'])
                vecs = Vector_generate(vecs_)

                mats_ = SvGetSocketAnyType(self, self.inputs['Matrixes'])
                mats = Matrix_generate(mats_)
            else:
                vecs = [[]]
                mats = [Matrix()]

            # outputs
            vectors_ = self.vecscorrect(vecs, mats)
            vectors = Vector_degenerate(vectors_)
            SvSetSocketAnyType(self, 'Vectors', vectors)

    def vecscorrect(self, vecs, mats):
        out = []
        lengthve = len(vecs)-1
        for i, m in enumerate(mats):
            out_ = []
            k = i
            if k > lengthve:
                k = lengthve
            for v in vecs[k]:
                out_.append(m*v)
            out.append(out_)
        return out

    def update_socket(self, context):
        updateNode(self, context)


def register():
    bpy.utils.register_class(MatrixApplyNode)


def unregister():
    bpy.utils.unregister_class(MatrixApplyNode)
