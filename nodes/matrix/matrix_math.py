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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from mathutils import Matrix
import re

from sverchok.node_tree import SverchCustomTreeNode, MatrixSocket, StringsSocket
from sverchok.data_structure import (updateNode, fullList, match_long_repeat,
                                     Matrix_listing, Matrix_generate)

operationItems = [
    ("MULTIPLY", "Multiply", "Multiply two matrices", 0),
    ("INVERT", "Invert", "Invert matrix", 1),
    ("FILTER", "Filter", "Filter matrix components", 2)
]

prePostItems = [
    ("PRE", "Pre", "Calculate A op B", 0),
    ("POST", "Post", "Calculate B op A", 1)
]


class SvMatrixMathNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Math operation on matrices '''
    bl_idname = 'SvMatrixMathNode'
    bl_label = 'Matrix Math'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def update_operation(self, context):
        self.label = "Matrix " + self.operation.title()
        self.update_sockets()
        updateNode(self, context)

    prePost = EnumProperty(
        name='Pre Post',
        description='Order of operations PRE = A op B vs POST = B op A)',
        items=prePostItems,
        default="PRE",
        update=updateNode)

    operation = EnumProperty(
        name="Operation",
        description="Operation to apply on the given matrices",
        items=operationItems,
        default="MULTIPLY",
        update=update_operation)

    filter_t = BoolProperty(
        name="Filter Translation",
        description="Filter out the translation component of the matrix",
        default=False,
        update=updateNode)

    filter_r = BoolProperty(
        name="Filter Rotation",
        description="Filter out the rotation component of the matrix",
        default=False,
        update=updateNode)

    filter_s = BoolProperty(
        name="Filter Scale",
        description="Filter out the scale component of the matrix",
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('MatrixSocket', "A", "A")
        self.inputs.new('MatrixSocket', "B", "B")

        self.outputs.new('MatrixSocket', "C", "C")

        self.operation = "MULTIPLY"

    def update_sockets(self):
        inputs = self.inputs

        if self.operation == "MULTIPLY":
            # two matrix inputs available
            if not "B" in inputs:
                inputs.new("MatrixSocket", "B")
        else:
            # one matrix input available
            if "B" in inputs:
                inputs.remove(inputs["B"])

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text = "")
        if self.operation == "MULTIPLY":
            layout.prop(self, "prePost", expand=True)
        elif self.operation == "FILTER":
            row = layout.row(align=True)
            row.prop(self, "filter_t", toggle=True, text="T")
            row.prop(self, "filter_r", toggle=True, text="R")
            row.prop(self, "filter_s", toggle=True, text="S")

    def operation_filter(self, a):
        T, R, S = a.decompose()

        if self.filter_t:
            mat_t = Matrix().Identity(4)
        else:
            mat_t = Matrix().Translation(T)

        if self.filter_r:
            mat_r = Matrix().Identity(4)
        else:
            mat_r = R.to_matrix().to_4x4()

        if self.filter_s:
            mat_s = Matrix().Identity(4)
        else:
            mat_s = Matrix().Identity(4)
            mat_s[0][0] = S[0]
            mat_s[1][1] = S[1]
            mat_s[2][2] = S[2]

        m = mat_t * mat_r * mat_s

        return m

    def get_operation(self):
        if self.operation == "MULTIPLY":
            return lambda a, b: a * b
        elif self.operation == "FILTER":
            return self.operation_filter
        elif self.operation == "INVERT":
            return lambda a: a.inverted()

    def process(self):
        outputs = self.outputs
        if not outputs['C'].is_linked:
            return

        inputs = self.inputs
        id_mat = Matrix_listing([Matrix.Identity(4)])
        A = Matrix_generate(inputs['A'].sv_get(default=id_mat))

        if self.operation in  { "MULTIPLY" }:
            # two matrix inputs available
            B = Matrix_generate(inputs['B'].sv_get(default=id_mat))

            if self.prePost == "PRE":
                parameters = match_long_repeat([A, B])
            else:
                parameters = match_long_repeat([B, A])
        else:
            # one matrix input available
            parameters = [A]

        operation = self.get_operation()

        matrixList = []
        for params in zip(*parameters):
            c = operation(*params)
            matrixList.append(c)

        matrices = Matrix_listing(matrixList)

        outputs['C'].sv_set(matrices)


def register():
    bpy.utils.register_class(SvMatrixMathNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixMathNode)
