
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy
from sverchok.utils.manifolds import ortho_project_curve

if scipy is None:
    add_dummy('SvExOrthoProjectCurveNode', "Ortho Project on Curve", 'scipy')
else:

    class SvExOrthoProjectCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Ortho Project Curve
        Tooltip: Find the orthogonal projection of the point onto the curve
        """
        bl_idname = 'SvExOrthoProjectCurveNode'
        bl_label = 'Ortho Project on Curve'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EVAL_SURFACE'

        samples : IntProperty(
            name = "Init Resolution",
            default = 5,
            min = 3,
            update = updateNode)
        
        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'samples')

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            p = self.inputs.new('SvVerticesSocket', "Point")
            p.use_prop = True
            p.prop = (0.0, 0.0, 0.0)
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
            for curves, src_points_i in zip_long_repeat(curves_s, src_point_s):
                for curve, src_points in zip_long_repeat(curves, src_points_i):
                    new_points = []
                    new_t = []
                    for src_point in src_points:
                        src_point = np.array(src_point)
                        result = ortho_project_curve(src_point, curve, init_samples = self.samples)
                        t = result.nearest_u
                        point = result.nearest.tolist()
                        new_t.append(t)
                        new_points.append(point)
                    points_out.append(new_points)
                    t_out.append(new_t)

            self.outputs['Point'].sv_set(points_out)
            self.outputs['T'].sv_set(t_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExOrthoProjectCurveNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExOrthoProjectCurveNode)

