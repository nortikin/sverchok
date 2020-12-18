import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, ZeroCurvatureException
from sverchok.utils.curve.algorithms import curve_frame_on_surface_array
from sverchok.utils.surface.core import SvSurface

class SvCurveFrameOnSurfNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Curve Frame on Surface
        Tooltip: Calculate reference frame of the curve in UV space of the surface, which is lying in the surface
        """
        bl_idname = 'SvCurveFrameOnSurfNode'
        bl_label = 'Curve Frame on Surface'
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

        error_modes = [
                ('ERROR', "Raise error", "Raise an error", 0),
                ('ANY', "Arbitrary frame", "Calculate any frame that has Z axis along curve's tangent", 1)
            ]

        def draw_buttons(self, context, layout):
            layout.prop(self, 'join', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvSurfaceSocket', "Surface")
            self.inputs.new('SvCurveSocket', "UVCurve")
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.outputs.new('SvMatrixSocket', 'Matrix')
            self.outputs.new('SvVerticesSocket', 'Tangent')
            self.outputs.new('SvVerticesSocket', 'Normal')
            self.outputs.new('SvVerticesSocket', 'Binormal')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surface_s = self.inputs['Surface'].sv_get()
            curve_s = self.inputs['UVCurve'].sv_get()
            ts_s = self.inputs['T'].sv_get()

            surface_s = ensure_nesting_level(surface_s, 2, data_types = (SvSurface,))
            curve_s = ensure_nesting_level(curve_s, 2, data_types = (SvCurve,))
            ts_s = ensure_nesting_level(ts_s, 3)

            matrix_out = []
            tangents_out = []
            normals_out = []
            binormals_out = []
            for surfaces_i, curves_i, ts_i in zip_long_repeat(surface_s, curve_s, ts_s):
                new_matrices = []
                new_tangents = []
                new_normals = []
                new_binormals = []
                for surface, curve, ts in zip_long_repeat(surfaces_i, curves_i, ts_i):
                    ts = np.array(ts)

                    matrices_np, points, tangents, normals, binormals = curve_frame_on_surface_array(surface, curve, ts)
                    curve_matrices = []
                    for matrix_np, point in zip(matrices_np, points):
                        matrix = Matrix(matrix_np.tolist()).to_4x4()
                        matrix.translation = Vector(point)
                        curve_matrices.append(matrix)

                    if self.join:
                        new_matrices.extend(curve_matrices)
                        new_tangents.extend(tangents.tolist())
                        new_normals.extend(normals.tolist())
                        new_binormals.extend(binormals.tolist())
                    else:
                        new_matrices.append(curve_matrices)
                        new_tangents.append(tangents.tolist())
                        new_normals.append(normals.tolist())
                        new_binormals.append(binormals.tolist())

                if self.join:
                    matrix_out.extend(new_matrices)
                    tangents_out.extend(new_tangents)
                    normals_out.extend(new_normals)
                    binormals_out.extend(new_binormals)
                else:
                    matrix_out.append(new_matrices)
                    tangents_out.append(new_tangents)
                    normals_out.append(new_normals)
                    binormals_out.append(new_binormals)

            self.outputs['Matrix'].sv_set(matrix_out)
            self.outputs['Tangent'].sv_set(tangents_out)
            self.outputs['Normal'].sv_set(normals_out)
            self.outputs['Binormal'].sv_set(binormals_out)

def register():
    bpy.utils.register_class(SvCurveFrameOnSurfNode)

def unregister():
    bpy.utils.unregister_class(SvCurveFrameOnSurfNode)

