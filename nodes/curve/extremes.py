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
from sverchok.utils.field.scalar import SvScalarField
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.optimize import minimize_scalar

    def goal(curve, point_from):
        def distance(t):
            dv = curve.evaluate(t) - np.array(point_from)
            return np.linalg.norm(dv)
        return distance

    class SvExCurveExtremesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Curve Extremes
        Tooltip: Find a point on curve which provides the maximum or minimum for specified scalar field
        """
        bl_idname = 'SvExCurveExtremesNode'
        bl_label = 'Curve Extremes'
        bl_icon = 'OUTLINER_OB_EMPTY'

        samples : IntProperty(
            name = "Max Points",
            default = 1,
            min = 1,
            update = updateNode)

        directions = [
                ('MIN', "Min", "Find the minimum of the field", 0),
                ('MAX', "Max", "Find the maximum of the field", 1)
            ]

        direction : EnumProperty(
            name = "Direction",
            items = directions,
            default = 'MIN',
            update = updateNode)

        on_fail_options = [
                ('FAIL', "Fail", "Raise an exception (node becomes red)", 0),
                ('SKIP', "Skip", "Skip such interval or curve - just return an empty set of points", 1)
            ]

        on_fail : EnumProperty(
            name = "On fail",
            items = on_fail_options,
            default = 'FAIL',
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'direction', expand=True)

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            layout.prop(self, 'on_fail')
        
        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvScalarFieldSocket', "Field")
            self.inputs.new('SvStringsSocket', "MaxPoints").prop_name = 'samples'
            self.outputs.new('SvVerticesSocket', "Point")
            self.outputs.new('SvStringsSocket', "T")

        def solve(self, curve, field, samples):

            def goal(t):
                p = curve.evaluate(t)
                v = field.evaluate(p[0], p[1], p[2])
                if self.direction == 'MAX':
                    return -v
                else:
                    return v

            t_min, t_max = curve.get_u_bounds()
            tknots = np.linspace(t_min, t_max, num=samples+1)

            res_ts = []
            res_vs = []

            for t1, t2 in zip(tknots, tknots[1:]):
                guess = (t1+t2)/2.0
                result = minimize_scalar(goal,
                            bounds = (t1, t2),
                            bracket = (t1, t2),
                            method = 'Bounded')
                if result.success:
                    if t_min <= result.x <= t_max:
                        t = result.x
                        v = result.fun
                        res_vs.append(v)
                        res_ts.append(t)
                    else:
                        self.info("Found T: %s, but it is outside of %s - %s", result.x, t_min, t_max)
                else:
                    if self.on_fail == 'FAIL':
                        raise Exception(f"Can't find the extreme point for {curve} on {t1} - {t2}: {result.message}")

            if len(res_ts) == 0:
                if self.on_fail == 'FAIL':
                    raise Exception(f"Can't find the extreme point for {curve}: no candidate points")
                else:
                    return []
            else:
                target_v = min(res_vs)
                res_ts = [t for t,v in zip(res_ts, res_vs) if v == target_v]
                return res_ts

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curves_s = self.inputs['Curve'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
            fields_s = self.inputs['Field'].sv_get()
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
            samples_s = self.inputs['MaxPoints'].sv_get()
            samples_s = ensure_nesting_level(samples_s, 2)

            t_out = []
            point_out = []
            for curves, fields, samples_i in zip_long_repeat(curves_s, fields_s, samples_s):
                new_t = []
                new_points = []
                for curve, field, samples in zip_long_repeat(curves, fields, samples_i):
                    ts = self.solve(curve, field, samples)
                    ps = curve.evaluate_array(np.array(ts)).tolist()
                    new_t.extend(ts)
                    new_points.extend(ps)
                t_out.append(new_t)
                point_out.append(new_points)

            self.outputs['Point'].sv_set(point_out)
            self.outputs['T'].sv_set(t_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExCurveExtremesNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExCurveExtremesNode)

