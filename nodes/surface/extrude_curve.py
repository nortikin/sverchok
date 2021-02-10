
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node
from sverchok.utils.logging import info, exception

from sverchok.utils.curve import SvCurve
from sverchok.utils.surface.algorithms import (
        SvExtrudeCurveCurveSurface, SvExtrudeCurveFrenetSurface,
        SvExtrudeCurveZeroTwistSurface, SvExtrudeCurveMathutilsSurface,
        SvExtrudeCurveTrackNormalSurface,
        SvExtrudeCurveNormalDirSurface,
        PROFILE, EXTRUSION
    )
from sverchok.utils.math import ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, NORMAL_DIR

class SvExtrudeCurveCurveSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude Curve along Curve
    Tooltip: Generate a surface by extruding a curve along another curve
    """
    bl_idname = 'SvExExtrudeCurveCurveSurfaceNode'
    bl_label = 'Extrude Curve Along Curve'
    bl_icon = 'MOD_THICKNESS'

    modes = [
        ('NONE', "None", "No rotation", 0),
        (FRENET, "Frenet", "Frenet / native rotation", 1),
        (ZERO, "Zero-twist", "Zero-twist rotation", 2),
        (HOUSEHOLDER, "Householder", "Use Householder reflection matrix", 3),
        (TRACK, "Tracking", "Use quaternion-based tracking", 4),
        (DIFF, "Rotation difference", "Use rotational difference calculation", 5),
        ('NORMALTRACK', "Track normal", "Try to maintain constant normal direction by tracking along curve", 6),
        (NORMAL_DIR, "Specified plane", "Use plane defined by normal vector in Normal input; i.e., offset in direction perpendicular to Normal input", 7)
    ]

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['Resolution'].hide_safe = self.algorithm not in {ZERO, 'NORMALTRACK'}
        self.inputs['Normal'].hide_safe = self.algorithm != NORMAL_DIR

    algorithm : EnumProperty(
            name = "Algorithm",
            items = modes,
            default = 'NONE',
            update = update_sockets)

    resolution : IntProperty(
        name = "Resolution",
        min = 10, default = 50,
        update = updateNode)

    origins = [
        (PROFILE, "Global origin", "Global origin", 0),
        (EXTRUSION, "Extrusion origin", "Extrusion origin", 1)
    ]

    origin : EnumProperty(
            name = "Origin",
            items = origins,
            default = PROFILE, # for existing nodes
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "algorithm")
        layout.prop(self, "origin")

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Profile")
        self.inputs.new('SvCurveSocket', "Extrusion")
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        p = self.inputs.new('SvVerticesSocket', "Normal")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.origin = EXTRUSION # default for newly created nodes
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        profile_s = self.inputs['Profile'].sv_get()
        extrusion_s = self.inputs['Extrusion'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        if 'Normal' in self.inputs:
            normal_s = self.inputs['Normal'].sv_get()
        else:
            normal_s = [[(0, 0, 1)]]

        if isinstance(profile_s[0], SvCurve):
            profile_s = [profile_s]
        if isinstance(extrusion_s[0], SvCurve):
            extrusion_s = [extrusion_s]

        surface_out = []
        for profiles, extrusions, normals, resolution in zip_long_repeat(profile_s, extrusion_s, normal_s, resolution_s):
            if isinstance(resolution, (list, tuple)):
                resolution = resolution[0]

            for profile, extrusion, normal in zip_long_repeat(profiles, extrusions, normals):
                if self.algorithm == 'NONE':
                    surface = SvExtrudeCurveCurveSurface(profile, extrusion, origin=self.origin)
                elif self.algorithm == FRENET:
                    surface = SvExtrudeCurveFrenetSurface(profile, extrusion, origin=self.origin)
                elif self.algorithm == ZERO:
                    surface = SvExtrudeCurveZeroTwistSurface(profile, extrusion, resolution, origin=self.origin)
                elif self.algorithm == 'NORMALTRACK':
                    surface = SvExtrudeCurveTrackNormalSurface(profile, extrusion, resolution, origin=self.origin)
                elif self.algorithm == NORMAL_DIR:
                    surface = SvExtrudeCurveNormalDirSurface(profile, extrusion, normal, origin=self.origin)
                else:
                    surface = SvExtrudeCurveMathutilsSurface(profile, extrusion, self.algorithm,
                                orient_axis = 'Z', up_axis = 'X',
                                origin = self.origin)
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExtrudeCurveCurveSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExtrudeCurveCurveSurfaceNode)

