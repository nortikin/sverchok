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

mode_items = [
    ("QUATERNION", "Quaternion",   "Rotation given as a Quaternion", 0),
    ("EULER",      "Euler Angles", "Rotation given as Euler Angles", 1),
    ("AXISANGLE",  "Axis Angle",   "Rotation given as Axis & Angle", 2),
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
    ("DEG", "Deg", "Degrees", "", 1),
    ("UNI", "Uni", "Unities", "", 2)
]

angle_unit_conversion = {
    "RAD": {"RAD": 1, "DEG": 180/pi, "UNI": 1/(2*pi)},
    "DEG": {"RAD": pi/180, "DEG": 1, "UNI": 1/360},
    "UNI": {"RAD": 2*pi, "DEG": 360, "UNI": 1}
}

input_sockets = {
    "QUATERNION": ["Quaternion"],
    "EULER":      ["Angle X", "Angle Y", "Angle Z"],
    "AXISANGLE":  ["Axis", "Angle"],
}

mat_t = Matrix().Identity(4)  # pre-allocate once for performance (translation)
mat_s = Matrix().Identity(4)  # pre-allocate once for performance (scale)


class SvMatrixInNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Loc, Rot, Scale, Angle
    Tooltip: Generate matrix from various components
    """
    bl_idname = 'SvMatrixInNodeMK3'
    bl_label = 'Matrix In'
    sv_icon = 'SV_MATRIX_IN'

    replacement_nodes = [('SvMatrixInNodeMK4', None, None)]

    def update_mode(self, context):

        # hide all input sockets
        for k, names in input_sockets.items():
            for name in names:
                self.inputs[name].hide_safe = True

        # show mode specific input sockets
        for name in input_sockets[self.mode]:
            self.inputs[name].hide_safe = False

        updateNode(self, context)

    def update_angle_units(self, context):
        ''' Update all the angles to preserve their values in the new units '''

        auc = angle_unit_conversion[self.last_angle_units][self.angle_units]

        self.last_angle_units = self.angle_units  # keep track of the last units

        self.syncing = True  # deactivate updates
        self.angle = self.angle * auc
        self.angle_x = self.angle_x * auc
        self.angle_y = self.angle_y * auc
        self.angle_z = self.angle_z * auc
        self.syncing = False  # reactivate updates

        updateNode(self, context)

    def update_angle(self, context):
        ''' Wrapper to suppress angle updates when units are changed '''
        if self.syncing:
            return

        updateNode(self, context)

    mode: EnumProperty(
        name='Mode', description='The input component format of the matrix',
        items=mode_items, default="AXISANGLE", update=update_mode)

    euler_order: EnumProperty(
        name="Euler Order", description="Order of the Euler rotations",
        default="XYZ", items=euler_order_items, update=updateNode)

    angle_units: EnumProperty(
        name="Angle Units", description="Angle units (radians/degrees/unities)",
        default="DEG", items=angle_unit_items, update=update_angle_units)

    last_angle_units: EnumProperty(
        name="Last Angle Units", description="Angle units (radians/degrees/unities)",
        default="DEG", items=angle_unit_items)

    scale: FloatVectorProperty(
        name='Scale', description='Scale component of the matrix',
        size=3, default=(1.0, 1.0, 1.0), precision=3, subtype="XYZ", update=updateNode)

    location_: FloatVectorProperty(
        name='Location', description='Location component of the matrix',
        size=3, default=(0.0, 0.0, 0.0), precision=3, subtype="XYZ", update=updateNode)

    quaternion: FloatVectorProperty(
        name="Quaternion", description="Quaternion to convert to rotation matrix",
        size=4, subtype="QUATERNION", default=(1.0, 0.0, 0.0, 0.0), precision=3,
        update=updateNode)

    angle_x: FloatProperty(
        name='Angle X', description='Rotation angle about X axis',
        default=0.0, precision=3, update=update_angle)

    angle_y: FloatProperty(
        name='Angle Y', description='Rotation angle about Y axis',
        default=0.0, precision=3, update=update_angle)

    angle_z: FloatProperty(
        name='Angle Z', description='Rotation angle about Z axis',
        default=0.0, precision=3, update=update_angle)

    angle: FloatProperty(
        name='Angle', description='Rotation angle about the given axis',
        default=0.0, precision=3, update=update_angle)

    axis: FloatVectorProperty(
        name='Axis', description='Axis of rotation',
        size=3, default=(0.0, 0.0, 1.0), precision=3, subtype="XYZ", update=updateNode)

    flat_output: BoolProperty(
        name="Flat output", description="Flatten output by list-joining level 1",
        default=True, update=updateNode)

    syncing: BoolProperty(
        name='Syncing', description='Syncing flag', default=False)

    def migrate_from(self, old_node):
        ''' Migration from MK2 (attributes mapping) '''
        self.location_ = old_node.l_
        self.scale = old_node.s_
        self.axis = old_node.r_
        self.angle = old_node.a_

    def sv_init(self, context):

        self.inputs.new('SvVerticesSocket', "Location").prop_name = "location_"
        self.inputs.new('SvVerticesSocket', "Scale").prop_name = 'scale'
        self.inputs.new('SvQuaternionSocket', "Quaternion").prop_name = "quaternion"

        self.inputs.new('SvStringsSocket', "Angle X").prop_name = 'angle_x'
        self.inputs.new('SvStringsSocket', "Angle Y").prop_name = 'angle_y'
        self.inputs.new('SvStringsSocket', "Angle Z").prop_name = 'angle_z'

        self.inputs.new('SvVerticesSocket', "Axis").prop_name = "axis"
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'

        self.outputs.new('SvMatrixSocket', "Matrices")

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False, text="")
        if self.mode == "EULER":
            col = layout.column(align=True)
            col.prop(self, "euler_order", text="")
        if self.mode in {"EULER", "AXISANGLE"}:
            row = layout.row(align=True)
            row.prop(self, "angle_units", expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        self.node_replacement_menu(context, layout)

    def process(self):
        if not self.outputs['Matrices'].is_linked:
            return

        inputs = self.inputs

        matrix_list = []
        add_matrix = matrix_list.extend if self.flat_output else matrix_list.append

        if self.mode == "QUATERNION":
            input_l = inputs["Location"].sv_get(deepcopy=False)
            input_s = inputs["Scale"].sv_get(deepcopy=False)
            input_q = inputs["Quaternion"].sv_get(deepcopy=False)
            if inputs["Quaternion"].is_linked:
                input_q = [input_q]
            else:
                input_q = [[Quaternion(input_q[0][0])]]
            I = [input_l, input_q, input_s]
            params1 = match_long_repeat(I)
            for ll, ql, sl in zip(*params1):
                params2 = match_long_repeat([ll, ql, sl])
                matrices = []
                for location, quaternion, scale in zip(*params2):
                    # translation
                    mat_t[0][3] = location[0]
                    mat_t[1][3] = location[1]
                    mat_t[2][3] = location[2]
                    # rotation
                    mat_r = quaternion.to_matrix().to_4x4()
                    # scale
                    mat_s[0][0] = scale[0]
                    mat_s[1][1] = scale[1]
                    mat_s[2][2] = scale[2]
                    # composite matrix
                    m = mat_t @ mat_r @ mat_s
                    matrices.append(m)
                add_matrix(matrices)

        elif self.mode == "EULER":
            socket_names = ["Location", "Angle X", "Angle Y", "Angle Z", "Scale"]
            I = [inputs[name].sv_get(deepcopy=False) for name in socket_names]
            params1 = match_long_repeat(I)
            auc = angle_unit_conversion[self.angle_units]["RAD"]  # convert to radians
            for ll, axl, ayl, azl, sl in zip(*params1):
                params2 = match_long_repeat([ll, axl, ayl, azl, sl])
                matrices = []
                for location, angleX, angleY, angleZ, scale in zip(*params2):
                    # translation
                    mat_t[0][3] = location[0]
                    mat_t[1][3] = location[1]
                    mat_t[2][3] = location[2]
                    # rotation
                    angles = (angleX * auc, angleY * auc, angleZ * auc)
                    euler = Euler(angles, self.euler_order)
                    mat_r = euler.to_quaternion().to_matrix().to_4x4()
                    # scale
                    mat_s[0][0] = scale[0]
                    mat_s[1][1] = scale[1]
                    mat_s[2][2] = scale[2]
                    # composite matrix
                    m = mat_t @ mat_r @ mat_s
                    matrices.append(m)
                add_matrix(matrices)

        elif self.mode == "AXISANGLE":
            socket_names = ["Location", "Axis", "Angle", "Scale"]
            I = [inputs[name].sv_get(deepcopy=False) for name in socket_names]
            params1 = match_long_repeat(I)
            auc = angle_unit_conversion[self.angle_units]["RAD"]  # convert to radians
            for ll, xl, al, sl in zip(*params1):
                params2 = match_long_repeat([ll, xl, al, sl])
                matrices = []
                for location, axis, angle, scale in zip(*params2):
                    # translation
                    mat_t[0][3] = location[0]
                    mat_t[1][3] = location[1]
                    mat_t[2][3] = location[2]
                    # rotation
                    mat_r = Quaternion(axis, angle * auc).to_matrix().to_4x4()
                    # scale
                    mat_s[0][0] = scale[0]
                    mat_s[1][1] = scale[1]
                    mat_s[2][2] = scale[2]
                    # composite matrix
                    m = mat_t @ mat_r @ mat_s
                    matrices.append(m)
                add_matrix(matrices)

        self.outputs['Matrices'].sv_set(matrix_list)


def register():
    bpy.utils.register_class(SvMatrixInNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvMatrixInNodeMK3)
