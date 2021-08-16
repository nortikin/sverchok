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
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level,\
    repeat_last_for_length
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve.nurbs import SvGeomdlCurve
from sverchok.utils.curve.splprep import scipy_nurbs_approximate
from sverchok.dependencies import geomdl, scipy
from sverchok.utils.dummy_nodes import add_dummy

if geomdl is None and scipy is None:
    add_dummy('SvApproxNurbsCurveMk2Node', "Approximate NURBS Curve", 'geomdl or scipy')

if geomdl is not None:
    from geomdl import fitting
    
class SvApproxNurbsCurveMk2Node(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Curve
    Tooltip: Approximate NURBS Curve
    """
    bl_idname = 'SvApproxNurbsCurveMk2Node'
    bl_label = 'Approximate NURBS Curve'
    bl_icon = 'CURVE_NCURVE'

    degree : IntProperty(
            name = "Degree",
            min = 1, max = 6,
            default = 3,
            update = updateNode)

    centripetal : BoolProperty(
            name = "Centripetal",
            default = False,
            update = updateNode)

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=supported_metrics + xyz_metrics,
        update=updateNode)

    def update_sockets(self, context):
        self.inputs['PointsCnt'].hide_safe = not (self.implementation == 'GEOMDL' and self.has_points_cnt)
        self.inputs['Smoothing'].hide_safe = not (self.implementation == 'SCIPY' and self.has_smoothing)
        self.inputs['Weights'].hide_safe = not (self.implementation == 'SCIPY')
        updateNode(self, context)

    has_points_cnt : BoolProperty(
            name = "Specify points count",
            default = False,
            update = update_sockets)

    points_cnt : IntProperty(
            name = "Points count",
            min = 3, default = 5,
            update = updateNode)

    def get_implementations(self, context):
        implementations = []
        if geomdl is not None:
            implementations.append(('GEOMDL', "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
        if scipy is not None:
            implementations.append(('SCIPY', "SciPy", "SciPy package implementation", 1))
        return implementations
    
    implementation : EnumProperty(name = "Implementation",
            description = "Approximation algorithm implementation",
            items = get_implementations,
            update = update_sockets)

    smoothing : FloatProperty(
            name = "Smoothing",
            description = "Smoothing factor. Set to 0 to do interpolation",
            min = 0.0,
            default = 0.1,
            update = updateNode)
    
    has_smoothing : BoolProperty(
            name = "Specify smoothing",
            default = False,
            update = update_sockets)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            description = "Make the curve cyclic (closed)",
            default = False,
            update = updateNode)

    auto_cyclic : BoolProperty(
            name = "Auto",
            description = "Make the curve cyclic only if it's start and end points are close enough",
            default = False,
            update = updateNode)

    cyclic_threshold : FloatProperty(
            name = "Cyclic threshold",
            description = "Maximum distance between start and end points to make the curve closed",
            default = 0.0,
            min = 0.0,
            precision = 4,
            update = updateNode)

    remove_doubles : BoolProperty(
            name = "Remove doubles",
            description = "Remove consecutive points that go too close",
            default = False,
            update = updateNode)

    threshold : FloatProperty(
            name = "Threshold",
            description = "Threshold for remove doubles function",
            default = 0.0001,
            precision = 5,
            min = 0.0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')
        if self.implementation == 'GEOMDL':
            layout.prop(self, 'centripetal')
            layout.prop(self, 'has_points_cnt')
        else:
            row = layout.row(align=True)
            row.prop(self, 'is_cyclic')
            if self.is_cyclic:
                row.prop(self, 'auto_cyclic')
                if self.auto_cyclic:
                    layout.prop(self, 'cyclic_threshold')
            layout.prop(self, 'metric')
            layout.prop(self, 'has_smoothing')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.implementation == 'SCIPY':
            layout.prop(self, 'remove_doubles')
            if self.remove_doubles:
                layout.prop(self, 'threshold')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Weights")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvStringsSocket', "PointsCnt").prop_name = 'points_cnt'
        self.inputs.new('SvStringsSocket', "Smoothing").prop_name = 'smoothing'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "Knots")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        weights_s = self.inputs['Weights'].sv_get(default=[[[None]]])
        degree_s = self.inputs['Degree'].sv_get()
        points_cnt_s = self.inputs['PointsCnt'].sv_get()
        smoothing_s = self.inputs['Smoothing'].sv_get()

        input_level = get_data_nesting_level(vertices_s)
        vertices_s = ensure_nesting_level(vertices_s, 4)
        degree_s = ensure_nesting_level(degree_s, 2)
        points_cnt_s = ensure_nesting_level(points_cnt_s, 2)
        smoothing_s = ensure_nesting_level(smoothing_s, 2)
        has_weights = self.inputs['Weights'].is_linked
        if has_weights:
            weights_s = ensure_nesting_level(weights_s, 3)

        nested_output = input_level > 3

        curves_out = []
        points_out = []
        knots_out = []
        for params in zip_long_repeat(vertices_s, weights_s, degree_s, points_cnt_s, smoothing_s):
            new_curves = []
            new_points = []
            new_knots = []
            for vertices, weights, degree, points_cnt, smoothing in zip_long_repeat(*params):

                if self.implementation == 'GEOMDL':
                    kwargs = dict(centripetal = self.centripetal)
                    if self.has_points_cnt:
                        kwargs['ctrlpts_size'] = points_cnt

                    curve = fitting.approximate_curve(vertices, degree, **kwargs)
                    control_points = curve.ctrlpts
                    knotvector = curve.knotvector
                    curve = SvGeomdlCurve(curve)
                else: # SCIPY:
                    points = np.array(vertices)
                    if has_weights:
                        weights = repeat_last_for_length(weights, len(vertices))
                    else:
                        weights = None
                    if not self.has_smoothing:
                        smoothing = None

                    if self.is_cyclic:
                        if self.auto_cyclic: 
                            dv = np.linalg.norm(points[0] - points[-1])
                            is_cyclic = dv <= self.cyclic_threshold
                            self.info("Dv %s, threshold %s => is_cyclic %s", dv, self.cyclic_threshold, is_cyclic)
                        else:
                            is_cyclic = True
                    else:
                        is_cyclic = False

                    curve = scipy_nurbs_approximate(points,
                                weights = weights,
                                metric = self.metric,
                                degree = degree,
                                filter_doubles = None if not self.remove_doubles else self.threshold,
                                smoothing = smoothing,
                                is_cyclic = is_cyclic)

                    control_points = curve.get_control_points().tolist()
                    knotvector = curve.get_knotvector().tolist()

                new_curves.append(curve)
                new_points.append(control_points)
                new_knots.append(knotvector)

            if nested_output:
                curves_out.append(new_curves)
                points_out.append(new_points)
                knots_out.append(new_knots)
            else:
                curves_out.extend(new_curves)
                points_out.extend(new_points)
                knots_out.extend(new_knots)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(points_out)
        self.outputs['Knots'].sv_set(knots_out)

def register():
    if geomdl is not None or scipy is not None:
        bpy.utils.register_class(SvApproxNurbsCurveMk2Node)

def unregister():
    if geomdl is not None or scipy is not None:
        bpy.utils.unregister_class(SvApproxNurbsCurveMk2Node)

