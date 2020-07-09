
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.scalar import SvScalarField
from sverchok.dependencies import skimage
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.utils.marching_squares import make_contours

if skimage is None:
    add_dummy('SvExMarchingSquaresNode', "Marching Squares", 'skimage')
else:
    from skimage import measure

    class SvExMarchingSquaresNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Marching Squares
        Tooltip: Marching Squares
        """
        bl_idname = 'SvExMarchingSquaresNode'
        bl_label = 'Marching Squares'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_MSQUARES'

        iso_value : FloatProperty(
                name = "Value",
                default = 1.0,
                update = updateNode)

        sample_size : IntProperty(
                name = "Samples",
                default = 50,
                min = 4,
                update = updateNode)

        z_value : FloatProperty(
                name = "Z",
                default = 0.0,
                update = updateNode)

        min_x : FloatProperty(
                name = "Min X",
                default = -1.0,
                update = updateNode)

        max_x : FloatProperty(
                name = "Max X",
                default = 1.0,
                update = updateNode)

        min_y : FloatProperty(
                name = "Min Y",
                default = -1.0,
                update = updateNode)

        max_y : FloatProperty(
                name = "Max Y",
                default = 1.0,
                update = updateNode)

        @throttled
        def update_sockets(self, context):
            self.outputs['Faces'].hide_safe = not self.make_faces

        make_faces : BoolProperty(
                name = "Make faces",
                default = False,
                update = update_sockets)

        connect_bounds : BoolProperty(
                name = "Connect boundary",
                default = True,
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvScalarFieldSocket', "Field")
            self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.inputs.new('SvStringsSocket', "MinX").prop_name = 'min_x'
            self.inputs.new('SvStringsSocket', "MaxX").prop_name = 'max_x'
            self.inputs.new('SvStringsSocket', "MinY").prop_name = 'min_y'
            self.inputs.new('SvStringsSocket', "MaxY").prop_name = 'max_y'
            self.inputs.new('SvStringsSocket', "Z").prop_name = 'z_value'
            self.inputs.new('SvMatrixSocket', "Matrix")
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'make_faces', toggle=True)
            layout.prop(self, 'connect_bounds', toggle=True)

        def apply_matrix(self, matrix, xs, ys, zs):
            matrix = matrix.inverted()
            m = np.array(matrix.to_3x3())
            t = np.array(matrix.translation)
            points = np.stack((xs, ys, zs)).T
            points = np.apply_along_axis(lambda v: m @ v + t,1, points).T
            return points[0], points[1], points[2]

        def unapply_matrix(self, matrix, verts_s):
            def unapply(verts):
                m = np.array(matrix.to_3x3())
                t = np.array(matrix.translation)
                points = np.array(verts)
                points = np.apply_along_axis(lambda v: m @ v + t,1, points)
                return points.tolist()
            return list(map(unapply, verts_s))

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            fields_s = self.inputs['Field'].sv_get()
            min_x_s = self.inputs['MinX'].sv_get()
            max_x_s = self.inputs['MaxX'].sv_get()
            min_y_s = self.inputs['MinY'].sv_get()
            max_y_s = self.inputs['MaxY'].sv_get()
            value_s = self.inputs['Value'].sv_get()
            z_value_s = self.inputs['Z'].sv_get()
            samples_s = self.inputs['Samples'].sv_get()
            matrix_s = self.inputs['Matrix'].sv_get(default=[Matrix()])

            value_s = ensure_nesting_level(value_s, 2)
            z_value_s = ensure_nesting_level(z_value_s, 2)
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
            matrix_s = ensure_nesting_level(matrix_s, 2, data_types=(Matrix,))

            parameters = zip_long_repeat(fields_s, matrix_s, min_x_s, max_x_s, min_y_s, max_y_s, z_value_s, value_s, samples_s)

            verts_out = []
            edges_out = []
            faces_out = []
            for field_i, matrix_i, min_x_i, max_x_i, min_y_i, max_y_i, z_value_i, value_i, samples_i in parameters:
                objects = zip_long_repeat(field_i, matrix_i, min_x_i, max_x_i,
                                min_y_i, max_y_i, z_value_i, value_i, samples_i)
                for field, matrix, min_x, max_x, min_y, max_y, z_value, value, samples in objects:

                    has_matrix = matrix != Matrix()

                    x_range = np.linspace(min_x, max_x, num=samples)
                    y_range = np.linspace(min_y, max_y, num=samples)
                    z_range = np.array([z_value])
                    xs, ys, zs = np.meshgrid(x_range, y_range, z_range, indexing='ij')
                    xs, ys, zs = xs.flatten(), ys.flatten(), zs.flatten()
                    if has_matrix:
                        xs, ys, zs = self.apply_matrix(matrix, xs, ys, zs)
                    field_values = field.evaluate_grid(xs, ys, zs)
                    field_values = field_values.reshape((samples, samples))

                    contours = measure.find_contours(field_values, level=value)

                    x_size = (max_x - min_x)/samples
                    y_size = (max_y - min_y)/samples

                    new_verts, new_edges, new_faces = make_contours(samples, samples, min_x, x_size, min_y, y_size, z_value, contours, make_faces=self.make_faces, connect_bounds = self.connect_bounds)
                    if has_matrix:
                        new_verts = self.unapply_matrix(matrix, new_verts)
                    verts_out.extend(new_verts)
                    edges_out.extend(new_edges)
                    faces_out.extend(new_faces)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if skimage is not None:
        bpy.utils.register_class(SvExMarchingSquaresNode)

def unregister():
    if skimage is not None:
        bpy.utils.unregister_class(SvExMarchingSquaresNode)

