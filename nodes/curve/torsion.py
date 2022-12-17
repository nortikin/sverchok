import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.curve.core import SvCurve

class SvCurveTorsionNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: Curve Torsion / Twist
        Tooltip: Calculate torsion of the curve at given parameter value
        """
        bl_idname = 'SvExCurveTorsionNode'
        bl_label = 'Curve Torsion'
        bl_icon = 'CURVE_NCURVE'

        t_value : FloatProperty(
                name = "T",
                default = 0.5,
                update = updateNode)

        numpy_out : BoolProperty(
                name = "NumPy output",
                description = "Output data as NumPy arrays",
                default = False,
                update = updateNode)

        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'numpy_out')

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.outputs.new('SvStringsSocket', "Torsion")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()

            input_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
            nested_output = input_level > 1

            curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
            ts_s = ensure_nesting_level(ts_s, 3)

            torsion_out = []
            for params in zip_long_repeat(curve_s, ts_s):
                new_torsion = []
                for curve, ts in zip_long_repeat(*params):
                    ts = np.asarray(ts)
                    torsions = curve.torsion_array(ts)
                    if not self.numpy_out:
                        torsions = torsions.tolist()
                    new_torsion.append(torsions)
                if nested_output:
                    torsion_out.append(new_torsion)
                else:
                    torsion_out.extend(new_torsion)

            self.outputs['Torsion'].sv_set(torsion_out)

def register():
    bpy.utils.register_class(SvCurveTorsionNode)

def unregister():
    bpy.utils.unregister_class(SvCurveTorsionNode)

