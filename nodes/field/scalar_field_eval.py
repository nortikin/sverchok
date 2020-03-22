
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.modules.eval_formula import get_variables, sv_compile, safe_eval_compiled
from sverchok.utils.logging import info, exception
from sverchok.utils.math import from_cylindrical, from_spherical, to_cylindrical, to_spherical

from sverchok.utils.math import coordinate_modes
from sverchok.utils.field.scalar import SvExScalarFieldLambda

class SvExScalarFieldEvaluateNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Evaluate
    Tooltip: Evaluate Scalar Field at specific point(s)
    """
    bl_idname = 'SvExScalarFieldEvaluateNode'
    bl_label = 'Evaluate Scalar Field'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvExScalarFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
        d = self.inputs.new('SvVerticesSocket', "Vertices")
        d.use_prop = True
        d.prop = (0.0, 0.0, 0.0)
        self.outputs.new('SvStringsSocket', 'Value')

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
                new_values = [value]
            else:
                XYZ = np.array(vertices)
                xs = XYZ[:,0]
                ys = XYZ[:,1]
                zs = XYZ[:,2]
                new_values = field.evaluate_grid(xs, ys, zs).tolist()
            values_out.append(new_values)

        self.outputs['Value'].sv_set(values_out)

def register():
    bpy.utils.register_class(SvExScalarFieldEvaluateNode)

def unregister():
    bpy.utils.unregister_class(SvExScalarFieldEvaluateNode)

