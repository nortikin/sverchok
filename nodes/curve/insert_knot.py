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

class SvCurveInsertKnotNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Insert Knot
    Tooltip: Inset knot in a NURBS curve
    """
    bl_idname = 'SvCurveInsertKnotNode'
    bl_label = 'NURBS Curve - Insert Knot'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FLIP_CURVE'

    knot : FloatProperty(
            name = "Knot",
            description = "New knot value",
            default = 0.5,
            update = updateNode)

    count : IntProperty(
            name = "Count",
            description = "Number of times to insert the knot",
            default = 1,
            min = 0,
            update = updateNode)
        
    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Knot").prop_name = 'knot'
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        knot_s = self.inputs['Knot'].sv_get()
        count_s = self.inputs['Count'].sv_get()

        input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        flat_output = input_level < 2
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        knot_s = ensure_nesting_level(knot_s, 3)
        count_s = ensure_nesting_level(count_s, 3)

        curves_out = []
        for curves, knots_i, counts_i in zip_long_repeat(curve_s, knot_s, count_s):
            new_curves = []
            for curve, knots, counts in zip_long_repeat(curves, knots_i, counts_i):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("One of curves is not NURBS")
                for knot, count in zip_long_repeat(knots, counts):
                    curve = curve.insert_knot(knot, count)
                new_curves.append(curve)
            if flat_output:
                curves_out.extend(new_curves)
            else:
                curves_out.append(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCurveInsertKnotNode)

def unregister():
    bpy.utils.unregister_class(SvCurveInsertKnotNode)

