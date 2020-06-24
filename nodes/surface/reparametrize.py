import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface, SvReparametrizedSurface

class SvReparametrizeSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Reparametrize Surface
    Tooltip: Change parametrization of the surface by linear mapping of U, V parameters to the new bounds
    """
    bl_idname = 'SvReparametrizeSurfaceNode'
    bl_label = 'Reparametrize Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FLIP_CURVE'

    new_u_min : FloatProperty(
            name = "New U Min",
            description = "New lower bound of surface's U parameter",
            default = 0.0,
            update = updateNode)

    new_u_max : FloatProperty(
            name = "New U Max",
            description = "New upper bound of surface's U parameter",
            default = 1.0,
            update = updateNode)

    new_v_min : FloatProperty(
            name = "New V Min",
            description = "New lower bound of surface's V parameter",
            default = 0.0,
            update = updateNode)

    new_v_max : FloatProperty(
            name = "New V Max",
            description = "New upper bound of surface's V parameter",
            default = 1.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvStringsSocket', "NewUMin").prop_name = 'new_u_min'
        self.inputs.new('SvStringsSocket', "NewUMax").prop_name = 'new_u_max'
        self.inputs.new('SvStringsSocket', "NewVMin").prop_name = 'new_v_min'
        self.inputs.new('SvStringsSocket', "NewVMax").prop_name = 'new_v_max'
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        umin_s = self.inputs['NewUMin'].sv_get()
        umax_s = self.inputs['NewUMax'].sv_get()
        vmin_s = self.inputs['NewVMin'].sv_get()
        vmax_s = self.inputs['NewVMax'].sv_get()

        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        umin_s = ensure_nesting_level(umin_s, 2)
        umax_s = ensure_nesting_level(umax_s, 2)
        vmin_s = ensure_nesting_level(vmin_s, 2)
        vmax_s = ensure_nesting_level(vmax_s, 2)

        surface_out = []
        for surfaces, umins, umaxs, vmins, vmaxs in zip_long_repeat(surface_s, umin_s, umax_s, vmin_s, vmax_s):
            new_surfaces = []
            for surface, u_min, u_max, v_min, v_max in zip_long_repeat(surfaces, umins, umaxs, vmins, vmaxs):
                new_surface = SvReparametrizedSurface(surface, u_min, u_max, v_min, v_max)
                new_surfaces.append(new_surface)
            surface_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvReparametrizeSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvReparametrizeSurfaceNode)

