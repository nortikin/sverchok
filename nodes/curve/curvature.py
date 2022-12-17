import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve, DEFAULT_TANGENT_DELTA

class SvCurveCurvatureNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: Curve Curvature
        Tooltip: Calculate curvature of the curve
        """
        bl_idname = 'SvExCurveCurvatureNode'
        bl_label = 'Curve Curvature'
        bl_icon = 'CURVE_NCURVE'

        t_value : FloatProperty(
                name = "T",
                default = 0.5,
                update = updateNode)

        tangent_delta : FloatProperty(
                name = "Tangent step",
                description = "Derivatives calculation step; bigger values lead to more smooth results",
                min = 0.0,
                precision = 8,
                default = DEFAULT_TANGENT_DELTA,
                update = updateNode)
        
        numpy_out : BoolProperty(
                name = "NumPy output",
                description = "Output data as NumPy arrays",
                default = False,
                update = updateNode)

        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'numpy_out')
            layout.prop(self, 'tangent_delta')

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.outputs.new('SvStringsSocket', "Curvature")
            self.outputs.new('SvStringsSocket', "Radius")
            self.outputs.new('SvMatrixSocket', 'Center')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()

            input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
            nested_output = input_level > 1

            curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
            ts_s = ensure_nesting_level(ts_s, 3)

            center_out = []
            curvature_out = []
            radius_out = []
            for params in zip_long_repeat(curve_s, ts_s):
                new_centers = []
                new_curvature = []
                new_radius = []
                for curve, ts in zip_long_repeat(*params):
                    ts = np.asarray(ts)

                    verts = curve.evaluate_array(ts)

                    curvatures = curve.curvature_array(ts)
                    radiuses = 1.0 / curvatures

                    tangents = curve.tangent_array(ts)
                    tangents = tangents / np.linalg.norm(tangents, axis=1)[np.newaxis].T
                    binormals = curve.binormal_array(ts)
                    normals = curve.main_normal_array(ts)

                    radius_vectors = radiuses[np.newaxis].T * normals
                    centers = verts + radius_vectors

                    matrices_np = np.dstack((-normals, tangents, binormals))
                    matrices_np = np.transpose(matrices_np, axes=(0,2,1))
                    dets = np.linalg.det(matrices_np)
                    good_idx = abs(dets) > 1e-6
                    matrices_np[good_idx] = np.linalg.inv(matrices_np[good_idx])

                    curve_centers = []
                    for ok, matrix_np, center in zip(good_idx, matrices_np, centers):
                        if ok:
                            matrix = Matrix(matrix_np.tolist()).to_4x4()
                            matrix.translation = Vector(center)
                        else:
                            matrix = Matrix.Translation(center)
                        if self.numpy_out:
                            matrix = np.array(matrix)
                        curve_centers.append(matrix)

                    if not self.numpy_out:
                        curvatures = curvatures.tolist()
                        radiuses = radiuses.tolist()
                    new_curvature.append(curvatures)
                    new_radius.append(radiuses)
                    new_centers.append(curve_centers)

                if nested_output:
                    center_out.append(new_centers)
                    radius_out.append(new_radius)
                    curvature_out.append(new_curvature)
                else:
                    center_out.extend(new_centers)
                    radius_out.extend(new_radius)
                    curvature_out.extend(new_curvature)

            self.outputs['Center'].sv_set(center_out)
            self.outputs['Curvature'].sv_set(curvature_out)
            self.outputs['Radius'].sv_set(radius_out)

def register():
    bpy.utils.register_class(SvCurveCurvatureNode)

def unregister():
    bpy.utils.unregister_class(SvCurveCurvatureNode)
