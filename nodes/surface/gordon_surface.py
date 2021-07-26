# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.math import supported_metrics
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.gordon import gordon_surface

class SvGordonSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Gordon Surface Curves Net
    Tooltip: Generate a NURBS surface from a net of curves (a.k.a. Gordon Surface)
    """
    bl_idname = 'SvGordonSurfaceNode'
    bl_label = 'NURBS Surface from Curves Net'
    bl_icon = 'GP_MULTIFRAME_EDITING'
    sv_icon = 'SV_SURFACE_FROM_CURVES'

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="POINTS", items=supported_metrics,
        update=updateNode)
    
    def update_sockets(self, context):
        self.inputs['T1'].hide_safe = self.explicit_t_values != True
        self.inputs['T2'].hide_safe = self.explicit_t_values != True
        updateNode(self, context)

    explicit_t_values : BoolProperty(
        name = "Explicit T values",
        default = False,
        update = update_sockets)

    knotvector_accuracy : IntProperty(
        name = "Knotvector accuracy",
        default = 4,
        min = 1, max = 10,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'explicit_t_values')

    def draw_buttons_ext(self, context, layout):
        if not self.explicit_t_values:
            layout.prop(self, 'metric')
        layout.prop(self, 'knotvector_accuracy')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "CurvesU")
        self.inputs.new('SvCurveSocket', "CurvesV")
        self.inputs.new('SvStringsSocket', "T1")
        self.inputs.new('SvStringsSocket', "T2")
        self.inputs.new('SvVerticesSocket', "Intersections")
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        u_curves_s = self.inputs['CurvesU'].sv_get()
        v_curves_s = self.inputs['CurvesV'].sv_get()
        intersections_s = self.inputs['Intersections'].sv_get()

        if self.explicit_t_values:
            t1_s = self.inputs['T1'].sv_get()
            t2_s = self.inputs['T2'].sv_get()
        else:
            t1_s = [[[]]]
            t2_s = [[[]]]

        u_curves_s = ensure_nesting_level(u_curves_s, 2, data_types=(SvCurve,))
        v_curves_s = ensure_nesting_level(v_curves_s, 2, data_types=(SvCurve,))
        t1_s = ensure_nesting_level(t1_s, 3)
        t2_s = ensure_nesting_level(t2_s, 3)
        intersections_s = ensure_nesting_level(intersections_s, 4)

        surface_out = []
        for u_curves, v_curves, t1s, t2s, intersections in zip_long_repeat(u_curves_s, v_curves_s, t1_s, t2_s, intersections_s):
            u_curves = [SvNurbsCurve.to_nurbs(c) for c in u_curves]
            if any(c is None for c in u_curves):
                raise Exception("Some of U curves are not NURBS!")
            v_curves = [SvNurbsCurve.to_nurbs(c) for c in v_curves]
            if any(c is None for c in v_curves):
                raise Exception("Some of V curves are not NURBS!")

            if self.explicit_t_values:
                if len(t1s) < len(u_curves):
                    t1s = repeat_last_for_length(t1s, len(u_curves))
                elif len(t1s) > len(u_curves):
                    raise Exception(f"Number of items in T1 input {len(t1s)} > number of U-curves {len(u_curves)}")

                if len(t1s[0]) != len(v_curves):
                    raise Exception(f"Length of items in T1 input {len(t1s[0])} != number of V-curves {len(v_curves)}")

                if len(t2s) < len(v_curves):
                    t2s = repeat_last_for_length(t2s, len(v_curves))
                elif len(t2s) > len(v_curves):
                    raise Exception(f"Number of items in T2 input {len(t2s)} > number of V-curves {len(v_curves)}")

                if len(t2s[0]) != len(u_curves):
                    raise Exception(f"Length of items in T2 input {len(t2s[0])} != number of U-curves {len(u_curves)}")

            if self.explicit_t_values:
                kwargs = {'u_knots': np.array(t1s), 'v_knots': np.array(t2s)}
            else:
                kwargs = dict()
            _, _, _, surface = gordon_surface(u_curves, v_curves, intersections, metric=self.metric, knotvector_accuracy = self.knotvector_accuracy, **kwargs)
            surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvGordonSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvGordonSurfaceNode)

