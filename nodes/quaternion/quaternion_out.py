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


modeItems = [
    ("WXYZ", "WXYZ", "Convert quaternion into components", 0),
    ("EULER", "Euler Angles", "Convert quaternion into Euler angles", 1),
    ("AXISANGLE", "Axis Angle", "Convert quaternion into Axis & Angle", 2),
    ("MATRIX", "Matrix", "Convert quaternion into Rotation Matrix", 3),
]

eulerOrderItems = [
    ('XYZ', "XYZ", "", 0),
    ('XZY', 'XZY', "", 1),
    ('YXZ', 'YXZ', "", 2),
    ('YZX', 'YZX', "", 3),
    ('ZXY', 'ZXY', "", 4),
    ('ZYX', 'ZYX', "", 5)
]

angleUnitItems = [
    ("RAD", "Rad", "Radians", "", 0),
    ("DEG", "Deg", 'Degrees', "", 1),
    ("UNI", "Uni", 'Unities', "", 2)
]

angleConversion = {"RAD": 1.0, "DEG": 180.0 / pi, "UNI": 0.5 / pi}

output_sockets = {
    "WXYZ": ["W", "X", "Y", "Z"],
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
    sv_icon = 'SV_COMBINE_OUT'

    def update_mode(self, context):

        # hide all output sockets
        for k, names in output_sockets.items():
            for name in names:
                self.outputs[name].hide_safe = True

        # show mode specific output sockets
        for name in output_sockets[self.mode]:
            self.outputs[name].hide_safe = False

        updateNode(self, context)

    mode = EnumProperty(
        name='Mode', description='Output mode (wxyz, Euler, Axis-Angle, Matrix)',
        items=modeItems, default="WXYZ", update=update_mode)

    eulerOrder = EnumProperty(
        name="Euler Order", description="Order of the Euler rotations",
        default="XYZ", items=eulerOrderItems, update=updateNode)

    quaternion = FloatVectorProperty(
        name="Quaternion", description="Quaternion to convert",
        size=4, subtype="QUATERNION", default=(0.0, 0.0, 0.0, 0.0),
        update=updateNode)

    angleUnits = EnumProperty(
        name="Angle Units", description="Angle units (radians/degrees/unities)",
        default="RAD", items=angleUnitItems, update=updateNode)

    normalize = BoolProperty(
        name='Normalize', description='Normalize the input quaternion',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvQuaternionSocket', "Quaternions").prop_name = "quaternion"
        # component outputs
        self.outputs.new('StringsSocket', "W")
        self.outputs.new('StringsSocket', "X")
        self.outputs.new('StringsSocket', "Y")
        self.outputs.new('StringsSocket', "Z")
        # euler angle ouputs
        self.outputs.new('StringsSocket', "Angle X")
        self.outputs.new('StringsSocket', "Angle Y")
        self.outputs.new('StringsSocket', "Angle Z")
        # axis-angle output
        self.outputs.new('VerticesSocket', "Axis")
        self.outputs.new('StringsSocket', "Angle")
        # matrix ouptut
        self.outputs.new('MatrixSocket', "Matrix")

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False, text="")
        if self.mode == "EULER":
            col = layout.column(align=True)
            col.prop(self, "eulerOrder", text="")
        if self.mode in {"EULER", "AXISANGLE"}:
            row = layout.row(align=True)
            row.prop(self, "angleUnits", expand=True)
        if self.mode == "WXYZ":
            layout.prop(self, "normalize", toggle=True)

    def process(self):
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        input_Q = self.inputs['Quaternions'].sv_get()[0]
        quaternionList = [Quaternion(q) for q in input_Q]

        if self.mode == "WXYZ":
            for i, name in enumerate("WXYZ"):
                if outputs[name].is_linked:
                    outputs[name].sv_set([[q[i] for q in quaternionList]])

        elif self.mode == "EULER":
            au = angleConversion[self.angleUnits]
            for i, name in enumerate("XYZ"):
                if outputs["Angle " + name].is_linked:
                    angles = [q.to_euler(self.eulerOrder)[i] * au for q in quaternionList]
                    outputs["Angle " + name].sv_set([angles])

        elif self.mode == "AXISANGLE":
            if outputs['Axis'].is_linked:
                axisList = [tuple(q.axis) for q in quaternionList]
                outputs['Axis'].sv_set([axisList])

            if outputs['Angle'].is_linked:
                au = angleConversion[self.angleUnits]
                angleList = [q.angle * au for q in quaternionList]
                outputs['Angle'].sv_set([angleList])

        elif self.mode == "MATRIX":
            if outputs['Matrix'].is_linked:
                matrixList = [q.to_matrix().to_4x4() for q in quaternionList]
                outputs['Matrix'].sv_set(matrixList)


def register():
    bpy.utils.register_class(SvQuaternionOutNode)


def unregister():
    bpy.utils.unregister_class(SvQuaternionOutNode)
