# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvLine
from sverchok.utils.curve.algorithms import reverse_curve
from sverchok.utils.surface import SvSurface
from sverchok.utils.surface.algorithms import SvBlendSurface

class SvBlendSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Blend / Fillet Surface
    Tooltip: Generate additional interface surface to blend two surfaces smoothly
    """
    bl_idname = 'SvBlendSurfaceNode'
    bl_label = 'Blend Surfaces'
    bl_icon = 'SURFACE_DATA'
    sv_icon = 'SV_BLEND_SURFACE'

    curve_options = [
            ('UMIN', "Min U", "Use surface edge with minimal U parameter value", 0),
            ('UMAX', "Max U", "Use surface edge with maximal U parameter value", 1),
            ('VMIN', "Min V", "Use surface edge with minimal V parameter value", 2),
            ('VMAX', "Max V", "Use surface edge with maximal V parameter value", 3),
            ('USER', "Custom", "Use user-defined curve in surface's U/V space", 4)
        ]

    @throttled
    def update_sockets(self, context):
        self.inputs['UVCurve1'].hide_safe = self.curve1_mode != 'USER'
        self.inputs['UVCurve2'].hide_safe = self.curve2_mode != 'USER'

    curve1_mode : EnumProperty(
            name = "Curve 1",
            description = "What curve on the first surface to use",
            items = curve_options,
            default = 'UMIN',
            update = update_sockets)

    curve2_mode : EnumProperty(
            name = "Curve 2",
            description = "What curve on the second surface to use",
            items = curve_options,
            default = 'UMIN',
            update = update_sockets)

    bulge1 : FloatProperty(
            name = "Bulge1",
            description = "Bulge factor for the first surface; set to negative value to bulge in another direction",
            default = 1.0, 
            update = updateNode)

    bulge2 : FloatProperty(
            name = "Bulge2",
            description = "Bulge factor for the second surface; set to negative value to bulge in another direction",
            default = 1.0,
            update = updateNode)

    flip1 : BoolProperty(
            name = "Flip Curve 1",
            description = "Reverse direction of the first curve",
            default = False,
            update = updateNode)

    flip2 : BoolProperty(
            name = "Flip Curve 2",
            description = "Reverse direction of the second curve",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        box = layout.row(align=True)
        box.prop(self, 'curve1_mode', text='')
        box.prop(self, 'flip1', toggle=True, text='Flip')
        box = layout.row(align=True)
        box.prop(self, 'curve2_mode', text='')
        box.prop(self, 'flip2', toggle=True, text='Flip')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', 'Surface1')
        self.inputs.new('SvCurveSocket', 'UVCurve1')
        self.inputs.new('SvStringsSocket', 'Bulge1').prop_name = 'bulge1'
        self.inputs.new('SvSurfaceSocket', 'Surface2')
        self.inputs.new('SvCurveSocket', 'UVCurve2')
        self.inputs.new('SvStringsSocket', 'Bulge2').prop_name = 'bulge2'
        self.outputs.new('SvSurfaceSocket', 'Surface')
        self.update_sockets(context)

    def make_uv_curve(self, surface, mode, flip):
        u_min, u_max = surface.get_u_min(), surface.get_u_max()
        v_min, v_max = surface.get_v_min(), surface.get_v_max()

        if mode == 'UMIN':
            u1 = u2 = u_min
            v1, v2 = v_min, v_max
        elif mode == 'UMAX':
            u1 = u2 = u_max
            v1, v2 = v_min, v_max
        elif mode == 'VMIN':
            u1, u2 = u_min, u_max
            v1 = v2 = v_min
        elif mode == 'VMAX':
            u1, u2 = u_min, u_max
            v1 = v2 = v_max
        else:
            raise Exception("unknown mode")

        p1 = (u1, v1, 0)
        p2 = (u2, v2, 0)
        if flip:
            curve = SvLine.from_two_points(p2, p1)
        else:
            curve = SvLine.from_two_points(p1, p2)
        return curve

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface1_s = self.inputs['Surface1'].sv_get()
        surface2_s = self.inputs['Surface2'].sv_get()
        uv_curve1_s = self.inputs['UVCurve1'].sv_get(default=[[None]])
        uv_curve2_s = self.inputs['UVCurve2'].sv_get(default=[[None]])
        bulge1_s = self.inputs['Bulge1'].sv_get()
        bulge2_s = self.inputs['Bulge2'].sv_get()

        surface1_s = ensure_nesting_level(surface1_s, 2, data_types=(SvSurface,))
        if self.inputs['UVCurve1'].is_linked:
            uv_curve1_s = ensure_nesting_level(uv_curve1_s, 2, data_types=(SvCurve,))
        surface2_s = ensure_nesting_level(surface2_s, 2, data_types=(SvSurface,))
        if self.inputs['UVCurve2'].is_linked:
            uv_curve2_s = ensure_nesting_level(uv_curve2_s, 2, data_types=(SvCurve,))
        bulge1_s = ensure_nesting_level(bulge1_s, 2)
        bulge2_s = ensure_nesting_level(bulge2_s, 2)

        surfaces_out = []
        for surface1_i, curve1_i, bulge1_i, surface2_i, curve2_i, bulge2_i in zip_long_repeat(surface1_s, uv_curve1_s, bulge1_s, surface2_s, uv_curve2_s, bulge2_s):
            new_surfaces = []
            for surface1, curve1, bulge1, surface2, curve2, bulge2 in zip_long_repeat(surface1_i, curve1_i, bulge1_i, surface2_i, curve2_i, bulge2_i):
                if self.curve1_mode != 'USER':
                    curve1 = self.make_uv_curve(surface1, self.curve1_mode, self.flip1)
                elif self.flip1:
                    curve1 = reverse_curve(curve1)
                if self.curve2_mode != 'USER':
                    curve2 = self.make_uv_curve(surface2, self.curve2_mode, self.flip2)
                elif self.flip2:
                    curve2 = reverse_curve(curve2)

                surface = SvBlendSurface(surface1, surface2, curve1, curve2, bulge1, bulge2)
                new_surfaces.append(surface)
            surfaces_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvBlendSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvBlendSurfaceNode)

