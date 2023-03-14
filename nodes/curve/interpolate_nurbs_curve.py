
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.algorithms import curve_segment
from sverchok.utils.geom import Spline
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve.freecad import SvSolidEdgeCurve
from sverchok.dependencies import geomdl, FreeCAD

if FreeCAD is not None:
    import Part
    from Part import BSplineCurve
    from FreeCAD import Vector

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
            description = "Auto close the curve. \nIf used with Explicit Knots, an additional knot \nmust be appended to Knots list",
            default = False,
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['Degree'].hide_safe = not (self.implementation == 'GEOMDL' or self.implementation == 'NATIVE')
        self.inputs['Knots'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'explicit_knots')
        self.inputs['Tangents'].hide_safe = not (self.implementation == 'FREECAD' and self.use_constraints == True and self.constraints_mode == 'AllTangents')
        self.inputs['TangentsMask'].hide_safe = not (self.implementation == 'FREECAD' and self.use_constraints == True and self.constraints_mode == 'AllTangents')
        self.inputs['InitialTangent'].hide_safe = not (self.implementation == 'FREECAD' and self.use_constraints == True and self.constraints_mode == 'EndpointTangents')
        self.inputs['FinalTangent'].hide_safe = not (self.implementation == 'FREECAD' and self.use_constraints == True and self.constraints_mode == 'EndpointTangents')
        self.inputs['Tolerance'].hide_safe = not (self.implementation == 'FREECAD')
        updateNode(self, context)

    has_knots : BoolProperty(
            name = "Explicit Knots",
            description = "If disabled, Euclidean(Chord-Length) parametrization is used",
            default = False,
            update = update_sockets)

    has_tangents : BoolProperty(
            name = "Custom Tangents",
            description = "Define tangent vectors per point",
            default = False,
            update = update_sockets)

    has_tangents_mask : BoolProperty(
            name = "Custom Tangents Flags",
            description = "Activates or deactivates the corresponding tangent constraints",
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
            description = "Interpolation algorithm implementation",
            items = implementations,
            update = update_sockets)

    method: EnumProperty(
            name = 'Method',
            description = "Methods for calculating the knots",
            default = "parametrization",
            items = [("parametrization", "Parametrization", "Parametrize the init points using certain metric"),
                     ("explicit_knots", "Explicit Knots", "Explicitly specify the knots")
                    ],
            update = update_sockets)

    constraints_mode: EnumProperty(
            name = 'Mode',
            description = "Constraints Mode",
            default = "EndpointTangents",
            items = [("EndpointTangents", "Endpoint Tangents", "Set the tangents at the beginning and the end of the curve", 0),
                     ("AllTangents", "All Tangents", "Set a tangent vector for every single interpolation point", 1)
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

    scale : BoolProperty(
            name = "Autoscale Tangents",
            description = "Automatic scale of all active tangents",
            default = False,
            update = updateNode)

    use_constraints : BoolProperty(
            name = "Tangent Constraints",
            description = "Use tangent constraints",
            default = True,
            update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')
        if self.implementation == 'GEOMDL':
            layout.prop(self, 'centripetal')
        elif self.implementation == 'NATIVE':
            layout.prop(self, 'cyclic')
            layout.prop(self, 'metric')
        else: # FREECAD:
            layout.prop(self, 'cyclic')
            layout.prop(self, 'method')
            if self.method == 'parametrization':
                layout.prop(self, 'metric')
            else: # "Explicit Knots":
                pass
            row = layout.row(align = True)
            row.prop(self, 'use_constraints')
            if self.use_constraints:
                layout.prop(self, 'constraints_mode')
                layout.prop(self, 'scale')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvVerticesSocket', "Tangents")
        self.inputs.new('SvStringsSocket', "TangentsMask")
        self.inputs.new('SvVerticesSocket', "InitialTangent")
        self.inputs.new('SvVerticesSocket', "FinalTangent")
        self.inputs.new('SvStringsSocket', "Knots")
        self.inputs.new('SvVerticesSocket', "Vertices")
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
        tangents_mask_s = self.inputs['TangentsMask'].sv_get(default=[[[None]]])
        start_tangent_s = self.inputs['InitialTangent'].sv_get(default=[[[None]]])
        end_tangent_s = self.inputs['FinalTangent'].sv_get(default=[[[None]]])
        tolerance_s = self.inputs['Tolerance'].sv_get()

        tolerance_s = ensure_nesting_level(tolerance_s, 2)

        has_tangents = self.inputs['Tangents'].is_linked
        if has_tangents:
            tangents_s = ensure_nesting_level(tangents_s, 3)

        has_tangents_mask = self.inputs['TangentsMask'].is_linked
        if has_tangents_mask:
            tangents_mask_s = ensure_nesting_level(tangents_mask_s, 2)

        has_endpoint_tangents = (self.inputs['InitialTangent'].is_linked and self.inputs['FinalTangent'].is_linked)
        if has_endpoint_tangents:
            start_tangent = ensure_nesting_level(start_tangent_s, 3)
            end_tangent = ensure_nesting_level(end_tangent_s, 3)

        has_knots = self.inputs['Knots'].is_linked
        if has_knots:
            knots_s = ensure_nesting_level(knots_s, 2)

        curves_out = []
        points_out = []
        knots_out = []
        for vertices, degree, knots, tangents, tangents_mask, start_tangent, end_tangent, tolerance in zip_long_repeat(vertices_s, degree_s, knots_s, tangents_s, tangents_mask_s, start_tangent_s, end_tangent_s, tolerance_s):
            if isinstance(degree, (tuple, list)):
                degree = degree[0]
            if isinstance(tolerance, (tuple, list)):
                tolerance = tolerance[0]
            if isinstance(start_tangent, (tuple, list)):
                start_tangent = start_tangent[0]
            if isinstance(end_tangent, (tuple, list)):
                end_tangent = end_tangent[0]

            vertices = np.array(vertices)
            if self.implementation == 'GEOMDL':
                implementation = SvNurbsCurve.GEOMDL
                metric = 'CENTRIPETAL' if self.centripetal else 'DISTANCE'
                curve = SvNurbsMaths.interpolate_curve(implementation, degree, vertices, metric=metric, cyclic=self.cyclic, logger=self.sv_logger)
            elif self.implementation == 'FREECAD':
                if has_tangents == True: # create tangents flags
                    if has_tangents_mask == False: # generate auto mask
                        num_verts = len(vertices)
                        flags = [] # tangent flags
                        for i in range(num_verts):
                            if tangents[i] == (0.0, 0.0, 0.0): # handle zero-lenght tangents
                                flags.append(False)
                            else:
                                flags.append(True)
                    else:
                        flags = tangents_mask
                else:
                    pass
                bspline = Part.BSplineCurve()
                if self.method == 'parametrization':
                    num_verts = len(vertices)
                    distances = np.linalg.norm(vertices[:-1] - vertices[1:], axis=1) # point to point distances
                    sum_distances = sum(distances)
                    if self.cyclic == True: # we need one more knot
                        verts_ext = [] #verts extended list
                        for i in range(num_verts):
                            verts_ext.append(vertices[i])
                        verts_ext.append(vertices[0]) # add the first vertex at the end
                        verts = np.array(verts_ext)
                        tknots = Spline.create_knots(verts, metric = self.metric) # extended knots list
                        tknots = np.multiply(tknots, sum_distances) # scale knots to match OCCT
                    else: # Cyclic disabled:
                        tknots = Spline.create_knots(vertices, metric = self.metric)
                        tknots = np.multiply(tknots, sum_distances) # scale knots to match OCCT
                    if self.use_constraints == True and self.constraints_mode == 'AllTangents':
                        if has_tangents:
                            bspline.interpolate(Points = vertices,
                                                PeriodicFlag = self.cyclic,
                                                Tolerance = tolerance,
                                                Parameters = tknots,
                                                Tangents = tangents,
                                                TangentFlags = flags,
                                                Scale = self.scale
                                                )
                        else: # no tangents:
                            bspline.interpolate(Points = vertices,
                                                PeriodicFlag = self.cyclic,
                                                Tolerance = tolerance,
                                                Parameters = tknots
                                                )
                    elif self.use_constraints == True and self.constraints_mode == 'EndpointTangents':
                        if has_endpoint_tangents: # needs both the start and the end tangent
                            bspline.interpolate(Points = vertices,
                                                PeriodicFlag = self.cyclic,
                                                Tolerance = tolerance,
                                                Parameters = tknots,
                                                InitialTangent = Vector(start_tangent[0], start_tangent[1], start_tangent[2]),
                                                FinalTangent = Vector(end_tangent[0], end_tangent[1], end_tangent[2]),
                                                Scale = self.scale
                                                )
                        else: # one or both tangents not present:
                            bspline.interpolate(Points = vertices,
                                                PeriodicFlag = self.cyclic,
                                                Tolerance = tolerance,
                                                Parameters = tknots
                                                )
                    else: # self.use_constraints == False:
                        bspline.interpolate(Points = vertices,
                                            PeriodicFlag = self.cyclic,
                                            Tolerance = tolerance,
                                            Parameters = tknots
                                            )
                else: # Explicit Knots:
                    if self.use_constraints == True and self.constraints_mode == 'AllTangents':
                        if has_knots and has_tangents:
                            bspline.interpolate(Points = vertices,
                                                PeriodicFlag = self.cyclic,
                                                Tolerance = tolerance,
                                                Parameters = knots,
                                                Tangents = tangents,
                                                TangentFlags = flags,
                                                Scale = self.scale
                                                )
                        elif has_tangents and not (has_knots):
                            bspline.interpolate(Points = vertices,
                                                PeriodicFlag = self.cyclic,
                                                Tolerance = tolerance,
                                                Tangents = tangents,
                                                TangentFlags = flags,
                                                Scale = self.scale
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
                    elif self.use_constraints == True and self.constraints_mode == 'EndpointTangents':
                        if has_endpoint_tangents: # needs both the start and the end tangent
                            if has_knots == True:
                                bspline.interpolate(Points = vertices,
                                                    PeriodicFlag = self.cyclic,
                                                    Tolerance = tolerance,
                                                    Parameters = knots,
                                                    InitialTangent = Vector(start_tangent[0], start_tangent[1], start_tangent[2]),
                                                    FinalTangent = Vector(end_tangent[0], end_tangent[1], end_tangent[2]),
                                                    Scale = self.scale
                                                    )
                            else: # no linked knots:
                                bspline.interpolate(Points = vertices,
                                                    PeriodicFlag = self.cyclic,
                                                    Tolerance = tolerance,
                                                    InitialTangent = Vector(start_tangent[0], start_tangent[1], start_tangent[2]),
                                                    FinalTangent = Vector(end_tangent[0], end_tangent[1], end_tangent[2]),
                                                    Scale = self.scale
                                                    )
                        else: # one or both tangents not present:
                            if has_knots == True:
                                bspline.interpolate(Points = vertices,
                                                    PeriodicFlag = self.cyclic,
                                                    Tolerance = tolerance,
                                                    Parameters = knots
                                                    )
                            else: # no linked knots:
                                bspline.interpolate(Points = vertices,
                                                    PeriodicFlag = self.cyclic,
                                                    Tolerance = tolerance
                                                    )
                    else: # self.use_constraints == False:
                        if has_knots == True:
                             bspline.interpolate(Points = vertices,
                                                 PeriodicFlag = self.cyclic,
                                                 Parameters = knots,
                                                 Tolerance = tolerance
                                                )
                        else: # no linked knots:
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
                curve = SvNurbsMaths.interpolate_curve(implementation, degree, vertices, metric=metric, cyclic=self.cyclic, logger=self.sv_logger)

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

