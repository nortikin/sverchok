import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvExCurve

class SvExCurveRangeNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Domain / Range
    Tooltip: Output minimum and maximum values of T parameter allowed by the curve
    """
    bl_idname = 'SvExCurveRangeNode'
    bl_label = 'Curve Domain'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_DOMAIN'

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Curve")
        self.outputs.new('SvStringsSocket', "TMin")
        self.outputs.new('SvStringsSocket', "TMax")
        self.outputs.new('SvStringsSocket', "Range")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        t_min_out = []
        t_max_out = []
        range_out = []

        if isinstance(curve_s[0], SvExCurve):
            curve_s = [curve_s]

        for curves in curve_s:
            t_min_new = []
            t_max_new = []
            range_new = []
            for curve in curves:
                t_min, t_max = curve.get_u_bounds()
                t_range = t_max - t_min
                t_min_new.append(t_min)
                t_max_new.append(t_max)
                range_new.append(t_range)
            t_min_out.append(t_min_new)
            t_max_out.append(t_max_new)
            range_out.append(range_new)

        self.outputs['TMin'].sv_set(t_min_out)
        self.outputs['TMax'].sv_set(t_max_out)
        self.outputs['Range'].sv_set(range_out)

def register():
    bpy.utils.register_class(SvExCurveRangeNode)

def unregister():
    bpy.utils.unregister_class(SvExCurveRangeNode)

