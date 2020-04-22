import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface, SvFlipSurface

class SvFlipSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Flip Surface
    Tooltip: Reverse parametrization of the curve along U and/or V direction
    """
    bl_idname = 'SvFlipSurfaceNode'
    bl_label = 'Flip Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FLIP_CURVE'

    modes = [
        ('UV', "UV", "Flip both U and V directions", 0),
        ('U', "U", "Flip U direction only", 1),
        ('V', "V", "Flip V direction only", 2)
    ]

    flip_mode : EnumProperty(
            name = "Flip",
            description = "Which directions of surface to flip",
            items = modes,
            default = 'UV',
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'flip_mode', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))

        flip_u = self.flip_mode in {'U', 'UV'}
        flip_v = self.flip_mode in {'V', 'UV'}
        
        surface_out = []
        for surfaces in surface_s:
            for surface in surfaces:
                new_surface = SvFlipSurface(surface, flip_u, flip_v)
                surface_out.append(new_surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvFlipSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvFlipSurfaceNode)

