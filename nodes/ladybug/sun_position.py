
import numpy as np
from math import pi

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
import bmesh
from mathutils import Vector, Euler, Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_mesh_utils import polygons_to_edges, mesh_join
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.logging import info, exception
from sverchok.dependencies import ladybug

if ladybug is not None:
    from ladybug.sunpath import Sunpath

    class SvExLadyBugSunPositionNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Ladybug Sun Position
        Tooltip: Generate location from latitude and longitude coordinates
        """
        bl_idname = 'SvExLadyBugSunPositionNode'
        bl_label = 'Sun Position'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        sun_dist: FloatProperty(
            name="Sun Distance",
            default=20,
            update=updateNode)
        month: IntProperty(
            name="Month",
            default=6,
            min=1,
            max=12,
            update=updateNode)
        day: IntProperty(
            name="Day",
            default=15,
            min=1,
            update=updateNode)
        hour: FloatProperty(
            name="Hour",
            default=12,
            update=updateNode)
        north_angle: FloatProperty(
            name="North Angle",
            default=0,
            update=updateNode)
        daylight_savings: BoolProperty(
            name="Daylight Savings",
            default=False,
            update=updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, "sun_dist")
            layout.prop(self, "north_angle")

        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Location")
            self.inputs.new('SvStringsSocket', "Month").prop_name = 'month'
            self.inputs.new('SvStringsSocket', "Day").prop_name = 'day'
            self.inputs.new('SvStringsSocket', "Hour").prop_name = 'hour'

            self.outputs.new('SvStringsSocket', "Altitude")
            self.outputs.new('SvStringsSocket', "Azimuth")
            self.outputs.new('SvMatrixSocket', "Sun Position")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            location_s = self.inputs['Location'].sv_get()
            month_s = self.inputs['Month'].sv_get()
            day_s = self.inputs['Day'].sv_get()
            hour_s = self.inputs['Hour'].sv_get()

            altitude_s, azimuth_s = [], []
            sun_pos = []
            for location, months, days, hours in zip_long_repeat(location_s, month_s, day_s, hour_s):
                sp = Sunpath.from_location(location)

                # sp = Sunpath.from_location(location, north_angle=40)
                altitude, azimuth = [], []
                for mo, day, ho in zip_long_repeat(months, days, hours):

                    sun = sp.calculate_sun(month=mo, day=day, hour=ho)
                    alt_l = sun.altitude
                    azi_l = sun.azimuth
                    altitude.append(sun.altitude)
                    azimuth.append(sun.azimuth)
                    angles = (alt_l * pi/180, 0, -azi_l*pi/180+ self.north_angle*pi/180)
                    euler = Euler(angles, 'XYZ')
                    mat_r = euler.to_quaternion().to_matrix().to_4x4()
                    pos = mat_r @ Vector((0, self.sun_dist, 0))
                    mat_t = Matrix.Translation(pos)
                    angles = ((90-alt_l) * pi/180, 0, (180-azi_l)*pi/180 + self.north_angle*pi/180)
                    euler = Euler(angles, 'XYZ')
                    mat_r = euler.to_quaternion().to_matrix().to_4x4()
                    m = mat_t @ mat_r
                    sun_pos.append(m)
                altitude_s.append(altitude)
                azimuth_s.append(azimuth)
            self.outputs['Altitude'].sv_set(altitude_s)
            self.outputs['Azimuth'].sv_set(azimuth_s)
            self.outputs['Sun Position'].sv_set(sun_pos)


def register():
    if ladybug is not None:
        bpy.utils.register_class(SvExLadyBugSunPositionNode)

def unregister():
    if ladybug is not None:
        bpy.utils.unregister_class(SvExLadyBugSunPositionNode)
