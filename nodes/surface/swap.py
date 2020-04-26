import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface, SvSwapSurface

class SvSwapSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Swap Surface
    Tooltip: Swap U and V directions in the parametrization of the surface
    """
    bl_idname = 'SvSwapSurfaceNode'
    bl_label = 'Swap Surface U/V'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FLIP_CURVE'

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))

        surface_out = []
        for surfaces in surface_s:
            for surface in surfaces:
                new_surface = SvSwapSurface(surface)
                surface_out.append(new_surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvSwapSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvSwapSurfaceNode)

