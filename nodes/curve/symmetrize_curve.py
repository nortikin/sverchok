# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
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
    bl_icon = 'MOD_MIRROR'

    directions = [
        ('X+', "-X to +X", "-X to +X", 0),
        ('X-', "+X to -X", "+X to -X", 1),
        ('Y+', "-Y to +Y", "-Y to +Y", 2),
        ('Y-', "+Y to -Y", "+Y to -Y", 3),
        ('Z+', "-Z to +Z", "-Z to +Z", 4),
        ('Z-', "+Z to -Z", "+Z to -Z", 5),
        ('CUSTOM', "Custom", "Custom", 6)
    ]

    output_modes = [
        ('CONCAT', "Concatenate", "Concatenate original parts of curve and their mirrored versions", 0),
        ('NEST', "Output pairs", "Generate a list of 2-lists: original curve segment and it's mirrored version", 1),
        ('FLAT', "Flat output", "Generate a single flat list of all curve segments", 2),
        ('SEPARATE', "Separate outputs", "Generate a list of original curve parts and a separate list of their mirrored counterparts", 3),
    ]

    def mode_change(self, context):
        self.inputs['Point'].hide_safe = self.direction != 'CUSTOM'
        self.inputs['Normal'].hide_safe = self.direction != 'CUSTOM'
        self.outputs['MirroredCurve'].hide_safe = self.output_mode != 'SEPARATE'
        self.outputs['Curve'].label = 'Curve' if self.output_mode != 'SEPARATE' else 'OriginalCurve'
        updateNode(self, context)

    direction : EnumProperty(
            name = "Direction",
            description = "Which sides to copy from and to",
            items = directions,
            default = "X+",
            update = mode_change)

    output_mode : EnumProperty(
            name = "Output mode",
            items = output_modes,
            default = 'CONCAT',
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

    flip : BoolProperty(
            name = "Reverse",
            description = "Reverse the direction of mirrored curves",
            default = True,
            update = updateNode)

    use_nurbs : BoolProperty(
            name = "Use NURBS algorithm",
            description = "Use special algorithm for NURBS curves",
            default = True,
            update = updateNode)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "use_nurbs")
        layout.prop(self, "accuracy")

    def draw_buttons(self, context, layout):
        layout.label(text='Direction:')
        layout.prop(self, "direction", text='')
        layout.label(text='Output mode:')
        layout.prop(self, "output_mode", text='')
        if self.output_mode != 'CONCAT':
            layout.prop(self, "flip")

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvVerticesSocket', "Point").prop_name = 'plane_point'
        self.inputs.new('SvVerticesSocket', "Normal").prop_name = 'plane_normal'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvCurveSocket', "MirroredCurve")
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

        tolerance = 10 ** (-self.accuracy)

        curve_out = []
        mirrored_curve_out = []
        for params in zip_long_repeat(curve_s, point_s, normal_s):
            new_curves = []
            new_mirrored_curves = []
            for curve, point, normal in zip_long_repeat(*params):
                plane, sign = self._get_plane(point, normal)
                result = symmetrize_curve(curve, plane, sign,
                                         concatenate = self.output_mode == 'CONCAT',
                                         flip = self.flip,
                                         separate_output = self.output_mode == 'SEPARATE',
                                         flat_output = self.output_mode == 'FLAT',
                                         support_nurbs = self.use_nurbs,
                                         tolerance = tolerance)
                if self.output_mode == 'SEPARATE':
                    curve, mirrored_curve = result
                    new_curves.append(curve)
                    new_mirrored_curves.append(mirrored_curve)
                else:
                    new_curves.append(result)
            if flat_output:
                curve_out.extend(new_curves)
                mirrored_curve_out.extend(new_mirrored_curves)
            else:
                curve_out.append(new_curves)
                mirrored_curve_out.append(new_mirrored_curves)

        self.outputs['Curve'].sv_set(curve_out)
        self.outputs['MirroredCurve'].sv_set(mirrored_curve_out)

def register():
    bpy.utils.register_class(SvSymmetrizeCurveNode)

def unregister():
    bpy.utils.unregister_class(SvSymmetrizeCurveNode)

