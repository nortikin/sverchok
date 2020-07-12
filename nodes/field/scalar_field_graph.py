
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.marching_squares import make_contours
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import skimage

if skimage is None:
    add_dummy('SvExScalarFieldGraphNode', "Scalar Field Graph", 'skimage')
else:
    from skimage import measure

    class SvExScalarFieldGraphNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Scalar Field Graph
        Tooltip: Generate a graphical representation of the scalar field
        """
        bl_idname = 'SvExScalarFieldGraphNode'
        bl_label = 'Scalar Field Graph'
        bl_icon = 'OUTLINER_OB_EMPTY'

        samples_xy : IntProperty(
            name = "Samples X/Y",
            default = 50,
            min = 3,
            update = updateNode)

        samples_z : IntProperty(
            name = "Samples Z",
            default = 10,
            min = 2,
            update = updateNode)

        samples_value : IntProperty(
            name = "Value samples",
            default = 10,
            min = 2,
            update = updateNode)

        join : BoolProperty(
            name = "Join",
            default = True,
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
                default = False,
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'make_faces', toggle=True)
            layout.prop(self, 'connect_bounds', toggle=True)
            layout.prop(self, 'join', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvScalarFieldSocket', "Field")
            self.inputs.new('SvVerticesSocket', "Bounds")
            self.inputs.new('SvStringsSocket', "SamplesXY").prop_name = 'samples_xy'
            self.inputs.new('SvStringsSocket', "SamplesZ").prop_name = 'samples_z'
            self.inputs.new('SvStringsSocket', "ValueSamples").prop_name = 'samples_value'
            self.outputs.new('SvVerticesSocket', 'Vertices')
            self.outputs.new('SvStringsSocket', 'Edges')
            self.outputs.new('SvStringsSocket', "Faces")
            self.update_sockets(context)

        def get_bounds(self, vertices):
            vs = np.array(vertices)
            min = vs.min(axis=0)
            max = vs.max(axis=0)
            return min.tolist(), max.tolist()

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            field_s = self.inputs['Field'].sv_get()
            bounds_s = self.inputs['Bounds'].sv_get()
            samples_xy_s = self.inputs['SamplesXY'].sv_get()
            samples_z_s = self.inputs['SamplesZ'].sv_get()
            samples_value_s = self.inputs['ValueSamples'].sv_get()

            verts_out = []
            edges_out = []
            faces_out = []

            inputs = zip_long_repeat(field_s, bounds_s, samples_xy_s, samples_z_s, samples_value_s)
            for field, bounds, samples_xy, samples_z, samples_value in inputs:
                if isinstance(samples_xy, (list, tuple)):
                    samples_xy = samples_xy[0]
                if isinstance(samples_z, (list, tuple)):
                    samples_z = samples_z[0]
                if isinstance(samples_value, (list, tuple)):
                    samples_value = samples_value[0]

                b1, b2 = self.get_bounds(bounds)
                min_x, max_x = b1[0], b2[0]
                min_y, max_y = b1[1], b2[1]
                min_z, max_z = b1[2], b2[2]

                x_size = (max_x - min_x)/samples_xy
                y_size = (max_y - min_y)/samples_xy

                x_range = np.linspace(min_x, max_x, num=samples_xy)
                y_range = np.linspace(min_y, max_y, num=samples_xy)
                z_range = np.linspace(min_z, max_z, num=samples_z)
                xs, ys, zs = np.meshgrid(x_range, y_range, z_range, indexing='ij')
                xs, ys, zs = xs.flatten(), ys.flatten(), zs.flatten()
                field_values = field.evaluate_grid(xs, ys, zs)
                min_field = field_values.min()
                max_field = field_values.max()
                field_values = field_values.reshape((samples_xy, samples_xy, samples_z))
                field_stops = np.linspace(min_field, max_field, num=samples_value)

                new_verts = []
                new_edges = []
                new_faces = []
                for i in range(samples_z):
                    z_value = zs[i]
                    z_verts = []
                    z_edges = []
                    z_faces = []
                    for j in range(samples_value):
                        value = field_stops[j]
                        contours = measure.find_contours(field_values[:,:,i], level=value)

                        value_verts, value_edges, value_faces = make_contours(samples_xy, samples_xy,
                                        min_x, x_size, min_y, y_size, z_value, contours,
                                        make_faces=self.make_faces, connect_bounds = self.connect_bounds)
                        if value_verts:
                            z_verts.extend(value_verts)
                            z_edges.extend(value_edges)
                            z_faces.extend(value_faces)

                    new_verts.extend(z_verts)
                    new_edges.extend(z_edges)
                    new_faces.extend(z_faces)

                if self.join:
                    new_verts, new_edges, new_faces = mesh_join(new_verts, new_edges, new_faces)

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
    if skimage is not None:
        bpy.utils.register_class(SvExScalarFieldGraphNode)

def unregister():
    if skimage is not None:
        bpy.utils.unregister_class(SvExScalarFieldGraphNode)

