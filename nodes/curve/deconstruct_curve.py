import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve

class SvDeconstructCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Deconstruct Curve
    Tooltip: Output degree, control points, weights, knot vector of the curve (when they are defined)
    """
    bl_idname = 'SvDeconstructCurveNode'
    bl_label = 'Deconstruct Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_FRAME'

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvStringsSocket', "Degree")
        self.outputs.new('SvStringsSocket', "KnotVector")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Weights")

    def deconstruct(self, curve):
        nurbs = SvNurbsCurve.to_nurbs(curve)
        if nurbs is None:
            nurbs = curve

        try:
            degree = nurbs.get_degree()
        except:
            degree = None

        if hasattr(nurbs, 'get_knotvector'):
            knots = nurbs.get_knotvector().tolist()
        else:
            knots = []

        try:
            points = nurbs.get_control_points().tolist()
        except:
            points = []

        if hasattr(nurbs, 'get_weights'):
            weights = nurbs.get_weights().tolist()
        else:
            weights = []

        return degree, knots, points, weights

    def make_edges(self, n):
        return [(i, i+1) for i in range(n-1)]

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        in_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))

        degree_out = []
        knots_out = []
        points_out = []
        edges_out = []
        weights_out = []

        for curves in curve_s:
            new_degrees = []
            new_knots = []
            new_points = []
            new_edges = []
            new_weights = []
            for curve in curves:
                degree, knots, points, weights = self.deconstruct(curve)
                edges = self.make_edges(len(points))
                new_degrees.append(degree)
                new_knots.append(knots)
                new_points.append(points)
                new_weights.append(weights)
                new_edges.append(edges)
            if in_level == 2:
                degree_out.append(new_degrees)
                knots_out.append(new_knots)
                points_out.append(new_points)
                weights_out.append(new_weights)
                edges_out.append(new_edges)
            else:
                degree_out.extend(new_degrees)
                knots_out.extend(new_knots)
                points_out.extend(new_points)
                weights_out.extend(new_weights)
                edges_out.extend(new_edges)

        self.outputs['Degree'].sv_set(degree_out)
        self.outputs['KnotVector'].sv_set(knots_out)
        self.outputs['ControlPoints'].sv_set(points_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Weights'].sv_set(weights_out)

def register():
    bpy.utils.register_class(SvDeconstructCurveNode)

def unregister():
    bpy.utils.unregister_class(SvDeconstructCurveNode)

