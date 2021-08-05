# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import remove_excessive_knots

class SvCurveRemoveExcessiveKnotsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Remove Excessive Knots
    Tooltip: Remove all excessive knots from a NURBS curve
    """
    bl_idname = 'SvCurveRemoveExcessiveKnotsNode'
    bl_label = 'Remove Excessive Knots (NURBS Curve)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_CLEAN_KNOTS'

    tolerance : FloatProperty(
            name = "Tolerance",
            default = 1e-6,
            precision = 8,
            min = 0,
            update = updateNode)
        
    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvCurveSocket', "Curve")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'tolerance')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()

        input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        flat_output = input_level < 2
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))

        tolerance = self.tolerance

        curves_out = []
        for curves in curve_s:
            new_curves = []
            for curve in curves:
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("One of curves is not NURBS")
                curve = remove_excessive_knots(curve, tolerance=tolerance)
                new_curves.append(curve)
            if flat_output:
                curves_out.extend(new_curves)
            else:
                curves_out.append(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCurveRemoveExcessiveKnotsNode)

def unregister():
    bpy.utils.unregister_class(SvCurveRemoveExcessiveKnotsNode)

