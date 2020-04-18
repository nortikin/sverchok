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
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper
from mathutils import Quaternion, Matrix, Euler
from math import pi


mode_items = [
    ("WXYZ", "WXYZ", "Convert components into quaternion", 0),
    ("SCALARVECTOR", "Scalar Vector", "Convert Scalar & Vector into quaternion", 1),
    ("EULER", "Euler Angles", "Convert Euler angles into quaternion", 2),
    ("AXISANGLE", "Axis Angle", "Convert Axis & Angle into quaternion", 3),
    ("MATRIX", "Matrix", "Convert Rotation Matrix into quaternion", 4),
]

id_mat = [[tuple(v) for v in Matrix()]]  # identity matrix

input_sockets = {
    "WXYZ": ["W", "X", "Y", "Z"],
    "SCALARVECTOR": ["Scalar", "Vector"],
    "EULER": ["Angle X", "Angle Y", "Angle Z"],
    "AXISANGLE": ["Angle", "Axis"],
    "MATRIX": ["Matrix"]
}


class SvQuaternionInNodeMK2(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Quaternions, In
    Tooltip: Generate quaternions from various quaternion components
    """
    bl_idname = 'SvQuaternionInNodeMK2'
    bl_label = 'Quaternion In'
    sv_icon = 'SV_QUATERNION_IN'

    def update_sockets(self):
        # hide all input sockets
        for k, names in input_sockets.items():
            for name in names:
                self.inputs[name].hide_safe = True

        # show mode specific input sockets
        for name in input_sockets[self.mode]:
            self.inputs[name].hide_safe = False

    def update_mode(self, context):

        self.update_sockets()

        updateNode(self, context)

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.angle = self.angle * au
        self.angle_x = self.angle_x * au
        self.angle_y = self.angle_y * au
        self.angle_z = self.angle_z * au

    mode : EnumProperty(
        name='Mode', description='The input component format of the quaternion',
        items=mode_items, default="WXYZ", update=update_mode)

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
        default=0.0, precision=3, update=SvAngleHelper.update_angle)

    angle_y : FloatProperty(
        name='Angle Y', description='Rotation angle about Y axis',
        default=0.0, precision=3, update=SvAngleHelper.update_angle)

    angle_z : FloatProperty(
        name='Angle Z', description='Rotation angle about Z axis',
        default=0.0, precision=3, update=SvAngleHelper.update_angle)

    angle : FloatProperty(
        name='Angle', description='Rotation angle about the given axis',
        default=0.0, update=SvAngleHelper.update_angle)

    axis : FloatVectorProperty(
        name='Axis', description='Axis of rotation',
        size=3, default=(1.0, 0.0, 0.0), subtype="XYZ", update=updateNode)

    normalize : BoolProperty(
        name='Normalize', description='Normalize the output quaternion',
        default=False, update=updateNode)

    def migrate_from(self, old_node):
        self.angle_units = old_node.angle_units

    def migrate_props_pre_relink(self, old_node):
        self.update_sockets()

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
            self.draw_angle_euler_buttons(context, layout)

        if self.mode in {"WXYZ", "SCALARVECTOR"}:
            layout.prop(self, "normalize", toggle=True)

    def draw_buttons_ext(self, context, layout):
        if self.mode in {"EULER", "AXISANGLE"}:
            self.draw_angle_units_buttons(context, layout)

    def process(self):
        if not self.outputs['Quaternions'].is_linked:
            return

        inputs = self.inputs

        quaternion_list = []

        if self.mode == "WXYZ":
            I = [inputs[n].sv_get()[0] for n in "WXYZ"]
            params = match_long_repeat(I)
            for wxyz in zip(*params):
                q = Quaternion(wxyz)
                if self.normalize:
                    q.normalize()
                quaternion_list.append(q)

        elif self.mode == "SCALARVECTOR":
            I = [inputs[n].sv_get()[0] for n in ["Scalar", "Vector"]]
            params = match_long_repeat(I)
            for scalar, vector in zip(*params):
                q = Quaternion([scalar, *vector])
                if self.normalize:
                    q.normalize()
                quaternion_list.append(q)

        elif self.mode == "EULER":
            I = [inputs["Angle " + n].sv_get()[0] for n in "XYZ"]
            params = match_long_repeat(I)
            # conversion factor from the current angle units to radians
            au = self.radians_conversion_factor()
            for angleX, angleY, angleZ in zip(*params):
                euler = Euler((angleX * au, angleY * au, angleZ * au), self.euler_order)
                q = euler.to_quaternion()
                if self.normalize:
                    q.normalize()
                quaternion_list.append(q)

        elif self.mode == "AXISANGLE":
            I = [inputs[n].sv_get()[0] for n in ["Axis", "Angle"]]
            params = match_long_repeat(I)
            # conversion factor from the current angle units to radians
            au = self.radians_conversion_factor()
            for axis, angle in zip(*params):
                q = Quaternion(axis, angle * au)
                if self.normalize:
                    q.normalize()
                quaternion_list.append(q)

        elif self.mode == "MATRIX":
            input_M = inputs["Matrix"].sv_get(default=id_mat)
            for m in input_M:
                q = Matrix(m).to_quaternion()
                if self.normalize:
                    q.normalize()
                quaternion_list.append(q)

        self.outputs['Quaternions'].sv_set(quaternion_list)


def register():
    bpy.utils.register_class(SvQuaternionInNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvQuaternionInNodeMK2)
