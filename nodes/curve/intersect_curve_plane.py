
import bpy
from bpy.props import BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.geom import PlaneEquation
from sverchok.utils.manifolds import intersect_curve_plane, EQUATION, NURBS


class SvExCrossCurvePlaneNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Intersect Curve with Plane
    Tooltip: Intersect Curve with Plane
    """
    bl_idname = 'SvExCrossCurvePlaneNode'
    bl_label = 'Intersect Curve with Plane'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CROSS_CURVE_PLANE'
    sv_dependencies = {'scipy'}

    samples : IntProperty(
        name = "Init Resolution",
        description = "A number of segments to subdivide the curve in; defines the maximum number of intersection points that is possible to find.",
        default = 10,
        min = 1,
        update = updateNode)

    accuracy : IntProperty(
        name = "Accuracy",
        description = "Accuracy level - number of exact digits after decimal points.",
        default = 4,
        min = 1,
        update = updateNode)

    use_nurbs : BoolProperty(
        name = "Use NURBS algorithm",
        description = "Use special algorithm for NURBS curves",
        default = False,
        update = updateNode)

    join : BoolProperty(
        name = "Join",
        description = "If checked, output one list of points for all curves; otherwise, output a separate list of points for each curve",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'join')
        layout.prop(self, 'use_nurbs')
        layout.prop(self, 'samples')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        d = self.inputs.new('SvVerticesSocket', "Point")
        d.use_prop = True
        d.default_proerty = (0.0, 0.0, 0.0)
        d = self.inputs.new('SvVerticesSocket', "Normal")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 1.0)
        self.outputs.new('SvVerticesSocket', "Point")
        self.outputs.new('SvStringsSocket', "T")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        point_s = self.inputs['Point'].sv_get()
        normal_s = self.inputs['Normal'].sv_get()
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

        points_out = []
        t_out = []

        tolerance = 10**(-self.accuracy)

        for curves, points, normals in zip_long_repeat(curves_s, point_s, normal_s):
            new_points = []
            new_ts = []
            for curve, point, normal in zip_long_repeat(curves, points, normals):
                method = EQUATION
                if self.use_nurbs:
                    c = SvNurbsCurve.to_nurbs(curve)
                    if c is not None:
                        curve = c
                        method = NURBS

                plane = PlaneEquation.from_normal_and_point(normal, point)
                ps = intersect_curve_plane(curve, plane,
                        method = method,
                        init_samples = self.samples,
                        tolerance = tolerance,
                        logger = self.sv_logger)
                ts = [p[0] for p in ps]
                points = [p[1].tolist() for p in ps]

                if self.join:
                    new_points.extend(points)
                    new_ts.extend(ts)
                else:
                    new_points.append(points)
                    new_ts.append(ts)

            points_out.append(new_points)
            t_out.append(new_ts)

        self.outputs['Point'].sv_set(points_out)
        self.outputs['T'].sv_set(t_out)


def register():
    bpy.utils.register_class(SvExCrossCurvePlaneNode)


def unregister():
    bpy.utils.unregister_class(SvExCrossCurvePlaneNode)
