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
from sverchok.utils.geom import Spline
from sverchok.utils.curve.nurbs import SvGeomdlCurve
from sverchok.utils.curve.splprep import scipy_nurbs_approximate
from sverchok.utils.curve.freecad import SvSolidEdgeCurve
from sverchok.dependencies import geomdl, scipy, FreeCAD

if geomdl is not None:
    from geomdl import fitting

if FreeCAD is not None:
    import Part
    from Part import BSplineCurve


class SvApproxNurbsCurveMk3Node(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Curve
    Tooltip: Approximate NURBS Curve
    """
    bl_idname = 'SvApproxNurbsCurveMk3Node'
    bl_label = 'Approximate NURBS Curve'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_APPROXIMATE_CURVE'
    sv_dependencies = {'geomdl', 'scipy', 'FreeCAD'}

    degree : IntProperty(
            name = "Degree",
            min = 1,
            default = 3,
            update = updateNode)

    centripetal : BoolProperty(
            name = "Centripetal",
            default = False,
            update = updateNode)

    metric: EnumProperty(
            name = 'Metric',
            description = "Knot mode",
            default = "DISTANCE", items=supported_metrics + xyz_metrics,
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['PointsCnt'].hide_safe = not (self.implementation == 'GEOMDL' and self.has_points_cnt)
        self.inputs['Degree'].hide_safe = not (self.implementation == 'GEOMDL' or self.implementation == 'SCIPY')

        self.inputs['Smoothing'].hide_safe = not (self.implementation == 'SCIPY' and self.has_smoothing)
        self.inputs['Weights'].hide_safe = not (self.implementation == 'SCIPY')

        self.inputs['Knots'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'explicit_knots')
        self.inputs['DegreeMin'].hide_safe = not (self.implementation == 'FREECAD')
        self.inputs['DegreeMax'].hide_safe = not (self.implementation == 'FREECAD')
        self.inputs['Tolerance'].hide_safe = not (self.implementation == 'FREECAD')
        self.inputs['LengthWeight'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'vari_smoothing')
        self.inputs['CurvatureWeight'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'vari_smoothing')
        self.inputs['TorsionWeight'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'vari_smoothing')

        updateNode(self, context)

    has_points_cnt : BoolProperty(
            name = "Specify points count",
            default = False,
            update = update_sockets)

    points_cnt : IntProperty(
            name = "Points count",
            min = 3, default = 5,
            update = updateNode)

    implementations = []
    if geomdl is not None:
        implementations.append(('GEOMDL', "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
    if scipy is not None:
        implementations.append(('SCIPY', "SciPy", "SciPy package implementation", 1))
    if FreeCAD is not None:
        implementations.append(('FREECAD', "FreeCAD", "FreeCAD package implementation", 2))

    implementation : EnumProperty(
            name = "Implementation",
            description = "Approximation algorithm implementation",
            items = implementations,
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

    method: EnumProperty(
            name = 'Method',
            description = "Approximation Method",
            default = "parametrization",
            items = [("parametrization", "Parametrization", "Parametrize the init points using certain metric"),
                     ("vari_smoothing", "Variational Smoothing", "Smoothing algorithm, which tries to minimize an additional criterium"),
                     ("explicit_knots", "Explicit Knots", "Explicitly specify the knots")
                    ],
        update = update_sockets)

    degree_min : IntProperty(
            name = "Minimal Degree",
            min = 1,
            default = 3,
            update = updateNode)

    degree_max : IntProperty(
            name = "Maximal Degree",
            min = 1,
            default = 5,
            update = updateNode)

    tolerance : FloatProperty(
            name = "Tolerance",
            description = "Maximal distance from the init points",
            default = 0.0001,
            precision = 6,
            min = 0.0,
            update = updateNode)

    continuity_p: EnumProperty( # method : Parametrization
        name = 'Continuity',
        description = "Internal Curve Continuity",
        default = "C2",
        items = [("C0", "C0", "Only positional continuity"),
                 ("G1", "G1", "Geometric tangent continuity"),
                 ("C1", "C1", "Continuity of the first derivative all along the Curve"),
                 ("G2", "G2", "Geometric curvature continuity"),
                 ("C2", "C2", "Continuity of the second derivative all along the Curve"),
                 ("C3", "C3", "Continuity of the third derivative all along the Curve"),
                 ("CN", "CN", "Infinite order of continuity")
                ],
        update = updateNode)

    continuity_s: EnumProperty( # method : Variational Smoothing
        name = 'Continuity',
        description = "Internal Curve Continuity",
        default = "C2",
        items = [("C0", "C0", "Only positional continuity"),
                 ("C1", "C1", "Continuity of the first derivative all along the Curve"),
                 ("C2", "C2", "Continuity of the second derivative all along the Curve")
                ],
        update = updateNode)

    length_weight : FloatProperty(
            name = "Length Weight",
            description = "Variational smoothing parameter",
            default = 1.0,
            precision = 6,
            min = 0.0,
            update = updateNode)

    curvature_weight : FloatProperty(
            name = "Curvature Weight",
            description = "Variational smoothing parameter",
            default = 1.0,
            precision = 6,
            min = 0.0,
            update = updateNode)

    torsion_weight : FloatProperty(
            name = "Torsion Weight",
            description = "Variational smoothing parameter",
            default = 1.0,
            precision = 6,
            min = 0.0,
            update = updateNode)

    param_type: EnumProperty(name='Metric',
        description = "Parametrization Metric",
        default = "ChordLength",
        items = [('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
                 ('ChordLength', 'Euclidean', "Also known as Chord-Length or Distance. Parameters of points are proportionate to distances between them", 1),
                 ('Uniform', 'Points', "Also known as Uniform. Parameters of points are distributed uniformly", 2),
                 ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance metric", 3),
                 ('Centripetal', 'Centripetal', "Parameters of points are proportionate to square roots of distances between them", 4),
                 ('X', "X Axis", "Distance along X axis", 5),
                 ('Y', "Y Axis", "Distance along Y axis", 6),
                 ('Z', "Z Axis", "Distance along Z axis", 7)
                 ],
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text = '')
        if self.implementation == 'GEOMDL':
            layout.prop(self, 'centripetal')
            layout.prop(self, 'has_points_cnt')
        elif self.implementation == 'SCIPY':
            row = layout.row(align = True)
            row.prop(self, 'is_cyclic')
            if self.is_cyclic:
                row.prop(self, 'auto_cyclic')
                if self.auto_cyclic:
                    layout.prop(self, 'cyclic_threshold')
            layout.prop(self, 'metric')
            layout.prop(self, 'has_smoothing')
        else:
            layout.prop(self, 'method')
            if self.method == 'parametrization':
                layout.prop(self, 'continuity_p')
                layout.prop(self, 'param_type')
            elif self.method == 'vari_smoothing':
                layout.prop(self, 'continuity_s')
            else: # "Explicit Knots":
                layout.prop(self, 'continuity_p')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.implementation == 'SCIPY':
            layout.prop(self, 'remove_doubles')
            if self.remove_doubles:
                layout.prop(self, 'threshold')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "LengthWeight").prop_name = 'length_weight'
        self.inputs.new('SvStringsSocket', "CurvatureWeight").prop_name = 'curvature_weight'
        self.inputs.new('SvStringsSocket', "TorsionWeight").prop_name = 'torsion_weight'
        self.inputs.new('SvStringsSocket', "Knots")
        
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Weights")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvStringsSocket', "PointsCnt").prop_name = 'points_cnt'
        self.inputs.new('SvStringsSocket', "Smoothing").prop_name = 'smoothing'

        self.inputs.new('SvStringsSocket', "DegreeMin").prop_name = 'degree_min'
        self.inputs.new('SvStringsSocket', "DegreeMax").prop_name = 'degree_max'
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'

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

        knots_s = self.inputs['Knots'].sv_get(default=[[[None]]])
        degree_min_s = self.inputs['DegreeMin'].sv_get()
        degree_max_s = self.inputs['DegreeMax'].sv_get()
        tolerance_s = self.inputs['Tolerance'].sv_get()
        length_weight_s = self.inputs['LengthWeight'].sv_get()
        curvature_weight_s = self.inputs['CurvatureWeight'].sv_get()
        torsion_weight_s = self.inputs['TorsionWeight'].sv_get()

        input_level = get_data_nesting_level(vertices_s)
        vertices_s = ensure_nesting_level(vertices_s, 4)
        degree_s = ensure_nesting_level(degree_s, 2)
        points_cnt_s = ensure_nesting_level(points_cnt_s, 2)
        smoothing_s = ensure_nesting_level(smoothing_s, 2)

        degree_min_s = ensure_nesting_level(degree_min_s, 2)
        degree_max_s = ensure_nesting_level(degree_max_s, 2)
        tolerance_s = ensure_nesting_level(tolerance_s, 2)
        length_weight_s = ensure_nesting_level(length_weight_s, 2)
        curvature_weight_s = ensure_nesting_level(curvature_weight_s, 2)
        torsion_weight_s = ensure_nesting_level(torsion_weight_s, 2)

        has_weights = self.inputs['Weights'].is_linked
        if has_weights:
            weights_s = ensure_nesting_level(weights_s, 3)

        has_knots = self.inputs['Knots'].is_linked
        if has_knots:
            knots_s = ensure_nesting_level(knots_s, 3)

        nested_output = input_level > 3

        curves_out = []
        points_out = []
        knots_out = []
        for params in zip_long_repeat(vertices_s, weights_s, knots_s, degree_s, points_cnt_s, smoothing_s, degree_min_s, degree_max_s, tolerance_s, length_weight_s, curvature_weight_s, torsion_weight_s):
            new_curves = []
            new_points = []
            new_knots = []
            for vertices, weights, knots, degree, points_cnt, smoothing, degree_min, degree_max, tolerance, length_weight, curvature_weight, torsion_weight in zip_long_repeat(*params):

                if self.implementation == 'GEOMDL':
                    kwargs = dict(centripetal = self.centripetal)
                    if self.has_points_cnt:
                        kwargs['ctrlpts_size'] = points_cnt

                    curve = fitting.approximate_curve(vertices, degree, **kwargs)
                    control_points = curve.ctrlpts
                    knotvector = curve.knotvector
                    curve = SvGeomdlCurve(curve)

                elif self.implementation == 'SCIPY':
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

                else: # FREECAD:
                    bspline = Part.BSplineCurve()
                    if self.method == 'parametrization':
                        if self.param_type == "ChordLength" or self.param_type == "Uniform" or self.param_type == "Centripetal": # use OCCT for metric calculations
                            bspline.approximate(Points = vertices,
                                                DegMin = degree_min,
                                                DegMax = degree_max,
                                                Tolerance = tolerance,
                                                Continuity = self.continuity_p,
                                                ParamType = self.param_type
                                                )
                        else: # Manhattan, Chebishev and XYZ metrics:
                            verts = np.array(vertices)
                            tknots = Spline.create_knots(verts, metric = self.param_type)
                            bspline.approximate(Points = vertices,
                                                DegMin = degree_min,
                                                DegMax = degree_max,
                                                Tolerance = tolerance,
                                                Continuity = self.continuity_p,
                                                Parameters = tknots
                                                )
                    elif self.method == 'explicit_knots':
                        if has_knots:
                            bspline.approximate(Points = vertices,
                                                Parameters = knots,
                                                DegMin = degree_min,
                                                DegMax = degree_max,
                                                Tolerance = tolerance,
                                                Continuity = self.continuity_p
                                                )
                        else:
                            bspline.approximate(Points = vertices,
                                                DegMin = degree_min,
                                                DegMax = degree_max,
                                                Tolerance = tolerance,
                                                Continuity = self.continuity_p
                                                )

                    else: # Variable Smoothing:
                        bspline.approximate(Points = vertices,
                                            DegMin = degree_min,
                                            DegMax = degree_max,
                                            Tolerance = tolerance,
                                            Continuity = self.continuity_s,
                                            LengthWeight = length_weight,
                                            CurvatureWeight = curvature_weight,
                                            TorsionWeight = torsion_weight
                                            )
                    curve = bspline.toShape()
                    curve = SvSolidEdgeCurve(curve)
                    curve = curve.to_nurbs()
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
    bpy.utils.register_class(SvApproxNurbsCurveMk3Node)


def unregister():
    bpy.utils.unregister_class(SvApproxNurbsCurveMk3Node)


