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
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from mathutils import Quaternion
from math import pi


mode_items = [
    ("WXYZ", "WXYZ", "Convert quaternion into components", 0),
    ("SCALARVECTOR", "Scalar Vector", "Convert quaternion into Scalar & Vector", 1),
    ("EULER", "Euler Angles", "Convert quaternion into Euler angles", 2),
    ("AXISANGLE", "Axis Angle", "Convert quaternion into Axis & Angle", 3),
    ("MATRIX", "Matrix", "Convert quaternion into Rotation Matrix", 4),
]

euler_order_items = [
    ('XYZ', "XYZ", "", 0),
    ('XZY', 'XZY', "", 1),
    ('YXZ', 'YXZ', "", 2),
    ('YZX', 'YZX', "", 3),
    ('ZXY', 'ZXY', "", 4),
    ('ZYX', 'ZYX', "", 5)
]

angle_unit_items = [
    ("RAD", "Rad", "Radians", "", 0),
    ("DEG", "Deg", 'Degrees', "", 1),
    ("UNI", "Uni", 'Unities', "", 2)
]

angle_conversion = {"RAD": 1.0, "DEG": 180.0 / pi, "UNI": 0.5 / pi}

output_sockets = {
    "WXYZ": ["W", "X", "Y", "Z"],
    "SCALARVECTOR": ["Scalar", "Vector"],
    "EULER": ["Angle X", "Angle Y", "Angle Z"],
    "AXISANGLE": ["Angle", "Axis"],
    "MATRIX": ["Matrix"]
}


class SvQuaternionOutNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Quaternions, Out
    Tooltip: Convert quaternions into various quaternion components
    """
    bl_idname = 'SvQuaternionOutNode'
    bl_label = 'Quaternion Out'
    sv_icon = 'SV_QUATERNION_OUT'

    def update_mode(self, context):

        # hide all output sockets
        for k, names in output_sockets.items():
            for name in names:
                self.outputs[name].hide_safe = True

        # show mode specific output sockets
        for name in output_sockets[self.mode]:
            self.outputs[name].hide_safe = False

        updateNode(self, context)

    mode : EnumProperty(
        name='Mode', description='The output component format of the quaternion',
        items=mode_items, default="WXYZ", update=update_mode)

    euler_order : EnumProperty(
        name="Euler Order", description="Order of the Euler rotations",
        default="XYZ", items=euler_order_items, update=updateNode)

    quaternion : FloatVectorProperty(
        name="Quaternion", description="Quaternion to convert",
        size=4, subtype="QUATERNION", default=(0.0, 0.0, 0.0, 0.0),
        update=updateNode)

    angle_units : EnumProperty(
        name="Angle Units", description="Angle units (radians/degrees/unities)",
        default="RAD", items=angle_unit_items, update=updateNode)

    normalize : BoolProperty(
        name='Normalize', description='Normalize the input quaternion',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvQuaternionSocket', "Quaternions").prop_name = "quaternion"
        # component outputs
        self.outputs.new('SvStringsSocket', "W")
        self.outputs.new('SvStringsSocket', "X")
        self.outputs.new('SvStringsSocket', "Y")
        self.outputs.new('SvStringsSocket', "Z")
        # scalar-vector output
        self.outputs.new('SvStringsSocket', "Scalar")
        self.outputs.new('SvVerticesSocket', "Vector")
        # euler angle ouputs
        self.outputs.new('SvStringsSocket', "Angle X")
        self.outputs.new('SvStringsSocket', "Angle Y")
        self.outputs.new('SvStringsSocket', "Angle Z")
        # axis-angle output
        self.outputs.new('SvVerticesSocket', "Axis")
        self.outputs.new('SvStringsSocket', "Angle")
        # matrix ouptut
        self.outputs.new('SvMatrixSocket', "Matrix")

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False, text="")
        if self.mode == "EULER":
            col = layout.column(align=True)
            col.prop(self, "euler_order", text="")
        if self.mode in {"EULER", "AXISANGLE"}:
            row = layout.row(align=True)
            row.prop(self, "angle_units", expand=True)
        if self.mode in {"WXYZ", "SCALARVECTOR"}:
            layout.prop(self, "normalize", toggle=True)

    def process(self):
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        input_Q = self.inputs['Quaternions'].sv_get()
        quaternion_list = [Quaternion(q) for q in input_Q]

        if self.mode == "WXYZ":
            if self.normalize:
                quaternion_list = [q.normalized() for q in quaternion_list]

            for i, name in enumerate("WXYZ"):
                if outputs[name].is_linked:
                    outputs[name].sv_set([[q[i] for q in quaternion_list]])

        elif self.mode == "SCALARVECTOR":
            if self.normalize:
                quaternion_list = [q.normalized() for q in quaternion_list]

            if outputs['Scalar'].is_linked:
                scalar_list = [q[0] for q in quaternion_list]
                outputs['Scalar'].sv_set([scalar_list])

            if outputs['Vector'].is_linked:
                vector_list = [tuple(q[1:]) for q in quaternion_list]
                outputs['Vector'].sv_set([vector_list])

        elif self.mode == "EULER":
            au = angle_conversion[self.angle_units]
            for i, name in enumerate("XYZ"):
                if outputs["Angle " + name].is_linked:
                    angles = [q.to_euler(self.euler_order)[i] * au for q in quaternion_list]
                    outputs["Angle " + name].sv_set([angles])

        elif self.mode == "AXISANGLE":
            if outputs['Axis'].is_linked:
                axis_list = [tuple(q.axis) for q in quaternion_list]
                outputs['Axis'].sv_set([axis_list])

            if outputs['Angle'].is_linked:
                au = angle_conversion[self.angle_units]
                angle_list = [q.angle * au for q in quaternion_list]
                outputs['Angle'].sv_set([angle_list])

        elif self.mode == "MATRIX":
            if outputs['Matrix'].is_linked:
                matrix_list = [q.to_matrix().to_4x4() for q in quaternion_list]
                outputs['Matrix'].sv_set(matrix_list)


def register():
    bpy.utils.register_class(SvQuaternionOutNode)


def unregister():
    bpy.utils.unregister_class(SvQuaternionOutNode)
