
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvCurveOffsetOnSurface
from sverchok.utils.surface import SvSurface

class SvCurveOffsetOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Offset Curve on Surface
    Tooltip: Offset a Curve along it's normal, while remaining in the surface
    """
    bl_idname = 'SvCurveOffsetOnSurfaceNode'
    bl_label = 'Offset Curve on Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_OFFSET'

    offset : FloatProperty(
            name = "Offset",
            default = 0.1,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvCurveSocket', "UVCurve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        surface_s = self.inputs['Surface'].sv_get()
        offset_s = self.inputs['Offset'].sv_get()

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        offset_s = ensure_nesting_level(offset_s, 2)

        curves_out = []
        uv_curves_out = []
        for curves, surfaces, offsets in zip_long_repeat(curve_s, surface_s, offset_s):
            new_curves = []
            new_uv_curves = []
            for curve, surface, offset in zip_long_repeat(curves, surfaces, offsets):
                new_curve = SvCurveOffsetOnSurface(curve, surface, offset, uv_space=False)
                new_uv_curve = SvCurveOffsetOnSurface(curve, surface, offset, uv_space=True)
                new_curves.append(new_curve)
                new_uv_curves.append(new_uv_curve)
            curves_out.append(new_curves)
            uv_curves_out.append(new_uv_curves)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['UVCurve'].sv_set(uv_curves_out)

def register():
    bpy.utils.register_class(SvCurveOffsetOnSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvCurveOffsetOnSurfaceNode)

