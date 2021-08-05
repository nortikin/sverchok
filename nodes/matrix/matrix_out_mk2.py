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
from bpy.props import EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from mathutils import Matrix


mode_items = [
    ("QUATERNION", "Quaternion", "Convert rotation component of the matrix into Quaternion", 0),
    ("EULER", "Euler Angles", "Convert rotation component of the matrix into Euler angles", 1),
    ("AXISANGLE", "Axis Angle", "Convert rotation component of the matrix into Axis & Angle", 2),
]

output_sockets = {
    "QUATERNION": ["Quaternion"],
    "EULER": ["Angle X", "Angle Y", "Angle Z"],
    "AXISANGLE": ["Angle", "Axis"],
}


class SvMatrixOutNodeMK2(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper, SvRecursiveNode):
    """
    Triggers: Matrix, Out
    Tooltip: Convert a matrix into its location, scale & rotation components
    """
    bl_idname = 'SvMatrixOutNodeMK2'
    bl_label = 'Matrix Out'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_OUT'

    flat_output: bpy.props.BoolProperty(
        name="Flat Quaternions output",
        description="Flatten Quaternions output by list-joining level 1",
        default=True, update=updateNode)

    def migrate_from(self, old_node):
        ''' Migration from old nodes (attributes mapping) '''
        if old_node.bl_idname == "MatrixOutNode":
            self.angle_units = AngleUnits.DEGREES
            self.last_angle_units = AngleUnits.DEGREES

    def migrate_props_pre_relink(self, old_node):
        self.update_sockets()

    def rclick_menu(self, context, layout):
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        self.node_replacement_menu(context, layout)

    def update_sockets(self):
        # hide all the mode related output sockets
        for k, names in output_sockets.items():
            for name in names:
                self.outputs[name].hide_safe = True

        # show the output sockets specific to the current mode
        for name in output_sockets[self.mode]:
            self.outputs[name].hide_safe = False

    def update_mode(self, context):
        self.update_sockets()
        updateNode(self, context)

    mode : EnumProperty(
        name='Mode', description='The output component format of the Matrix',
        items=mode_items, default="AXISANGLE", update=update_mode)

    def sv_init(self, context):
        self.sv_new_input('SvMatrixSocket', "Matrix", is_mandatory=True, nesting_level=2)
        # translation and scale outputs
        self.outputs.new('SvVerticesSocket', "Location")
        self.outputs.new('SvVerticesSocket', "Scale")
        # quaternion output
        self.outputs.new('SvQuaternionSocket', "Quaternion")
        # euler angles outputs
        self.outputs.new('SvStringsSocket', "Angle X")
        self.outputs.new('SvStringsSocket', "Angle Y")
        self.outputs.new('SvStringsSocket', "Angle Z")
        # axis-angle output
        self.outputs.new('SvVerticesSocket', "Axis")
        self.outputs.new('SvStringsSocket', "Angle")

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False, text="")

        if self.mode == "EULER":
            self.draw_angle_euler_buttons(context, layout)

    def draw_buttons_ext(self, context, layout):
        if self.mode in {"EULER", "AXISANGLE"}:
            self.draw_angle_units_buttons(context, layout)
        elif self.mode == 'QUATERNION':
            layout.prop(self, 'flat_output')

    def process_data(self, params):
        input_M = params[0]
        outputs = self.outputs
        # decompose matrices into: Translation, Rotation (quaternion) and Scale
        result = []
        for mat_list in input_M:
            location_list = []
            quaternion_list = [] # rotations (as quaternions)
            scale_list = []
            angles = [[], [], []]
            axis_list, angle_list = [], []
            for m in mat_list:
                T, R, S = m.decompose()
                location_list.append(list(T))
                quaternion_list.append(R)
                scale_list.append(list(S))

            if self.mode == "EULER":
                # conversion factor from radians to the current angle units
                au = self.angle_conversion_factor(AngleUnits.RADIANS, self.angle_units)

                for i, name in enumerate("XYZ"):
                    if outputs["Angle " + name].is_linked:
                        angles[i] = [q.to_euler(self.euler_order)[i] * au for q in quaternion_list]
            elif self.mode == "AXISANGLE":
                if outputs['Axis'].is_linked:
                    axis_list = [tuple(q.axis) for q in quaternion_list]

                if outputs['Angle'].is_linked:
                    # conversion factor from radians to the current angle units
                    au = self.angle_conversion_factor(AngleUnits.RADIANS, self.angle_units)
                    angle_list = [q.angle * au for q in quaternion_list]

            result.append([location_list, scale_list, quaternion_list, *angles, axis_list, angle_list])

        if self.mode == 'QUATERNION':
            output_data = list(zip(*result))
            if len(output_data[2]) == 1 and self.flat_output:
                output_data[2] = output_data[2][0]
            return output_data

        return list(zip(*result))




def register():
    bpy.utils.register_class(SvMatrixOutNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvMatrixOutNodeMK2)
