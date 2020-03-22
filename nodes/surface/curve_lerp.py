
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok.utils.curve import SvExCurve
from sverchok.utils.surface import SvExCurveLerpSurface

class SvExCurveLerpNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Lerp Linear Surface
    Tooltip: Generate a linear surface between two curves (curves linear interpolation)
    """
    bl_idname = 'SvExCurveLerpNode'
    bl_label = 'Linear Surface'
    bl_icon = 'MOD_THICKNESS'

    v_min : FloatProperty(
        name = "V Min",
        default = 0.0,
        update = updateNode)

    v_max : FloatProperty(
        name = "V Max",
        default = 1.0,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Curve1").display_shape = 'DIAMOND'
        self.inputs.new('SvExCurveSocket', "Curve2").display_shape = 'DIAMOND'
        self.inputs.new('SvStringsSocket', "VMin").prop_name = 'v_min'
        self.inputs.new('SvStringsSocket', "VMax").prop_name = 'v_max'
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve1_s = self.inputs['Curve1'].sv_get()
        curve2_s = self.inputs['Curve2'].sv_get()
        vmin_s = self.inputs['VMin'].sv_get()
        vmax_s = self.inputs['VMax'].sv_get()

        vmin_s = ensure_nesting_level(vmin_s, 2)
        vmax_s = ensure_nesting_level(vmax_s, 2)

        if isinstance(curve1_s[0], SvExCurve):
            curve1_s = [curve1_s]
        if isinstance(curve2_s[0], SvExCurve):
            curve2_s = [curve2_s]

        surface_out = []
        for curve1s, curve2s, vmins, vmaxs in zip_long_repeat(curve1_s, curve2_s, vmin_s, vmax_s):
            for curve1, curve2, vmin, vmax in zip_long_repeat(curve1s, curve2s, vmins, vmaxs):
                surface = SvExCurveLerpSurface(curve1, curve2)
                surface.v_bounds = (vmin, vmax)
                surface_out.append(surface)
        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExCurveLerpNode)

def unregister():
    bpy.utils.unregister_class(SvExCurveLerpNode)

