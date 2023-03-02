import numpy as np

import bpy
from bpy.props import EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.manifolds import curve_extremes


def goal(curve, point_from):
    def distance(t):
        dv = curve.evaluate(t) - np.array(point_from)
        return np.linalg.norm(dv)
    return distance


class SvExCurveExtremesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curve Extremes
    Tooltip: Find a point on curve which provides the maximum or minimum for specified scalar field
    """
    bl_idname = 'SvExCurveExtremesNode'
    bl_label = 'Curve Extremes'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_EXTREMES'
    sv_dependencies = {'scipy'}

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
                ts = curve_extremes(curve, field, samples, self.direction, self.on_fail, self.sv_logger)
                ps = curve.evaluate_array(np.array(ts)).tolist()
                new_t.extend(ts)
                new_points.extend(ps)
            t_out.append(new_t)
            point_out.append(new_points)

        self.outputs['Point'].sv_set(point_out)
        self.outputs['T'].sv_set(t_out)


def register():
    bpy.utils.register_class(SvExCurveExtremesNode)


def unregister():
    bpy.utils.unregister_class(SvExCurveExtremesNode)
