
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve

class SvEvalCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Evaluate Curve
        Tooltip: Evaluate Curve
        """
        bl_idname = 'SvExEvalCurveNode'
        bl_label = 'Evaluate Curve'
        bl_icon = 'CURVE_NCURVE'

        modes = [
            ('AUTO', "Automatic", "Evaluate the curve at evenly spaced points", 0),
            ('MANUAL', "Manual", "Evaluate the curve at specified points", 1)
        ]

        @throttled
        def update_sockets(self, context):
            self.inputs['T'].hide_safe = self.eval_mode != 'MANUAL'
            self.inputs['Samples'].hide_safe = self.eval_mode != 'AUTO'

        eval_mode : EnumProperty(
            name = "Mode",
            items = modes,
            default = 'AUTO',
            update = update_sockets)

        sample_size : IntProperty(
                name = "Samples",
                default = 50,
                min = 4,
                update = updateNode)

        t_value : FloatProperty(
            name = "T",
            default = 0.5,
            update = updateNode)

        join : BoolProperty(
                name = "Join",
                description = "Output single list of vertices / edges for all input curves",
                default = True,
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'eval_mode', expand=True)
            layout.prop(self, 'join', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvVerticesSocket', "Tangents")
            self.update_sockets(context)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get(default=[[]])
            samples_s = self.inputs['Samples'].sv_get(default=[[]])

            need_tangent = self.outputs['Tangents'].is_linked

            curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,), input_name='Curve')
            ts_s = ensure_nesting_level(ts_s, 3, input_name='T')
            samples_s = ensure_nesting_level(samples_s, 2, input_name='Samples')

            verts_out = []
            edges_out = []
            tangents_out = []
            for curves, ts_i, samples_i in zip_long_repeat(curve_s, ts_s, samples_s):
                if self.eval_mode == 'AUTO':
                    ts_i = [None]
                else:
                    samples_i = [None]

                new_verts = []
                new_edges = []
                new_tangents = []
                for curve, ts, samples in zip_long_repeat(curves, ts_i, samples_i):
                    if self.eval_mode == 'AUTO':
                        t_min, t_max = curve.get_u_bounds()
                        ts = np.linspace(t_min, t_max, num=samples, dtype=np.float64)
                    else:
                        ts = np.array(ts)

                    curve_verts = curve.evaluate_array(ts)
                    curve_verts = curve_verts.tolist()
                    n = len(ts)
                    curve_edges = [(i,i+1) for i in range(n-1)]
                    
                    new_verts.append(curve_verts)
                    new_edges.append(curve_edges)
                    if need_tangent:
                        curve_tangents = curve.tangent_array(ts).tolist()
                        new_tangents.append(curve_tangents)
                if self.join:
                    verts_out.extend(new_verts)
                    edges_out.extend(new_edges)
                    tangents_out.extend(new_tangents)
                else:
                    verts_out.append(new_verts)
                    edges_out.append(new_edges)
                    tangents_out.append(new_tangents)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Tangents'].sv_set(tangents_out)

def register():
    bpy.utils.register_class(SvEvalCurveNode)

def unregister():
    bpy.utils.unregister_class(SvEvalCurveNode)

