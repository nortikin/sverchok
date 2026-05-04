import numpy as np

import bpy
from bpy.props import FloatVectorProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import nurbs_curve_extremes

class SvNurbsCurveExtremesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Curve Extremes
    Tooltip: Find a point on a NURBS curve which provides the maximum or minimum for specified scalar field
    """
    bl_idname = 'SvNurbsCurveExtremesNode'
    bl_label = 'NURBS Curve Extremes'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_EXTREMES'

    sign_options = [
            ('MIN', "Minimum", "Find the minimum along specified direction", 0),
            ('MAX', "Minimum", "Find the maximum along specified direction", 1),
        ]

    sign_option: EnumProperty(
            name = "Sign",
            items = sign_options,
            default = 'MIN',
            update = updateNode)

    global_only: BoolProperty(
            name = "Global only",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'sign_option', expand=True)
        layout.prop(self, 'global_only')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)
        self.outputs.new('SvVerticesSocket', "Point")
        self.outputs.new('SvStringsSocket', "T")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        input_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        is_nested = input_level > 1
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        direction_s = self.inputs['Direction'].sv_get()
        direction_s = ensure_nesting_level(direction_s, 3)

        sign = -1 if self.sign_option == 'MIN' else 1

        t_out = []
        point_out = []
        for params in zip_long_repeat(curves_s, direction_s):
            new_t = []
            new_points = []
            for curve, direction in zip_long_repeat(*params):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise UnsupportedCurveTypeException("Curve is not NURBS")
                ts = nurbs_curve_extremes(curve, direction, sign=sign, global_only=self.global_only)
                ps = curve.evaluate_array(np.array(ts)).tolist()
                if is_nested:
                    new_t.append(ts)
                    new_points.append(ps)
                else:
                    new_t.extend(ts)
                    new_points.extend(ps)
            t_out.append(new_t)
            point_out.append(new_points)

        self.outputs['Point'].sv_set(point_out)
        self.outputs['T'].sv_set(t_out)

def register():
    bpy.utils.register_class(SvNurbsCurveExtremesNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsCurveExtremesNode)

