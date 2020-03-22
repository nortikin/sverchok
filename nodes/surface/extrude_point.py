
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.curve import SvExCurve
from sverchok.utils.surface import SvExExtrudeCurvePointSurface

class SvExExtrudeCurvePointNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude Curve to Point
    Tooltip: Generate a (conic) surface by extruding a curve towards a point
    """
    bl_idname = 'SvExExtrudeCurvePointNode'
    bl_label = 'Extrude to Point'
    bl_icon = 'MOD_THICKNESS'

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Profile").display_shape = 'DIAMOND'
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point_s = self.inputs['Point'].sv_get()
        curve_s = self.inputs['Profile'].sv_get()

        if isinstance(curve_s[0], SvExCurve):
            curve_s = [curve_s]
        point_s = ensure_nesting_level(point_s, 3)

        surface_out = []
        for curves, points in zip_long_repeat(curve_s, point_s):
            for curve, point in zip_long_repeat(curves, points):
                surface = SvExExtrudeCurvePointSurface(curve, np.array(point))
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExExtrudeCurvePointNode)

def unregister():
    bpy.utils.unregister_class(SvExExtrudeCurvePointNode)

