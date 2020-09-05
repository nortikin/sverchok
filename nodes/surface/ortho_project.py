
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy
from sverchok.utils.manifolds import ortho_project_surface

if scipy is None:
    add_dummy('SvExOrthoProjectSurfaceNode', "Ortho Project on Surface", 'scipy')
else:

    class SvExOrthoProjectSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Ortho Project Surface
        Tooltip: Find the orthogonal projection of the point onto the surface
        """
        bl_idname = 'SvExOrthoProjectSurfaceNode'
        bl_label = 'Ortho Project on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_ORTHO_SURFACE'

        samples : IntProperty(
            name = "Init Resolution",
            default = 5,
            min = 3,
            update = updateNode)
        
        def draw_buttons(self, context, layout):
            layout.prop(self, 'samples')

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

            points_out = []
            uv_out = []
            for surfaces, src_points_i in zip_long_repeat(surfaces_s, src_point_s):
                for surface, src_points in zip_long_repeat(surfaces, src_points_i):
                    new_points = []
                    new_uv = []
                    for src_point in src_points:
                        src_point = np.array(src_point)
                        u, v, point = ortho_project_surface(src_point, surface, init_samples=self.samples)
                        new_uv.append((u, v, 0))
                        new_points.append(point)
                    points_out.append(new_points)
                    uv_out.append(new_uv)

            self.outputs['Point'].sv_set(points_out)
            self.outputs['UVPoint'].sv_set(uv_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExOrthoProjectSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExOrthoProjectSurfaceNode)

