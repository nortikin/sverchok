
import numpy as np

import bpy
from bpy.props import FloatProperty, BoolProperty, IntProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.dependencies import skimage
from sverchok.utils.marching_squares import make_contours

if skimage is not None:
    from skimage import measure


class SvExMarchingSquaresNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Marching Squares
    Tooltip: Marching Squares
    """
    bl_idname = 'SvExMarchingSquaresNode'
    bl_label = 'Marching Squares'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_MSQUARES'
    sv_dependencies = {'skimage'}

    iso_value : FloatProperty(
            name = "Value",
            description="The value, for which the iso-curves should be built [list of values are allowed]",
            default = 1.0,
            update = updateNode)

    sample_size : IntProperty(
            name = "Samples",
            description = "Number of samples along X and Y axes. This defines the resolution of curves: the bigger is value, the more vertices will the node generate, and the more precise the curves will be",
            default = 50,
            min = 4,
            update = updateNode)

    z_value : FloatProperty(
            name = "Z",
            description = "The value of Z coordinate to generate the curves at [list of values are allowed]. By default the node will use the section of scalar field by XOY plane to draw the iso-curves for",
            default = 0.0,
            update = updateNode)

    min_x : FloatProperty(
            name = "Min X",
            description = "Minimum and maximum values of X and Y coordinates to find the iso-curves in",
            default = -1.0,
            update = updateNode)

    max_x : FloatProperty(
            name = "Max X",
            description = "Minimum and maximum values of X and Y coordinates to find the iso-curves in",
            default = 1.0,
            update = updateNode)

    min_y : FloatProperty(
            name = "Min Y",
            description = "Minimum and maximum values of X and Y coordinates to find the iso-curves in",
            default = -1.0,
            update = updateNode)

    max_y : FloatProperty(
            name = "Max Y",
            description = "Minimum and maximum values of X and Y coordinates to find the iso-curves in",
            default = 1.0,
            update = updateNode)

    def update_sockets(self, context):
        self.outputs['Faces'].hide_safe = not self.make_faces
        updateNode(self, context)

    make_faces : BoolProperty(
            name = "Make faces",
            description = "If checked, the node will generate Faces for iso-curves that are closed within specified X/Y bounds",
            default = False,
            update = update_sockets)

    connect_bounds : BoolProperty(
            name = "Connect boundary",
            description = "If checked, the node will connect pieces of the same curve, that was split because it was cut by specified X/Y bounds. Otherwise, several separate pieces will be generated in such case",
            default = True,
            update = updateNode)

    join : BoolProperty(
            name = "Flat output",
            description = "If checked, generate one flat list of objects for all input iso values. Otherwise, generate a separate list of objects for each input iso value.",
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
        layout.prop(self, 'join')
        layout.prop(self, 'make_faces')
        layout.prop(self, 'connect_bounds')

    def apply_matrix(self, matrix, xs, ys, zs):
        matrix = matrix.inverted()
        m = np.array(matrix.to_3x3())
        t = np.array(matrix.translation)
        points = np.stack((xs, ys, zs)).T
        points = np.apply_along_axis(lambda v: m @ v + t,1, points).T
        return points[0], points[1], points[2]

    def unapply_matrix(self, matrix, verts_s):
        matrix = matrix.inverted()
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
        input_level = get_data_nesting_level(fields_s, data_types=(SvScalarField,))
        nested_output = input_level > 1
        fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        matrix_s = ensure_nesting_level(matrix_s, 2, data_types=(Matrix,))

        parameters = zip_long_repeat(fields_s, matrix_s, min_x_s, max_x_s, min_y_s, max_y_s, z_value_s, value_s, samples_s)

        verts_out = []
        edges_out = []
        faces_out = []
        for field_i, matrix_i, min_x_i, max_x_i, min_y_i, max_y_i, z_value_i, value_i, samples_i in parameters:
            new_verts = []
            new_edges = []
            new_faces = []
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

                value_verts, value_edges, value_faces = make_contours(samples, samples, min_x, x_size, min_y, y_size, z_value, contours, make_faces=self.make_faces, connect_bounds = self.connect_bounds)
                if has_matrix:
                    value_verts = self.unapply_matrix(matrix, value_verts)

                if self.join:
                    new_verts.extend(value_verts)
                    new_edges.extend(value_edges)
                    new_faces.extend(value_faces)
                else:
                    new_verts.append(value_verts)
                    new_edges.append(value_edges)
                    new_faces.append(value_faces)

            if nested_output:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
            else:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvExMarchingSquaresNode)


def unregister():
    bpy.utils.unregister_class(SvExMarchingSquaresNode)
