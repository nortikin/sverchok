
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvConstPipeSurface
from sverchok.utils.math import ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL

class SvPipeSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Constant Cylindric Pipe
    Tooltip: Generate a cylindric pipe surface
    """
    bl_idname = 'SvPipeSurfaceNode'
    bl_label = 'Pipe (Surface)'
    bl_icon = 'MOD_THICKNESS'

    modes = [
        (FRENET, "Frenet", "Frenet / native rotation", 0),
        (ZERO, "Zero-twist", "Zero-twist rotation", 1),
        (HOUSEHOLDER, "Householder", "Use Householder reflection matrix", 2),
        (TRACK, "Tracking", "Use quaternion-based tracking", 3),
        (DIFF, "Rotation difference", "Use rotational difference calculation", 4),
        (TRACK_NORMAL, "Track normal", "Try to maintain constant normal direction by tracking along curve", 5)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Resolution'].hide_safe = self.algorithm not in {ZERO, TRACK_NORMAL}

    algorithm : EnumProperty(
            name = "Algorithm",
            items = modes,
            default = HOUSEHOLDER,
            update = update_sockets)

    resolution : IntProperty(
        name = "Resolution",
        min = 10, default = 50,
        update = updateNode)

    radius : FloatProperty(
        name = "Radius",
        description = "Pipe radius",
        min = 0.0, default = 0.1,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "algorithm")

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        profile_s = self.inputs['Curve'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()

        profile_s = ensure_nesting_level(profile_s, 2, data_types=(SvCurve,))
        resolution_s = ensure_nesting_level(resolution_s, 2)
        radius_s = ensure_nesting_level(radius_s, 2)

        surface_out = []
        for profiles, radiuses, resolutions in zip_long_repeat(profile_s, radius_s, resolution_s):
            new_surfaces = []
            for profile, radius, resolution in zip_long_repeat(profiles, radiuses, resolutions):
                surface = SvConstPipeSurface(profile, radius,
                            algorithm = self.algorithm,
                            resolution = resolution)
                new_surfaces.append(surface)
            surface_out.append(new_surfaces)
        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvPipeSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvPipeSurfaceNode)

