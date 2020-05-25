
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.curve import SvCurve, SvBezierCurve, SvConcatCurve, SvCubicBezierCurve

class SvTangentsCurveNode(bpy.types.Node, SverchCustomTreeNode):
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

    def draw_buttons(self, context, layout):
        layout.prop(self, 'cyclic', toggle=True)
        layout.prop(self, 'concat', toggle=True)

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

        points_s = ensure_nesting_level(points_s, 3)
        tangents_s = ensure_nesting_level(tangents_s, 3)

        curve_out = []
        controls_out = []
        for points, tangents in zip_long_repeat(points_s, tangents_s):
            new_curves = []
            new_controls = []
            control_points = []
            pairs = list(zip_long_repeat(points, tangents))
            segments = list(zip(pairs, pairs[1:]))
            if self.cyclic:
                segments.append((pairs[-1], pairs[0]))
            for pair1, pair2 in segments:
                point1, tangent1 = pair1
                point2, tangent2 = pair2
                point1, tangent1 = np.array(point1), np.array(tangent1)
                point2, tangent2 = np.array(point2), np.array(tangent2)
                tangent1, tangent2 = tangent1/2.0, tangent2/2.0
                curve = SvCubicBezierCurve(
                            point1,
                            point1 + tangent1,
                            point2 - tangent2,
                            point2)
                curve_controls = [curve.p0.tolist(), curve.p1.tolist(),
                                  curve.p2.tolist(), curve.p3.tolist()]
                new_curves.append(curve)
                new_controls.append(curve_controls)
            if self.concat:
                new_curves = [SvConcatCurve(new_curves)]
            curve_out.append(new_curves)
            controls_out.append(new_controls)

        self.outputs['Curve'].sv_set(curve_out)
        self.outputs['ControlPoints'].sv_set(controls_out)

def register():
    bpy.utils.register_class(SvTangentsCurveNode)

def unregister():
    bpy.utils.unregister_class(SvTangentsCurveNode)

