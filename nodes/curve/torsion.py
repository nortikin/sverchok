import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat

class SvCurveTorsionNode(bpy.types.Node, SverchCustomTreeNode):
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

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.outputs.new('SvStringsSocket', "Torsion")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()

            torsion_out = []
            for curve, ts in zip_long_repeat(curve_s, ts_s):
                ts = np.array(ts)
                torsions = curve.torsion_array(ts)
                torsion_out.append(torsions.tolist())

            self.outputs['Torsion'].sv_set(torsion_out)

def register():
    bpy.utils.register_class(SvCurveTorsionNode)

def unregister():
    bpy.utils.unregister_class(SvCurveTorsionNode)

