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
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExSurfaceExtremesNode', "Surface Extremes", 'scipy')
else:
    from scipy.optimize import minimize

    class SvExSurfaceExtremesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Surface Extremes
        Tooltip: Find the point on the surface which provides the maximum or minimum for specified scalar field
        """
        bl_idname = 'SvExSurfaceExtremesNode'
        bl_label = 'Surface Extremes'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_SURFACE_EXTREMES'

        directions = [
                ('MIN', "Min", "Find the minimum of the field", 0),
                ('MAX', "Max", "Find the maximum of the field", 1)
            ]

        direction : EnumProperty(
            name = "Direction",
            items = directions,
            default = 'MIN',
            update = updateNode)

        find_global : BoolProperty(
            name = "Search Best",
            default = True,
            update = updateNode)

        on_fail_options = [
                ('FAIL', "Fail", "Raise an exception (node becomes red)", 0),
                ('SKIP', "Skip", "Skip such interval or curve - just return an empty set of points", 1)
            ]

        on_fail : EnumProperty(
            name = "On fail",
            items = on_fail_options,
            default = 'SKIP',
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
            layout.prop(self, 'direction', expand=True)
            layout.prop(self, 'find_global', toggle=True)

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            layout.prop(self, 'method')
            layout.prop(self, 'on_fail')
        
        def sv_init(self, context):
            self.inputs.new('SvSurfaceSocket', "Surface")
            self.inputs.new('SvScalarFieldSocket', "Field")
            self.inputs.new('SvVerticesSocket', "StartUV")
            self.outputs.new('SvVerticesSocket', "Point")
            self.outputs.new('SvVerticesSocket', "UVPoint")

        def solve(self, surface, field, starts):

            def goal(p):
                point = surface.evaluate(p[0], p[1])
                value = field.evaluate(point[0], point[1], point[2])
                if self.direction == 'MAX':
                    return - value
                else:
                    return value

            u_min = surface.get_u_min()
            u_max = surface.get_u_max()
            v_min = surface.get_v_min()
            v_max = surface.get_v_max()

            uvs = []
            values = []
            for start in starts:
                if start is None:
                    init_u = (u_min+u_max)/2.0
                    init_v = (v_min+v_max)/2.0
                else:
                    init_u = start[0]
                    init_v = start[1]

                result = minimize(goal,
                            x0 = np.array([init_u, init_v]),
                            bounds = [(u_min, u_max), (v_min, v_max)],
                            method = self.method
                        )
                if not result.success:
                    if self.on_fail == 'FAIL':
                        raise Exception(f"Can't find the extreme point of {surface} at {u_min}-{u_max}, {v_min}-{v_max}: {result.message}")
                else:
                    #print(f"{init_u},{init_v} ==> {result.x} = {result.fun}")
                    uvs.append(result.x)
                    values.append(result.fun)

            uvs = np.array(uvs)
            values = np.array(values)

            if self.find_global:
                if len(values) > 0:
                    target = values.min()
                    good = (values == target)
                    return uvs[good]
                else:
                    return uvs
            else:
                return uvs

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surface_s = self.inputs['Surface'].sv_get()
            surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
            fields_s = self.inputs['Field'].sv_get()
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
            if self.inputs['StartUV'].is_linked:
                start_s = self.inputs['StartUV'].sv_get()
                start_s = ensure_nesting_level(start_s, 4)
            else:
                start_s = [[[None]]]

            uv_out = []
            point_out = []
            for surfaces, fields, start_i in zip_long_repeat(surface_s, fields_s, start_s):
                new_uv = []
                new_points = []
                for surface, field, starts in zip_long_repeat(surfaces, fields, start_i):
                    uvs = self.solve(surface, field, starts)
                    uv_points = [(u, v, 0) for u,v in uvs]

                    us = uvs[:,0]
                    vs = uvs[:,1]
                    points = surface.evaluate_array(us, vs)

                    new_uv.extend(uv_points)
                    new_points.extend(points.tolist())
                uv_out.append(new_uv)
                point_out.append(new_points)

            self.outputs['Point'].sv_set(point_out)
            self.outputs['UVPoint'].sv_set(uv_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExSurfaceExtremesNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExSurfaceExtremesNode)

