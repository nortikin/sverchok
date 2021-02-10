
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvCurveSegment
from sverchok.utils.curve.algorithms import curve_segment

class SvCurveSegmentNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Segment
    Tooltip: Generate a curve as a segment of another curve
    """
    bl_idname = 'SvExCurveSegmentNode'
    bl_label = 'Curve Segment'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_SEGMENT'

    t_min : FloatProperty(
        name = "T Min",
        default = 0.2,
        update = updateNode)

    t_max : FloatProperty(
        name = "T Max",
        default = 0.8,
        update = updateNode)

    rescale : BoolProperty(
        name = "Rescale to 0..1",
        default = False,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "TMin").prop_name = 't_min'
        self.inputs.new('SvStringsSocket', "TMax").prop_name = 't_max'
        self.outputs.new('SvCurveSocket', "Segment")

    def draw_buttons(self, context, layout):
        layout.prop(self, "rescale", toggle=True)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        tmin_s = self.inputs['TMin'].sv_get()
        tmax_s = self.inputs['TMax'].sv_get()

        tmin_s = ensure_nesting_level(tmin_s, 2)
        tmax_s = ensure_nesting_level(tmax_s, 2)
        if isinstance(curve_s[0], SvCurve):
            curve_s = [curve_s]

        curve_out = []
        for curves, tmins, tmaxs in zip_long_repeat(curve_s, tmin_s, tmax_s):
            for curve, t_min, t_max in zip_long_repeat(curves, tmins, tmaxs):
                new_curve = curve_segment(curve, t_min, t_max, self.rescale)
                curve_out.append(new_curve)

        self.outputs['Segment'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvCurveSegmentNode)

def unregister():
    bpy.utils.unregister_class(SvCurveSegmentNode)

