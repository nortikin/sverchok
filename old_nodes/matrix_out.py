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
from sverchok.data_structure import (Matrix_generate, Matrix_location, Matrix_scale, Matrix_rotation)


class MatrixOutNode(SverchCustomTreeNode, bpy.types.Node):
    ''' Matrix Destructor '''
    bl_idname = 'MatrixOutNode'
    bl_label = 'Matrix out'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_OUT'

    replacement_nodes = [('SvMatrixOutNodeMK2', None, dict(Rotation="Axis"))]

    def rclick_menu(self, context, layout):
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        self.node_replacement_menu(context, layout)

    def sv_init(self, context):
        self.outputs.new('SvVerticesSocket', "Location")
        self.outputs.new('SvVerticesSocket', "Scale")
        self.outputs.new('SvVerticesSocket', "Rotation")
        self.outputs.new('SvStringsSocket', "Angle")
        self.inputs.new('SvMatrixSocket', "Matrix")

    def process(self):
        L,S,R,A = self.outputs
        M = self.inputs[0]
        if M.is_linked:
            matrixes = M.sv_get()
            if L.is_linked:
                locs = Matrix_location(matrixes, to_list=True)
                L.sv_set(locs)
            if S.is_linked:
                locs = Matrix_scale(matrixes, to_list=True)
                S.sv_set(locs)
            if R.is_linked or A.is_linked:
                locs = Matrix_rotation(matrixes, to_list=True)
                rots, angles = [],[]
                for lists in locs:
                    rots.append([pair[0] for pair in lists])
                    for pair in lists:
                        angles.append(degrees(pair[1]))
                R.sv_set(rots)
                A.sv_set([angles])


def register():
    bpy.utils.register_class(MatrixOutNode)


def unregister():
    bpy.utils.unregister_class(MatrixOutNode)
