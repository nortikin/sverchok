
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.algorithms import reparametrize_curve

class SvReparametrizeCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Reparametrize Curve
    Tooltip: Change parameterization of the curve by linear mapping of T parameter to the new bounds
    """
    bl_idname = 'SvReparametrizeCurveNode'
    bl_label = 'Reparametrize Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_REPARAM_CURVE'

    new_t_min : FloatProperty(
            name = "New T Min",
            description = "New lower bound of curve's T parameter",
            default = 0.0,
            update = updateNode)

    new_t_max : FloatProperty(
            name = "New T Max",
            description = "New upper bound of curve's T parameter",
            default = 1.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "NewTMin").prop_name = 'new_t_min'
        self.inputs.new('SvStringsSocket', "NewTMax").prop_name = 'new_t_max'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        tmin_s = self.inputs['NewTMin'].sv_get()
        tmax_s = self.inputs['NewTMax'].sv_get()

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        tmin_s = ensure_nesting_level(tmin_s, 2)
        tmax_s = ensure_nesting_level(tmax_s, 2)

        curve_out = []
        for curves, tmins, tmaxs in zip_long_repeat(curve_s, tmin_s, tmax_s):
            new_curves = []
            for curve, t_min, t_max in zip_long_repeat(curves, tmins, tmaxs):
                new_curve = reparametrize_curve(curve, t_min, t_max)
                new_curves.append(new_curve)
            curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvReparametrizeCurveNode)

def unregister():
    bpy.utils.unregister_class(SvReparametrizeCurveNode)

