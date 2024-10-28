# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_solver_applications import (
        snap_curves,
        BIAS_CURVE1, BIAS_CURVE2, BIAS_MID,
        TANGENT_ANY, TANGENT_PRESERVE, TANGENT_MATCH,
        TANGENT_CURVE1, TANGENT_CURVE2
    )

class SvSnapCurvesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Snap Curves
    Tooltip: Snap ends of curves to common point, optionally controlling curve tangents.
    """
    bl_idname = 'SvSnapCurvesNode'
    bl_label = 'Snap NURBS Curves'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SNAP_CURVES'

    bias_modes = [
            (BIAS_MID, "Middle point", "Snap to middle point between end of first curve and start of second curve", 0),
            (BIAS_CURVE1, "Curve 1", "Snap start of second curve to the end of the first curve", 1),
            (BIAS_CURVE2, "Curve 2", "Snap end of first curve to the start of the second curve",
             2)
        ]

    tangent_modes = [
            (TANGENT_ANY, "No matter", "Tangents will probably change", 0),
            (TANGENT_PRESERVE, "Preserve", "Preserve tangent vectors of all curves at both ends", 1),
            (TANGENT_MATCH, "Medium", "Adjust tangent vectors of curves so that they will be average between end tangent of the first curve and start tangent of the second curve", 2),
            (TANGENT_CURVE1, "Curve 1", "Preserve tangent vector of the first curve at it's end, and adjust the tangent vector of the second curve to match", 3),
            (TANGENT_CURVE2, "Curve 2", "Preserve tangent vector of the second curve at it'send, and adjust the tangent vector of the first curve to match", 4)
        ]

    input_modes = [
        ('TWO', "Two curves", "Process two curves", 0),
        ('N', "List of curves", "Process several curves", 1)
    ]

    def update_sockets(self, context):
        self.inputs['Curve1'].hide_safe = self.input_mode != 'TWO'
        self.inputs['Curve2'].hide_safe = self.input_mode != 'TWO'
        self.inputs['Curves'].hide_safe = self.input_mode != 'N'
        updateNode(self, context)

    input_mode : EnumProperty(
        name = "Input mode",
        items = input_modes,
        default = 'TWO',
        update = update_sockets)

    bias : EnumProperty(
            name = "Bias",
            items = bias_modes,
            update = updateNode)

    tangent : EnumProperty(
            name = "Tangents",
            items = tangent_modes,
            update = updateNode)

    cyclic : BoolProperty(
            name = "Cyclic",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curves")
        self.inputs.new('SvCurveSocket', "Curve1")
        self.inputs.new('SvCurveSocket', "Curve2")
        self.outputs.new('SvCurveSocket', "Curves")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'input_mode', text='')
        layout.prop(self, 'bias')
        layout.prop(self, 'tangent')
        layout.prop(self, 'cyclic')

    def get_inputs(self):
        curves_s = []
        if self.input_mode == 'TWO':
            curve1_s = self.inputs['Curve1'].sv_get()
            curve2_s = self.inputs['Curve2'].sv_get()
            level1 = get_data_nesting_level(curve1_s, data_types=(SvCurve,))
            level2 = get_data_nesting_level(curve2_s, data_types=(SvCurve,))
            nested_input = level1 > 1 or level2 > 1
            curve1_s = ensure_nesting_level(curve1_s, 2, data_types=(SvCurve,))
            curve2_s = ensure_nesting_level(curve2_s, 2, data_types=(SvCurve,))
            for inputs in zip_long_repeat(curve1_s, curve2_s):
                curves_s.append( list( *zip_long_repeat(*inputs) ) )
        else:
            curves_s = self.inputs['Curves'].sv_get()
            level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
            nested_input = level > 1
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        return nested_input, curves_s

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_out = []
        nested_input, curves_s = self.get_inputs()
        for curves in curves_s:
            curves = [SvNurbsCurve.to_nurbs(c) for c in curves]
            if any(c is None for c in curves):
                raise Exception("Some of curves are not NURBS!")
            new_curves = snap_curves(curves,
                                     bias = self.bias,
                                     tangent = self.tangent,
                                     cyclic = self.cyclic)
            if nested_input:
                curves_out.append(new_curves)
            else:
                curves_out.extend(new_curves)

        self.outputs['Curves'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvSnapCurvesNode)

def unregister():
    bpy.utils.unregister_class(SvSnapCurvesNode)

