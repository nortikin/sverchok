
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.rbf import SvExRbfScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExMinimalScalarFieldNode', "Minimal Scalar Field", 'scipy')
else:
    from scipy.interpolate import Rbf

    class SvExMinimalScalarFieldNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Minimal Scalar Field
        Tooltip: Minimal Scalar Field
        """
        bl_idname = 'SvExMinimalScalarFieldNode'
        bl_label = 'Minimal Scalar Field'
        bl_icon = 'OUTLINER_OB_EMPTY'

        functions = [
            ('multiquadric', "Multi Quadric", "Multi Quadric", 0),
            ('inverse', "Inverse", "Inverse", 1),
            ('gaussian', "Gaussian", "Gaussian", 2),
            ('cubic', "Cubic", "Cubic", 3),
            ('quintic', "Quintic", "Qunitic", 4),
            ('thin_plate', "Thin Plate", "Thin Plate", 5)
        ]

        function : EnumProperty(
                name = "Function",
                items = functions,
                default = 'multiquadric',
                update = updateNode)

        epsilon : FloatProperty(
                name = "Epsilon",
                default = 1.0,
                min = 0.0,
                update = updateNode)
        
        smooth : FloatProperty(
                name = "Smooth",
                default = 0.0,
                min = 0.0,
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "Values")
            self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon'
            self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth'
            self.outputs.new('SvScalarFieldSocket', "Field")

        def draw_buttons(self, context, layout):
            layout.prop(self, "function")

        def process(self):

            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            values_s = self.inputs['Values'].sv_get()
            epsilon_s = self.inputs['Epsilon'].sv_get()
            smooth_s = self.inputs['Smooth'].sv_get()

            fields_out = []
            for vertices, values, epsilon, smooth in zip_long_repeat(vertices_s, values_s, epsilon_s, smooth_s):
                if isinstance(epsilon, (list, int)):
                    epsilon = epsilon[0]
                if isinstance(smooth, (list, int)):
                    smooth = smooth[0]

                XYZ_from = np.array(vertices)
                xs_from = XYZ_from[:,0]
                ys_from = XYZ_from[:,1]
                zs_from = XYZ_from[:,2]
                
                values = np.array(values)

                rbf = Rbf(xs_from, ys_from, zs_from, values,
                        function = self.function,
                        smooth = smooth,
                        epsilon = epsilon, mode='1-D')

                field = SvExRbfScalarField(rbf)
                fields_out.append(field)

            self.outputs['Field'].sv_set(fields_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExMinimalScalarFieldNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExMinimalScalarFieldNode)

