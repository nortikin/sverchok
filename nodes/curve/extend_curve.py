
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvTaylorCurve, SvLine, SvCircle, SvCurveLengthSolver
from sverchok.utils.curve.algorithms import concatenate_curves, reverse_curve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.geom import circle_by_two_derivatives

class SvExtendCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extend Curve
    Tooltip: Smoothly extend a curve beyound it's range
    """
    bl_idname = 'SvExtendCurveNode'
    bl_label = 'Extend Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTEND_CURVE'

    t_before : FloatProperty(
        name = "Start extension",
        min = 0.0,
        default = 1.0,
        update = updateNode)

    t_after : FloatProperty(
        name = "End extension",
        min = 0.0,
        default = 1.0,
        update = updateNode)

    modes = [
        ('LINE', "1 - Line", "Straight line segment", 0),
        ('ARC', "1 - Arc", "Circular arc", 1),
        ('QUAD', "2 - Smooth - Normal", "Smooth curve", 2),
        ('CUBIC', "3 - Smooth - Curvature", "Smooth curve", 3)
    ]

    mode : EnumProperty(
        name = "Type",
        items = modes,
        default = 'LINE',
        update = updateNode)

    len_modes = [
        ('T', "Curve parameter", "Specify curve parameter extension", 0),
        ('L', "Curve length", "Specify curve length extension", 1)
    ]

    len_mode : EnumProperty(
        name = "Length mode",
        items = len_modes,
        default = 'T',
        update = updateNode)

    len_resolution : IntProperty(
        name = "Length resolution",
        default = 50,
        min = 3,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "StartExt").prop_name = 't_before'
        self.inputs.new('SvStringsSocket', "EndExt").prop_name = 't_after'
        self.outputs.new('SvCurveSocket', "ExtendedCurve")
        self.outputs.new('SvCurveSocket', "StartExtent")
        self.outputs.new('SvCurveSocket', "EndExtent")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text='')
        layout.label(text='Extend by:')
        layout.prop(self, "len_mode", text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.len_mode == 'L':
            layout.prop(self, 'len_resolution')

    def make_line(self, point, tangent, t_ext, sign):
        if sign < 0:
            before_start = point - t_ext*tangent # / np.linalg.norm(tangent_start)
            return SvLine.from_two_points(before_start, point)
        else:
            after_end = point + t_ext*tangent # / np.linalg.norm(tangent_end)
            return SvLine.from_two_points(point, after_end)

    def set_length(self, base_curve, curve, t_ext, sign=1):
        if curve is None:
            return None
        if self.len_mode == 'T':
            curve.u_bounds = (0, t_ext)
            if isinstance(curve, SvLine) and sign < 0:
                unit = curve.direction / np.linalg.norm(curve.direction)
                t_target = t_ext / np.linalg.norm(curve.direction)
                start = curve.point + curve.direction - t_ext*unit
                curve.point = start
                curve.u_bounds = (0, t_target)
        elif self.len_mode == 'L':
            if isinstance(curve, SvLine):
                if sign > 0:
                    curve.direction = curve.direction
                    t_ext = t_ext / np.linalg.norm(curve.direction)
                    curve.u_bounds = (0, t_ext)
                else:
                    unit = curve.direction / np.linalg.norm(curve.direction)
                    t_target = t_ext / np.linalg.norm(curve.direction)
                    start = curve.point + curve.direction - t_ext*unit
                    curve.point = start
                    curve.u_bounds = (0, t_target)
            else:
                u_min, u_max = base_curve.get_u_bounds()
                base_length = base_curve.calc_length(u_min, u_max, self.len_resolution)
                # base_length / (u_max - u_min) ~= t_ext / (t_target - 0)
                t_mid = t_ext * (u_max - u_min) / base_length
                #self.debug(f"Base curve len: {base_length}, range: {u_max - u_min}, T_ext {t_ext} => T_mid {t_mid}")
                curve.u_bounds = (0, t_mid)
                solver = SvCurveLengthSolver(curve)
                solver.prepare('SPL', self.len_resolution)
                t_target = solver.solve(np.array([t_ext]))[0]
                #self.debug(f"C: {type(curve)}: L = {t_mid} => T = {t_target}")
                curve.u_bounds = (0, t_target)
        return curve

    def extend_curve(self, curve, t_before, t_after):
        u_min, u_max = curve.get_u_bounds()
        start, end = curve.evaluate(u_min), curve.evaluate(u_max)
        start_extent, end_extent = None, None
        is_nurbs = isinstance(curve, SvNurbsCurve)

        if self.mode == 'LINE':
            tangent_start = curve.tangent(u_min)
            tangent_end = curve.tangent(u_max)

            if t_before > 0:
                start_extent = self.make_line(start, tangent_start, t_before, -1)
                start_extent = self.set_length(curve, start_extent, t_before, -1)
            if t_after > 0:
                end_extent = self.make_line(end, tangent_end, t_after, +1)
                end_extent = self.set_length(curve, end_extent, t_after, +1)

        elif self.mode == 'ARC':
            tangent_start = curve.tangent(u_min)
            tangent_end = curve.tangent(u_max)
            second_start = curve.second_derivative(u_min)
            second_end = curve.second_derivative(u_max)

            if t_before > 0:
                if np.linalg.norm(second_start) > 1e-6:
                    eq1 = circle_by_two_derivatives(start, -tangent_start, second_start)
                    start_extent = SvCircle.from_equation(eq1)
                    start_extent = self.set_length(curve, start_extent, t_before, -1)
                    if is_nurbs:
                        start_extent = start_extent.to_nurbs()
                    start_extent = reverse_curve(start_extent)
                else:
                    start_extent = self.make_line(start, tangent_start, t_before, -1)
                    start_extent = self.set_length(curve, start_extent, t_before, -1)

            if t_after > 0:
                if np.linalg.norm(second_end) > 1e-6:
                    eq2 = circle_by_two_derivatives(end, tangent_end, second_end)
                    end_extent = SvCircle.from_equation(eq2)
                else:
                    end_extent = self.make_line(end, tangent_end, t_after, +1)
                end_extent = self.set_length(curve, end_extent, t_after, +1)

        elif self.mode == 'QUAD':
            tangent_start = curve.tangent(u_min)
            tangent_end = curve.tangent(u_max)
            second_start = curve.second_derivative(u_min)
            second_end = curve.second_derivative(u_max)

            if t_before > 0:
                start_extent = SvTaylorCurve(start, [-tangent_start, second_start])
                start_extent = self.set_length(curve, start_extent, t_before)
                if is_nurbs:
                    start_extent = start_extent.to_nurbs()
                start_extent = reverse_curve(start_extent)

            if t_after > 0:
                end_extent = SvTaylorCurve(end, [tangent_end, second_end])
                end_extent = self.set_length(curve, end_extent, t_after)

        elif self.mode == 'CUBIC':
            tangent_start = curve.tangent(u_min)
            tangent_end = curve.tangent(u_max)
            second_start = curve.second_derivative(u_min)
            second_end = curve.second_derivative(u_max)
            third_start, third_end = curve.third_derivative_array(np.array([u_min, u_max]))

            if t_before > 0:
                start_extent = SvTaylorCurve(start, [-tangent_start, second_start, -third_start])
                start_extent = self.set_length(curve, start_extent, t_before)
                if is_nurbs:
                    start_extent = start_extent.to_nurbs()
                start_extent = reverse_curve(start_extent)
            if t_after > 0:
                end_extent = SvTaylorCurve(end, [tangent_end, second_end, third_end])
                end_extent = self.set_length(curve, end_extent, t_after)

        else:
            raise Exception("Unsupported mode")

        if is_nurbs:
            if start_extent is not None and not isinstance(start_extent, SvNurbsCurve):
                start_extent = start_extent.to_nurbs(implementation=curve.get_nurbs_implementation())
            if end_extent is not None and not isinstance(end_extent, SvNurbsCurve):
                end_extent = end_extent.to_nurbs(implementation=curve.get_nurbs_implementation())

        return start_extent, end_extent

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        t_before_s = self.inputs['StartExt'].sv_get()
        t_after_s = self.inputs['EndExt'].sv_get()

        t_before_s = ensure_nesting_level(t_before_s, 2)
        t_after_s = ensure_nesting_level(t_after_s, 2)
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))

        start_out = []
        end_out = []
        curve_out = []
        for curves, t_before_i, t_after_i in zip_long_repeat(curve_s, t_before_s, t_after_s):
            for curve, t_before, t_after in zip_long_repeat(curves, t_before_i, t_after_i):
                start_extent, end_extent = self.extend_curve(curve, t_before, t_after)
                start_out.append(start_extent)
                end_out.append(end_extent)
                curves = []
                if start_extent is not None:
                    curves.append(start_extent)
                curves.append(curve)
                if end_extent is not None:
                    curves.append(end_extent)
                new_curve = concatenate_curves(curves)
                curve_out.append(new_curve)

        self.outputs['StartExtent'].sv_set(start_out)
        self.outputs['EndExtent'].sv_set(end_out)
        self.outputs['ExtendedCurve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvExtendCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExtendCurveNode)

