
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.core.socket_data import SvNoDataError
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvBezierCurve, SvCubicBezierCurve

CUBIC = '3_2pt_2cp'
CUBIC_TANGENT = '3_2pt_tan'
CUBIC_4PT = '3_4pt'
QUADRATIC = '2'
GENERIC = 'GEN'

CONTROL1_SOCKET = 1
CONTROL2_SOCKET = 2

class SvBezierSplineNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bezier Spline
    Tooltip: Generate Bezier curve spline
    """
    bl_idname = 'SvBezierSplineNode'
    bl_label = 'Bezier Spline (Curve)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POLYLINE'

    @throttled
    def update_sockets(self, context):
        self.inputs['Start'].hide_safe = self.mode == GENERIC
        self.inputs['End'].hide_safe = self.mode == GENERIC
        self.inputs[CONTROL1_SOCKET].hide_safe = self.mode == GENERIC
        self.inputs[CONTROL2_SOCKET].hide_safe = self.mode == GENERIC or self.mode == QUADRATIC
        self.inputs[CONTROL1_SOCKET].name = "Tangent1" if self.mode == CUBIC_TANGENT else "Control1"
        self.inputs[CONTROL2_SOCKET].name = "Tangent2" if self.mode == CUBIC_TANGENT else "Control2"
        self.inputs['ControlPoints'].hide_safe = self.mode != GENERIC

    modes = [
        (CUBIC, "Cubic 2pts + 2 controls", "Cubic spline by two end points and two additional control points", 0),
        (CUBIC_TANGENT, "Cubic 2pts + 2 Tangents", "Cubic spline by two end points and two tangent vectors", 1),
        (CUBIC_4PT, "Cubic 4pts", "Cubic spline through four points", 2),
        (QUADRATIC, "Quadratic", "Quadratic spline by two end points and one additional control point", 3),
        (GENERIC, "Generic", "Generic Bezier spline with any number of control points", 5)
    ]

    mode : EnumProperty(
            name = "Mode",
            items = modes,
            default = CUBIC,
            update = update_sockets)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            description = "Whether the generated curve should be closed",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text='')
        if self.mode == GENERIC:
            layout.prop(self, 'is_cyclic', toggle=True)

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Start")    # 0
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Control1") # 1
        p.use_prop = True
        p.prop = (1.0, 1.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Control2") # 2
        p.use_prop = True
        p.prop = (2.0, -1.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "End")      # 3
        p.use_prop = True
        p.prop = (3.0, 0.0, 0.0)
        self.inputs.new('SvVerticesSocket', "ControlPoints") # 4
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        start_s = self.inputs['Start'].sv_get()
        end_s = self.inputs['End'].sv_get()
        knot1_s = self.inputs[CONTROL1_SOCKET].sv_get()
        knot2_s = self.inputs[CONTROL2_SOCKET].sv_get()
        controls_s = self.inputs['ControlPoints'].sv_get(default=[[[[]]]])

        start_s = ensure_nesting_level(start_s, 3)
        end_s = ensure_nesting_level(end_s, 3)
        knot1_s = ensure_nesting_level(knot1_s, 3)
        knot2_s = ensure_nesting_level(knot2_s, 3)
        controls_s = ensure_nesting_level(controls_s, 4)

        curves_out = []
        for starts, ends, knot1s, knot2s, controls_i in zip_long_repeat(start_s, end_s, knot1_s, knot2_s, controls_s):
            new_curves = []
            for start, end, knot1, knot2, controls in zip_long_repeat(starts, ends, knot1s, knot2s, controls_i):
                start, end = np.array(start), np.array(end)
                knot1, knot2 = np.array(knot1), np.array(knot2)
                if self.mode == CUBIC:
                    curve = SvCubicBezierCurve(start, knot1, knot2, end)
                elif self.mode == CUBIC_TANGENT:
                    curve = SvCubicBezierCurve(
                                start,
                                start + knot1,
                                end + knot2,
                                end)
                elif self.mode == CUBIC_4PT:
                    curve = SvCubicBezierCurve.from_four_points(start, knot1, knot2, end)
                elif self.mode == QUADRATIC:
                    curve = SvBezierCurve([start, knot1, end])
                else: # GENERIC
                    if not controls:
                        raise SvNoDataError(socket=self.inputs['ControlPoints'], node=self)
                    if len(controls) < 2:
                        raise Exception("At least three control points are required to build a Bezier spline!")
                    if self.is_cyclic:
                        controls = controls + [controls[0]]
                    curve = SvBezierCurve(controls)
                new_curves.append(curve)
            curves_out.append(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvBezierSplineNode)

def unregister():
    bpy.utils.unregister_class(SvBezierSplineNode)

