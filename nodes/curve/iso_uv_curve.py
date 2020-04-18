
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvIsoUvCurve
from sverchok.utils.surface import SvSurface

class SvIsoUvCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Iso UV Curve
    Tooltip: Generate a curve which is characterized by constant value of U or V parameter in surface's UV space
    """
    bl_idname = 'SvExIsoUvCurveNode'
    bl_label = 'Iso U/V Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_UV_ISO_CURVE'

    value : FloatProperty(
        name = "Value",
        default = 0.5,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'value'
        self.outputs.new('SvCurveSocket', "UCurve")
        self.outputs.new('SvCurveSocket', "VCurve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        value_s = self.inputs['Value'].sv_get()

        if isinstance(surface_s[0], SvSurface):
            surface_s = [surface_s]
        value_s = ensure_nesting_level(value_s, 2)

        u_curves_out = []
        v_curves_out = []
        for surfaces, values in zip_long_repeat(surface_s, value_s):
            for surface, value in zip_long_repeat(surfaces, values):
                u_curve = SvIsoUvCurve(surface, 'V', value)
                v_curve = SvIsoUvCurve(surface, 'U', value)
                u_curves_out.append(u_curve)
                v_curves_out.append(v_curve)

        self.outputs['UCurve'].sv_set(u_curves_out)
        self.outputs['VCurve'].sv_set(v_curves_out)

def register():
    bpy.utils.register_class(SvIsoUvCurveNode)

def unregister():
    bpy.utils.unregister_class(SvIsoUvCurveNode)

