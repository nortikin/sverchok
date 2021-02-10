
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.rbf import SvRbfVectorField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy
from sverchok.utils.math import rbf_functions

if scipy is None:
    add_dummy('SvExMinimalVectorFieldNode', "Minimal Vector Field", 'scipy')
else:
    from scipy.interpolate import Rbf

    class SvExMinimalVectorFieldNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: RBF Minimal Vector Field
        Tooltip: RBF Vector Field
        """
        bl_idname = 'SvExMinimalVectorFieldNode'
        bl_label = 'RBF Vector Field'
        bl_icon = 'OUTLINER_OB_EMPTY'

        function : EnumProperty(
                name = "Function",
                items = rbf_functions,
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

        types = [
                    ('R', "Relative", "Field value in the point means the vector of force applied to this point", 0),
                    ('A', "Absolute", "Field value in the point means the new point where this point should be moved to", 1)
                ]

        field_type : EnumProperty(
                name = "Type",
                description = "Field type",
                items = types,
                default = 'R',
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "VerticesFrom")
            self.inputs.new('SvVerticesSocket', "VerticesTo")
            self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon'
            self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth'
            self.outputs.new('SvVectorFieldSocket', "Field")

        def draw_buttons(self, context, layout):
            layout.prop(self, "field_type", text='')
            layout.prop(self, "function")

        def process(self):

            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_from_s = self.inputs['VerticesFrom'].sv_get()
            vertices_to_s = self.inputs['VerticesTo'].sv_get()
            epsilon_s = self.inputs['Epsilon'].sv_get()
            smooth_s = self.inputs['Smooth'].sv_get()

            fields_out = []
            for vertices_from, vertices_to, epsilon, smooth in zip_long_repeat(vertices_from_s, vertices_to_s, epsilon_s, smooth_s):
                if isinstance(epsilon, (list, int)):
                    epsilon = epsilon[0]
                if isinstance(smooth, (list, int)):
                    smooth = smooth[0]

                XYZ_from = np.array(vertices_from)
                xs_from = XYZ_from[:,0]
                ys_from = XYZ_from[:,1]
                zs_from = XYZ_from[:,2]
                
                XYZ_to = np.array(vertices_to)
                if self.field_type == 'R':
                    XYZ_to = XYZ_from + XYZ_to

                rbf = Rbf(xs_from, ys_from, zs_from, XYZ_to,
                        function = self.function,
                        smooth = smooth,
                        epsilon = epsilon, mode='N-D')

                field = SvRbfVectorField(rbf, relative = self.field_type == 'R')
                fields_out.append(field)

            self.outputs['Field'].sv_set(fields_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExMinimalVectorFieldNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExMinimalVectorFieldNode)

