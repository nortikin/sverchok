
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve.nurbs import SvNurbsCurve, SvNativeNurbsCurve, SvGeomdlCurve
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.algorithms import curve_segment
from sverchok.utils.geom import Spline
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve.freecad import SvSolidEdgeCurve
from sverchok.dependencies import geomdl, FreeCAD

if FreeCAD is not None:
    import Part
    from Part import BSplineCurve

class SvExInterpolateNurbsCurveNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Curve interpolation
    Tooltip: Interpolate NURBS Curve
    """
    bl_idname = 'SvExInterpolateNurbsCurveNodeMK2'
    bl_label = 'Interpolate NURBS Curve'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_INTERPOLATE_CURVE'

    degree : IntProperty(
            name = "Degree",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    centripetal : BoolProperty(
            name = "Centripetal",
            description = "Metric used for parametrization",
            default = False,
            update = updateNode)

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE",
        items=supported_metrics + xyz_metrics,
        update=updateNode)

    cyclic : BoolProperty(
            name = "Cyclic",
            description = "Auto close the curve. \nIf used with Explicit Knots an additional knot \nmust be appended to Knots list",
            default = False,
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['Degree'].hide_safe = not (self.implementation == 'GEOMDL' or self.implementation == 'NATIVE')
        self.inputs['Knots'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'explicit_knots')
        self.inputs['Tangents'].hide_safe = not (self.implementation == 'FREECAD')
        self.inputs['Tolerance'].hide_safe = not (self.implementation == 'FREECAD')
        updateNode(self, context)

    has_knots : BoolProperty(
            name = "Explicit Knots",
            description = "If disabled, chord-length parametrization is used",
            default = False,
            update = update_sockets)

    has_tangents : BoolProperty(
            name = "Custom Tangents",
            description = "Define tangent vectors per point",
            default = False,
            update = update_sockets)

    implementations = []
    if geomdl is not None:
        implementations.append(('GEOMDL', "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
    implementations.append(('NATIVE', "Sverchok", "Sverchok built-in implementation", 1))
    if FreeCAD is not None:
        implementations.append(('FREECAD', "FreeCAD", "FreeCAD package implementation", 2))

    implementation : EnumProperty(
            name = "Implementation",
            description = "Approximation algorithm implementation",
            items = implementations,
            update = update_sockets)

    method: EnumProperty(
            name = 'Method',
            description = "Approximation Method",
            default = "parametrization",
            items = [("parametrization", "Parametrization", "Parametrize the init points using certain metric"),
                     ("explicit_knots", "Explicit Knots", "Explicitly specify the knots")
                    ],
            update = update_sockets)

    tolerance : FloatProperty(
            name = "Tolerance",
            description = "Maximal distance from the init points",
            min = 0.0,
            max = 1.0,
            default = 0.0,
            precision = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')
        if self.implementation == 'GEOMDL':
            layout.prop(self, 'centripetal')
        elif self.implementation == 'NATIVE':
            layout.prop(self, 'cyclic')
            layout.prop(self, 'metric')
        else: # FREECAD:
            layout.prop(self, 'method')
            if self.method == 'parametrization':
                layout.prop(self, 'metric')
            else: # "Explicit Knots":
                pass
            layout.prop(self, 'cyclic')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvStringsSocket', "Knots")
        self.inputs.new('SvStringsSocket', "Tangents")
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'

        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "Knots")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        degree_s = self.inputs['Degree'].sv_get()
        knots_s = self.inputs['Knots'].sv_get(default=[[[None]]])
        tangents_s = self.inputs['Tangents'].sv_get(default=[[[None]]])
        tolerance_s = self.inputs['Tolerance'].sv_get()
        
        tolerance_s = ensure_nesting_level(tolerance_s, 2)

        has_tangents = self.inputs['Tangents'].is_linked
        if has_tangents:
            tangents_s = ensure_nesting_level(tangents_s, 3)

        has_knots = self.inputs['Knots'].is_linked
        if has_knots:
            knots_s = ensure_nesting_level(knots_s, 2)

        curves_out = []
        points_out = []
        knots_out = []
        for vertices, degree, knots, tangents, tolerance in zip_long_repeat(vertices_s, degree_s, knots_s, tangents_s, tolerance_s):
            if isinstance(degree, (tuple, list)):
                degree = degree[0]
            if isinstance(tolerance, (tuple, list)):
                tolerance = tolerance[0]

            vertices = np.array(vertices)
            if self.implementation == 'GEOMDL':
                implementation = SvNurbsCurve.GEOMDL
                metric = 'CENTRIPETAL' if self.centripetal else 'DISTANCE'
                curve = SvNurbsMaths.interpolate_curve(implementation, degree, vertices, metric=metric, cyclic=self.cyclic, logger=self.get_logger())
            elif self.implementation == 'FREECAD':
                num_verts = len(vertices)
                flags = [] # tangent flags
                for i in range(num_verts):
                    flags.append(True)
                bspline = Part.BSplineCurve()
                if self.method == 'parametrization':
                    if self.cyclic == True:
                        verts_ext = [] #verts extended list
                        for i in range(num_verts):
                            verts_ext.append(vertices[i])
                        verts_ext.append(vertices[0]) # add the first vertex at the end
                        verts = np.array(verts_ext)
                        tknots = Spline.create_knots(verts, metric = self.metric) # extended knots list
                    else: # Cyclic disabled:
                        tknots = Spline.create_knots(vertices, metric = self.metric)
                    if has_tangents:
                        bspline.interpolate(Points = vertices,
                                            PeriodicFlag = self.cyclic,
                                            Tolerance = tolerance,
                                            Parameters = tknots,
                                            Tangents = tangents,
                                            TangentFlags = flags
                                            )
                    else: # no tangents:
                        bspline.interpolate(Points = vertices,
                                        PeriodicFlag = self.cyclic,
                                        Tolerance = tolerance,
                                        Parameters = tknots
                                        )
                else: # Explicit Knots:
                    if has_knots and has_tangents:
                        bspline.interpolate(Points = vertices,
                                            PeriodicFlag = self.cyclic,
                                            Tolerance = tolerance,
                                            Parameters = knots,
                                            Tangents = tangents,
                                            TangentFlags = flags
                                            )
                    elif has_tangents and not (has_knots):
                        bspline.interpolate(Points = vertices,
                                            PeriodicFlag = self.cyclic,
                                            Tolerance = tolerance,
                                            Tangents = tangents,
                                            TangentFlags = flags
                                            )
                    elif has_knots and not (has_tangents):
                        bspline.interpolate(Points = vertices,
                                            PeriodicFlag = self.cyclic,
                                            Tolerance = tolerance,
                                            Parameters = knots
                                            )
                    else: # no tangents and no knots:
                        bspline.interpolate(Points = vertices,
                                            PeriodicFlag = self.cyclic,
                                            Tolerance = tolerance
                                            )
                if self.cyclic == True: # rebuild OCCT Periodic B-Spline as compatible NURBS
                    cpoints = bspline.getPoles()
                    cpoints_ext = [] # control points extended list
                    for i in range(len(cpoints)):
                        cpoints_ext.append(cpoints[i])
                    cpoints_ext.extend([cpoints[0], cpoints[1]]) # wrapping over first and second control points
                    control_points = np.array(cpoints_ext)
                    weights_ext = bspline.getWeights()
                    weights_ext.extend([1.0, 1.0]) # extend weights list to match control points number
                    weights = np.array(weights_ext)
                    kv = np.array(bspline.KnotSequence) # original knotvector
                    kv_scale = [] # scaled knotvector
                    for i in range(len(kv)):
                        kv_scale.append(kv[i]/kv[-3])
                    knotvector = np.array(kv_scale)
                    curve_nurbs = SvNurbsMaths.build_curve(SvNurbsMaths.FREECAD,
                                                           bspline.Degree,
                                                           knotvector,
                                                           control_points,
                                                           weights
                                                           )
                    curve = curve_segment(curve_nurbs, 0.0, 1.0, use_native = True, rescale = False) # clamp the curve
                else: # not cyclic
                    curve = bspline.toShape()
                    curve = SvSolidEdgeCurve(curve)
                    curve = curve.to_nurbs()
            else: # NATIVE:
                implementation = SvNurbsCurve.NATIVE
                metric = self.metric
                curve = SvNurbsMaths.interpolate_curve(implementation, degree, vertices, metric=metric, cyclic=self.cyclic, logger=self.get_logger())

            points_out.append(curve.get_control_points().tolist())
            knots_out.append(curve.get_knotvector().tolist())
            curves_out.append(curve)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(points_out)
        self.outputs['Knots'].sv_set(knots_out)

def register():
    bpy.utils.register_class(SvExInterpolateNurbsCurveNodeMK2)

def unregister():
    bpy.utils.unregister_class(SvExInterpolateNurbsCurveNodeMK2)

