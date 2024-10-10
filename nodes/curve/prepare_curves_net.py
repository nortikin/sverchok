# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.prepare_curves_net import prepare_curves_net, UNIFORM, FIT, EXPLICIT, PRIMARY_U, PRIMARY_V

class SvPrepareCurvesNetNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curves Net
    Tooltip: Adjust semi-intersecting curves in order to make a correct curves net
    """
    bl_idname = 'SvPrepareCurvesNetNode'
    bl_label = 'Prepare NURBS Curves Net'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_FROM_CURVES'
    sv_dependencies = {'scipy'}

    t_modes = [
            (UNIFORM, "Uniform", "Use uniform T values distribution according to curves count", 0),
            (FIT, "By Curves Location", "Automatically find T values for nearest points", 1),
            (EXPLICIT, "Explicit", "Use explicitly provided T values", 2)
        ]

    bias_modes = [
            (PRIMARY_U, "Curve 1", "Curves along U direction are main, adjust curves along V direction", 0),
            (PRIMARY_V, "Curve 2", "Curves along V direction are main, adjust curves along U direction", 1)
        ]

    def update_sockets(self, context):
        self.inputs['T1'].hide_safe = self.u_mode != EXPLICIT
        self.inputs['T2'].hide_safe = self.v_mode != EXPLICIT
        updateNode(self, context)

    bias : EnumProperty(
            name = "Bias",
            items = bias_modes,
            default = 'U',
            update = updateNode)

    u_mode : EnumProperty(
            name = "T1 values",
            items = t_modes,
            default = UNIFORM,
            update = update_sockets)

    v_mode : EnumProperty(
            name = "T2 values",
            items = t_modes,
            default = UNIFORM,
            update = update_sockets)

    preserve_tangents : BoolProperty(
            name = "Preserve tangents",
            default = False,
            update = updateNode)

    crop_u : BoolProperty(
            name = "Crop Curves 1",
            default = False,
            update = updateNode)

    crop_v : BoolProperty(
            name = "Crop Curves 2",
            default = False,
            update = updateNode)

    fit_samples : IntProperty(
            name = "Fit Samples",
            description = "Initial number of subdivisions for search of nearest points",
            default = 50,
            min = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Primary curves:')
        layout.prop(self, 'bias', text='')
        layout.label(text='Curve 1 parameters:')
        layout.prop(self, 'u_mode', text='')
        layout.label(text='Curve 2 parameters:')
        layout.prop(self, 'v_mode', text='')
        layout.prop(self, 'preserve_tangents')
        layout.prop(self, 'crop_u')
        layout.prop(self, 'crop_v')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'fit_samples')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve1")
        self.inputs.new('SvCurveSocket', "Curve2")
        self.inputs.new('SvStringsSocket', "T1")
        self.inputs.new('SvStringsSocket', "T2")
        self.outputs.new('SvCurveSocket', 'Curve1')
        self.outputs.new('SvCurveSocket', 'Curve2')
        self.outputs.new('SvVerticesSocket', 'Intersections')
        self.outputs.new('SvStringsSocket', 'T1')
        self.outputs.new('SvStringsSocket', 'T2')
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        u_curves_s = self.inputs['Curve1'].sv_get()
        v_curves_s = self.inputs['Curve2'].sv_get()
        input_level_u = get_data_nesting_level(u_curves_s, data_types=(SvCurve,))
        input_level_v = get_data_nesting_level(v_curves_s, data_types=(SvCurve,))
        flat_output = max(input_level_u, input_level_v) <= 2
        u_curves_s = ensure_nesting_level(u_curves_s, 3, data_types=(SvCurve,))
        v_curves_s = ensure_nesting_level(v_curves_s, 3, data_types=(SvCurve,))

        if self.u_mode == EXPLICIT:
            u_values_s = self.inputs['T1'].sv_get()
            u_values_s = ensure_nesting_level(u_values_s, 4)
        else:
            u_values_s = [[None]]
        if self.v_mode == EXPLICIT:
            v_values_s = self.inputs['T2'].sv_get()
            v_values_s = ensure_nesting_level(v_values_s, 4)
        else:
            v_values_s = [[None]]

        u_curves_out = []
        v_curves_out = []
        pts_out = []
        u_out = []
        v_out = []
        for params in zip_long_repeat(u_curves_s, v_curves_s, u_values_s, v_values_s):
            new_u_curves = []
            new_v_curves = []
            new_pts = []
            new_u_values = []
            new_v_values = []
            for u_curves, v_curves, u_values, v_values in zip_long_repeat(*params):
                u_curves = [SvNurbsCurve.to_nurbs(c) for c in u_curves]
                v_curves = [SvNurbsCurve.to_nurbs(c) for c in v_curves]
                if any(c is None for c in u_curves):
                    raise Exception("Some of U curves are not NURBS curves")
                if any(c is None for c in v_curves):
                    raise Exception("Some of V curves are not NURBS curves")
                res = prepare_curves_net(u_curves, v_curves,
                                         u_values, v_values,
                                         bias = self.bias,
                                         u_mode = self.u_mode,
                                         v_mode = self.v_mode,
                                         fit_samples = self.fit_samples,
                                         crop_u = self.crop_u, crop_v = self.crop_v,
                                         preserve_tangents = self.preserve_tangents)
                u_curves, v_curves, pts, u_values, v_values = res
                new_u_curves.append(u_curves)
                new_v_curves.append(v_curves)
                new_pts.append(pts)
                new_u_values.append(u_values.tolist())
                new_v_values.append(v_values.tolist())
            if flat_output:
                u_curves_out.extend(new_u_curves)
                v_curves_out.extend(new_v_curves)
                pts_out.extend(new_pts)
                u_out.extend(new_u_values)
                v_out.extend(new_v_values)
            else:
                u_curves_out.append(new_u_curves)
                v_curves_out.append(new_v_curves)
                pts_out.append(new_pts)
                u_out.append(new_u_values)
                v_out.append(new_v_values)

        self.outputs['Curve1'].sv_set(u_curves_out)
        self.outputs['Curve2'].sv_set(v_curves_out)
        self.outputs['Intersections'].sv_set(pts_out)
        self.outputs['T1'].sv_set(u_out)
        self.outputs['T2'].sv_set(v_out)

def register():
    bpy.utils.register_class(SvPrepareCurvesNetNode)


def unregister():
    bpy.utils.unregister_class(SvPrepareCurvesNetNode)

