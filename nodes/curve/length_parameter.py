import numpy as np

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurveLengthSolver, SvCurve
from sverchok.utils.nodes_mixins.draft_mode import DraftMode


class SvCurveLengthParameterNode(DraftMode, bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Length Parameter
    Tooltip: Solve curve length (natural) parameter
    """
    bl_idname = 'SvExCurveLengthParameterNode'
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

    @throttled
    def update_sockets(self, context):
        self.inputs['Length'].hide_safe = self.eval_mode != 'MANUAL'
        self.inputs['Samples'].hide_safe = self.eval_mode != 'AUTO'

    eval_modes = [
        ('AUTO', "Automatic", "Evaluate the curve at evenly spaced points", 0),
        ('MANUAL', "Manual", "Evaluate the curve at specified points", 1)
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

    draft_properties_mapping = dict(length = 'length_draft')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.inputs.new('SvStringsSocket', "Length").prop_name = 'length'
        self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
        self.outputs.new('SvStringsSocket', "T")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'eval_mode', expand=True)

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

    def process(self):

        if not any((s.is_linked for s in self.outputs)):
            return

        need_eval = self.outputs['Vertices'].is_linked

        curves_s = self.inputs['Curve'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        length_s = self.inputs['Length'].sv_get()
        samples_s = self.inputs['Samples'].sv_get(default=[[]])

        length_s = ensure_nesting_level(length_s, 3)
        resolution_s = ensure_nesting_level(resolution_s, 2)
        samples_s = ensure_nesting_level(samples_s, 2)
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

        ts_out = []
        verts_out = []
        for curves, resolutions, input_lengths_i, samples_i in zip_long_repeat(curves_s, resolution_s, length_s, samples_s):
            for curve, resolution, input_lengths, samples in zip_long_repeat(curves, resolutions, input_lengths_i, samples_i):

                mode = self.mode
                if self.id_data.sv_draft:
                    mode = 'LIN'
                solver = SvCurveLengthSolver(curve)
                solver.prepare(mode, resolution)

                if self.eval_mode == 'AUTO':
                    total_length = solver.get_total_length()
                    input_lengths = np.linspace(0.0, total_length, num = samples)
                else:
                    input_lengths = np.array(input_lengths)

                ts = solver.solve(input_lengths)

                ts_out.append(ts.tolist())
                if need_eval:
                    verts = curve.evaluate_array(ts).tolist()
                    verts_out.append(verts)

        self.outputs['T'].sv_set(ts_out)
        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvCurveLengthParameterNode)

def unregister():
    bpy.utils.unregister_class(SvCurveLengthParameterNode)

