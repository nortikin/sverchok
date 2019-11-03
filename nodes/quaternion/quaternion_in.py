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
from bpy.props import EnumProperty, FloatProperty, BoolProperty, StringProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from mathutils import Quaternion, Matrix, Euler
from math import pi


modeItems = [
    ("WXYZ", "WXYZ", "Convert components into quaternion", 0),
    ("SCALARVECTOR", "Scalar Vector", "Convert Scalar & Vector into quaternion", 1),
    ("EULER", "Euler Angles", "Convert Euler angles into quaternion", 2),
    ("AXISANGLE", "Axis Angle", "Convert Axis & Angle into quaternion", 3),
    ("MATRIX", "Matrix", "Convert Rotation Matrix into quaternion", 4),
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

angleConversion = {"RAD": 1.0, "DEG": pi / 180.0, "UNI": 2 * pi}

idMat = [[tuple(v) for v in Matrix()]]  # identity matrix

input_sockets = {
    "WXYZ": ["W", "X", "Y", "Z"],
    "SCALARVECTOR": ["Scalar", "Vector"],
    "EULER": ["Angle X", "Angle Y", "Angle Z"],
    "AXISANGLE": ["Angle", "Axis"],
    "MATRIX": ["Matrix"]
}


class SvQuaternionInNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Quaternions, In
    Tooltip: Generate quaternions from various quaternion components
    """
    bl_idname = 'SvQuaternionInNode'
    bl_label = 'Quaternion In'
    sv_icon = 'SV_QUATERNION_IN'

    def update_mode(self, context):

        # hide all input sockets
        for k, names in input_sockets.items():
            for name in names:
                self.inputs[name].hide_safe = True

        # show mode specific input sockets
        for name in input_sockets[self.mode]:
            self.inputs[name].hide_safe = False

        updateNode(self, context)

    mode : EnumProperty(
        name='Mode', description='The input component format of the quaternion',
        items=modeItems, default="WXYZ", update=update_mode)

    eulerOrder : EnumProperty(
        name="Euler Order", description="Order of the Euler rotations",
        default="XYZ", items=eulerOrderItems, update=updateNode)

    angleUnits : EnumProperty(
        name="Angle Units", description="Angle units (radians/degrees/unities)",
        default="RAD", items=angleUnitItems, update=updateNode)

    component_w : FloatProperty(
        name='W', description='W component',
        default=0.0, precision=3, update=updateNode)

    component_x : FloatProperty(
        name='X', description='X component',
        default=0.0, precision=3,  update=updateNode)

    component_y : FloatProperty(
        name='Y', description='Y component',
        default=0.0, precision=3, update=updateNode)

    component_z : FloatProperty(
        name='Z', description='Z component',
        default=0.0, precision=3, update=updateNode)

    scalar : FloatProperty(
        name='Scalar', description='Scalar component of the quaternion',
        default=0.0, update=updateNode)

    vector : FloatVectorProperty(
        name='Vector', description='Vector component of the quaternion',
        size=3, default=(0.0, 0.0, 0.0), subtype="XYZ", update=updateNode)

    angle_x : FloatProperty(
        name='Angle X', description='Rotation angle about X axis',
        default=0.0, precision=3, update=updateNode)

    angle_y : FloatProperty(
        name='Angle Y', description='Rotation angle about Y axis',
        default=0.0, precision=3, update=updateNode)

    angle_z : FloatProperty(
        name='Angle Z', description='Rotation angle about Z axis',
        default=0.0, precision=3, update=updateNode)

    angle : FloatProperty(
        name='Angle', description='Rotation angle about the given axis',
        default=0.0, update=updateNode)

    axis : FloatVectorProperty(
        name='Axis', description='Axis of rotation',
        size=3, default=(1.0, 0.0, 0.0), subtype="XYZ", update=updateNode)

    normalize : BoolProperty(
        name='Normalize', description='Normalize the output quaternion',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "W").prop_name = 'component_w'
        self.inputs.new('SvStringsSocket', "X").prop_name = 'component_x'
        self.inputs.new('SvStringsSocket', "Y").prop_name = 'component_y'
        self.inputs.new('SvStringsSocket', "Z").prop_name = 'component_z'
        self.inputs.new('SvStringsSocket', "Scalar").prop_name = 'scalar'
        self.inputs.new('SvVerticesSocket', "Vector").prop_name = "vector"
        self.inputs.new('SvStringsSocket', "Angle X").prop_name = 'angle_x'
        self.inputs.new('SvStringsSocket', "Angle Y").prop_name = 'angle_y'
        self.inputs.new('SvStringsSocket', "Angle Z").prop_name = 'angle_z'
        self.inputs.new('SvVerticesSocket', "Axis").prop_name = "axis"
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'
        self.inputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvQuaternionSocket', "Quaternions")

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False, text="")
        if self.mode == "EULER":
            col = layout.column(align=True)
            col.prop(self, "eulerOrder", text="")
        if self.mode in {"EULER", "AXISANGLE"}:
            row = layout.row(align=True)
            row.prop(self, "angleUnits", expand=True)
        if self.mode in {"WXYZ", "SCALARVECTOR"}:
            layout.prop(self, "normalize", toggle=True)

    def process(self):
        if not self.outputs['Quaternions'].is_linked:
            return

        inputs = self.inputs

        quaternionList = []

        if self.mode == "WXYZ":
            I = [inputs[n].sv_get()[0] for n in "WXYZ"]
            params = match_long_repeat(I)
            for wxyz in zip(*params):
                q = Quaternion(wxyz)
                if self.normalize:
                    q.normalize()
                quaternionList.append(q)

        elif self.mode == "SCALARVECTOR":
            I = [inputs[n].sv_get()[0] for n in ["Scalar", "Vector"]]
            params = match_long_repeat(I)
            for scalar, vector in zip(*params):
                q = Quaternion([scalar, *vector])
                if self.normalize:
                    q.normalize()
                quaternionList.append(q)

        elif self.mode == "EULER":
            I = [inputs["Angle " + n].sv_get()[0] for n in "XYZ"]
            params = match_long_repeat(I)
            au = angleConversion[self.angleUnits]
            for angleX, angleY, angleZ in zip(*params):
                euler = Euler((angleX * au, angleY * au, angleZ * au), self.eulerOrder)
                q = euler.to_quaternion()
                if self.normalize:
                    q.normalize()
                quaternionList.append(q)

        elif self.mode == "AXISANGLE":
            I = [inputs[n].sv_get()[0] for n in ["Axis", "Angle"]]
            params = match_long_repeat(I)
            au = angleConversion[self.angleUnits]
            for axis, angle in zip(*params):
                q = Quaternion(axis, angle * au)
                if self.normalize:
                    q.normalize()
                quaternionList.append(q)

        elif self.mode == "MATRIX":
            input_M = inputs["Matrix"].sv_get(default=idMat)
            for m in input_M:
                q = Matrix(m).to_quaternion()
                if self.normalize:
                    q.normalize()
                quaternionList.append(q)

        self.outputs['Quaternions'].sv_set(quaternionList)


def register():
    bpy.utils.register_class(SvQuaternionInNode)


def unregister():
    bpy.utils.unregister_class(SvQuaternionInNode)
