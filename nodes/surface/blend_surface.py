# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvLine
from sverchok.utils.curve.algorithms import reverse_curve
from sverchok.utils.surface import SvSurface
from sverchok.utils.surface.algorithms import SvBlendSurface
from sverchok.utils.surface.gordon import nurbs_blend_surfaces

class SvBlendSurfaceNodeMk2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Blend / Fillet Surface
    Tooltip: Generate additional interface surface to blend two surfaces smoothly
    """
    bl_idname = 'SvBlendSurfaceNodeMk2'
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

    def update_sockets(self, context):
        self.inputs['UVCurve1'].hide_safe = self.curve1_mode != 'USER'
        self.inputs['UVCurve2'].hide_safe = self.curve2_mode != 'USER'
        self.inputs['Samples'].hide_safe = not self.use_nurbs
        updateNode(self, context)

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

    tangency_modes = [
            (SvBlendSurface.G1, "G1 - Tangency", "G1 tangency: match tangent vectors", 0),
            (SvBlendSurface.G2, "G2 - Curvature", "G2 tangency: match tangent vectors, normal vectors and curvature values", 1)
        ]

    tangency_mode : EnumProperty(
            name = "Smoothness",
            description = "How smooth the tangency should be",
            items = tangency_modes,
            update = updateNode)

    absolute_bulge : BoolProperty(
            name = "Absolute bulge",
            description = "If checked, then bulge values specified are actual required tangent vector lengths; otherwise, bulge values are specified as multipliers of surface's tangent vectors",
            default = True,
            update = updateNode)

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

    use_nurbs : BoolProperty(
            name = "NURBS",
            description = "Generate a NURBS surface",
            default = False,
            update = update_sockets)

    samples : IntProperty(
            name = "Samples",
            default = 10,
            min = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'tangency_mode')
        layout.prop(self, 'absolute_bulge')
        box = layout.row(align=True)
        box.prop(self, 'curve1_mode', text='')
        box.prop(self, 'flip1', toggle=True, text='Flip')
        box = layout.row(align=True)
        box.prop(self, 'curve2_mode', text='')
        box.prop(self, 'flip2', toggle=True, text='Flip')
        layout.prop(self, 'use_nurbs')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', 'Surface1')
        self.inputs.new('SvCurveSocket', 'UVCurve1')
        self.inputs.new('SvStringsSocket', 'Bulge1').prop_name = 'bulge1'
        self.inputs.new('SvSurfaceSocket', 'Surface2')
        self.inputs.new('SvCurveSocket', 'UVCurve2')
        self.inputs.new('SvStringsSocket', 'Bulge2').prop_name = 'bulge2'
        self.inputs.new('SvStringsSocket', 'Samples').prop_name = 'samples'
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
        samples_s = self.inputs['Samples'].sv_get()

        surface1_s = ensure_nesting_level(surface1_s, 2, data_types=(SvSurface,))
        if self.inputs['UVCurve1'].is_linked:
            uv_curve1_s = ensure_nesting_level(uv_curve1_s, 2, data_types=(SvCurve,))
        surface2_s = ensure_nesting_level(surface2_s, 2, data_types=(SvSurface,))
        if self.inputs['UVCurve2'].is_linked:
            uv_curve2_s = ensure_nesting_level(uv_curve2_s, 2, data_types=(SvCurve,))
        bulge1_s = ensure_nesting_level(bulge1_s, 2)
        bulge2_s = ensure_nesting_level(bulge2_s, 2)
        samples_s = ensure_nesting_level(samples_s, 2)

        surfaces_out = []
        for params in zip_long_repeat(surface1_s, uv_curve1_s, bulge1_s, surface2_s, uv_curve2_s, bulge2_s, samples_s):
            new_surfaces = []
            for surface1, curve1, bulge1, surface2, curve2, bulge2, samples in zip_long_repeat(*params):
                if self.curve1_mode != 'USER':
                    curve1 = self.make_uv_curve(surface1, self.curve1_mode, self.flip1)
                elif self.flip1:
                    curve1 = reverse_curve(curve1)
                if self.curve2_mode != 'USER':
                    curve2 = self.make_uv_curve(surface2, self.curve2_mode, self.flip2)
                elif self.flip2:
                    curve2 = reverse_curve(curve2)

                if self.use_nurbs:
                    surface = nurbs_blend_surfaces(surface1, surface2, curve1, curve2, bulge1, bulge2, 3, samples,
                                absolute_bulge = self.absolute_bulge,
                                tangency = self.tangency_mode,
                                logger = self.get_logger())
                else:
                    surface = SvBlendSurface(surface1, surface2, curve1, curve2, bulge1, bulge2,
                                absolute_bulge = self.absolute_bulge,
                                tangency = self.tangency_mode)
                new_surfaces.append(surface)
            surfaces_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvBlendSurfaceNodeMk2)

def unregister():
    bpy.utils.unregister_class(SvBlendSurfaceNodeMk2)

