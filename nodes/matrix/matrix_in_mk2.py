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
import mathutils
from bpy.props import FloatProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (matrixdef, Vector_generate, updateNode)


class SvMatrixGenNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' MatrixGeneratorMK2 '''
    bl_idname = 'SvMatrixGenNodeMK2'
    bl_label = 'Matrix in'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_IN'

    l_: FloatVectorProperty(
        name='L', default=(0.0,0.0,0.0), description='Location', precision=3, update=updateNode)
    s_: FloatVectorProperty(
        name='S', default=(1.0,1.0,1.0), description='Scale', precision=3, update=updateNode)
    r_: FloatVectorProperty(
        name='R', default=(0.0,0.0,1.0), description='Rotation', precision=3, update=updateNode)
    a_: FloatProperty(
        name='A', description='Angle', default=0.0, precision=3, update=updateNode)

    def sv_init(self, context):

        inew = self.inputs.new
        inew('SvVerticesSocket', "Location").prop_name = 'l_'
        inew('SvVerticesSocket', "Scale").prop_name = 's_'
        inew('SvVerticesSocket', "Rotation").prop_name = 'r_'
        inew('SvStringsSocket', "Angle").prop_name = 'a_'

        self.outputs.new('SvMatrixSocket', "Matrix")

    def process(self):
        L,S,R,A = self.inputs
        Ma = self.outputs[0]
        if not Ma.is_linked:
            return
        loc = Vector_generate(L.sv_get())
        scale = Vector_generate(S.sv_get())
        rot = Vector_generate(R.sv_get())
        rotA, angle = [[]], [[0.0]]

        # ability to add vector & vector difference instead of only rotation values
        if A.is_linked:
            if A.links[0].from_socket.bl_idname == 'SvVerticesSocket':
                rotA = Vector_generate(A.sv_get())
                angle = [[]]
            elif A.links[0].from_socket.bl_idname == 'SvStringsSocket':
                angle = A.sv_get()
                rotA = [[]]
        else:
            angle = A.sv_get()
            rotA = [[]]

        max_l = max(len(loc[0]), len(scale[0]), len(rot[0]), len(angle[0]), len(rotA[0]))
        orig = []
        for l in range(max_l):
            M = mathutils.Matrix()
            orig.append(M)
        matrixes_ = matrixdef(orig, loc, scale, rot, angle, rotA)
        Ma.sv_set(matrixes_)


def register():
    bpy.utils.register_class(SvMatrixGenNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvMatrixGenNodeMK2)
