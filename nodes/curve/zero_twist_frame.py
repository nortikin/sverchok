import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, throttle_and_update_node
from sverchok.utils.curve import SvCurve, SvNormalTrack

class SvCurveZeroTwistFrameNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Curve Zero-Twist Frame
        Tooltip: Calculate Zero-Twist Perpendicular frame for curve
        """
        bl_idname = 'SvExCurveZeroTwistFrameNode'
        bl_label = 'Curve Zero-Twist Frame'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_CURVE_FRAME'

        resolution : IntProperty(
            name = "Resolution",
            min = 10, default = 50,
            update = updateNode)

        t_value : FloatProperty(
                name = "T",
                default = 0.5,
                update = updateNode)

        join : BoolProperty(
                name = "Join",
                description = "If enabled, join generated lists of matrices; otherwise, output separate list of matrices for each curve",
                default = True,
                update = updateNode)

        @throttle_and_update_node
        def update_sockets(self, context):
            self.outputs['CumulativeTorsion'].hide_safe = self.algorithm != 'FRENET'

        algorithms = [
                ('FRENET', "Integrate torsion", "Substract torsion integral from Frenet matrices", 0),
                ('TRACK', "Track normal", "Try to maintain constant normal direction by tracking it along the curve", 1)
            ]

        algorithm : EnumProperty(
                name = "Algorithm",
                items = algorithms,
                default = 'FRENET',
                update = update_sockets)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'algorithm', text='')
            layout.prop(self, 'join', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.outputs.new('SvStringsSocket', "CumulativeTorsion")
            self.outputs.new('SvMatrixSocket', 'Matrix')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()
            resolution_s = self.inputs['Resolution'].sv_get()

            curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
            resolution_s = ensure_nesting_level(resolution_s, 2)
            ts_s = ensure_nesting_level(ts_s, 3)

            torsion_out = []
            matrix_out = []
            for curves, resolution_i, ts_i in zip_long_repeat(curve_s, resolution_s, ts_s):
                for curve, resolution, ts in zip_long_repeat(curves, resolution_i, ts_i):
                    ts = np.array(ts)

                    if self.algorithm == 'FRENET':
                        curve.pre_calc_torsion_integral(resolution)
                        new_torsion, new_matrices = curve.zero_torsion_frame_array(ts)
                        new_torsion = new_torsion.tolist()
                    else: # TRACK
                        tracker = SvNormalTrack(curve, resolution)
                        matrices_np = tracker.evaluate_array(ts)
                        points = curve.evaluate_array(ts)
                        new_matrices = []
                        for m, point in zip(matrices_np, points):
                            matrix = Matrix(m.tolist()).to_4x4()
                            matrix.translation = Vector(point)
                            new_matrices.append(matrix)
                        new_torsion = []

                    torsion_out.append(new_torsion)
                    if self.join:
                        matrix_out.extend(new_matrices)
                    else:
                        matrix_out.append(new_matrices)

            self.outputs['CumulativeTorsion'].sv_set(torsion_out)
            self.outputs['Matrix'].sv_set(matrix_out)

def register():
    bpy.utils.register_class(SvCurveZeroTwistFrameNode)

def unregister():
    bpy.utils.unregister_class(SvCurveZeroTwistFrameNode)

