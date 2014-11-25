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

from math import degrees

import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Matrix_generate,
                            Matrix_location, Matrix_scale, Matrix_rotation,
                            SvGetSocketAnyType, SvSetSocketAnyType)


class MatrixOutNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Matrix Destructor '''
    bl_idname = 'MatrixOutNode'
    bl_label = 'Matrix out'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.outputs.new('VerticesSocket', "Location", "Location")
        self.outputs.new('VerticesSocket', "Scale", "Scale")
        self.outputs.new('VerticesSocket', "Rotation", "Rotation")
        self.outputs.new('StringsSocket', "Angle", "Angle")
        self.inputs.new('MatrixSocket', "Matrix", "Matrix")

    def process(self):
        if 'Matrix' in self.inputs and self.inputs['Matrix'].is_linked:
            matrixes_ = SvGetSocketAnyType(self, self.inputs['Matrix'])
            matrixes = Matrix_generate(matrixes_)

            if 'Location' in self.outputs and self.outputs['Location'].is_linked:
                locs = Matrix_location(matrixes, list=True)
                SvSetSocketAnyType(self, 'Location', locs)

            if 'Scale' in self.outputs and self.outputs['Scale'].is_linked:
                locs = Matrix_scale(matrixes, list=True)
                SvSetSocketAnyType(self, 'Scale', locs)

            if ('Rotation' in self.outputs and self.outputs['Rotation'].is_linked) \
               or ('Angle' in self.outputs and self.outputs['Angle'].is_linked):

                locs = Matrix_rotation(matrixes, list=True)
                rots = []
                angles = []
                for lists in locs:
                    rots.append([pair[0] for pair in lists])
                    for pair in lists:
                        angles.append(degrees(pair[1]))
                SvSetSocketAnyType(self, 'Rotation', rots)
                SvSetSocketAnyType(self, 'Angle', [angles])
        else:
            matrixes = [[]]

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(MatrixOutNode)


def unregister():
    bpy.utils.unregister_class(MatrixOutNode)
