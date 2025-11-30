# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.manifolds import nurbs_curve_curvature_extremes, curve_curvature_maximum, curve_curvature_zero

class SvCurveCurvatureExtremesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curve Curvature Extremes
    Tooltip: Find points on curve where curvature is zero or maximum
    """
    bl_idname = 'SvCurveCurvatureExtremesNode'
    bl_label = 'Curve Curvature Extremes'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_EXTREMES'
    sv_dependencies = {'scipy'}

    samples : IntProperty(
        name = "Max Points",
        default = 10,
        min = 1,
        update = updateNode)

    use_nurbs : BoolProperty(
        name = "Use NURBS algorithm",
        default = False,
        update = updateNode)

    global_only : BoolProperty(
        name = "Global only",
        default = True,
        update = updateNode)

    find_zeros : BoolProperty(
        name = "Find zero curvature",
        default = True,
        update = updateNode)

    tolerance : FloatProperty(
        name = "Tolerance",
        precision = 8,
        default = 1e-6,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'global_only')
        layout.prop(self, 'use_nurbs')
        if not self.use_nurbs:
            layout.prop(self, 'samples')
        layout.prop(self, 'find_zeros')
        if self.find_zeros:
            layout.prop(self, 'tolerance')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvStringsSocket', "MinT")
        self.outputs.new('SvVerticesSocket', "MinPoints")
        self.outputs.new('SvStringsSocket', "MaxT")
        self.outputs.new('SvVerticesSocket', "MaxPoints")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        input_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        nested_output = input_level > 1
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

        need_max = self.outputs['MaxT'].is_linked or self.outputs['MaxPoints'].is_linked
        need_min = self.outputs['MinT'].is_linked or self.outputs['MinPoints'].is_linked

        if self.find_zeros:
            tolerance = self.tolerance
        else:
            tolerance = None

        min_t_out = []
        max_t_out = []
        min_points_out = []
        max_points_out = []
        for curves in curves_s:
            new_min_t = []
            new_max_t = []
            new_min_points = []
            new_max_points = []
            for curve in curves:
                nurbs_curve = SvNurbsCurve.to_nurbs(curve)
                if nurbs_curve is not None:
                    is_nurbs = True
                    curve = nurbs_curve
                else:
                    is_nurbs = False
                if self.use_nurbs and is_nurbs:
                    result = nurbs_curve_curvature_extremes(curve,
                                    global_only = self.global_only,
                                    need_maximum = need_max,
                                    need_minimum = need_min,
                                    min_tolerance = tolerance
                                )
                    if need_min:
                        ts = result['minimum']
                        points = curve.evaluate_array(ts)
                        new_min_t.append(ts.tolist())
                        new_min_points.append(points.tolist())
                    if need_max:
                        ts = result['maximum']
                        points = curve.evaluate_array(ts)
                        new_max_t.append(ts.tolist())
                        new_max_points.append(points.tolist())
                else:
                    if need_min:
                        ts = curve_curvature_zero(curve,
                                    init_samples = self.samples,
                                    global_only = self.global_only,
                                    tolerance = tolerance
                                )
                        points = curve.evaluate_array(ts)
                        new_min_t.append(ts.tolist())
                        new_min_points.append(points.tolist())
                    if need_max:
                        ts = curve_curvature_maximum(curve,
                                    init_samples = self.samples,
                                    global_only = self.global_only
                                )
                        points = curve.evaluate_array(ts)
                        new_max_t.append(ts.tolist())
                        new_max_points.append(points.tolist())

            if nested_output:
                min_t_out.append(new_min_t)
                max_t_out.append(new_max_t)
                min_points_out.append(new_min_points)
                max_points_out.append(new_max_points)
            else:
                min_t_out.extend(new_min_t)
                max_t_out.extend(new_max_t)
                min_points_out.extend(new_min_points)
                max_points_out.extend(new_max_points)

        self.outputs['MinT'].sv_set(min_t_out)
        self.outputs['MaxT'].sv_set(max_t_out)
        self.outputs['MinPoints'].sv_set(min_points_out)
        self.outputs['MaxPoints'].sv_set(max_points_out)

def register():
    bpy.utils.register_class(SvCurveCurvatureExtremesNode)

def unregister():
    bpy.utils.unregister_class(SvCurveCurvatureExtremesNode)

