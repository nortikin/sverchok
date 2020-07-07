
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.surface import SvSurface
from sverchok.utils.marching_squares import make_contours
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import skimage

if skimage is None:
    add_dummy('SvExMSquaresOnSurfaceNode', "Marching Squares on Surface", 'skimage')
else:
    from skimage import measure

    class SvExMSquaresOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Marching Squares on Surface
        Tooltip: Marching Squares on Surface
        """
        bl_idname = 'SvExMSquaresOnSurfaceNode'
        bl_label = 'Marching Squares on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_MSQUARES'

        iso_value : FloatProperty(
                name = "Value",
                default = 1.0,
                update = updateNode)

        samples_u : IntProperty(
                name = "Samples U",
                default = 50,
                min = 4,
                update = updateNode)

        samples_v : IntProperty(
                name = "Samples V",
                default = 50,
                min = 4,
                update = updateNode)

        connect_bounds : BoolProperty(
                name = "Connect boundary",
                default = True,
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvScalarFieldSocket', "Field")
            self.inputs.new('SvSurfaceSocket', "Surface")
            self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
            self.inputs.new('SvStringsSocket', "SamplesU").prop_name = 'samples_u'
            self.inputs.new('SvStringsSocket', "SamplesV").prop_name = 'samples_v'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")

        def draw_buttons(self, context, layout):
            layout.prop(self, 'connect_bounds', toggle=True)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            fields_s = self.inputs['Field'].sv_get()
            surface_s = self.inputs['Surface'].sv_get()
            samples_u_s = self.inputs['SamplesU'].sv_get()
            samples_v_s = self.inputs['SamplesV'].sv_get()
            value_s = self.inputs['Value'].sv_get()

            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
            surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
            samples_u_s = ensure_nesting_level(samples_u_s, 2)
            samples_v_s = ensure_nesting_level(samples_v_s, 2)
            value_s = ensure_nesting_level(value_s, 2)

            verts_out = []
            edges_out = []
            for field_i, surface_i, samples_u_i, samples_v_i, value_i in zip_long_repeat(fields_s, surface_s, samples_u_s, samples_v_s, value_s):
                for field, surface, samples_u, samples_v, value in zip_long_repeat(field_i, surface_i, samples_u_i, samples_v_i, value_i):

                    u_min, u_max = surface.get_u_min(), surface.get_u_max()
                    v_min, v_max = surface.get_v_min(), surface.get_v_max()

                    u_range = np.linspace(u_min, u_max, num=samples_u)
                    v_range = np.linspace(v_min, v_max, num=samples_v)

                    us, vs = np.meshgrid(u_range, v_range, indexing='ij')
                    us, vs = us.flatten(), vs.flatten()

                    surface_points = surface.evaluate_array(us, vs)
                    xs = surface_points[:,0]
                    ys = surface_points[:,1]
                    zs = surface_points[:,2]

                    field_values = field.evaluate_grid(xs, ys, zs)
                    field_values = field_values.reshape((samples_u, samples_v))

                    contours = measure.find_contours(field_values, level=value)

                    u_size = (u_max - u_min)/samples_u
                    v_size = (v_max - v_min)/samples_v

                    uv_contours, new_edges, _ = make_contours(samples_u, samples_v, u_min, u_size, v_min, v_size, 0, contours, make_faces=False, connect_bounds = self.connect_bounds)

#                 new_verts = uv_points
                    for uv_points in uv_contours:
                        us = np.array([p[0] for p in uv_points])
                        vs = np.array([p[1] for p in uv_points])

                        new_verts = surface.evaluate_array(us, vs).tolist()

                        verts_out.append(new_verts)
                    edges_out.extend(new_edges)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)

def register():
    if skimage is not None:
        bpy.utils.register_class(SvExMSquaresOnSurfaceNode)

def unregister():
    if skimage is not None:
        bpy.utils.unregister_class(SvExMSquaresOnSurfaceNode)

