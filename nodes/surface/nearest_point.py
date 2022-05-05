import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix
from mathutils.kdtree import KDTree

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.surface import SvSurface
from sverchok.utils.manifolds import nearest_point_on_surface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExNearestPointOnSurfaceNode', "Nearest Point on Surface", 'scipy')
else:

    class SvExNearestPointOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Nearest Point on Surface
        Tooltip: Find the point on the surface which is the nearest to the given point
        """
        bl_idname = 'SvExNearestPointOnSurfaceNode'
        bl_label = 'Nearest Point on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_NEAREST_SURFACE'

        samples : IntProperty(
            name = "Init Resolution",
            default = 10,
            min = 3,
            update = updateNode)
        
        precise : BoolProperty(
            name = "Precise",
            default = True,
            update = updateNode)

        methods = [
            ('L-BFGS-B', "L-BFGS-B", "L-BFGS-B algorithm", 0),
            ('CG', "Conjugate Gradient", "Conjugate gradient algorithm", 1),
            ('TNC', "Truncated Newton", "Truncated Newton algorithm", 2),
            ('SLSQP', "SLSQP", "Sequential Least SQuares Programming algorithm", 3)
        ]

        method : EnumProperty(
            name = "Method",
            items = methods,
            default = 'L-BFGS-B',
            update = updateNode)

        sequential : BoolProperty(
            name = "Sequential",
            description = "If enabled, the node will use nearest point for one source point as initial guess for finding the nearest point for the next source point",
            default = False,
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'samples')
            layout.prop(self, 'precise')

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            if self.precise:
                layout.prop(self, 'method')
                layout.prop(self, 'sequential')

        def sv_init(self, context):
            self.inputs.new('SvSurfaceSocket', "Surface")
            p = self.inputs.new('SvVerticesSocket', "Point")
            p.use_prop = True
            p.default_property = (0.0, 0.0, 0.0)
            self.outputs.new('SvVerticesSocket', "Point")
            self.outputs.new('SvVerticesSocket', "UVPoint")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surfaces_s = self.inputs['Surface'].sv_get()
            surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
            src_point_s = self.inputs['Point'].sv_get()
            src_point_s = ensure_nesting_level(src_point_s, 4)

            need_points = self.outputs['Point'].is_linked

            points_out = []
            points_uv_out = []
            for surfaces, src_points_i in zip_long_repeat(surfaces_s, src_point_s):
                for surface, src_points in zip_long_repeat(surfaces, src_points_i):

                    new_uv = []
                    new_u = []
                    new_v = []
                    new_points = []

                    result = nearest_point_on_surface(src_points, surface,
                                init_samples = self.samples,
                                precise = self.precise,
                                method = self.method,
                                sequential = self.sequential,
                                output_points = need_points
                            )

                    if need_points:
                        new_u, new_v, new_points = result
                    else:
                        new_u, new_v = result

                    new_uv = [(u,v,0) for u, v in zip(new_u, new_v)]

                    points_out.append(new_points)
                    points_uv_out.append(new_uv)

            self.outputs['Point'].sv_set(points_out)
            self.outputs['UVPoint'].sv_set(points_uv_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExNearestPointOnSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExNearestPointOnSurfaceNode)

