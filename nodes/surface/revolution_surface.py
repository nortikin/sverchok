
import numpy as np
from math import pi

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvRevolutionSurface

class SvRevolutionSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Revolution Surface
    Tooltip: Generate a surface of revolution (similar to Spin / Lathe modifier)
    """
    bl_idname = 'SvExRevolutionSurfaceNode'
    bl_label = 'Revolution Surface'
    bl_icon = 'MOD_SCREW'

    v_min : FloatProperty(
        name = "Angle From",
        description = "Minimal value of V surface parameter",
        default = 0.0,
        update = updateNode)

    v_max : FloatProperty(
        name = "Angle To",
        description = "Minimal value of V surface parameter",
        default = 2*pi,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Profile")
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.prop = (0.0, 0.0, 1.0)
        self.inputs.new('SvStringsSocket', 'AngleFrom').prop_name = 'v_min'
        self.inputs.new('SvStringsSocket', 'AngleTo').prop_name = 'v_max'
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point_s = self.inputs['Point'].sv_get()
        direction_s = self.inputs['Direction'].sv_get()
        curve_s = self.inputs['Profile'].sv_get()
        v_min_s = self.inputs['AngleFrom'].sv_get()
        v_max_s = self.inputs['AngleTo'].sv_get()

        if isinstance(curve_s[0], SvCurve):
            curve_s = [curve_s]
        point_s = ensure_nesting_level(point_s, 3)
        direction_s = ensure_nesting_level(direction_s, 3)
        v_min_s = ensure_nesting_level(v_min_s, 2)
        v_max_s = ensure_nesting_level(v_max_s, 2)

        surface_out = []
        for curves, points, directions, v_mins, v_maxs in zip_long_repeat(curve_s, point_s, direction_s, v_min_s, v_max_s):
            for curve, point, direction, v_min, v_max in zip_long_repeat(curves, points, directions, v_mins, v_maxs):
                surface = SvRevolutionSurface(curve, np.array(point), np.array(direction))
                surface.v_bounds = (v_min, v_max)
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvRevolutionSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvRevolutionSurfaceNode)

