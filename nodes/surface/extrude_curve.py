
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.curve import SvExCurve
from sverchok.utils.surface import SvExExtrudeCurveCurveSurface, SvExExtrudeCurveFrenetSurface, SvExExtrudeCurveZeroTwistSurface

class SvExExtrudeCurveCurveSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude Curve along Curve
    Tooltip: Generate a surface by extruding a curve along another curve
    """
    bl_idname = 'SvExExtrudeCurveCurveSurfaceNode'
    bl_label = 'Extrude Curve Along Curve'
    bl_icon = 'MOD_THICKNESS'

    modes = [
        ('NONE', "None", "No rotation", 0),
        ('FRENET', "Frenet", "Frenet / native rotation", 1),
        ('ZERO', "Zero-twist", "Zero-twist rotation", 2)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Resolution'].hide_safe = self.algorithm != 'ZERO'

    algorithm : EnumProperty(
            name = "Algorithm",
            items = modes,
            default = 'NONE',
            update = update_sockets)

    resolution : IntProperty(
        name = "Resolution",
        min = 10, default = 50,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "algorithm")

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Profile").display_shape = 'DIAMOND'
        self.inputs.new('SvExCurveSocket', "Extrusion").display_shape = 'DIAMOND'
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        profile_s = self.inputs['Profile'].sv_get()
        extrusion_s = self.inputs['Extrusion'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()

        if isinstance(profile_s[0], SvExCurve):
            profile_s = [profile_s]
        if isinstance(extrusion_s[0], SvExCurve):
            extrusion_s = [extrusion_s]

        surface_out = []
        for profiles, extrusions, resolution in zip_long_repeat(profile_s, extrusion_s, resolution_s):
            if isinstance(resolution, (list, tuple)):
                resolution = resolution[0]

            for profile, extrusion in zip_long_repeat(profiles, extrusions):
                if self.algorithm == 'NONE':
                    surface = SvExExtrudeCurveCurveSurface(profile, extrusion)
                elif self.algorithm == 'FRENET':
                    surface = SvExExtrudeCurveFrenetSurface(profile, extrusion)
                elif self.algorithm == 'ZERO':
                    surface = SvExExtrudeCurveZeroTwistSurface(profile, extrusion, resolution)
                else:
                    raise Exception("Unsupported algorithm")
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExExtrudeCurveCurveSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExExtrudeCurveCurveSurfaceNode)

