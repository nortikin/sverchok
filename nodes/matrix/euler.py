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

from math import radians

import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty

from mathutils import Matrix, Euler

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat)

def matrix_euler(param, order):
    mats = []
    for angles in zip(*match_long_repeat(param)):
        a_r = [radians(x) for x in angles]
        mat = Euler(a_r, order).to_matrix().to_4x4()
        mats.append(mat)
    return mats


class SvMatrixEulerNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: from axis rotation
    Tooltip:  Construct a Matirx from Euler rotations

    """
    bl_idname = 'SvMatrixEulerNode'
    bl_label = 'Matrix Euler'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_EULER'

    X: FloatProperty(name='X', description='X rotation', default=0.0, update=updateNode)
    Y: FloatProperty(name='Y', description='Y rotation', default=0.0, update=updateNode)
    Z: FloatProperty(name='Z', description='Z rotation', default=0.0, update=updateNode)

    def change_prop(self, context):
        for i, name in enumerate(self.order):
            self.inputs[i].prop_name = name
        updateNode(self, context)

    orders = [
        ('XYZ', "XYZ",        "", 0),
        ('XZY', 'XZY',        "", 1),
        ('YXZ', 'YXZ',        "", 2),
        ('YZX', 'YZX',        "", 3),
        ('ZXY', 'ZXY',        "", 4),
        ('ZYX', 'ZYX',        "", 5),
    ]
    order: EnumProperty(
        name="Order", description="Order",
        default="XYZ", items=orders, update=change_prop)
    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "pos0").prop_name = 'X'
        self.inputs.new('SvStringsSocket', "pos1").prop_name = 'Y'
        self.inputs.new('SvStringsSocket', "pos1").prop_name = 'Z'
        self.outputs.new('SvMatrixSocket', "Matrix")

    def draw_buttons(self, context, layout):
        layout.prop(self, "order", text="Order:")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "order", text="Order:")
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "order", text="Order:")
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

    def process(self):
        if not self.outputs['Matrix'].is_linked:
            return
        inputs = self.inputs
        params = [s.sv_get() for s in inputs]
        mats = []
        m_add = mats.extend if  self.flat_output else mats.append
        params = match_long_repeat(params)
        for par in zip(*params):
            matrixes = matrix_euler(par, self.order)
            m_add(matrixes)
        self.outputs['Matrix'].sv_set(mats)


def register():
    bpy.utils.register_class(SvMatrixEulerNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixEulerNode)
