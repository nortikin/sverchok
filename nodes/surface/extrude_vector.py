
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.curve import SvExCurve
from sverchok.utils.surface import SvExExtrudeCurveVectorSurface

class SvExExtrudeCurveVectorNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude Curve
    Tooltip: Generate a surface by extruding a curve along a vector
    """
    bl_idname = 'SvExExtrudeCurveVectorNode'
    bl_label = 'Extrude Curve along Vector'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTRUDE_CURVE_VECTOR'

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Profile").display_shape = 'DIAMOND'
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vector_s = self.inputs['Vector'].sv_get()
        curve_s = self.inputs['Profile'].sv_get()

        if isinstance(curve_s[0], SvExCurve):
            curve_s = [curve_s]
        vector_s = ensure_nesting_level(vector_s, 3)

        surface_out = []
        for curves, vectors in zip_long_repeat(curve_s, vector_s):
            for curve, vector in zip_long_repeat(curves, vectors):
                surface = SvExExtrudeCurveVectorSurface(curve, vector)
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExExtrudeCurveVectorNode)

def unregister():
    bpy.utils.unregister_class(SvExExtrudeCurveVectorNode)

