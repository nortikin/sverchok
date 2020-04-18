
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception

class SvVectorFieldApplyNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Field Apply
    Tooltip: Apply Vector Field to vertices
    """
    bl_idname = 'SvExVectorFieldApplyNode'
    bl_label = 'Apply Vector Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_APPLY_VFIELD'

    coefficient : FloatProperty(
            name = "Coefficient",
            default = 1.0,
            update = updateNode)

    iterations : IntProperty(
            name = "Iterations",
            default = 1,
            min = 1,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVectorFieldSocket', "Field")
        d = self.inputs.new('SvVerticesSocket', "Vertices")
        d.use_prop = True
        d.prop = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
        self.inputs.new('SvStringsSocket', "Iterations").prop_name = 'iterations'
        self.outputs.new('SvVerticesSocket', 'Vertices')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        coeffs_s = self.inputs['Coefficient'].sv_get()
        fields_s = self.inputs['Field'].sv_get()
        iterations_s = self.inputs['Iterations'].sv_get()

        vertices_s = ensure_nesting_level(vertices_s, 4)
        coeffs_s = ensure_nesting_level(coeffs_s, 3)

        verts_out = []
        for fields, vertices_l, coeffs_l, iterations_l in zip_long_repeat(fields_s, vertices_s, coeffs_s, iterations_s):
            if not isinstance(iterations_l, (list, tuple)):
                iterations_l = [iterations_l]
            if not isinstance(fields, (list, tuple)):
                fields = [fields]

            for field, vertices, coeffs, iterations in zip_long_repeat(fields, vertices_l, coeffs_l, iterations_l):

                if len(vertices) == 0:
                    new_verts = []
                elif len(vertices) == 1:
                    vertex = vertices[0]
                    coeff = coeffs[0]
                    for i in range(iterations):
                        vector = field.evaluate(*vertex)
                        vertex = (np.array(vertex) + coeff * vector).tolist()
                    new_verts = [vertex]
                else:
                    coeffs = repeat_last_for_length(coeffs, len(vertices))
                    vertices = np.array(vertices)
                    for i in range(iterations):
                        xs = vertices[:,0]
                        ys = vertices[:,1]
                        zs = vertices[:,2]
                        new_xs, new_ys, new_zs = field.evaluate_grid(xs, ys, zs)
                        new_vectors = np.dstack((new_xs[:], new_ys[:], new_zs[:]))
                        new_vectors = np.array(coeffs)[np.newaxis].T * new_vectors[0]
                        vertices = vertices + new_vectors
                    new_verts = vertices.tolist()

                verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvVectorFieldApplyNode)

def unregister():
    bpy.utils.unregister_class(SvVectorFieldApplyNode)

