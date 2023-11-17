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
from sverchok.data_structure import updateNode, match_long_repeat, make_repeaters
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper
from mathutils import Quaternion, Matrix, Euler

rotation_mode_items = [
    ("QUATERNION", "Quaternion",   "Rotation given as a Quaternion", 0),
    ("EULER",      "Euler Angles", "Rotation given as Euler Angles", 1),
    ("AXISANGLE",  "Axis Angle",   "Rotation given as Axis & Angle", 2),
]

input_sockets = {
    "QUATERNION": ["Quaternion"],
    "EULER":      ["Angle X", "Angle Y", "Angle Z"],
    "AXISANGLE":  ["Axis", "Angle"],
}

mat_t = Matrix().Identity(4)  # pre-allocate once for performance (translation)
mat_s = Matrix().Identity(4)  # pre-allocate once for performance (scale)

def quaternion_matrices(params):
    matrices = []
    mat_num = max(map(len, params))
    params2 = make_repeaters(params)
    for i, location, quaternion, scale in zip(range(mat_num), *params2):
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
    return matrices
def euler_matrices(params, euler_order, angle_units):
    mat_num = max(map(len, params))
    params2 = make_repeaters(params)
    matrices = []
    for i, location, angleX, angleY, angleZ, scale in zip(range(mat_num), *params2):
        # translation
        mat_t[0][3] = location[0]
        mat_t[1][3] = location[1]
        mat_t[2][3] = location[2]
        # rotation
        angles = (angleX * angle_units, angleY * angle_units, angleZ * angle_units)
        euler = Euler(angles, euler_order)
        # mat_r = euler.to_quaternion().to_matrix().to_4x4()
        mat_r = euler.to_matrix().to_4x4()

        # scale
        mat_s[0][0] = scale[0]
        mat_s[1][1] = scale[1]
        mat_s[2][2] = scale[2]
        # composite matrix
        m = mat_t @ mat_r @ mat_s
        matrices.append(m)
    return matrices

def axis_angle_matrices(params, angle_units):
    max_len = max(map(len, params))

    params2 = make_repeaters(params)
    # params2 = match_long_repeat([ll, xl, al, sl])
    matrices = []
    for i, location, axis, angle, scale in zip(range(max_len), *params2):
    # for location, axis, angle, scale in zip(*params2):
        # translation
        mat_t[0][3] = location[0]
        mat_t[1][3] = location[1]
        mat_t[2][3] = location[2]
        # rotation
        mat_r = Quaternion(axis, angle * angle_units).to_matrix().to_4x4()
        # scale
        mat_s[0][0] = scale[0]
        mat_s[1][1] = scale[1]
        mat_s[2][2] = scale[2]
        # composite matrix
        m = mat_t @ mat_r @ mat_s
        matrices.append(m)
    return matrices

class SvMatrixInNodeMK4(SverchCustomTreeNode, bpy.types.Node, SvAngleHelper):
    """
    Triggers: Loc, Rot, Scale, Angle
    Tooltip: Generate matrix from various components.\n\tIn: Location, Scale, Axis, Angle, Quaternion\n\tParams: Format (Quaternion/Euler Angles/[Axis Angle]), Euler order (XYZ...ZXY)\n\tOut: Matrix
    """
    bl_idname = 'SvMatrixInNodeMK4'
    bl_label = 'Matrix In'
    sv_icon = 'SV_MATRIX_IN'

    def update_rotation_mode(self, context):

        # hide all input sockets
        for k, names in input_sockets.items():
            for name in names:
                self.inputs[name].hide_safe = True

        # show mode specific input sockets
        for name in input_sockets[self.rotation_mode]:
            self.inputs[name].hide_safe = False

        updateNode(self, context)

    def update_angles(self, context, angle_units):
        ''' Update all the angles to preserve their values in the new units '''
        self.angle = self.angle * angle_units
        self.angle_x = self.angle_x * angle_units
        self.angle_y = self.angle_y * angle_units
        self.angle_z = self.angle_z * angle_units

    rotation_mode: EnumProperty(
        name='Rotation Mode', description='The rotation component format of the matrix',
        items=rotation_mode_items, default="AXISANGLE", update=update_rotation_mode)

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
        default=0.0, precision=3, update=SvAngleHelper.update_angle)

    angle_y: FloatProperty(
        name='Angle Y', description='Rotation angle about Y axis',
        default=0.0, precision=3, update=SvAngleHelper.update_angle)

    angle_z: FloatProperty(
        name='Angle Z', description='Rotation angle about Z axis',
        default=0.0, precision=3, update=SvAngleHelper.update_angle)

    angle: FloatProperty(
        name='Angle', description='Rotation angle about the given axis',
        default=0.0, precision=3, update=SvAngleHelper.update_angle)

    axis: FloatVectorProperty(
        name='Axis', description='Axis of rotation',
        size=3, default=(0.0, 0.0, 1.0), precision=3, subtype="XYZ", update=updateNode)

    flat_output: BoolProperty(
        name="Flat output", description="Flatten output by list-joining level 1",
        default=True, update=updateNode)

    def migrate_from(self, old_node):
        ''' Migration from old nodes (attributes mapping) '''
        if old_node.bl_idname == "SvMatrixGenNodeMK2":
            self.location_ = old_node.l_
            self.scale = old_node.s_
            self.axis = old_node.r_
            self.angle = old_node.a_
            self.angle_units = AngleUnits.DEGREES
            self.last_angle_units = AngleUnits.DEGREES

        elif old_node.bl_idname == "SvMatrixInNodeMK3":
            self.rotation_mode = old_node.mode

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

        self.update_rotation_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "rotation_mode", expand=False, text="")
        if self.rotation_mode == "EULER":
            self.draw_angle_euler_buttons(context, layout)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

        if self.rotation_mode in {"EULER", "AXISANGLE"}:
            self.draw_angle_units_buttons(context, layout)

    def rclick_menu(self, context, layout):
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

    def process(self):
        if not self.outputs['Matrices'].is_linked:
            return

        inputs = self.inputs

        matrix_list = []
        add_matrix = matrix_list.extend if self.flat_output else matrix_list.append

        if self.rotation_mode == "QUATERNION":
            input_l = inputs["Location"].sv_get(deepcopy=False)
            input_s = inputs["Scale"].sv_get(deepcopy=False)
            input_q = inputs["Quaternion"].sv_get(deepcopy=False)
            if inputs["Quaternion"].is_linked:
                input_q = [input_q]
            else:
                input_q = [[Quaternion(input_q[0][0])]]
            I = [input_l, input_q, input_s]
            params1 = match_long_repeat(I)
            for p in zip(*params1):
                add_matrix(quaternion_matrices(p))

        elif self.rotation_mode == "EULER":
            socket_names = ["Location", "Angle X", "Angle Y", "Angle Z", "Scale"]
            I = [inputs[name].sv_get(deepcopy=False) for name in socket_names]
            params1 = match_long_repeat(I)
            # conversion factor from the current angle units to radians
            angle_units = self.radians_conversion_factor()
            for p in zip(*params1):
                add_matrix(euler_matrices(p, self.euler_order, angle_units))

        elif self.rotation_mode == "AXISANGLE":
            socket_names = ["Location", "Axis", "Angle", "Scale"]
            I = [inputs[name].sv_get(deepcopy=False) for name in socket_names]
            params1 = match_long_repeat(I)
            # conversion factor from the current angle units to radians
            angle_units = self.radians_conversion_factor()
            for p in zip(*params1):
                add_matrix(axis_angle_matrices(p, angle_units))

        self.outputs['Matrices'].sv_set(matrix_list)


def register():
    bpy.utils.register_class(SvMatrixInNodeMK4)


def unregister():
    bpy.utils.unregister_class(SvMatrixInNodeMK4)
