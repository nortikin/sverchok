import numpy as np
from math import ceil

import bpy
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurveLengthSolver, SvCurve
from sverchok.utils.nodes_mixins.draft_mode import DraftMode


class SvCurveLengthParameterMk2Node(DraftMode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curve Length Parameter
    Tooltip: Solve curve length (natural) parameter
    """
    bl_idname = 'SvCurveLengthParameterMk2Node'
    bl_label = 'Curve Length Parameter'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_LENGTH_P'

    resolution : IntProperty(
        name = 'Resolution',
        min = 1,
        default = 50,
        update = updateNode)

    length : FloatProperty(
        name = "Length",
        min = 0.0,
        default = 0.5,
        update = updateNode)

    length_draft : FloatProperty(
        name = "[D] Length",
        min = 0.0,
        default = 0.5,
        update = updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]

    mode: EnumProperty(name='Interpolation mode', default="SPL", items=modes, update=updateNode)

    def update_sockets(self, context):
        self.inputs['Length'].hide_safe = self.eval_mode != 'MANUAL'
        self.inputs['Samples'].hide_safe = self.eval_mode != 'AUTO'
        self.inputs['SegmentLength'].hide_safe = self.eval_mode != 'LENGTH'
        updateNode(self, context)

    eval_modes = [
        ('AUTO', "By Count", "Evaluate the curve at evenly spaced points", 0),
        ('LENGTH', "By Length", "Evaluate the curve so that length of each segment will be equal to user-specified value", 1),
        ('MANUAL', "Manual", "Evaluate the curve at specified points", 2)
    ]

    eval_mode : EnumProperty(
        name = "Mode",
        items = eval_modes,
        default = 'AUTO',
        update = update_sockets)

    sample_size : IntProperty(
            name = "Samples",
            default = 50,
            min = 4,
            update = updateNode)

    segment_length : FloatProperty(
            name = "Segment Length",
            description = "Length of each segment",
            default = 1.0,
            min = 0.0,
            update = updateNode)

    specify_accuracy : BoolProperty(
        name = "Specify accuracy",
        default = False,
        update = updateNode)

    accuracy : IntProperty(
        name = "Accuracy",
        default = 3,
        min = 0,
        update = updateNode)

    accuracy_draft : IntProperty(
        name = "[D] Accuracy",
        default = 1,
        min = 0,
        update = updateNode)

    rounding_modes = [
            ('DOWN', "Longer Segments", "Round the number of segments down, so length of each segment can be greater than specified", 0),
            ('UP', "Shorter Segments", "Round the number of segments up, so length of each segment can be less than specified", 1),
            ('CUT', "Precise (Cut)", "Make each segment of precisely specified length, but the last point will be before end point", 2)
        ]

    rounding_mode : EnumProperty(
        name = "Rounding",
        description = "What to do if the length of the curve is not an integer multiple of the specified segment length",
        items = rounding_modes,
        default = 'DOWN',
        update = updateNode)

    draft_properties_mapping = dict(length = 'length_draft', accuracy = 'accuracy_draft')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.inputs.new('SvStringsSocket', "Length").prop_name = 'length'
        self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
        self.inputs.new('SvStringsSocket', "SegmentLength").prop_name = 'segment_length'
        self.outputs.new('SvStringsSocket', "T")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text = 'Mode:')
        layout.prop(self, 'eval_mode', text='')
        if self.eval_mode == 'LENGTH':
            layout.label(text='Rounding:')
            layout.prop(self, 'rounding_mode', text='')
        layout.prop(self, 'specify_accuracy')
        if self.specify_accuracy:
            if self.id_data.sv_draft:
                layout.prop(self, 'accuracy_draft')
            else:
                layout.prop(self, 'accuracy')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'mode', expand=True)

    def does_support_draft_mode(self):
        return True

    def draw_label(self):
        label = self.label or self.name
        if self.id_data.sv_draft:
            label = "[D] " + label
        return label

    def migrate_from(self, old_node):
        if old_node.bl_idname == 'SvExCurveLengthParameterNode':
            if old_node.eval_mode == 'AUTO':
                self.eval_mode = 'AUTO'
            elif old_node.eval_mode == 'MANUAL':
                self.eval_mode = 'MANUAL'

    def prepare_lengths(self, total_length, segment_length):
        if segment_length >= total_length:
            return np.array([0.0, total_length])
        if self.rounding_mode == 'DOWN':
            n = int(total_length // segment_length)
            return np.linspace(0.0, total_length, num = n+1)
        elif self.rounding_mode == 'UP':
            n = ceil(total_length / segment_length)
            return np.linspace(0.0, total_length, num = n+1)
        else: # CUT
            return np.arange(0.0, total_length, step = segment_length)

    def process(self):

        if not any((s.is_linked for s in self.outputs)):
            return

        need_eval = self.outputs['Vertices'].is_linked

        curves_s = self.inputs['Curve'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        length_s = self.inputs['Length'].sv_get()
        segment_length_s = self.inputs['SegmentLength'].sv_get()
        samples_s = self.inputs['Samples'].sv_get(default=[[]])

        length_s = ensure_nesting_level(length_s, 3)
        resolution_s = ensure_nesting_level(resolution_s, 2)
        samples_s = ensure_nesting_level(samples_s, 2)
        segment_length_s = ensure_nesting_level(segment_length_s, 2)
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

        ts_out = []
        verts_out = []
        for params in zip_long_repeat(curves_s, resolution_s, length_s, samples_s, segment_length_s):
            for curve, resolution, input_lengths, samples, segment_length in zip_long_repeat(*params):

                mode = self.mode
                accuracy = self.accuracy
                if self.id_data.sv_draft:
                    mode = 'LIN'
                    accuracy = self.accuracy_draft

                if self.specify_accuracy:
                    tolerance = 10 ** (-accuracy)
                else:
                    tolerance = None

                solver = SvCurveLengthSolver(curve)
                solver.prepare(mode, resolution, tolerance=tolerance)

                if self.eval_mode == 'AUTO':
                    total_length = solver.get_total_length()
                    input_lengths = np.linspace(0.0, total_length, num = samples)
                elif self.eval_mode == 'LENGTH':
                    total_length = solver.get_total_length()
                    input_lengths = self.prepare_lengths(total_length, segment_length)
                elif self.eval_mode == 'MANUAL':
                    input_lengths = np.array(input_lengths)

                ts = solver.solve(input_lengths)

                ts_out.append(ts.tolist())
                if need_eval:
                    verts = curve.evaluate_array(ts).tolist()
                    verts_out.append(verts)

        self.outputs['T'].sv_set(ts_out)
        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvCurveLengthParameterMk2Node)

def unregister():
    bpy.utils.unregister_class(SvCurveLengthParameterMk2Node)

