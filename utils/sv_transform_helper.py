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
from bpy.props import (EnumProperty, BoolProperty)

from sverchok.data_structure import updateNode
from sverchok.node_tree import throttled
from sverchok.settings import get_params

from math import pi

euler_order_items = [
    ('XYZ', 'XYZ', "", 0),
    ('XZY', 'XZY', "", 1),
    ('YXZ', 'YXZ', "", 2),
    ('YZX', 'YZX', "", 3),
    ('ZXY', 'ZXY', "", 4),
    ('ZYX', 'ZYX', "", 5)
]


class AngleUnits:
    RADIANS = "RAD"
    DEGREES = "DEG"
    UNITIES = "UNI"

    @classmethod
    def get_blender_enum(cls):
        return [
            (AngleUnits.RADIANS, "Rad", "Radians", "", 0),
            (AngleUnits.DEGREES, "Deg", "Degrees", "", 1),
            (AngleUnits.UNITIES, "Uni", "Unities", "", 2)
        ]


angle_remap_options = {
    # from               to
    (AngleUnits.RADIANS, AngleUnits.DEGREES): 180/pi,
    (AngleUnits.RADIANS, AngleUnits.UNITIES): 1/(2*pi),
    (AngleUnits.DEGREES, AngleUnits.RADIANS): pi/180,
    (AngleUnits.DEGREES, AngleUnits.UNITIES): 1/360,
    (AngleUnits.UNITIES, AngleUnits.RADIANS): 2*pi,
    (AngleUnits.UNITIES, AngleUnits.DEGREES): 360
}


class SvAngleHelper():

    def get_preferences(self):
        props = get_params({
            'auto_update_angle_values': False,
        })
        return props.auto_update_angle_values

    def angle_conversion_factor(self, from_angle_units, to_angle_units):
        if from_angle_units == to_angle_units:
            return 1

        multiplier = angle_remap_options.get((from_angle_units, to_angle_units))

        if not multiplier:
            raise Error(f"node {self.name} failure to map angle units, {from_angle_units}->{to_angle_units}")

        return multiplier

    def radians_conversion_factor(self):
        return self.angle_conversion_factor(self.angle_units, AngleUnits.RADIANS)

    def degrees_conversion_factor(self):
        return self.angle_conversion_factor(self.angle_units, AngleUnits.DEGREES)

    def unities_conversion_factor(self):
        return self.angle_conversion_factor(self.angle_units, AngleUnits.UNITIES)

    def update_angle(self, context):
        ''' Wrapper to inhibit angle updates when units are changed '''
        if self.inhibit_updates:
            return

        updateNode(self, context)

    def update_angles(self, context, acf):
        ''' Override this in the derived class to update specific angle values'''
        # print("SvAngleHelper update_angles called")

    @throttled
    def update_angle_units(self, context):
        ''' Update all the angles to preserve their values in the new units '''
        if self.angle_units == self.last_angle_units:
            return

        auto_update_angle_values = self.get_preferences()

        if auto_update_angle_values:
            acf = self.angle_conversion_factor(self.last_angle_units, self.angle_units)

            self.inhibit_updates = True  # deactivate updates
            self.update_angles(context, acf)
            self.inhibit_updates = False  # reactivate updates

        self.last_angle_units = self.angle_units  # keep track of the last units

    def angle_unit_conversion_factor(self, new_angle_units):
        return self.angle_conversion_factor(self.angle_units, new_angle_units)

    euler_order: EnumProperty(
        name="Euler Order", description="Order of the Euler rotations",
        default="XYZ", items=euler_order_items, update=updateNode)

    angle_units: EnumProperty(
        name="Angle Units", description="Angle units (Radians/Degrees/Unities)",
        default=AngleUnits.DEGREES, items=AngleUnits.get_blender_enum(),
        update=update_angle_units)

    last_angle_units: EnumProperty(
        name="Last Angle Units", description="Angle units (Radians/Degrees/Unities)",
        default=AngleUnits.DEGREES, items=AngleUnits.get_blender_enum())

    inhibit_updates: BoolProperty(
        name='Inhibit Update', description='Flag to inhibit update calls', default=False)

    def draw_angle_euler_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "euler_order", text="")

    def draw_angle_units_buttons(self, context, layout):
        box = layout.box()
        box.label(text="Angle Units")
        row = box.row(align=True)
        row.prop(self, "angle_units", expand=True)
