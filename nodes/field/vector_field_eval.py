
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception

class SvExVectorFieldEvaluateNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Field Evaluate
    Tooltip: Evaluate Vector Field at specific point(s)
    """
    bl_idname = 'SvExVectorFieldEvaluateNode'
    bl_label = 'Evaluate Vector Field'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvExVectorFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
        d = self.inputs.new('SvVerticesSocket', "Vertices")
        d.use_prop = True
        d.prop = (0.0, 0.0, 0.0)
        self.outputs.new('SvVerticesSocket', 'Vectors')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        fields_s = self.inputs['Field'].sv_get()

        values_out = []
        for field, vertices in zip_long_repeat(fields_s, vertices_s):
            if len(vertices) == 0:
                new_values = []
            elif len(vertices) == 1:
                vertex = vertices[0]
                value = field.evaluate(*vertex)
                new_values = [tuple(value)]
            else:
                XYZ = np.array(vertices)
                xs = XYZ[:,0]
                ys = XYZ[:,1]
                zs = XYZ[:,2]
                new_xs, new_ys, new_zs = field.evaluate_grid(xs, ys, zs)
                new_vectors = np.dstack((new_xs[:], new_ys[:], new_zs[:]))
                new_values = new_vectors[0].tolist()

            values_out.append(new_values)

        self.outputs['Vectors'].sv_set(values_out)

def register():
    bpy.utils.register_class(SvExVectorFieldEvaluateNode)

def unregister():
    bpy.utils.unregister_class(SvExVectorFieldEvaluateNode)

