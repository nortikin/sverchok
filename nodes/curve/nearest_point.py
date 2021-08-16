import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix
from mathutils.kdtree import KDTree

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.manifolds import nearest_point_on_curve
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExNearestPointOnCurveNode', "Nearest Point on Curve", 'scipy')
else:

    class SvExNearestPointOnCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Nearest Point on Curve
        Tooltip: Find the point on the curve which is the nearest to the given point
        """
        bl_idname = 'SvExNearestPointOnCurveNode'
        bl_label = 'Nearest Point on Curve'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_NEAREST_CURVE'

        samples : IntProperty(
            name = "Init Resolution",
            default = 50,
            min = 3,
            update = updateNode)
        
        precise : BoolProperty(
            name = "Precise",
            default = True,
            update = updateNode)

        solvers = [
                ('Brent', "Brent", "Uses inverse parabolic interpolation when possible to speed up convergence of golden section method", 0),
                ('Bounded', "Bounded", "Uses the Brent method to find a local minimum in the interval", 1),
                ('Golden', 'Golden Section', "Uses the golden section search technique", 2)
            ]

        method : EnumProperty(
            name = "Method",
            description = "Solver method to use; select the one which works for your case",
            items = solvers,
            default = 'Brent',
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'samples')
            layout.prop(self, 'precise', toggle=True)

        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'method')

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            p = self.inputs.new('SvVerticesSocket', "Point")
            p.use_prop = True
            p.default_property = (0.0, 0.0, 0.0)
            self.outputs.new('SvVerticesSocket', "Point")
            self.outputs.new('SvStringsSocket', "T")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curves_s = self.inputs['Curve'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
            src_point_s = self.inputs['Point'].sv_get()
            src_point_s = ensure_nesting_level(src_point_s, 4)

            points_out = []
            t_out = []
            need_points = self.outputs['Point'].is_linked
            for curves, src_points_i in zip_long_repeat(curves_s, src_point_s):
                for curve, src_points in zip_long_repeat(curves, src_points_i):

                    results = nearest_point_on_curve(src_points, curve,
                                samples=self.samples, precise=self.precise, 
                                output_points = need_points,
                                method = self.method,
                                logger = self.get_logger())
                    if need_points:
                        new_t = [r[0] for r in results]
                        new_points = [r[1].tolist() for r in results]
                    else:
                        new_t = results
                        new_points = []

                    points_out.append(new_points)
                    t_out.append(new_t)

                self.outputs['Point'].sv_set(points_out)
                self.outputs['T'].sv_set(t_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExNearestPointOnCurveNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExNearestPointOnCurveNode)

