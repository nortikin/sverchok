# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from mathutils import Matrix, Vector
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Matrix_generate, match_long_repeat, updateNode, get_data_nesting_level, ensure_nesting_level, describe_data_shape, zip_long_repeat, numpy_full_list
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

    bevel_radius : FloatProperty(
            name = "Radius",
            description = "Bevel radius",
            default = 0.0,
            update = updateNode)

    tilt : FloatProperty(
            name = "Tilt",
            default = 0.0,
            update = updateNode)

    caps: BoolProperty(
            update = updateNode,
            description="Seals the ends of a beveled curve")

    bevel_depth: FloatProperty(
            name = "Bevel depth",
            description = "Changes the size of the bevel",
            min = 0.0,
            default = 0.2,
            update = updateNode)

    taper_radius_modes = [
            ('OVERRIDE', "Override", "Override the radius of the spline point with the taper radius", 0),
            ('MULTIPLY', "Multiply", "Multiply the radius of the spline point by the taper radius", 1),
            ('ADD', "Add", "Add the radius of the bevel point to the taper radius", 2)
        ]

    taper_radius_mode : EnumProperty(
            name = "Taper radius mode",
            description = "Determine how the effective radius of the spline point is computed when a taper object is specified",
            items = taper_radius_modes,
            default = 'OVERRIDE',
            update = updateNode)

    resolution: IntProperty(
            name = "Bevel Resolution",
            description = "Alters the smoothness of the bevel",
            min = 0,
            default = 3,
            update = updateNode)

    preview_resolution_u: IntProperty(
            name = "Resolution Preview U",
            default = 12,
            min = 1,
            max = 64,
            update = updateNode,
            description = "The resolution property defines the number of points that are"
                          " computed between every pair of control points.")

    use_smooth: BoolProperty(
            name = "Smooth shading",
            update = updateNode,
            default = True)

    show_wire: BoolProperty(
            name = "Show Wire",
            default = False,
            update = updateNode)

    def get_curve_name(self, index):
        return f'{self.basedata_name}.{index:04d}'

    def create_curve(self, index, matrix=None, bevel=None, taper=None):
        object_name = self.get_curve_name(index)
        curve_data = bpy.data.curves.new(object_name, 'CURVE')
        curve_data.dimensions = '3D'
        curve_object = bpy.data.objects.get(object_name)
        if not curve_object:
            curve_object = self.create_object(object_name, index, curve_data)

        if matrix is not None:
            curve_object.matrix_local = matrix

        if bevel is not None:
            curve_object.data.bevel_mode = 'OBJECT'
            curve_object.data.bevel_object = bevel
        else:
            curve_object.data.bevel_mode = 'ROUND'

        if taper is not None:
            curve_object.data.taper_object = taper
        else:
            curve_object.data.taper_object = None

        curve_object.data.taper_radius_mode = self.taper_radius_mode

        curve_object.data.bevel_depth = self.bevel_depth
        curve_object.data.bevel_resolution = self.resolution
        curve_object.data.resolution_u = self.preview_resolution_u
        curve_object.data.use_fill_caps = self.caps
        curve_object.show_wire = self.show_wire

        if self.material_pointer:
            curve_object.data.materials.clear()
            curve_object.data.materials.append(self.material_pointer)

        return curve_object

    def create_spline(self, curve_object, control_points, radiuses=None, tilts=None):
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

        if radiuses is not None:
            spline.bezier_points.foreach_set('radius', numpy_full_list(radiuses, len(spline.bezier_points)))
        if tilts is not None:
            spline.bezier_points.foreach_set('tilt', numpy_full_list(tilts, len(spline.bezier_points)))

        spline.use_smooth = self.use_smooth

        return spline

    def find_curve(self, index):
        object_name = self.get_curve_name(index)
        return bpy.data.objects.get(object_name)

    def draw_label(self):
        return f"Bezier Curve {self.basedata_name}"

    def draw_bevel_object_props(self, socket, context, layout):
        row = layout.row(align=True)
        if not socket.is_linked:
            row.prop_search(socket, 'object_ref_pointer', bpy.data, 'objects',
                            text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        else:
            row.label(text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        row = row.row(align=True)
        row.ui_units_x = 0.6
        row.prop(self, 'caps', text='C', toggle=True)

    def draw_taper_object_props(self, socket, context, layout):
        row = layout.row(align=True)
        if not socket.is_linked:
            row.prop_search(socket, 'object_ref_pointer', bpy.data, 'objects',
                            text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        else:
            row.label(text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'ControlPoints')
        self.inputs.new('SvCurveSocket', 'Curve')
        self.inputs.new('SvMatrixSocket', 'Matrix')
        self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'bevel_radius'
        self.inputs.new('SvStringsSocket', 'Tilt').prop_name = 'tilt'

        obj_socket = self.inputs.new('SvObjectSocket', 'BevelObject')
        obj_socket.custom_draw = 'draw_bevel_object_props'
        obj_socket.object_kinds = "CURVE"

        obj_socket = self.inputs.new('SvObjectSocket', 'TaperObject')
        obj_socket.custom_draw = 'draw_taper_object_props'
        obj_socket.object_kinds = "CURVE"

        self.outputs.new('SvObjectSocket', "Objects")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)
        layout.prop(self, 'bevel_depth')

        layout.label(text="Input mode:")
        layout.prop(self, 'input_mode', text='')

    def draw_buttons_ext(self, context, layout):
        col = layout.column()
        col.prop(self, 'show_wire')
        col.prop(self, 'use_smooth')
        col.prop(self, "preview_resolution_u")
        col.prop(self, 'resolution')
        col.prop(self, 'taper_radius_mode')

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

        matrix_s = self.inputs['Matrix'].sv_get(deepcopy=False, default=[None])
        radius_s = self.inputs['Radius'].sv_get(deepcopy=False)
        tilt_s = self.inputs['Tilt'].sv_get(deepcopy=False)
        bevel_s = self.inputs['BevelObject'].sv_get(deepcopy=False, default=[None])
        taper_s = self.inputs['TaperObject'].sv_get(deepcopy=False, default=[None])

        objects_out = []
        object_index = 0
        for matrix, control_points, radiuses, tilts, bevel, taper in zip_long_repeat(matrix_s, control_points_s, radius_s, tilt_s, bevel_s, taper_s):
            object_index += 1

            curve_object = self.create_curve(object_index, matrix, bevel, taper)
            self.debug("Object: %s", curve_object)
            if not curve_object:
                continue
            self.create_spline(curve_object, control_points, radiuses, tilts)

            objects_out.append(curve_object)

        self.outputs['Objects'].sv_set(objects_out)

classes = [SvBezierCurveOutNode]
register, unregister = bpy.utils.register_classes_factory(classes)

