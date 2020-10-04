# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat_nested, map_nested, unzip_dict_recursive, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve.circle_tangents import calc_two_circles_tangents, SvTwoCircleTangentsData

class SvTwoCircleTangentsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Two Circles Tangents
    Tooltip: Calculate outer and / or inner tangents of two circles
    """
    bl_idname = 'SvTwoCircleTangentsNode'
    bl_label = 'Two Circle Tangents'
    bl_icon = 'SPHERECURVE'
    sv_icon = 'SV_BIARC'

    planar_accuracy : IntProperty(
            name = "Planar Accuracy",
            description = "Tolerance value for checking if circles lie in a single plane",
            default = 6,
            min = 1,
            update = updateNode)

    @throttled
    def update_sockets(self, context):
        self.outputs['OuterTangent1'].hide_safe = not self.calc_outer
        self.outputs['OuterTangent2'].hide_safe = not self.calc_outer
        self.outputs['OuterArc1'].hide_safe = not self.calc_outer
        self.outputs['OuterArc2'].hide_safe = not self.calc_outer

        self.outputs['InnerTangent1'].hide_safe = not self.calc_inner
        self.outputs['InnerTangent2'].hide_safe = not self.calc_inner
        self.outputs['InnerArc1'].hide_safe = not self.calc_inner
        self.outputs['InnerArc2'].hide_safe = not self.calc_inner

    calc_outer : BoolProperty(
            name = "Outer Tangents",
            description = "Calculate outer tangents",
            default = True,
            update = update_sockets)

    calc_inner : BoolProperty(
            name = "Inner Tangents",
            description = "Calculate inner tangents",
            default = False,
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', 'Circle1')
        self.inputs.new('SvCurveSocket', 'Circle2')

        self.outputs.new('SvCurveSocket', 'OuterTangent1')
        self.outputs.new('SvCurveSocket', 'OuterTangent2')
        self.outputs.new('SvCurveSocket', 'OuterArc1')
        self.outputs.new('SvCurveSocket', 'OuterArc2')

        self.outputs.new('SvCurveSocket', 'InnerTangent1')
        self.outputs.new('SvCurveSocket', 'InnerTangent2')
        self.outputs.new('SvCurveSocket', 'InnerArc1')
        self.outputs.new('SvCurveSocket', 'InnerArc2')

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'calc_outer', toggle=True)
        layout.prop(self, 'calc_inner', toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'planar_accuracy')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        circle1_in = self.inputs['Circle1'].sv_get()
        circle2_in = self.inputs['Circle2'].sv_get()

        level1 = get_data_nesting_level(circle1_in, data_types=(SvCircle,))
        level2 = get_data_nesting_level(circle2_in, data_types=(SvCircle,))
        input_level = max(level1, level2)
        circle1_in = ensure_nesting_level(circle1_in, input_level, data_types=(SvCircle,))
        circle2_in = ensure_nesting_level(circle2_in, input_level, data_types=(SvCircle,))

        def to_dict(r):
            return dict(OuterTangent1 = r.outer_tangent1,
                    OuterTangent2 = r.outer_tangent2,
                    OuterArc1 = r.outer_arc1,
                    OuterArc2 = r.outer_arc2,
                    InnerTangent1 = r.inner_tangent1,
                    InnerTangent2 = r.inner_tangent2,
                    InnerArc1 = r.inner_arc1,
                    InnerArc2 = r.inner_arc2)

        inputs = zip_long_repeat_nested(circle1_in, circle2_in, max_level=input_level)
        results = map_nested(calc_two_circles_tangents, inputs, max_level=input_level, single_argument=False)
        results = unzip_dict_recursive(results, item_type=SvTwoCircleTangentsData, to_dict=to_dict)

        for output_name in results.keys():
            self.outputs[output_name].sv_set(results[output_name])

def register():
    bpy.utils.register_class(SvTwoCircleTangentsNode)

def unregister():
    bpy.utils.unregister_class(SvTwoCircleTangentsNode)

