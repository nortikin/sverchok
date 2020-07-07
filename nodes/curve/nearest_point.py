import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix
from mathutils.kdtree import KDTree

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExNearestPointOnCurveNode', "Nearest Point on Curve", 'scipy')
else:
    from scipy.optimize import minimize_scalar

    def init_guess(curve, points_from, samples=50):
        u_min, u_max = curve.get_u_bounds()
        us = np.linspace(u_min, u_max, num=samples)

        points = curve.evaluate_array(us).tolist()

        kdt = KDTree(len(us))
        for i, v in enumerate(points):
            kdt.insert(v, i)
        kdt.balance()

        us_out = []
        nearest_out = []
        for point_from in points_from:
            nearest, i, distance = kdt.find(point_from)
            us_out.append(us[i])
            nearest_out.append(tuple(nearest))

        return us_out, nearest_out

    def goal(curve, point_from):
        def distance(t):
            dv = curve.evaluate(t) - np.array(point_from)
            return np.linalg.norm(dv)
        return distance

    class SvExNearestPointOnCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Nearest Point on Curve
        Tooltip: Find the point on the curve which is the nearest to the given point
        """
        bl_idname = 'SvExNearestPointOnCurveNode'
        bl_label = 'Nearest Point on Curve'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EVAL_SURFACE'

        samples : IntProperty(
            name = "Init Resolution",
            default = 50,
            min = 3,
            update = updateNode)
        
        precise : BoolProperty(
            name = "Precise",
            default = True,
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'samples')
            layout.prop(self, 'precise', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            p = self.inputs.new('SvVerticesSocket', "Point")
            p.use_prop = True
            p.prop = (0.0, 0.0, 0.0)
            self.outputs.new('SvVerticesSocket', "Point")
            self.outputs.new('SvStringsSocket', "T")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curves_s = self.inputs['Curve'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
            src_point_s = self.inputs['Point'].sv_get()
            src_point_s = ensure_nesting_level(src_point_s, 4)

            points_out = []
            t_out = []
            for curves, src_points_i in zip_long_repeat(curves_s, src_point_s):
                for curve, src_points in zip_long_repeat(curves, src_points_i):
                    t_min, t_max = curve.get_u_bounds()

                    new_t = []
                    new_points = []

                    init_ts, init_points = init_guess(curve, src_points,samples=self.samples)
                    for src_point, init_t, init_point in zip(src_points, init_ts, init_points):
                        if self.precise:
                            if init_t <= t_min:
                                bracket = (init_t - 0.1, init_t, t_max)
                            elif init_t >= t_max:
                                bracket = (t_min, init_t, init_t + 0.1)
                            else:
                                bracket = (t_min, init_t, t_max)
                            result = minimize_scalar(goal(curve, src_point),
                                        bounds = (t_min, t_max),
                                        bracket = bracket,
                                        method = 'Brent'
                                    )
                            if not result.success:
                                raise Exception("Can't find the nearest point for {}: {}".format(src_point, result.message))
                            t0 = result.x
                        else:
                            t0 = init_t
                            new_points.append(init_point)
                        new_t.append(t0)

                    if self.precise and self.outputs['Point'].is_linked:
                        new_points = curve.evaluate_array(np.array(new_t)).tolist()

                    points_out.append(new_points)
                    t_out.append(new_t)

                self.outputs['Point'].sv_set(points_out)
                self.outputs['T'].sv_set(t_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExNearestPointOnCurveNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExNearestPointOnCurveNode)

