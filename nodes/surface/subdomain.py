
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface, SvSurfaceSubdomain

class SvSurfaceSubdomainNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Subdomain (iso trim)
    Tooltip: Take a sub-domain of the surface - trim a surface along constant U/V curves.
    """
    bl_idname = 'SvExSurfaceSubdomainNode'
    bl_label = 'Surface Subdomain'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_SUBDOMAIN'

    u_min : FloatProperty(
        name = "U Min",
        default = 0.0,
        update = updateNode)

    v_min : FloatProperty(
        name = "V Min",
        default = 0.0,
        update = updateNode)


    u_max : FloatProperty(
        name = "U Max",
        default = 1.0,
        update = updateNode)

    v_max : FloatProperty(
        name = "V Max",
        default = 1.0,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvStringsSocket', "UMin").prop_name = 'u_min'
        self.inputs.new('SvStringsSocket', "UMax").prop_name = 'u_max'
        self.inputs.new('SvStringsSocket', "VMin").prop_name = 'v_min'
        self.inputs.new('SvStringsSocket', "VMax").prop_name = 'v_max'
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        u_min_s = self.inputs['UMin'].sv_get()
        u_max_s = self.inputs['UMax'].sv_get()
        v_min_s = self.inputs['VMin'].sv_get()
        v_max_s = self.inputs['VMax'].sv_get()

        u_min_s = ensure_nesting_level(u_min_s, 2)
        u_max_s = ensure_nesting_level(u_max_s, 2)
        v_min_s = ensure_nesting_level(v_min_s, 2)
        v_max_s = ensure_nesting_level(v_max_s, 2)

        if isinstance(surface_s[0], SvSurface):
            surface_s = [surface_s]

        surface_out = []
        for surfaces, u_mins, u_maxs, v_mins, v_maxs in zip_long_repeat(surface_s, u_min_s, u_max_s, v_min_s, v_max_s):
            for surface, u_min, u_max, v_min, v_max in zip_long_repeat(surfaces, u_mins, u_maxs, v_mins, v_maxs):
                new_surface = SvSurfaceSubdomain(surface, (u_min, u_max), (v_min, v_max))
                surface_out.append(new_surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvSurfaceSubdomainNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceSubdomainNode)

