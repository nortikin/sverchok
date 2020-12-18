
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
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

        points_s = ensure_nesting_level(points_s, 3)
        tangents_s = ensure_nesting_level(tangents_s, 3)

        curve_out = []
        controls_out = []
        for points, tangents in zip_long_repeat(points_s, tangents_s):
            new_controls, new_curves = SvBezierCurve.build_tangent_curve(points, tangents,
                                            cyclic = self.cyclic, concat = self.concat,
                                            as_nurbs = self.make_nurbs)
            curve_out.append(new_curves)
            controls_out.append(new_controls)

        self.outputs['Curve'].sv_set(curve_out)
        self.outputs['ControlPoints'].sv_set(controls_out)

def register():
    bpy.utils.register_class(SvTangentsCurveNode)

def unregister():
    bpy.utils.unregister_class(SvTangentsCurveNode)

