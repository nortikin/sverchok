
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.logging import info, exception
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExCatenaryCurveNode', "Catenary Curve", 'scipy')
else:
    from sverchok.utils.catenary import CatenarySolver

    class SvExCatenaryCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Catenary Curve
        Tooltip: Generate Catenary Curve
        """
        bl_idname = 'SvExCatenaryCurveNode'
        bl_label = 'Catenary Curve'
        bl_icon = 'CURVE_NCURVE'
        sv_icon = 'SV_CATENARY'

        length : FloatProperty(
            name = "Length",
            min = 0.0,
            default = 3.0,
            update = updateNode)

        def sv_init(self, context):
            p = self.inputs.new('SvVerticesSocket', "Point1")
            p.use_prop = True
            p.prop = (-1.0, 0.0, 0.0)
            p = self.inputs.new('SvVerticesSocket', "Point2")
            p.use_prop = True
            p.prop = (1.0, 0.0, 0.0)
            p = self.inputs.new('SvVerticesSocket', "Gravity")
            p.use_prop = True
            p.prop = (0.0, 0.0, -1.0)

            self.inputs.new('SvStringsSocket', "Length").prop_name = 'length'

            self.outputs.new('SvCurveSocket', "Curve")

        join : BoolProperty(
                name = "Join",
                description = "Output single list of curves for all input points",
                default = True,
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'join', toggle=True)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            point1_s = self.inputs['Point1'].sv_get()
            point2_s = self.inputs['Point2'].sv_get()
            force_s = self.inputs['Gravity'].sv_get()
            length_s = self.inputs['Length'].sv_get()

            curves_out = []
            for point1s, point2s, forces, lengths in zip_long_repeat(point1_s, point2_s, force_s, length_s):
                new_curves = []
                for point1, point2, force, length in zip_long_repeat(point1s, point2s, forces, lengths):
                    solver = CatenarySolver(np.array(point1), np.array(point2), length, np.array(force))
                    curve = solver.solve()
                    new_curves.append(curve)
                if self.join:
                    curves_out.extend(new_curves)
                else:
                    curves_out.append(new_curves)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExCatenaryCurveNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExCatenaryCurveNode)

