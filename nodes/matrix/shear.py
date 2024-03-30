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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList


class MatrixShearNode(SverchCustomTreeNode, bpy.types.Node):
    '''Construct a Shear Matrix. Change the locations of vertices in two directions.
    In: Factor 1, Factor 2
    Params: XY-plane / XZ-plane / YZ-plane
    Out: Matrix
    '''
    bl_idname = 'MatrixShearNode'
    bl_label = 'Matrix Shear'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_SHEAR'

    # select Shear plane

    mode_items = [
        ("XY",       "XY-plane",        ""),
        ("XZ",       "XZ-plane",        ""),
        ("YZ",       "YZ-plane",        ""),
    ]
    factor1_: FloatProperty(name='Factor 1', description='Factor1', default=0.0, update=updateNode)
    factor2_: FloatProperty(name='Factor 2', description='Factor2', default=0.0, update=updateNode)

    plane_: EnumProperty(
        name="Plane", description="Function choice", default="XY", items=mode_items, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Factor1").prop_name = 'factor1_'
        self.inputs.new('SvStringsSocket', "Factor2").prop_name = 'factor2_'
        self.outputs.new('SvMatrixSocket', "Matrix")

    def draw_buttons(self, context, layout):
        layout.prop(self, "plane_", text="Shear plane:", expand=True)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        # inputs

        factor1 = self.inputs['Factor1'].sv_get()
        factor2 = self.inputs['Factor2'].sv_get()

        # outputs

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

        self.outputs['Matrix'].sv_set(matrixes_)


def register():
    bpy.utils.register_class(MatrixShearNode)


def unregister():
    bpy.utils.unregister_class(MatrixShearNode)
