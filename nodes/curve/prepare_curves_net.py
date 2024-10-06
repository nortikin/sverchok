# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_solver_applications import adjust_curve_points
from sverchok.utils.manifolds import nearest_point_on_curve

class SvPrepareCurvesNetNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curves Net
    Tooltip: Adjust semi-intersecting curves in order to make a correct curves net
    """
    bl_idname = 'SvPrepareCurvesNetNode'
    bl_label = 'Prepare NURBS Curves Net'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INTERSECT_CURVES'
    sv_dependencies = {'scipy'}

    t_modes = [
            ('COUNT', "By Curves Count", "Use uniform T values distribution according to curves count", 0),
            ('EXPLICIT', "Explicit", "Use explicitly provided T values", 1),
            ('FIT', "Nearest", "Automatically find T values for nearest points", 2)
        ]

    bias_modes = [
            ('U', "Curve 1", "Curves along U direction are main, adjust curves along V direction", 0),
            ('V', "Curve 2", "Curves along V direction are main, adjust curves along U direction", 1)
        ]

    def update_sockets(self, context):
        self.inputs['T1'].hide_safe = self.u_mode != 'EXPLICIT'
        self.inputs['T2'].hide_safe = self.v_mode != 'EXPLICIT'
        updateNode(self, context)

    bias : EnumProperty(
            name = "Bias",
            items = bias_modes,
            default = 'U',
            update = updateNode)

    u_mode : EnumProperty(
            name = "T1 values",
            items = t_modes,
            default = 'COUNT',
            update = update_sockets)

    v_mode : EnumProperty(
            name = "T2 values",
            items = t_modes,
            default = 'COUNT',
            update = update_sockets)

    preserve_tangents : BoolProperty(
            name = "Preserve tangents",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'bias')
        layout.prop(self, 'u_mode')
        layout.prop(self, 'v_mode')

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

    def prepare_t_by_count(self, curves, n):
        bounds = np.array([c.get_u_bounds() for c in curves])
        ts_min = bounds[:,0]
        ts_max = bounds[:,1]
        t_values = np.linspace(ts_min, ts_max, num=n).T
        pts = [c.evaluate_array(t) for c, t in zip(curves, t_values)]
        pts = np.array(pts)
        return t_values, pts

    def prepare_t(self, mode, curves, t_values, n):
        if mode == 'EXPLICIT':
            target_pts = [c.evaluate_array(t) for c, t in zip(curves, t_values)]
            target_pts = np.array(target_pts)
        elif mode == 'COUNT':
            t_values, target_pts = self.prepare_t_by_count(curves, n)
        else: # FIT
            raise Exception("Can't fit T values for base curves")
        return t_values, target_pts

    def fit_t(self, primary_curves, primary_t_values, secondary_curves):
        primary_curve_pts = [c.evaluate_array(primary_t_values[i]) for i, c in enumerate(primary_curves)]
        primary_curve_pts = np.array(primary_curve_pts)
        secondary_t_values = [nearest_point_on_curve(primary_curve_pts[:,i], curve, samples=100, output_points=False) for i, curve in enumerate(secondary_curves)]
        secondary_t_values = np.array(secondary_t_values)
        return secondary_t_values

    def prepare_uv(self, u_curves, v_curves, u_values, v_values):
        if self.u_mode != 'FIT':
            u_values, u_pts = self.prepare_t(self.u_mode, u_curves, u_values, len(v_curves))
        else:
            u_values, u_pts = None, None
        if self.v_mode != 'FIT':
            v_values, v_pts = self.prepare_t(self.v_mode, v_curves, v_values, len(u_curves))
        else:
            v_values, v_pts = None, None
        if self.bias == 'U':
            return u_values, v_values, u_pts
        else:
            return u_values, v_values, v_pts

    def process_single(self, u_curves, v_curves, u_values, v_values):
        u_values, v_values, target_pts = self.prepare_uv(u_curves, v_curves, u_values, v_values)
        if self.u_mode == 'FIT' and self.v_mode != 'FIT':
            u_values = self.fit_t(v_curves, v_values, u_curves)
        elif self.u_mode != 'FIT' and self.v_mode == 'FIT':
            v_values = self.fit_t(u_curves, u_values, v_curves)
        if target_pts is None:
            if self.bias == 'U':
                target_pts = [c.evaluate_array(t) for c, t in zip(u_curves, u_values)]
            else:
                target_pts = [c.evaluate_array(t) for c, t in zip(v_curves, v_values)]
            target_pts = np.array(target_pts)

        if self.bias == 'U':
            new_u_curves = u_curves
            new_v_curves = []
            for i, v_curve in enumerate(v_curves):
                pts = target_pts[:,i]
                new_curve = adjust_curve_points(v_curve, v_values[i], pts,
                                                preserve_tangents = self.preserve_tangents)
                new_v_curves.append(new_curve)
        else:
            new_u_curves = []
            new_v_curves = v_curves
            for i, u_curve in enumerate(u_curves):
                pts = target_pts[:,i]
                new_curve = adjust_curve_points(u_curve, u_values[i], pts,
                                                preserve_tangents = self.preserve_tangents)
                new_u_curves.append(new_curve)
        if self.bias == 'U':
            target_pts = np.transpose(target_pts, axes=(1,0,2))
        return new_u_curves, new_v_curves, target_pts, u_values, v_values

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if self.u_mode == 'FIT' and self.v_mode == 'FIT':
            raise Exception("Automatic T values fitting can not be enabled for both directions")

        u_curves_s = self.inputs['Curve1'].sv_get()
        v_curves_s = self.inputs['Curve2'].sv_get()
        u_curves_s = ensure_nesting_level(u_curves_s, 3, data_types=(SvCurve,))
        v_curves_s = ensure_nesting_level(v_curves_s, 3, data_types=(SvCurve,))

        if self.u_mode == 'EXPLICIT':
            u_values_s = self.inputs['T1'].sv_get()
            u_values_s = ensure_nesting_level(u_values_s, 4)
        else:
            u_values_s = [[None]]
        if self.v_mode == 'EXPLICIT':
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
                u_curves, v_curves, pts, u_values, v_values = self.process_single(u_curves, v_curves, u_values, v_values)
                new_u_curves.append(u_curves)
                new_v_curves.append(v_curves)
                new_pts.append(pts)
                new_u_values.append(u_values)
                new_v_values.append(v_values)
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

