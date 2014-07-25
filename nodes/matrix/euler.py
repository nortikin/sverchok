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
from bpy.props import EnumProperty, FloatProperty
from mathutils import Matrix

from node_tree import SverchCustomTreeNode, StringsSocket
from data_structure import (updateNode, fullList, Matrix_listing,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class MatrixEulerNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Construct a Matirx from Euler '''
    bl_idname = 'MatrixEulerNode'
    bl_label = 'Euler Matrix'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # select Shear plane

    x = FloatProperty(name='X', description='X rotation',
                             default=0.0,
                             options={'ANIMATABLE'}, update=updateNode)
    y = FloatProperty(name='Y', description='Y rotation',
                             default=0.0,
                             options={'ANIMATABLE'}, update=updateNode)
    z = FloatProperty(name='Z', description='Z rotation',
                             default=0.0,
                             options={'ANIMATABLE'}, update=updateNode)
    
    orders = [
        ('XYZ', "",        "", 0),
        ('XZY', "",        "", 1),
        ('YXZ', "",        "", 2),
        ('YZX', "",        "", 3),
        ('ZXY', "",        "", 4),
        ('ZYX', "",        "", 5),
    ]
    order = EnumProperty(name="Order", description="Order",
                          default="XYZ", items=orders,
                          update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "pos0").prop_name = 'x'
        self.inputs.new('StringsSocket', "pos1").prop_name = 'y'
        self.inputs.new('StringsSocket', "pos1").prop_name = 'z'
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")

    def draw_buttons(self, context, layout):
        layout.prop(self, "plane_", "Shear plane:", expand=True)

    def update(self):
        inputs = self.inputs 
        param = [s.sv_get()[0] for s in inputs]
        match_long_repeat 
        # outputs
        if 'Matrix' in self.outputs and self.outputs['Matrix'].links:

            max_l = max(len(factor1), len(factor2))
            fullList(factor1, max_l)
            fullList(factor2, max_l)
            matrixes_ = []
            for i in range(max_l):
                max_inner = max(len(factor1[i]), len(factor2[i]))
                fullList(factor1[i], max_inner)
                fullList(factor2[i], max_inner)
                for j in range(max_inner):
                    matrixes_.append(Matrix.Shear(self.plane_, 4, (factor1[i][j], factor2[i][j])))

            matrixes = Matrix_listing(matrixes_)
            SvSetSocketAnyType(self, 'Matrix', matrixes)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(MatrixShearNode)


def unregister():
    bpy.utils.unregister_class(MatrixShearNode)
