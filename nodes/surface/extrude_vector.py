
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.curve import SvCurve
from sverchok.utils.surface.algorithms import SvExtrudeCurveVectorSurface

class SvExtrudeCurveVectorNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude Curve
    Tooltip: Generate a surface by extruding a curve along a vector
    """
    bl_idname = 'SvExExtrudeCurveVectorNode'
    bl_label = 'Extrude Curve along Vector'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTRUDE_CURVE_VECTOR'

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Profile")
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vector_s = self.inputs['Vector'].sv_get()
        curve_s = self.inputs['Profile'].sv_get()

        if isinstance(curve_s[0], SvCurve):
            curve_s = [curve_s]
        vector_s = ensure_nesting_level(vector_s, 3)

        surface_out = []
        for curves, vectors in zip_long_repeat(curve_s, vector_s):
            for curve, vector in zip_long_repeat(curves, vectors):
                surface = SvExtrudeCurveVectorSurface.build(curve, vector)
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExtrudeCurveVectorNode)

def unregister():
    bpy.utils.unregister_class(SvExtrudeCurveVectorNode)

