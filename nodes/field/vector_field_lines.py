
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.sv_mesh_utils import mesh_join

class SvVectorFieldLinesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Field Lines
    Tooltip: Generate vector field lines
    """
    bl_idname = 'SvExVectorFieldLinesNode'
    bl_label = 'Vector Field Lines'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VECTOR_FIELD_LINES'

    step : FloatProperty(
            name = "Step",
            default = 0.1,
            min = 0.0,
            update = updateNode)

    iterations : IntProperty(
            name = "Iterations",
            default = 10,
            min = 1,
            update = updateNode)

    normalize : BoolProperty(
        name = "Normalize",
        default = True,
        update = updateNode)

    join : BoolProperty(
        name = "Join",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'normalize', toggle=True)
        layout.prop(self, 'join', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVectorFieldSocket', "Field")
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Step").prop_name = 'step'
        self.inputs.new('SvStringsSocket', "Iterations").prop_name = 'iterations'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')

    def generate_all(self, field, vertices, step, iterations):
        new_verts = np.empty((iterations, len(vertices), 3))
        for i in range(iterations):
            xs = vertices[:,0]
            ys = vertices[:,1]
            zs = vertices[:,2]
            new_xs, new_ys, new_zs = field.evaluate_grid(xs, ys, zs)
            vectors = np.stack((new_xs, new_ys, new_zs)).T
            if self.normalize:
                norms = np.linalg.norm(vectors, axis=1)[np.newaxis].T
                vertices = vertices + step * vectors / norms
            else:
                vertices = vertices + step * vectors
            new_verts[i,:,:] = vertices
        result = np.transpose(new_verts, axes=(1, 0, 2))
        return result.tolist()

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        step_s = self.inputs['Step'].sv_get()
        fields_s = self.inputs['Field'].sv_get()
        iterations_s = self.inputs['Iterations'].sv_get()

        vertices_s = ensure_nesting_level(vertices_s, 4)
        step_s = ensure_nesting_level(step_s, 2)

        verts_out = []
        edges_out = []

        for fields, vertices_l, steps_l, iterations_l in zip_long_repeat(fields_s, vertices_s, step_s, iterations_s):
            if not isinstance(iterations_l, (list, tuple)):
                iterations_l = [iterations_l]
            if not isinstance(steps_l, (list, tuple)):
                steps_l = [steps_l]
            if not isinstance(fields, (list, tuple)):
                fields = [fields]

            field_verts = []
            field_edges = []
            for field, vertices, step, iterations in zip_long_repeat(fields, vertices_l, steps_l, iterations_l):

                if len(vertices) == 0:
                    new_verts = []
                    new_edges = []
                else:
                    new_verts = self.generate_all(field, np.array(vertices), step, iterations)
                    new_edges = [[(i,i+1) for i in range(iterations-1)]] * len(vertices)
                    if self.join:
                        new_verts, new_edges, _ = mesh_join(new_verts, new_edges, [[]] * len(new_verts))
                if self.join:
                    field_verts.append(new_verts)
                    field_edges.append(new_edges)
                else:
                    field_verts.extend(new_verts)
                    field_edges.extend(new_edges)

            verts_out.extend(field_verts)
            edges_out.extend(field_edges)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)

def register():
    bpy.utils.register_class(SvVectorFieldLinesNode)

def unregister():
    bpy.utils.unregister_class(SvVectorFieldLinesNode)

