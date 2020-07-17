
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
import bmesh
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_mesh_utils import polygons_to_edges, mesh_join
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.logging import info, exception
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import ladybug

if ladybug is None:
    add_dummy('SvExLadyBugLocationNode', "Location", 'ladybug')
else:
    from ladybug.location import Location

    class SvExLadyBugLocationNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Ladybug location
        Tooltip: Generate location from latitude and longitude coordinates
        """
        bl_idname = 'SvExLadyBugLocationNode'
        bl_label = 'Location'
        bl_icon = 'WORLD'



        location_name: StringProperty(
            name="Name",
            default="",
            update=updateNode)
        latitude: FloatProperty(
            name="Latitude",
            default=0,
            precision=4,
            min=-90,
            max=90,
            update=updateNode)
        longitude: FloatProperty(
            name="Longitude",
            default=0,
            precision=4,
            min=-180,
            max=180,
            update=updateNode)
        time_zone: IntProperty(
            name="Time Zone",
            default=0,
            min=-12,
            max=+14,
            update=updateNode)
        elevation: IntProperty(
            name="Elevation",
            default=0,
            update=updateNode)

        # def draw_buttons(self, context, layout):
        #     layout.prop(self, "join", toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Name").prop_name = 'location_name'
            self.inputs.new('SvStringsSocket', "Latitude").prop_name = 'latitude'
            self.inputs.new('SvStringsSocket', "Longitude").prop_name = 'longitude'
            self.inputs.new('SvStringsSocket', "Time Zone").prop_name = 'time_zone'
            self.inputs.new('SvStringsSocket', "Elevation").prop_name = 'elevation'
            self.outputs.new('SvStringsSocket', "Location")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            name_s = self.inputs['Name'].sv_get()[0]
            latitude_s = self.inputs['Latitude'].sv_get()[0]
            longitude_s = self.inputs['Longitude'].sv_get()[0]
            time_zone_s = self.inputs['Time Zone'].sv_get()[0]
            elevation_s = self.inputs['Elevation'].sv_get()[0]

            locations = []
            for name, lat, lon, tz, el in zip_long_repeat(name_s, latitude_s, longitude_s, time_zone_s, elevation_s):
                loc = Location(name, '', latitude=lat, longitude=lon, time_zone=tz, elevation=el)
                locations.append(loc)
            self.outputs['Location'].sv_set(locations)


def register():
    if ladybug is not None:
        bpy.utils.register_class(SvExLadyBugLocationNode)

def unregister():
    if ladybug is not None:
        bpy.utils.unregister_class(SvExLadyBugLocationNode)
