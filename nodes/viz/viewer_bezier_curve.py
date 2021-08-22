# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from mathutils import Matrix, Vector
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Matrix_generate, match_long_repeat, updateNode, get_data_nesting_level, ensure_nesting_level, describe_data_shape, zip_long_repeat
from sverchok.utils.sv_obj_helper import SvObjHelper
from sverchok.utils.curve.core import SvCurve

def _split_points(vertices_s):
    result = []
    for vertices in vertices_s:
        out = []
        n = len(vertices)
        if n != 4 and n % 4 != 3:
            raise Exception("Invalid control points count")

        idx = 3
        points = vertices[:4]
        out.append(points)
        while idx + 3 < n:
            points = vertices[i : i+3]
            out.append(points)
            i += 3
        result.append(out)
    return result

def _split_nurbs(curves_s):
    result = []
    for curve in curves_s:
        if curve.get_degree() > 3:
            raise Exception("Only curves with degree <= 3 are supported")
        if curve.get_degree() < 3:
            curve = curve.elevate_degree(target=3)
        if not hasattr(curve, 'to_bezier_segments'):
            raise Exception("Curve can not be converted to a list of Bezier segments")
        segments = curve.to_bezier_segments()
        out = [segment.get_control_points().tolist() for segment in segments]
        result.append(out)
    return result

def _split_bezier(curves_s):
    result = []
    for segments in curves_s:
        out = []
        for segment in segments:
            if hasattr(segment, 'is_rational') and segment.is_rational():
                raise Exception("Rational curves are not supported")
            if segment.get_degree() > 3:
                raise Exception("Only curves with degree <= 3 are supported")
            if segment.get_degree() < 3:
                segment = segment.elevate_degree(target=3)

            pts = segment.get_control_points().tolist()
            out.append(pts)

        result.append(out)
    return result

class SvBezierCurveOutNode(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):
    """
    Triggers: Output Bezier Curve
    Tooltip: Create Blender's Bezier Curve object
    """

    bl_idname = 'SvBezierCurveOutNode'
    bl_label = 'Bezier Curve Out'
    bl_icon = 'CURVE_NCURVE'

    data_kind: StringProperty(default='CURVE')

    def update_sockets(self, context):
        self.inputs['ControlPoints'].hide_safe = self.input_mode not in ['SEGMENT_PTS', 'CURVE_PTS']
        self.inputs['Curve'].hide_safe = self.input_mode not in ['BEZIER', 'NURBS']

    input_modes = [
            ('SEGMENT_PTS', "Segment control points", "List of 4 control points for each Bezier segment", 0),
            ('CURVE_PTS', "Curve control points", "Single list of all (concatenated) splines", 1),
            ('BEZIER', "Bezier curve", "List of cubic Bezier Curve objects", 2),
            ('NURBS', "BSpline curve", "Non-rational NURBS (BSpline) curve object (made of several Bezier segments)", 3)
        ]

    input_mode : EnumProperty(
            name = "Input mode",
            items = input_modes,
            default = 'NURBS',
            update = update_sockets)

    def get_curve_name(self, index):
        return f'{self.basedata_name}.{index:04d}'

    def create_curve(self, index):
        object_name = self.get_curve_name(index)
        curve_data = bpy.data.curves.new(object_name, 'CURVE')
        curve_data.dimensions = '3D'
        curve_object = bpy.data.objects.get(object_name)
        if not curve_object:
            curve_object = self.create_object(object_name, index, curve_data)
        return curve_object

    def find_curve(self, index):
        object_name = self.get_curve_name(index)
        return bpy.data.objects.get(object_name)

    def draw_label(self):
        return f"Bezier Curve {self.basedata_name}"

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'ControlPoints')
        self.inputs.new('SvCurveSocket', 'Curve')
        self.outputs.new('SvObjectSocket', "Objects")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)
        layout.label(text="Input mode:")
        layout.prop(self, 'input_mode', text='')

    def process(self):
        if not self.activate:
            return

        if not self.inputs['ControlPoints'].is_linked and not self.inputs['Curve'].is_linked:
            return

        if self.inputs['ControlPoints'].is_linked:
            vertices_s = self.inputs['ControlPoints'].sv_get(default=[[]])
            if self.input_mode == 'SEGMENT_PTS':
                vertices_s = ensure_nesting_level(vertices_s, 4)
                control_points_s = vertices_s
            else:
                vertices_s = ensure_nesting_level(vertices_s, 3)
                control_points_s = _split_points(vertices_s)
        if self.inputs['Curve'].is_linked:
            curves_s = self.inputs['Curve'].sv_get(default=[[]])
            if self.input_mode == 'NURBS':
                curves_s = ensure_nesting_level(curves_s, 1, data_types=(SvCurve,))
                control_points_s = _split_nurbs(curves_s)
            elif self.input_mode == 'BEZIER':
                curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
                control_points_s = _split_bezier(curves_s)

        object_index = 0
        for control_points in control_points_s:
            object_index += 1

            curve_object = self.create_curve(object_index)
            self.debug("Object: %s", curve_object)
            if not curve_object:
                continue

            curve_object.data.splines.clear()
            spline = curve_object.data.splines.new(type='BEZIER')
            spline.bezier_points.add(len(control_points))

            first_point = start_point = spline.bezier_points[0]
            for idx, segment in enumerate(control_points):
                end_point = spline.bezier_points[idx+1]

                start_point.co = Vector(segment[0])
                start_point.handle_right = Vector(segment[1])

                end_point.handle_left = Vector(segment[2])
                end_point.co = Vector(segment[3])

                start_point = end_point

            first_point.handle_left = first_point.co
            end_point.handle_right = end_point.co


classes = [SvBezierCurveOutNode]
register, unregister = bpy.utils.register_classes_factory(classes)

