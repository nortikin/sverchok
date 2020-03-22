
import numpy as np
import math

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.logging import info, exception
from sverchok.utils.sv_mesh_utils import mesh_join

class SvExVectorFieldGraphNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Field Graph
    Tooltip: Generate a graphical representation of vector field
    """
    bl_idname = 'SvExVectorFieldGraphNode'
    bl_label = 'Vector Field Graph'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VECTOR_FIELD'

    samples_x : IntProperty(
        name = "Samples X",
        default = 10,
        min = 2,
        update = updateNode)

    samples_y : IntProperty(
        name = "Samples Y",
        default = 10,
        min = 2,
        update = updateNode)

    samples_z : IntProperty(
        name = "Samples Z",
        default = 10,
        min = 2,
        update = updateNode)

    scale : FloatProperty(
        name = "Scale",
        default = 1.0,
        min = 0.0,
        update = updateNode)

    join : BoolProperty(
        name = "Join",
        default = True,
        update = updateNode)

    @throttled
    def update_sockets(self, context):
        pass
        #self.inputs['Scale'].hide_safe = self.auto_scale

    auto_scale : BoolProperty(
        name = "Auto Scale",
        default = True,
        update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'auto_scale', toggle=True)
        layout.prop(self, 'join', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvExVectorFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
        self.inputs.new('SvVerticesSocket', "Bounds")
        self.inputs.new('SvStringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('SvStringsSocket', "SamplesX").prop_name = 'samples_x'
        self.inputs.new('SvStringsSocket', "SamplesY").prop_name = 'samples_y'
        self.inputs.new('SvStringsSocket', "SamplesZ").prop_name = 'samples_z'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        #self.outputs.new('SvStringsSocket', 'Faces')
        self.update_sockets(context)

    def get_bounds(self, vertices):
        vs = np.array(vertices)
        min = vs.min(axis=0)
        max = vs.max(axis=0)
        return min.tolist(), max.tolist()

    def generate_one(self, v1, v2, dv):
        dv = Vector(dv)
        size = dv.length
        dv = dv.normalized()
        orth = dv.orthogonal()
        arr1 = 0.1 * size * (orth - dv)
        arr2 = 0.1 * size * (-orth - dv)
        v3 = tuple(Vector(v2) + arr1)
        v4 = tuple(Vector(v2) + arr2)
        verts = [v1, v2, v3, v4]
        edges = [[0, 1], [1, 2], [1, 3]]
        return verts, edges

    def generate(self, points, vectors, scale):
        new_verts = []
        new_edges = []
        vectors = scale * vectors
        for v1, v2, dv in zip(points.tolist(), (points + vectors).tolist(), vectors.tolist()):
            verts, edges = self.generate_one(v1, v2, dv)
            new_verts.append(verts)
            new_edges.append(edges)
        return new_verts, new_edges

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field_s = self.inputs['Field'].sv_get()
        bounds_s = self.inputs['Bounds'].sv_get()
        scale_s = self.inputs['Scale'].sv_get()
        samples_x_s = self.inputs['SamplesX'].sv_get()
        samples_y_s = self.inputs['SamplesY'].sv_get()
        samples_z_s = self.inputs['SamplesZ'].sv_get()

        verts_out = []
        edges_out = []

        inputs = zip_long_repeat(field_s, bounds_s, scale_s, samples_x_s, samples_y_s, samples_z_s)
        for field, bounds, scale, samples_x, samples_y, samples_z in inputs:
            if isinstance(samples_x, (list, tuple)):
                samples_x = samples_x[0]
            if isinstance(samples_y, (list, tuple)):
                samples_y = samples_y[0]
            if isinstance(samples_z, (list, tuple)):
                samples_z = samples_z[0]
            if isinstance(scale, (list, tuple)):
                scale = scale[0]

            b1, b2 = self.get_bounds(bounds)
            b1n, b2n = np.array(b1), np.array(b2)
            self.debug("Bounds: %s - %s", b1, b2)

            x_range = np.linspace(b1[0], b2[0], num=samples_x)
            y_range = np.linspace(b1[1], b2[1], num=samples_y)
            z_range = np.linspace(b1[2], b2[2], num=samples_z)
            xs, ys, zs = np.meshgrid(x_range, y_range, z_range, indexing='ij')
            xs, ys, zs = xs.flatten(), ys.flatten(), zs.flatten()
            points = np.stack((xs, ys, zs)).T
            rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
            vectors = np.stack((rxs, rys, rzs)).T
            if self.auto_scale:
                norms = np.linalg.norm(vectors, axis=1)
                max_norm = norms.max()
                size = b2n - b1n
                size_x = size[0] / samples_x
                size_y = size[1] / samples_y
                size_z = size[2] / samples_z
                size = math.pow(size_x * size_y * size_z, 1.0/3.0)
                scale = scale * size / max_norm

            new_verts, new_edges = self.generate(points, vectors, scale)
            if self.join:
                new_verts, new_edges, _ = mesh_join(new_verts, new_edges, [[]] * len(new_verts))
            verts_out.append(new_verts)
            edges_out.append(new_edges)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)

def register():
    bpy.utils.register_class(SvExVectorFieldGraphNode)

def unregister():
    bpy.utils.unregister_class(SvExVectorFieldGraphNode)

