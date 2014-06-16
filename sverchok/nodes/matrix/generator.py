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

from node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from data_structure import (matrixdef, Matrix_listing,
                            Vector_generate,
                            SvGetSocketAnyType, SvSetSocketAnyType)


class MatrixGenNode(bpy.types.Node, SverchCustomTreeNode):
    ''' MatrixGenerator '''
    bl_idname = 'MatrixGenNode'
    bl_label = 'Matrix in'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('VerticesSocket', "Location", "Location")
        self.inputs.new('VerticesSocket', "Scale", "Scale")
        self.inputs.new('VerticesSocket', "Rotation", "Rotation")
        self.inputs.new('StringsSocket', "Angle", "Angle")
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")

    def update(self):
        # inputs
            if 'Location' in self.inputs and self.inputs['Location'].links and \
               type(self.inputs['Location'].links[0].from_socket) == VerticesSocket:

                loc_ = SvGetSocketAnyType(self, self.inputs['Location'])
                loc = Vector_generate(loc_)
            else:
                loc = [[]]

            if 'Scale' in self.inputs and self.inputs['Scale'].links and \
               type(self.inputs['Scale'].links[0].from_socket) == VerticesSocket:

                scale_ = SvGetSocketAnyType(self, self.inputs['Scale'])
                scale = Vector_generate(scale_)
            else:
                scale = [[]]

            if 'Rotation' in self.inputs and self.inputs['Rotation'].links and \
               type(self.inputs['Rotation'].links[0].from_socket) == VerticesSocket:

                rot_ = SvGetSocketAnyType(self, self.inputs['Rotation'])
                rot = Vector_generate(rot_)
                #print ('matrix_def', str(rot_))
            else:
                rot = [[]]

            rotA = [[]]
            angle = [[0.0]]
            if 'Angle' in self.inputs and self.inputs['Angle'].links:
                if type(self.inputs['Angle'].links[0].from_socket) == StringsSocket:
                    angle = SvGetSocketAnyType(self, self.inputs['Angle'])

                elif type(self.inputs['Angle'].links[0].from_socket) == VerticesSocket:
                    rotA_ = SvGetSocketAnyType(self, self.inputs['Angle'])
                    rotA = Vector_generate(rotA_)

            # outputs
            if 'Matrix' in self.outputs and self.outputs['Matrix'].links:

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
                #print ('matrix_def', str(matrixes))

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(MatrixGenNode)


def unregister():
    bpy.utils.unregister_class(MatrixGenNode)
