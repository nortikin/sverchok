# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve

class SvCurveDiscontinuityNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curve Break Discontinuity
    Tooltip: Find points of curve discontinuity, and break curve into segments
    """
    bl_idname = 'SvCurveDiscontinuityNode'
    bl_label = 'NURBS Curve Discontinuity'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_DISCONTINUITY'

    def update_sockets(self, context):
        self.inputs['AmplitudeTolerance'].hide_safe = self.direction_only
        updateNode(self, context)

    order : IntProperty(
            name = "Order",
            description = "Discontinuity order",
            default = 1,
            min = 1, max = 3,
            update = updateNode)

    direction_only : BoolProperty(
            name = "Geometric",
            description = "If checked, check only direction of derivatives, not their lengths",
            default = True,
            update = update_sockets)

    angle_tolerance : FloatProperty(
            name = "AngleTolerance",
            precision = 8,
            default = 1e-6,
            min = 0.0,
            update = updateNode)

    amplitude_tolerance : FloatProperty(
            name = "AmplitudeTolerance",
            precision = 8,
            default = 1e-6,
            min = 0.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Order").prop_name = 'order'
        self.inputs.new('SvStringsSocket', "AngleTolerance").prop_name = 'angle_tolerance'
        self.inputs.new('SvStringsSocket', "AmplitudeTolerance").prop_name = 'amplitude_tolerance'
        self.outputs.new('SvCurveSocket', "Segments")
        self.outputs.new('SvVerticesSocket', "Points")
        self.outputs.new('SvStringsSocket', "T")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'direction_only')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        order_s = self.inputs['Order'].sv_get()
        angle_tolerance_s = self.inputs['AngleTolerance'].sv_get()
        amplitude_tolerance_s = self.inputs['AmplitudeTolerance'].sv_get()

        input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        flat_output = input_level < 2

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        order_s = ensure_nesting_level(order_s, 2)
        angle_tolerance_s = ensure_nesting_level(angle_tolerance_s, 2)
        amplitude_tolerance_s = ensure_nesting_level(amplitude_tolerance_s, 2)

        segments_out = []
        points_out = []
        t_out = []
        for params in zip_long_repeat(curve_s, order_s, angle_tolerance_s, amplitude_tolerance_s):
            new_segments = []
            new_points = []
            new_t = []
            for curve, order, angle_tolerance, amplitude_tolerance in zip_long_repeat(*params):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("One of curves is not NURBS!")
                ts, points, segments = curve.split_at_fracture_points(
                                        order = order,
                                        direction_only = self.direction_only,
                                        or_worse = True,
                                        angle_tolerance = angle_tolerance,
                                        amplitude_tolerance = amplitude_tolerance,
                                        return_details = True)
                new_t.append(ts)
                new_points.append(points)
                new_segments.append(segments)
            if flat_output:
                segments_out.extend(new_segments)
                points_out.extend(new_points)
                t_out.extend(new_t)
            else:
                segments_out.append(new_segments)
                points_out.append(new_points)
                t_out.append(new_t)

        self.outputs['Segments'].sv_set(segments_out)
        self.outputs['Points'].sv_set(points_out)
        self.outputs['T'].sv_set(t_out)

def register():
    bpy.utils.register_class(SvCurveDiscontinuityNode)

def unregister():
    bpy.utils.unregister_class(SvCurveDiscontinuityNode)

