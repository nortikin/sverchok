import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat

class SvExCurveZeroTwistFrameNode(bpy.types.Node, SverchCustomTreeNode):
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

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
            self.inputs.new('SvStringsSocket', "T")
            self.outputs.new('SvStringsSocket', "CumulativeTorsion")
            self.outputs.new('SvMatrixSocket', 'Matrix')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()
            resolution_s = self.inputs['Resolution'].sv_get()

            torsion_out = []
            matrix_out = []
            for curve, resolution, ts in zip_long_repeat(curve_s, resolution_s, ts_s):
                if isinstance(resolution, (list, tuple)):
                    resolution = resolution[0]
                    
                ts = np.array(ts)

                vectors = curve.evaluate_array(ts)
                matrices_np, normals, binormals = curve.frame_array(ts)

                curve.pre_calc_torsion_integral(resolution)
                integral = curve.torsion_integral(ts)

                new_matrices = []
                for matrix_np, point, angle in zip(matrices_np, vectors, integral):
                    frenet_matrix = Matrix(matrix_np.tolist()).to_4x4()
                    rotation_matrix = Matrix.Rotation(-angle, 4, 'Z')
                    #print("Z:", rotation_matrix)
                    matrix = frenet_matrix @ rotation_matrix
                    matrix.translation = Vector(point)
                    new_matrices.append(matrix)

                torsion_out.append(integral.tolist())
                matrix_out.append(new_matrices)

            self.outputs['CumulativeTorsion'].sv_set(torsion_out)
            self.outputs['Matrix'].sv_set(matrix_out)

def register():
    bpy.utils.register_class(SvExCurveZeroTwistFrameNode)

def unregister():
    bpy.utils.unregister_class(SvExCurveZeroTwistFrameNode)

