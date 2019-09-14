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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Vector_generate, matrixdef, updateNode)


class MatrixDeformNode(bpy.types.Node, SverchCustomTreeNode):
    ''' MatrixDeform '''
    bl_idname = 'MatrixDeformNode'
    bl_label = 'Matrix Deform'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_DEFORM'

    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', "Original")
        self.inputs.new('SvVerticesSocket', "Location")
        self.inputs.new('SvVerticesSocket', "Scale")
        self.inputs.new('SvVerticesSocket', "Rotation")
        self.inputs.new('SvStringsSocket', "Angle")
        self.outputs.new('SvMatrixSocket', "Matrix")

    def process(self):
        O,L,S,R,A = self.inputs
        Om = self.outputs[0]
        if Om.is_linked:
            orig = O.sv_get()

            if L.is_linked:
                loc = Vector_generate(L.sv_get())
            else:
                loc = [[]]
            if S.is_linked:
                scale = Vector_generate(S.sv_get())
            else:
                scale = [[]]
            if R.is_linked:
                rot = Vector_generate(R.sv_get())
            else:
                rot = [[]]

            rotA, angle = [[]], [[0.0]]
            # ability to add vector & vector difference instead of only rotation values
            if A.is_linked:
                if A.links[0].from_socket.bl_idname == 'SvVerticesSocket':
                    rotA = Vector_generate(A.sv_get())
                    angle = [[]]
                else:
                    angle = A.sv_get()
                    rotA = [[]]
            matrixes_ = matrixdef(orig, loc, scale, rot, angle, rotA)
            Om.sv_set(matrixes_)


def register():
    bpy.utils.register_class(MatrixDeformNode)


def unregister():
    bpy.utils.unregister_class(MatrixDeformNode)
