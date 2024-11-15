import numpy as np

import bpy
from mathutils import Quaternion
from bpy.props import EnumProperty, IntProperty, FloatProperty
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

    param_modes = [
            (SvFrameAlongCurveField.CURVE_PARAMETER, "Curve Parameter", "Orientation axis corresponds to curve parameter", 0),
            (SvFrameAlongCurveField.CURVE_LENGTH, "Curve Length", "Orientation axis corresponds to curve arc length", 1)
        ]

    input_modes = [
            ('MAT', "Matrices", "Matrices", 0),
            ('QUAT', "Quaternions", "Quaternions", 1),
            ('TRACK', "Track Vectors", "Track Vectors", 2)
        ]

    def update_sockets(self, context):
        self.inputs['LengthResolution'].hide_safe = self.input_mode != 'MAT' or self.param_mode != SvFrameAlongCurveField.CURVE_LENGTH
        self.inputs['Quaternions'].hide_safe = self.input_mode != 'QUAT'
        self.inputs['Matrices'].hide_safe = self.input_mode != 'MAT'
        self.inputs['Vectors'].hide_safe = self.input_mode != 'TRACK'
        self.inputs['T'].label = 'T' if self.param_mode == SvFrameAlongCurveField.CURVE_PARAMETER else 'Length'
        self.inputs['T'].hide_safe = self.input_mode == 'MAT'
        updateNode(self, context)

    param_mode : EnumProperty(
        name = "Parametrization",
        items = param_modes,
        default = SvFrameAlongCurveField.CURVE_PARAMETER,
        update = update_sockets)

    input_mode : EnumProperty(
        name = "Input",
        items = input_modes,
        default = 'MAT',
        update = update_sockets)

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

    length_resolution : IntProperty(
        name = "Length Resolution",
        min = 3,
        default = 50,
        update = updateNode)

    z_axis : EnumProperty(
        name = "Orientation",
        description = "Which axis of the provided frames points along the curve",
        items = xyz_axes,
        default = 'Z',
        update = updateNode)

    track_axis : EnumProperty(
        name = "Track Axis",
        items = xyz_axes,
        default = 'X',
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Input:')
        layout.prop(self, 'input_mode', text='')
        layout.label(text='Parametrization:')
        layout.prop(self, 'param_mode', text='')
        layout.label(text='Orientation:')
        layout.prop(self, 'z_axis', expand=True)
        if self.input_mode == 'TRACK':
            layout.label(text='Track Axis:')
            layout.prop(self, 'track_axis', expand=True)
        layout.label(text='Interpolation:')
        layout.prop(self, 'interpolation_mode', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'samples')
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvMatrixSocket', "Matrices")
        self.inputs.new('SvQuaternionSocket', "Quaternions")
        p = self.inputs.new('SvVerticesSocket', "Vectors")
        p.use_prop = True
        p.default_property = (1.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "T")
        self.inputs.new('SvStringsSocket', "LengthResolution").prop_name = 'length_resolution'
        self.outputs.new('SvVectorFieldSocket', 'Field')
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        input_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        flat_output = input_level > 1
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        if self.input_mode == 'MAT':
            frames_s = self.inputs['Matrices'].sv_get()
            # list of frames per curve
            frames_s = ensure_nesting_level(frames_s, 3, data_types=(Matrix,))
            quats_s = [[[None]]]
            track_s = [[[None]]]
            ts_s = [[[None]]]
        elif self.input_mode == 'QUAT':
            quats_s = self.inputs['Quaternions'].sv_get()
            quats_s = ensure_nesting_level(quats_s, 4)
            frames_s = [[[None]]]
            track_s = [[[None]]]
            ts_s = self.inputs['T'].sv_get()
            ts_s = ensure_nesting_level(ts_s, 3)
        elif self.input_mode == 'TRACK':
            track_s = self.inputs['Vectors'].sv_get()
            track_s = ensure_nesting_level(track_s, 4)
            frames_s = [[[None]]]
            quats_s = [[[None]]]
            ts_s = self.inputs['T'].sv_get()
            ts_s = ensure_nesting_level(ts_s, 3)
        resolution_s = self.inputs['LengthResolution'].sv_get()
        resolution_s = ensure_nesting_level(resolution_s, 2)

        tolerance = 10**(-self.accuracy)
        intersection_params = IntersectionParams(self.samples, tolerance)

        fields = []
        for params in zip_long_repeat(curves_s, frames_s, quats_s, track_s, ts_s, resolution_s):
            new_fields = []
            for curve, frames, quats, tracks, ts, resolution in zip_long_repeat(*params):
                if self.input_mode == 'MAT':
                    field = SvFrameAlongCurveField.from_matrices(curve, frames,
                                        z_axis = self.z_axis,
                                        interpolation = self.interpolation_mode,
                                        parametrization = self.param_mode,
                                        intersection_params = intersection_params)
                elif self.input_mode == 'QUAT':
                    field = SvFrameAlongCurveField.from_quaternions(curve, ts, quats,
                                        z_axis = self.z_axis,
                                        interpolation = self.interpolation_mode,
                                        parametrization = self.param_mode,
                                        length_resolution = resolution)
                else: # TRACK:
                    field = SvFrameAlongCurveField.from_track_vectors(curve, ts, tracks,
                                        z_axis = self.z_axis,
                                        track_axis = self.track_axis,
                                        interpolation = self.interpolation_mode,
                                        parametrization = self.param_mode,
                                        length_resolution = resolution)

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

