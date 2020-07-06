
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import bvhtree

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.vector import SvVectorField
from sverchok.utils.surface import SvSurface
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.integrate import solve_ivp

    def solve_lines(surface, field, p0, tf, method='RK45', rotate=False):

        def f(t, ps):
            #print("P:", ps.shape)
            us = ps[0,:]
            vs = ps[1,:]

            derivs = surface.derivatives_data_array(us, vs)
            du = derivs.du
            dv = derivs.dv

            xs = derivs.points[:,0]
            ys = derivs.points[:,1]
            zs = derivs.points[:,2]

            vxs, vys, vzs = field.evaluate_grid(xs,ys,zs)
            vecs = np.stack((vxs, vys, vzs)).T

            vec_u = (vecs * du).sum(axis=1)
            vec_v = (vecs * dv).sum(axis=1)

            if rotate:
                vec_u, vec_v = -vec_v, vec_u

            res = np.array([vec_u, vec_v])
            #print("R:", res)
            return res

        res = solve_ivp(f, (0, tf), p0, method=method, vectorized=True)

        if not res.success:
            raise Exception("Can't solve the equation: " + res.message)
        return res.y.T

    class SvExVFieldLinesOnSurfNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Vector Field lines on Surface
        Tooltip: Vector Field lines on Surface
        """
        bl_idname = 'SvExVFieldLinesOnSurfNode'
        bl_label = 'Vector Field Lines on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'

        methods = [
            ('RK45', "Runge-Kutta 5(4)", "Runge-Kutta 5(4)", 0),
            ('RK23', "Runge-Kutta 3(2)", "Runge-Kutta 3(2)", 1),
            ('DOP853', "Runge-Kutta 8(7)", "Runge-Kutta 8(7)", 2),
            ('Radau', "Implicit Runge-Kutta", "Implicit Runge-Kutta - Radau IIA 5", 3),
            ('BDF', "Backward differentiation", "Implicit multi-step variable-order (1 to 5) method based on a backward differentiation formula for the derivative approximation", 4),
            ('LSODA', "Adams / BDF", "Adams/BDF method with automatic stiffness detection and switching", 5)
        ]

        method : EnumProperty(
            name = "Method",
            items = methods,
            default = 'RK45',
            update = updateNode)

        cograd : BoolProperty(
            name = "Iso lines",
            default = False,
            update = updateNode)

        max_t : FloatProperty(
            name = "Max T",
            default = 2.0,
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'method')
            layout.prop(self, 'cograd')

        def sv_init(self, context):
            self.inputs.new('SvVectorFieldSocket', 'Field')
            self.inputs.new('SvSurfaceSocket', 'Surface')
            self.inputs.new('SvVerticesSocket', 'StartUV')
            self.inputs.new('SvStringsSocket', 'MaxT').prop_name = 'max_t'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvVerticesSocket', "UVPoints")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            start_s = self.inputs['StartUV'].sv_get()
            field_s = self.inputs['Field'].sv_get()
            surface_s = self.inputs['Surface'].sv_get()
            maxt_s = self.inputs['MaxT'].sv_get()

            start_s = ensure_nesting_level(start_s, 3)
            field_s = ensure_nesting_level(field_s, 2, data_types=(SvVectorField,))
            surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
            maxt_s = ensure_nesting_level(maxt_s, 2)

            verts_out = []
            uv_out = []
            for starts, fields, surfaces, maxt_i in zip_long_repeat(start_s, field_s, surface_s, maxt_s):
                for start, field, surface, max_t in zip_long_repeat(starts, fields, surfaces, maxt_i):
                    u0, v0, _ = start
                    uvs = solve_lines(surface, field, np.array([u0,v0]),
                                max_t,
                                method=self.method,
                                rotate = self.cograd)
                    self.debug(f"Start {(u0,v0)} => {len(uvs)} points")
                    us = uvs[:,0]
                    vs = uvs[:,1]
                    new_uvs = [(u,v,0) for u,v in zip(us,vs)]
                    new_verts = surface.evaluate_array(us, vs).tolist()

                    verts_out.append(new_verts)
                    uv_out.append(new_uvs)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['UVPoints'].sv_set(uv_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExVFieldLinesOnSurfNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExVFieldLinesOnSurfNode)

