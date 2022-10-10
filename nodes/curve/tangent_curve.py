
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve import SvCurve, SvBezierCurve, SvConcatCurve, SvCubicBezierCurve

class SvTangentsCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Tangents Curve
    Tooltip: Generate Bezier curve from points and tangent vectors
    """
    bl_idname = 'SvTangentsCurveNode'
    bl_label = 'Tangents Curve'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_TANGENT_CURVE'

    concat : BoolProperty(
        name = "Concatenate",
        description = "Concatenate source curves and blending curves into one curve",
        default = True,
        update = updateNode)

    cyclic : BoolProperty(
        name = "Cyclic",
        default = False,
        update = updateNode)

    make_nurbs : BoolProperty(
        name = "NURBS output",
        description = "Generate a NURBS curve",
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'cyclic', toggle=True)
        layout.prop(self, 'concat', toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'make_nurbs', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Points")
        self.inputs.new('SvVerticesSocket', "Tangents")
        self.outputs.new('SvCurveSocket', 'Curve')
        self.outputs.new('SvVerticesSocket', "ControlPoints")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        points_s = self.inputs['Points'].sv_get()
        tangents_s = self.inputs['Tangents'].sv_get()

        input_level = get_data_nesting_level(points_s)
        output_nested = input_level > 3
        points_s = ensure_nesting_level(points_s, 4)
        tangents_s = ensure_nesting_level(tangents_s, 4)

        curve_out = []
        controls_out = []
        for params in zip_long_repeat(points_s, tangents_s):
            curves_i = []
            controls_i = []
            for points, tangents in zip_long_repeat(*params):
                new_controls, new_curve = SvBezierCurve.build_tangent_curve(points, tangents,
                                                cyclic = self.cyclic, concat = self.concat,
                                                as_nurbs = self.make_nurbs)
                curves_i.append(new_curve)
                controls_i.append(new_controls)
            if output_nested:
                curve_out.append(curves_i)
                controls_out.append(controls_i)
            else:
                curve_out.extend(curves_i)
                controls_out.extend(controls_i)

        self.outputs['Curve'].sv_set(curve_out)
        self.outputs['ControlPoints'].sv_set(controls_out)

def register():
    bpy.utils.register_class(SvTangentsCurveNode)

def unregister():
    bpy.utils.unregister_class(SvTangentsCurveNode)

