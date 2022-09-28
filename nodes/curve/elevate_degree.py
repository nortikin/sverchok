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

class SvCurveElevateDegreeNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Elevate Degree
    Tooltip: Elevate degree of a NURBS curve
    """
    bl_idname = 'SvCurveElevateDegreeNode'
    bl_label = 'Elevate Degree (NURBS Curve)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ELEVATE_CURVE_DEGREE'

    modes = [
            ('DELTA', "Elevate by", "Specify difference between current degree and target degree", 0),
            ('TARGET', "Set degree", "Specify target degree", 1)
        ]

    def update_sockets(self, context):
        self.inputs['Degree'].label = "Delta" if self.mode == 'DELTA' else "Degree"
        updateNode(self, context)

    mode : EnumProperty(
            name = "Mode",
            description = "How new curve degree is specified",
            items = modes,
            update = update_sockets)

    degree : IntProperty(
            name = "Degree",
            description = "Target degree or degree delta",
            min = 0,
            default = 1,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', text='')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', 'Degree').prop_name = 'degree'
        self.outputs.new('SvCurveSocket', 'Curve')
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        degree_s = self.inputs['Degree'].sv_get()

        input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        flat_output = input_level < 2
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        degree_s = ensure_nesting_level(degree_s, 2)

        curves_out = []
        for params in zip_long_repeat(curve_s, degree_s):
            new_curves = []
            for curve, degree in zip_long_repeat(*params):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("One of curves is not NURBS")
                if self.mode == 'DELTA':
                    kwargs = dict(delta = degree)
                else:
                    kwargs = dict(target = degree)
                curve = curve.elevate_degree(**kwargs)
                new_curves.append(curve)
            if flat_output:
                curves_out.extend(new_curves)
            else:
                curves_out.append(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCurveElevateDegreeNode)

def unregister():
    bpy.utils.unregister_class(SvCurveElevateDegreeNode)

