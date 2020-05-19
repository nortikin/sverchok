
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvCurveSegment

class SvSplitCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Split Curve
    Tooltip: Split one curve into several subdomains
    """
    bl_idname = 'SvSplitCurveNode'
    bl_label = 'Split Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_DOMAIN'

    cuts : IntProperty(
            name = "Cuts",
            description = "Numer of cut points (number of generated segments will be greater by 1)",
            default = 10,
            min = 1,
            update = updateNode)

    split : FloatProperty(
            name = "Split",
            description = "Value of curve's T parameter to split at",
            default = 0.5,
            update = updateNode)

    @throttled
    def update_sockets(self, context):
        self.inputs['Cuts'].hide_safe = self.mode != 'EVEN'
        self.inputs['Split'].hide_safe = self.mode != 'MANUAL'

    modes = [
            ('EVEN', "Even", "Split curve by even cuts of T parameter", 0),
            ('MANUAL', "Explicit", "Split curve at specified values of T parameter", 1)
        ]

    mode : EnumProperty(
            name = "Mode",
            items = modes,
            default = 'MANUAL',
            update = update_sockets)

    join : BoolProperty(
            name = "Join",
            description = "Output single list of curves for all provided curves",
            default = False,
            update = updateNode)

    rescale : BoolProperty(
        name = "Rescale to 0..1",
        description = "Rescale all generated curves to have domain of [0 .. 1]",
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)
        layout.prop(self, 'rescale', toggle=True)
        layout.prop(self, 'join', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Cuts").prop_name = 'cuts'
        self.inputs.new('SvStringsSocket', "Split").prop_name = 'split'
        self.outputs.new('SvCurveSocket', "Curves")
        self.update_sockets(context)

    def _cut(self, t_min, t_max, cuts):
        return np.linspace(t_min, t_max, num=cuts+1, endpoint=False)[1:].tolist()

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        cuts_s = self.inputs['Cuts'].sv_get()
        split_s = self.inputs['Split'].sv_get()
        
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        cuts_s = ensure_nesting_level(cuts_s, 2)
        split_s = ensure_nesting_level(split_s, 3)

        curves_out = []
        for curves, cuts_i, split_i in zip_long_repeat(curve_s, cuts_s, split_s):
            for curve, cuts, splits in zip_long_repeat(curves, cuts_i, split_i):
                new_curves = []
                t_min, t_max = curve.get_u_bounds()
                if self.mode == 'EVEN':
                    splits = self._cut(t_min, t_max, cuts)
                splits = [t_min] + splits + [t_max]
                pairs = zip(splits, splits[1:])
                for start, end in pairs:
                    new_curve = SvCurveSegment(curve, start, end, self.rescale)
                    new_curves.append(new_curve)
                if self.join:
                    curves_out.extend(new_curves)
                else:
                    curves_out.append(new_curves)
        self.outputs['Curves'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvSplitCurveNode)

def unregister():
    bpy.utils.unregister_class(SvSplitCurveNode)

