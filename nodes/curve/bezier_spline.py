
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.curve import SvBezierCurve

class SvBezierSplineNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bezier Spline
    Tooltip: Generate Bezier curve spline
    """
    bl_idname = 'SvBezierSplineNode'
    bl_label = 'Bezier Spline (Curve)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POLYLINE'

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Start")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Knot1")
        p.use_prop = True
        p.prop = (1.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Knot2")
        p.use_prop = True
        p.prop = (2.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "End")
        p.use_prop = True
        p.prop = (3.0, 0.0, 0.0)
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        start_s = self.inputs['Start'].sv_get()
        end_s = self.inputs['End'].sv_get()
        knot1_s = self.inputs['Knot1'].sv_get()
        knot2_s = self.inputs['Knot2'].sv_get()

        start_s = ensure_nesting_level(start_s, 3)
        end_s = ensure_nesting_level(end_s, 3)
        knot1_s = ensure_nesting_level(knot1_s, 3)
        knot2_s = ensure_nesting_level(knot2_s, 3)

        curves_out = []
        for starts, ends, knot1s, knot2s in zip_long_repeat(start_s, end_s, knot1_s, knot2_s):
            new_curves = []
            for start, end, knot1, knot2 in zip_long_repeat(starts, ends, knot1s, knot2s):
                curve = SvBezierCurve(start, knot1, knot2, end)
                new_curves.append(curve)
            curves_out.append(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvBezierSplineNode)

def unregister():
    bpy.utils.unregister_class(SvBezierSplineNode)

