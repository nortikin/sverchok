
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvExSurface, SvExSurfaceLerpSurface

class SvExSurfaceLerpNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Lerp Linear
    Tooltip: Linear interpolation of two surfaces
    """
    bl_idname = 'SvExSurfaceLerpNode'
    bl_label = 'Surface Lerp'
    bl_icon = 'MOD_THICKNESS'

    coefficient : FloatProperty(
        name = "Coefficient",
        default = 0.5,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvExSurfaceSocket', "Surface1").display_shape = 'DIAMOND'
        self.inputs.new('SvExSurfaceSocket', "Surface2").display_shape = 'DIAMOND'
        self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface1_s = self.inputs['Surface1'].sv_get()
        surface2_s = self.inputs['Surface2'].sv_get()
        coeff_s = self.inputs['Coefficient'].sv_get()

        coeff_s = ensure_nesting_level(coeff_s, 2)

        if isinstance(surface1_s[0], SvExSurface):
            surface1_s = [surface1_s]
        if isinstance(surface2_s[0], SvExSurface):
            surface2_s = [surface2_s]

        surface_out = []
        for surface1s, surface2s, coeffs in zip_long_repeat(surface1_s, surface2_s, coeff_s):
            for surface1, surface2, coeff in zip_long_repeat(surface1s, surface2s, coeffs):
                new_surface = SvExSurfaceLerpSurface(surface1, surface2, coeff)
                surface_out.append(new_surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExSurfaceLerpNode)

def unregister():
    bpy.utils.unregister_class(SvExSurfaceLerpNode)

