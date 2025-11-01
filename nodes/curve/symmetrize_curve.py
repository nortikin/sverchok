# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.core.sv_custom_exceptions import SvUnsupportedOptionException
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.geom import PlaneEquation
from sverchok.utils.manifolds import symmetrize_curve

class SvSymmetrizeCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Symmetrize Curve
    Tooltip: Symmetrize Curve
    """
    bl_idname = 'SvSymmetrizeCurveNode'
    bl_label = 'Symmetrize Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MOVE_CURVE_POINT'

    directions = [
        ('X+', "-X to +X", "-X to +X", 0),
        ('X-', "+X to -X", "+X to -X", 1),
        ('Y+', "-Y to +Y", "-Y to +Y", 2),
        ('Y-', "+Y to -Y", "+Y to -Y", 3),
        ('Z+', "-Z to +Z", "-Z to +Z", 4),
        ('Z-', "+Z to -Z", "+Z to -Z", 5),
        ('CUSTOM', "Custom", "Custom", 6)
    ]

    def mode_change(self, context):
        print("St:", self.direction)
        self.inputs['Point'].hide_safe = self.direction != 'CUSTOM'
        self.inputs['Normal'].hide_safe = self.direction != 'CUSTOM'
        updateNode(self, context)

    direction : EnumProperty(
            name = "Direction",
            description = "Which sides to copy from and to",
            items = directions,
            default = "X+",
            update = mode_change)

    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy level - number of exact digits after decimal points.",
            default = 6,
            min = 1,
            update = updateNode)

    plane_point : FloatVectorProperty(
            name = "Point",
            description = "Point on plane",
            default = (0.0, 0.0, 0.0),
            precision = 3,
            update = updateNode)

    plane_normal : FloatVectorProperty(
            name = "Normal",
            description = "Plane normal",
            default = (0.0, 0.0, 1.0),
            precision = 3,
            update = updateNode)

    concatenate : BoolProperty(
            name = "Concatenate",
            description = "Concatenate mirrored fragments into single curve, if possible",
            default = True,
            update = updateNode)

    flip : BoolProperty(
            name = "Reverse",
            description = "Reverse the direction of mirrored curves",
            default = True,
            update = updateNode)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "accuracy")

    def draw_buttons(self, context, layout):
        layout.prop(self, "direction")
        layout.prop(self, "concatenate")
        if not self.concatenate:
            layout.prop(self, "flip")

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvVerticesSocket', "Point").prop_name = 'plane_point'
        self.inputs.new('SvVerticesSocket', "Normal").prop_name = 'plane_normal'
        self.outputs.new('SvCurveSocket', "Curve")
        self.mode_change(context)

    def _get_plane(self, point, normal):
        if self.direction in ['X+','X-']:
            normal = (1,0,0)
            point = (0,0,0)
        elif self.direction in ['Y+', 'Y-']:
            normal = (0,1,0)
            point = (0,0,0)
        elif self.direction in ['Z+', 'Z-']:
            normal = (0,0,1)
            point = (0,0,0)

        if self.direction in ['X+', 'Y+', 'Z+', 'CUSTOM']:
            sign = -1
        else:
            sign = 1

        plane = PlaneEquation.from_normal_and_point(normal, point)
        return plane, sign


    def process(self):
        if not self.outputs['Curve'].is_linked:
            return

        curve_s = self.inputs['Curve'].sv_get()
        point_s = self.inputs['Point'].sv_get()
        normal_s = self.inputs['Normal'].sv_get()

        input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        flat_output = input_level < 2
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        point_s = ensure_nesting_level(point_s, 3)
        normal_s = ensure_nesting_level(normal_s, 3)

        curve_out = []
        for params in zip_long_repeat(curve_s, point_s, normal_s):
            new_curves = []
            for curve, point, normal in zip_long_repeat(*params):
                plane, sign = self._get_plane(point, normal)
                curve = symmetrize_curve(curve, plane, sign,
                                         concatenate = self.concatenate,
                                         flip = self.flip)
                new_curves.append(curve)
            if flat_output:
                curve_out.extend(new_curves)
            else:
                curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvSymmetrizeCurveNode)

def unregister():
    bpy.utils.unregister_class(SvSymmetrizeCurveNode)

