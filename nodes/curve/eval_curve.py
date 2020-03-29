
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvExCurve

class SvExEvalCurveNode(bpy.types.Node, SverchCustomTreeNode):
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

        def draw_buttons(self, context, layout):
            layout.prop(self, 'eval_mode', expand=True)

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', "Curve")
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

            if isinstance(curve_s[0], SvExCurve):
                curve_s = [curve_s]

            ts_s = ensure_nesting_level(ts_s, 2)
            samples_s = ensure_nesting_level(samples_s, 2)

            verts_out = []
            edges_out = []
            tangents_out = []
            for curves, ts_i, samples_i in zip_long_repeat(curve_s, ts_s, samples_s):
                if self.eval_mode == 'AUTO':
                    ts_i = [None]
                else:
                    samples_i = [None]
                for curve, ts, samples in zip_long_repeat(curves, ts_i, samples_i):
                    if self.eval_mode == 'AUTO':
                        t_min, t_max = curve.get_u_bounds()
                        ts = np.linspace(t_min, t_max, num=samples, dtype=np.float64)
                    else:
                        ts = np.array(ts)[np.newaxis].T

                    new_verts = curve.evaluate_array(ts)
                    new_verts = new_verts.tolist()
                    n = len(ts)
                    new_edges = [(i,i+1) for i in range(n-1)]
                    
                    verts_out.append(new_verts)
                    edges_out.append(new_edges)
                    if need_tangent:
                        new_tangents = curve.tangent_array(ts).tolist()
                        tangents_out.append(new_tangents)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Tangents'].sv_set(tangents_out)

def register():
    bpy.utils.register_class(SvExEvalCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExEvalCurveNode)

