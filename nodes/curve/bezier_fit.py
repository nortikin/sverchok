
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvBezierCurve
from sverchok.utils.geom import linear_approximation, Spline
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.optimize import curve_fit

    def init_guess(verts, npoints):
        approx = linear_approximation(verts)
        line = approx.most_similar_line()
        projections = line.projection_of_points(verts)
        m = projections.min(axis=0)
        M = projections.max(axis=0)
        return np.linspace(m, M, num=npoints)

    def goal(ts, *xs):
        n3 = len(xs)
        n = n3 // 3
        control_points = np.array(xs).reshape((n,3))
        curve = SvBezierCurve(control_points)
        pts = curve.evaluate_array(ts)
        return np.ravel(pts)

    class SvExBezierCurveFitNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Bezier Curve Fit / Approximate
        Tooltip: Approximate points with Bezier curve
        """
        bl_idname = 'SvExBezierCurveFitNode'
        bl_label = 'Approximate Bezier Curve'
        bl_icon = 'CURVE_NCURVE'

        degree : IntProperty(
                name = "Degree",
                min = 2,
                default = 3,
                update = updateNode)

        metrics = [
            ('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
            ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
            ('POINTS', 'Points', "Points based", 2),
            ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

        metric: EnumProperty(name='Metric',
            description = "Knot mode",
            default="DISTANCE", items=metrics,
            update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
            self.outputs.new('SvCurveSocket', "Curve")
            self.outputs.new('SvVerticesSocket', "ControlPoints")

        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'metric')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            degree_s = self.inputs['Degree'].sv_get()

            vertices_s = ensure_nesting_level(vertices_s, 3)
            degree_s = ensure_nesting_level(degree_s, 2)

            curve_out = []
            points_out = []
            for vertices, degree in zip_long_repeat(vertices_s, degree_s):
                if isinstance(degree, (tuple, list)):
                    degree = degree[0]

                n = len(vertices)
                npoints = degree + 1
                vertices = np.array(vertices)

                #xdata = np.linspace(0, 1, num=n)
                xdata = Spline.create_knots(vertices, metric=self.metric)
                ydata = np.ravel(vertices)

                p0 = init_guess(vertices, npoints)
                popt, pcov = curve_fit(goal, xdata, ydata, p0)
                control_points = popt.reshape((npoints,3))
                curve = SvBezierCurve(control_points)
                curve_out.append(curve)
                points_out.append(control_points.tolist())

            self.outputs['Curve'].sv_set(curve_out)
            self.outputs['ControlPoints'].sv_set(points_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExBezierCurveFitNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExBezierCurveFitNode)

