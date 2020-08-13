
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface.algorithms import SvCurveLerpSurface

class SvCurveLerpNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Lerp Linear Ruled Surface
    Tooltip: Generate a ruled (linear) surface between two curves - a.k.a. curves linear interpolation
    """
    bl_idname = 'SvExCurveLerpNode'
    bl_label = 'Ruled Surface'
    bl_icon = 'MOD_THICKNESS'

    v_min : FloatProperty(
        name = "V Min",
        default = 0.0,
        update = updateNode)

    v_max : FloatProperty(
        name = "V Max",
        default = 1.0,
        update = updateNode)

    native : BoolProperty(
        name = "Native",
        description = "Try to use native ruled surface implementation when possible; for example, make a NURBS surafce from two NURBS curves",
        default = True,
        update = updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'native', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve1")
        self.inputs.new('SvCurveSocket', "Curve2")
        self.inputs.new('SvStringsSocket', "VMin").prop_name = 'v_min'
        self.inputs.new('SvStringsSocket', "VMax").prop_name = 'v_max'
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve1_s = self.inputs['Curve1'].sv_get()
        curve2_s = self.inputs['Curve2'].sv_get()
        vmin_s = self.inputs['VMin'].sv_get()
        vmax_s = self.inputs['VMax'].sv_get()

        vmin_s = ensure_nesting_level(vmin_s, 2)
        vmax_s = ensure_nesting_level(vmax_s, 2)

        if isinstance(curve1_s[0], SvCurve):
            curve1_s = [curve1_s]
        if isinstance(curve2_s[0], SvCurve):
            curve2_s = [curve2_s]

        surface_out = []
        for curve1s, curve2s, vmins, vmaxs in zip_long_repeat(curve1_s, curve2_s, vmin_s, vmax_s):
            for curve1, curve2, vmin, vmax in zip_long_repeat(curve1s, curve2s, vmins, vmaxs):
                if self.native:
                    surface = SvCurveLerpSurface.build(curve1, curve2, vmin, vmax)
                else:
                    surface = SvCurveLerpSurface(curve1, curve2)
                    surface.v_bounds = (vmin, vmax)
                surface_out.append(surface)
        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvCurveLerpNode)

def unregister():
    bpy.utils.unregister_class(SvCurveLerpNode)

