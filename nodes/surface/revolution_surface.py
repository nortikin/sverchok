
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.curve import SvExCurve
from sverchok.utils.surface import SvExRevolutionSurface

class SvExRevolutionSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Revolution Surface
    Tooltip: Generate a surface of revolution (similar to Spin / Lathe modifier)
    """
    bl_idname = 'SvExRevolutionSurfaceNode'
    bl_label = 'Revolution Surface'
    bl_icon = 'MOD_SCREW'

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Profile").display_shape = 'DIAMOND'
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.prop = (0.0, 0.0, 1.0)
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point_s = self.inputs['Point'].sv_get()
        direction_s = self.inputs['Direction'].sv_get()
        curve_s = self.inputs['Profile'].sv_get()

        if isinstance(curve_s[0], SvExCurve):
            curve_s = [curve_s]
        point_s = ensure_nesting_level(point_s, 3)
        direction_s = ensure_nesting_level(direction_s, 3)

        surface_out = []
        for curves, points, directions in zip_long_repeat(curve_s, point_s, direction_s):
            for curve, point, direction in zip_long_repeat(curves, points, directions):
                surface = SvExRevolutionSurface(curve, np.array(point), np.array(direction))
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExRevolutionSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExRevolutionSurfaceNode)

