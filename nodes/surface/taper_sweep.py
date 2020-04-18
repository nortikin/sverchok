
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvTaperSweepSurface

class SvTaperSweepSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Taper Sweep Curve
    Tooltip: Generate a taper surface along a line
    """
    bl_idname = 'SvExTaperSweepSurfaceNode'
    bl_label = 'Taper Sweep'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_TAPER_SWEEP'

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Profile")
        self.inputs.new('SvCurveSocket', "Taper")
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.prop = (0.0, 0.0, 1.0)
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        profile_s = self.inputs['Profile'].sv_get()
        taper_s = self.inputs['Taper'].sv_get()
        point_s = self.inputs['Point'].sv_get()
        direction_s = self.inputs['Direction'].sv_get()

        if isinstance(profile_s[0], SvCurve):
            profile_s = [profile_s]
        if isinstance(taper_s[0], SvCurve):
            taper_s = [taper_s]

        point_s = ensure_nesting_level(point_s, 3)
        direction_s = ensure_nesting_level(direction_s, 3)

        surface_out = []
        for profiles, tapers, points, directions in zip_long_repeat(profile_s, taper_s, point_s, direction_s):
            for profile, taper, point, direction in zip_long_repeat(profiles, tapers, points, directions):
                surface = SvTaperSweepSurface(profile, taper, np.array(point), np.array(direction))
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvTaperSweepSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvTaperSweepSurfaceNode)

