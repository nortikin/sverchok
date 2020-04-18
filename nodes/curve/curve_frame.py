import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat

class SvCurveFrameNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Curve Frame
        Tooltip: Calculate (Frenet) frame matrix at any point of the curve
        """
        bl_idname = 'SvExCurveFrameNode'
        bl_label = 'Curve Frame'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_CURVE_FRAME'

        t_value : FloatProperty(
                name = "T",
                default = 0.5,
                update = updateNode)

        join : BoolProperty(
                name = "Join",
                description = "If enabled, join generated lists of matrices; otherwise, output separate list of matrices for each curve",
                default = True,
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'join', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.outputs.new('SvMatrixSocket', 'Matrix')
            self.outputs.new('SvVerticesSocket', 'Normal')
            self.outputs.new('SvVerticesSocket', 'Binormal')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()

            matrix_out = []
            normals_out = []
            binormals_out = []
            for curve, ts in zip_long_repeat(curve_s, ts_s):
                ts = np.array(ts)

                verts = curve.evaluate_array(ts)
                matrices_np, normals, binormals = curve.frame_array(ts)
                new_matrices = []
                for matrix_np, point in zip(matrices_np, verts):
                    matrix = Matrix(matrix_np.tolist()).to_4x4()
                    matrix.translation = Vector(point)
                    new_matrices.append(matrix)

                if self.join:
                    matrix_out.extend(new_matrices)
                else:
                    matrix_out.append(new_matrices)
                normals_out.append(normals.tolist())
                binormals_out.append(binormals.tolist())

            self.outputs['Matrix'].sv_set(matrix_out)
            self.outputs['Normal'].sv_set(normals_out)
            self.outputs['Binormal'].sv_set(binormals_out)

def register():
    bpy.utils.register_class(SvCurveFrameNode)

def unregister():
    bpy.utils.unregister_class(SvCurveFrameNode)

