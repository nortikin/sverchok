
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.core.sockets import setup_new_node_location
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat
from sverchok.utils.logging import info, exception
from sverchok.utils.marching_cubes import isosurface_np
from sverchok.dependencies import mcubes, skimage
from sverchok.utils.nodes_mixins.draft_mode import DraftMode

if skimage is not None:
    import skimage.measure

# This node can work without dependencies, but slower.

class SvExMarchingCubesNode(DraftMode, bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Marching Cubes
    Tooltip: Marching Cubes
    """
    bl_idname = 'SvExMarchingCubesNode'
    bl_label = 'Marching Cubes'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_MCUBES'

    iso_value : FloatProperty(
            name = "Value",
            default = 1.0,
            update = updateNode)

    sample_size : IntProperty(
            name = "Samples",
            default = 50,
            min = 4,
            update = updateNode)

    sample_size_draft : IntProperty(
            name = "[D] Samples",
            default = 25,
            min = 4,
            update = updateNode)

    samples_x : IntProperty(
            name = "Samples X",
            default = 50,
            min = 4,
            update = updateNode)

    samples_y : IntProperty(
            name = "Samples Y",
            default = 50,
            min = 4,
            update = updateNode)

    samples_z : IntProperty(
            name = "Samples Z",
            default = 50,
            min = 4,
            update = updateNode)

    samples_x_draft : IntProperty(
            name = "[D] Samples X",
            default = 50,
            min = 4,
            update = updateNode)

    samples_y_draft : IntProperty(
            name = "[D] Samples Y",
            default = 50,
            min = 4,
            update = updateNode)

    samples_z_draft : IntProperty(
            name = "[D] Samples Z",
            default = 50,
            min = 4,
            update = updateNode)

    @throttled
    def update_sockets(self, context):
        self.outputs['VertexNormals'].hide_safe = self.implementation != 'skimage'
        self.inputs['Samples'].hide_safe = self.sample_mode != 'UNI'
        self.inputs['SamplesX'].hide_safe = self.sample_mode != 'XYZ'
        self.inputs['SamplesY'].hide_safe = self.sample_mode != 'XYZ'
        self.inputs['SamplesZ'].hide_safe = self.sample_mode != 'XYZ'

    sample_modes = [
            ('UNI', "Uniform", "Use uniform sampling - equal number of samples along X, Y and Z", 0),
            ('XYZ', "Non-uniform", "Use separate number of samples for X, Y and Z", 1)
        ]

    sample_mode : EnumProperty(
            name = "Sampling",
            items = sample_modes,
            default = 'UNI',
            update = update_sockets)

    draft_properties_mapping = dict(
            sample_size = 'sample_size_draft',
            samples_x = 'samples_x_draft',
            samples_y = 'samples_y_draft',
            samples_z = 'samples_z_draft'
        )

    def get_modes(self, context):
        modes = []
        if skimage is not None:
            modes.append(("skimage", "SciKit-Image", "SciKit-Image", 0))
        if mcubes is not None:
            modes.append(("mcubes", "PyMCubes", "PyMCubes", 1))
        modes.append(('python', "Pure Python", "Pure Python implementation", 2))
        return modes

    implementation : EnumProperty(
            name = "Implementation",
            items = get_modes,
            update = update_sockets)

    class BoundsMenuHandler():
        @classmethod
        def get_items(cls, socket, context):
            return [("BOX", "Add Box node", "Add Box node")]

        @classmethod
        def on_selected(cls, tree, node, socket, item, context):
            new_node = tree.nodes.new('SvBoxNodeMk2')
            new_node.label = "Bounds"
            tree.links.new(new_node.outputs[0], node.inputs['Bounds'])
            setup_new_node_location(new_node, node)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.inputs.new('SvVerticesSocket', "Bounds").link_menu_handler = 'BoundsMenuHandler'
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
        self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
        self.inputs.new('SvStringsSocket', "SamplesX").prop_name = 'samples_x'
        self.inputs.new('SvStringsSocket', "SamplesY").prop_name = 'samples_y'
        self.inputs.new('SvStringsSocket', "SamplesZ").prop_name = 'samples_z'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', "VertexNormals")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "implementation", text="")
        layout.prop(self, "sample_mode")
    
    def draw_label(self):
        label = self.label or self.name
        if self.id_data.sv_draft:
            label = "[D] " + label
        return label

    def get_bounds(self, vertices):
        vs = np.array(vertices)
        min = vs.min(axis=0)
        max = vs.max(axis=0)
        return min.tolist(), max.tolist()

    def scale_back(self, b1n, b2n, samples_x, samples_y, samples_z, verts):
        scale_x =  (b2n[0] - b1n[0]) / (samples_x - 1)
        scale_y =  (b2n[1] - b1n[1]) / (samples_y - 1)
        scale_z =  (b2n[2] - b1n[2]) / (samples_z - 1)
        verts[:,0] = verts[:,0] * scale_x + b1n[0]
        verts[:,1] = verts[:,1] * scale_y + b1n[1]
        verts[:,2] = verts[:,2] * scale_z + b1n[2]
        return verts

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        fields_s = self.inputs['Field'].sv_get()
        vertices_s = self.inputs['Bounds'].sv_get()
        value_s = self.inputs['Value'].sv_get()
        samples_s = self.inputs['Samples'].sv_get()
        samples_x_s = self.inputs['SamplesX'].sv_get()
        samples_y_s = self.inputs['SamplesY'].sv_get()
        samples_z_s = self.inputs['SamplesZ'].sv_get()

        if isinstance(value_s[0], (list, tuple)):
            value_s = value_s[0]

        parameters = match_long_repeat([fields_s, vertices_s, value_s, samples_s, samples_x_s, samples_y_s, samples_z_s])
        single_bounds = len(vertices_s) == 1

        verts_out = []
        faces_out = []
        normals_out = []

        func_values = None
        prev_field = None
        prev_samples = (None, None, None)

        for field, vertices, value, samples, samples_x, samples_y, samples_z in zip(*parameters):
            if isinstance(value, (list, tuple)):
                value = value[0]

            if isinstance(samples, (list, tuple)):
                samples = samples[0]
            if self.sample_mode == 'UNI':
                samples_x = samples_y = samples_z = samples
            else:
                if isinstance(samples_x, (list, tuple)):
                    samples_x = samples_x[0]
                if isinstance(samples_y, (list, tuple)):
                    samples_y = samples_y[0]
                if isinstance(samples_z, (list, tuple)):
                    samples_z = samples_z[0]

            b1, b2 = self.get_bounds(vertices)
            b1n, b2n = np.array(b1), np.array(b2)
            self.debug("Bounds: %s - %s", b1, b2)

            self.debug("Eval for value = %s", value)

            same_field = (prev_field is field)
            same_samples = prev_samples == (samples_x, samples_y, samples_z)

            need_eval = func_values is None or not same_field or not same_samples or not single_bounds

            if not same_field or func_values is None:
                x_range = np.linspace(b1[0], b2[0], num=samples_x)
                y_range = np.linspace(b1[1], b2[1], num=samples_y)
                z_range = np.linspace(b1[2], b2[2], num=samples_z)
                xs, ys, zs = np.meshgrid(x_range, y_range, z_range, indexing='ij')
                func_values = field.evaluate_grid(xs.flatten(), ys.flatten(), zs.flatten())
                func_values = func_values.reshape((samples_x, samples_y, samples_z))

            if self.implementation == 'mcubes':
                new_verts, new_faces = mcubes.marching_cubes(
                        func_values,
                        value)                         # Isosurface value

                new_verts = self.scale_back(b1n, b2n, samples_x, samples_y, samples_z, new_verts)
                new_verts, new_faces = new_verts.tolist(), new_faces.tolist()
                new_normals = []
            elif self.implementation == 'skimage':
                new_verts, new_faces, normals, values = skimage.measure.marching_cubes_lewiner(
                        func_values, level = value,
                        step_size = 1)
                new_verts = self.scale_back(b1n, b2n, samples_x, samples_y, samples_z, new_verts)
                new_verts, new_faces = new_verts.tolist(), new_faces.tolist()
                new_normals = normals.tolist()
            else: # python
                new_verts, new_faces = isosurface_np(func_values, value)
                new_verts = self.scale_back(b1n, b2n, samples_x, samples_y, samples_z, new_verts)
                new_verts = new_verts.tolist()
                new_normals = []

            prev_field = field
            prev_samples = (samples_x, samples_y, samples_z)

            verts_out.append(new_verts)
            faces_out.append(new_faces)
            normals_out.append(new_normals)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['VertexNormals'].sv_set(normals_out)

    def does_support_draft_mode(self):
        return True

def register():
    bpy.utils.register_class(SvExMarchingCubesNode)

def unregister():
    bpy.utils.unregister_class(SvExMarchingCubesNode)

