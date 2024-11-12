import numpy as np

import bpy
from bpy.props import EnumProperty, IntProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.math import xyz_axes
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.field.frame_along_curve import IntersectionParams, SvFrameAlongCurveField

class SvSlerpCurveFieldNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Twist Curve Field
    Tooltip: Twist along Curve
    """
    bl_idname = 'SvSlerpCurveFieldNode'
    bl_label = 'Twist along Curve Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INTERP_FRAME'
    sv_dependencies = {'scipy'}

    interp_modes = [
            (SvFrameAlongCurveField.INTERP_LINEAR, "Linear", "Linear quaternion interpolation", 0),
            (SvFrameAlongCurveField.INTERP_SPLINE, "Spline", "Spline quaternion interpolation", 1)
        ]

    interpolation_mode : EnumProperty(
        name = "Interpolation",
        description = "Rotation interpolation mode",
        items = interp_modes,
        default = SvFrameAlongCurveField.INTERP_SPLINE,
        update = updateNode)

    samples : IntProperty(
        name = "Curve Resolution",
        description = "A number of segments to subdivide the curve in; defines the maximum number of intersection points that is possible to find.",
        default = 5,
        min = 1,
        update = updateNode)

    accuracy : IntProperty(
        name = "Accuracy",
        description = "Accuracy level - number of exact digits after decimal points.",
        default = 4,
        min = 1,
        update = updateNode)

    z_axis : EnumProperty(
        name = "Orientation",
        description = "Which axis of the provided frames points along the curve",
        items = xyz_axes,
        default = 'Z',
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'z_axis', expand=True)
        layout.prop(self, 'interpolation_mode')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'samples')
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvMatrixSocket', "Matrices")
        self.outputs.new('SvVectorFieldSocket', 'Field')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        input_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        flat_output = input_level > 1
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        frames_s = self.inputs['Matrices'].sv_get()
        # list of frames per curve
        frames_s = ensure_nesting_level(frames_s, 3, data_types=(Matrix,))

        tolerance = 10**(-self.accuracy)
        intersection_params = IntersectionParams(self.samples, tolerance)

        fields = []
        for curves, frames_i in zip_long_repeat(curves_s, frames_s):
            new_fields = []
            for curve, frames in zip_long_repeat(curves, frames_i):
                field = SvFrameAlongCurveField.from_matrices(curve, frames,
                                    z_axis = self.z_axis,
                                    interpolation = self.interpolation_mode,
                                    intersection_params = intersection_params)
                new_fields.append(field)
            if flat_output:
                fields.extend(new_fields)
            else:
                fields.append(new_fields)

        self.outputs['Field'].sv_set(fields)

def register():
    bpy.utils.register_class(SvSlerpCurveFieldNode)


def unregister():
    bpy.utils.unregister_class(SvSlerpCurveFieldNode)

