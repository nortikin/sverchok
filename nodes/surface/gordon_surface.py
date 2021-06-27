# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.math import supported_metrics
from sverchok.utils.nurbs_common import SvNurbsMaths
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

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="POINTS", items=supported_metrics,
        update=updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "CurvesU")
        self.inputs.new('SvCurveSocket', "CurvesV")
        self.inputs.new('SvVerticesSocket', "Intersections")
        self.outputs.new('SvSurfaceSocket', "Surface")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        u_curves_s = self.inputs['CurvesU'].sv_get()
        v_curves_s = self.inputs['CurvesV'].sv_get()
        intersections_s = self.inputs['Intersections'].sv_get()

        u_curves_s = ensure_nesting_level(u_curves_s, 2, data_types=(SvCurve,))
        v_curves_s = ensure_nesting_level(v_curves_s, 2, data_types=(SvCurve,))
        intersections_s = ensure_nesting_level(intersections_s, 4)

        surface_out = []
        for u_curves, v_curves, intersections in zip_long_repeat(u_curves_s, v_curves_s, intersections_s):
            u_curves = [SvNurbsCurve.to_nurbs(c) for c in u_curves]
            if any(c is None for c in u_curves):
                raise Exception("Some of U curves are not NURBS!")
            v_curves = [SvNurbsCurve.to_nurbs(c) for c in v_curves]
            if any(c is None for c in v_curves):
                raise Exception("Some of V curves are not NURBS!")

            _, _, _, surface = gordon_surface(u_curves, v_curves, intersections, metric=self.metric)
            surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvGordonSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvGordonSurfaceNode)

