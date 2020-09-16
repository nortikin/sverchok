import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface
from sverchok.utils.manifolds import raycast_surface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExRaycastSurfaceNode', "Raycast on Surface", 'scipy')
else:

    class SvExRaycastSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Raycast on Surface
        Tooltip: Raycast on Surface
        """
        bl_idname = 'SvExRaycastSurfaceNode'
        bl_label = 'Raycast on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_SURFACE_RAYCAST'

        samples : IntProperty(
            name = "Init Resolution",
            default = 10,
            min = 3,
            update = updateNode)
        
        precise : BoolProperty(
            name = "Precise",
            default = True,
            update = updateNode)

        @throttled
        def update_sockets(self, context):
            self.inputs['Source'].hide_safe = self.project_mode != 'CONIC'
            self.inputs['Direction'].hide_safe = self.project_mode != 'PARALLEL'

        modes = [
            ('PARALLEL', "Along Direction", "Project points along specified direction", 0),
            ('CONIC', "From Source", "Project points along the direction from the source point", 1)
        ]

        project_mode : EnumProperty(
            name = "Project",
            items = modes,
            default = 'PARALLEL',
            update = update_sockets)

        methods = [
            ('hybr', "Hybrd & Hybrj", "Use MINPACK’s hybrd and hybrj routines (modified Powell method)", 0),
            ('lm', "Levenberg-Marquardt", "Levenberg-Marquardt algorithm", 1),
            ('krylov', "Krylov", "Krylov algorithm", 2),
            ('broyden1', "Broyden 1", "Broyden1 algorithm", 3),
            ('broyden2', "Broyden 2", "Broyden2 algorithm", 4),
            ('anderson', 'Anderson', "Anderson algorithm", 5),
            ('df-sane', 'DF-SANE', "DF-SANE method", 6)
        ]

        method : EnumProperty(
            name = "Method",
            items = methods,
            default = 'hybr',
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.label(text="Project:")
            layout.prop(self, 'project_mode', text='')
            layout.prop(self, 'precise', toggle=True)
            if not self.precise:
                layout.prop(self, 'samples')

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            if self.precise:
                layout.prop(self, 'samples')
                layout.prop(self, 'method')

        def sv_init(self, context):
            self.inputs.new('SvSurfaceSocket', "Surface")
            p = self.inputs.new('SvVerticesSocket', "Source")
            p.use_prop = True
            p.default_property = (0.0, 0.0, 1.0)
            p = self.inputs.new('SvVerticesSocket', "Point")
            p.use_prop = True
            p.default_property = (0.0, 0.0, 1.0)
            p = self.inputs.new('SvVerticesSocket', "Direction")
            p.use_prop = True
            p.default_property = (0.0, 0.0, -1.0)
            self.outputs.new('SvVerticesSocket', "Point")
            self.outputs.new('SvVerticesSocket', "UVPoint")
            self.update_sockets(context)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surfaces_s = self.inputs['Surface'].sv_get()
            surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
            src_point_s = self.inputs['Source'].sv_get()
            src_point_s = ensure_nesting_level(src_point_s, 4)
            points_s = self.inputs['Point'].sv_get()
            points_s = ensure_nesting_level(points_s, 4)
            direction_s = self.inputs['Direction'].sv_get()
            direction_s = ensure_nesting_level(direction_s, 4)

            points_out = []
            points_uv_out = []
            for surfaces, src_points_i, points_i, directions_i in zip_long_repeat(surfaces_s, src_point_s, points_s, direction_s):
                for surface, src_points, points, directions in zip_long_repeat(surfaces, src_points_i, points_i, directions_i):
                    u_min = surface.get_u_min()
                    u_max = surface.get_u_max()
                    v_min = surface.get_v_min()
                    v_max = surface.get_v_max()

                    new_uv = []
                    new_u = []
                    new_v = []
                    new_points = []

                    if self.project_mode == 'PARALLEL':
                        directions = repeat_last_for_length(directions, len(points))
                    else: # CONIC
                        src_points = repeat_last_for_length(src_points, len(points))
                        directions = (np.array(points) - np.array(src_points)).tolist()

                    result = raycast_surface(surface, points, directions,
                                samples = self.samples,
                                precise = self.precise,
                                calc_points = self.outputs['Point'].is_linked,
                                method = self.method)

                    new_uv = result.uvs
                    new_points = result.points

                    points_out.append(new_points)
                    points_uv_out.append(new_uv)

            self.outputs['Point'].sv_set(points_out)
            self.outputs['UVPoint'].sv_set(points_uv_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExRaycastSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExRaycastSurfaceNode)

