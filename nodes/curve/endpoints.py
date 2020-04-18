import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve

class SvCurveEndpointsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve End Points
    Tooltip: Output two endpoints of the curve
    """
    bl_idname = 'SvExCurveEndpointsNode'
    bl_label = 'Curve Endpoints'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_ENDPOINTS'

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "Start")
        self.outputs.new('SvVerticesSocket', "End")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        if isinstance(curve_s[0], SvCurve):
            curve_s = [curve_s]

        start_out = []
        end_out = []
        for curves in curve_s:
            start_new = []
            end_new = []
            for curve in curves:
                t_min, t_max = curve.get_u_bounds()
                start = curve.evaluate(t_min).tolist()
                end = curve.evaluate(t_max).tolist()
                start_new.append(start)
                end_new.append(end)
            start_out.append(start_new)
            end_out.append(end_new)

        self.outputs['Start'].sv_set(start_out)
        self.outputs['End'].sv_set(end_out)

def register():
    bpy.utils.register_class(SvCurveEndpointsNode)

def unregister():
    bpy.utils.unregister_class(SvCurveEndpointsNode)

