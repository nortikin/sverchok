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

from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from sverchok.data_structure import (matrixdef, Matrix_listing,
                            Vector_generate,
                            SvGetSocketAnyType, SvSetSocketAnyType)


class MatrixGenNode(bpy.types.Node, SverchCustomTreeNode):
    ''' MatrixGenerator '''
    bl_idname = 'MatrixGenNode'
    bl_label = 'Matrix in'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        s = self.inputs.new('VerticesSocket', "Location", "Location")
        s.use_prop = True
        s = self.inputs.new('VerticesSocket', "Scale", "Scale")
        s.use_prop = True
        s.prop = (1, 1 , 1)
        s = self.inputs.new('VerticesSocket', "Rotation", "Rotation")
        s.use_prop = True
        s.prop = (0, 0, 1)
        self.inputs.new('StringsSocket', "Angle", "Angle")
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")

    def process(self):
        # inputs
        
        if not self.outputs['Matrix'].is_linked:
            return
    
        loc_ = self.inputs['Location'].sv_get()
        loc = Vector_generate(loc_)

        scale_ = self.inputs['Scale'].sv_get()
        scale = Vector_generate(scale_)


        rot_ = self.inputs['Rotation'].sv_get()
        rot = Vector_generate(rot_)

        rotA = [[]]
        angle = [[0.0]]
        if self.inputs['Angle'].is_linked:
            if type(self.inputs['Angle'].links[0].from_socket) == StringsSocket:
                angle = SvGetSocketAnyType(self, self.inputs['Angle'])

            elif type(self.inputs['Angle'].links[0].from_socket) == VerticesSocket:
                rotA_ = SvGetSocketAnyType(self, self.inputs['Angle'])
                rotA = Vector_generate(rotA_)

        max_l = max(len(loc[0]), len(scale[0]), len(rot[0]), len(angle[0]), len(rotA[0]))
        orig = []
        for l in range(max_l):
            M = mathutils.Matrix()
            orig.append(M)
        if len(orig) == 0:
            return
        matrixes_ = matrixdef(orig, loc, scale, rot, angle, rotA)
        matrixes = Matrix_listing(matrixes_)
        SvSetSocketAnyType(self, 'Matrix', matrixes)



def register():
    bpy.utils.register_class(MatrixGenNode)


def unregister():
    bpy.utils.unregister_class(MatrixGenNode)
