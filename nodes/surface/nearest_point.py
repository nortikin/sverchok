import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix
from mathutils.kdtree import KDTree

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.optimize import minimize

    def init_guess(surface, points_from, samples=50):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        us = np.linspace(u_min, u_max, num=samples)
        vs = np.linspace(v_min, v_max, num=samples)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()

        points = surface.evaluate_array(us, vs).tolist()

        kdt = KDTree(len(us))
        for i, v in enumerate(points):
            kdt.insert(v, i)
        kdt.balance()

        us_out = []
        vs_out = []
        nearest_out = []
        for point_from in points_from:
            nearest, i, distance = kdt.find(point_from)
            us_out.append(us[i])
            vs_out.append(vs[i])
            nearest_out.append(tuple(nearest))

        return us_out, vs_out, nearest_out

    def goal(surface, point_from):
        def distance(p):
            dv = surface.evaluate(p[0], p[1]) - np.array(point_from)
            return np.linalg.norm(dv)
        return distance

    class SvExNearestPointOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Nearest Point on Surface
        Tooltip: Find the point on the surface which is the nearest to the given point
        """
        bl_idname = 'SvExNearestPointOnSurfaceNode'
        bl_label = 'Nearest Point on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EVAL_SURFACE'

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

        def draw_buttons(self, context, layout):
            layout.prop(self, 'samples')
            layout.prop(self, 'precise', toggle=True)

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            if self.precise:
                layout.prop(self, 'method')

        def sv_init(self, context):
            self.inputs.new('SvSurfaceSocket', "Surface")
            p = self.inputs.new('SvVerticesSocket', "Point")
            p.use_prop = True
            p.prop = (0.0, 0.0, 0.0)
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
            points_uv_out = []
            for surfaces, src_points_i in zip_long_repeat(surfaces_s, src_point_s):
                for surface, src_points in zip_long_repeat(surfaces, src_points_i):
                    u_min = surface.get_u_min()
                    u_max = surface.get_u_max()
                    v_min = surface.get_v_min()
                    v_max = surface.get_v_max()

                    new_uv = []
                    new_u = []
                    new_v = []
                    new_points = []

                    init_us, init_vs, init_points = init_guess(surface, src_points, samples=self.samples)
                    for src_point, init_u, init_v, init_point in zip(src_points, init_us, init_vs, init_points):
                        if self.precise:
                            result = minimize(goal(surface, src_point),
                                        x0 = np.array([init_u, init_v]),
                                        bounds = [(u_min, u_max), (v_min, v_max)],
                                        method = self.method
                                    )
                            if not result.success:
                                raise Exception("Can't find the nearest point for {}: {}".format(src_point, result.message))
                            u0, v0 = result.x
                        else:
                            u0, v0 = init_u, init_v
                            new_points.append(init_point)
                        new_uv.append((u0, v0, 0))
                        new_u.append(u0)
                        new_v.append(v0)

                    if self.precise and self.outputs['Point'].is_linked:
                        new_points = surface.evaluate_array(np.array(new_u), np.array(new_v)).tolist()

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

