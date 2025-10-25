import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, ZeroCurvatureException

class SvCurveFrameNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: Curve Frenet Frame
        Tooltip: Calculate (Frenet) frame matrix at any point of the curve
        """
        bl_idname = 'SvExCurveFrameNode'
        bl_label = 'Curve Frame'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_CURVE_FRAME'

        t_value : FloatProperty(
                name = "T",
                description = "The value of curve’s T parameter",
                default = 0.5,
                update = updateNode)

        join : BoolProperty(
                name = "Join",
                description = "If enabled, join generated lists of matrices; otherwise, output separate list of matrices for each curve",
                default = True,
                update = updateNode)

        error_modes = [
                ('ERROR', "Raise error", "Raise an error", 0),
                ('ANY', "Arbitrary frame", "Calculate any frame that has Z axis along curve's tangent", 1)
            ]

        on_error : EnumProperty(
                name = "On zero curvature",
                description = "What the node should do if it encounters a point with zero curvature - it is impossible to calculate correct Frenet frame at such points",
                items = error_modes,
                default = 'ERROR',
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'join', toggle=True)

        def draw_buttons_ext(self, context, layout):
            layout.label(text='On zero curvature:')
            layout.prop(self, 'on_error', text='')

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
            objects_s2 = ensure_nesting_level(curve_s, 2)
            ts_s = self.inputs['T'].sv_get()
            ts_s3 = ensure_nesting_level(ts_s, 3)

            matrix_out = []
            normals_out = []
            binormals_out = []
            for obj, ts_list in zip_long_repeat(objects_s2, ts_s3):
                curve_matrix = []
                curve_normals = []
                curve_binormals = []
                for curve, tsn in zip_long_repeat(obj, ts_list):
                    ts = np.array(tsn)
                    verts = curve.evaluate_array(ts)
                    try:
                        matrices_np, normals, binormals = curve.frame_array(ts, on_zero_curvature = SvCurve.FAIL)
                    except ZeroCurvatureException as e:
                        if self.on_error == 'ERROR':
                            raise Exception(e.get_message() + ". It is impossible to calculate correct Frenet frames for such points")
                        else: # ANY
                            bad_mask = e.mask
                            good_mask = np.logical_not(bad_mask)
                            good_ts = ts[good_mask]
                            bad_ts = ts[bad_mask]

                            n = len(ts)
                            matrices_np = np.zeros((n, 3, 3))
                            normals = np.zeros((n, 3))
                            binormals = np.zeros((n, 3))
                            if good_mask.any():
                                matrices_np[good_mask], normals[good_mask], binormals[good_mask] = curve.frame_array(good_ts)
                            matrices_np[bad_mask], normals[bad_mask], binormals[bad_mask] = curve.arbitrary_frame_array(bad_ts)

                    new_matrices = []
                    for matrix_np, point in zip(matrices_np, verts):
                        matrix = Matrix(matrix_np.tolist()).to_4x4()
                        matrix.translation = Vector(point)
                        new_matrices.append(matrix)
                    
                    if self.join:
                        curve_matrix.extend(new_matrices)
                        curve_normals.extend(normals.tolist())
                        curve_binormals.extend(binormals.tolist())
                    else:
                        curve_matrix.append(new_matrices)
                        curve_normals.append(normals.tolist())
                        curve_binormals.append(binormals.tolist())
                    
                matrix_out.append(curve_matrix)
                normals_out.append(curve_normals)
                binormals_out.append(curve_binormals)

            self.outputs['Matrix'].sv_set(matrix_out)
            self.outputs['Normal'].sv_set(normals_out)
            self.outputs['Binormal'].sv_set(binormals_out)

def register():
    bpy.utils.register_class(SvCurveFrameNode)

def unregister():
    bpy.utils.unregister_class(SvCurveFrameNode)

