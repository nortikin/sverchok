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

from sv_node_tree import SverchCustomTreeNode, StringsSocket
from sv_data_structure import (updateNode, fullList, Matrix_listing,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class MatrixShearNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Construct a Shear Matirx '''
    bl_idname = 'MatrixShearNode'
    bl_label = 'Shear Matrix'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # select Shear plane

    mode_items = [
        ("XY",       "XY-plane",        ""),
        ("XZ",       "XZ-plane",        ""),
        ("YZ",       "YZ-plane",        ""),
    ]
    factor1_ = FloatProperty(name='Factor 1', description='Factor1',
                             default=0.0,
                             options={'ANIMATABLE'}, update=updateNode)
    factor2_ = FloatProperty(name='Factor 2', description='Factor2',
                             default=0.0,
                             options={'ANIMATABLE'}, update=updateNode)

    plane_ = EnumProperty(name="Plane", description="Function choice",
                          default="XY", items=mode_items,
                          update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Factor1").prop_name = 'factor1_'
        self.inputs.new('StringsSocket', "Factor2").prop_name = 'factor2_'
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")

    def draw_buttons(self, context, layout):
        layout.prop(self, "plane_", "Shear plane:", expand=True)

    def update(self):
        # inputs
        factor1 = []
        factor2 = []
        if 'Factor1' in self.inputs and self.inputs['Factor1'].links and \
           type(self.inputs['Factor1'].links[0].from_socket) == StringsSocket:

            factor1 = SvGetSocketAnyType(self, self.inputs['Factor1'])
        if not factor1:
            factor1 = [[self.factor1_]]

        if 'Factor2' in self.inputs and self.inputs['Factor2'].links and \
           type(self.inputs['Factor2'].links[0].from_socket) == StringsSocket:

            factor2 = SvGetSocketAnyType(self, self.inputs['Factor2'])
        if not factor2:
            factor2 = [[self.factor2_]]

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
