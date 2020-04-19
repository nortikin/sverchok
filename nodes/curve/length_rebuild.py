import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvLengthRebuiltCurve, SvCurve

class SvLengthRebuildCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Length Rebuild
    Tooltip: Re-parametrize the curve to make it's parameter equal to it's length.
    """
    bl_idname = 'SvLengthRebuildCurveNode'
    bl_label = 'Naturally Parametrized Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_LENGTH_P'

    resolution : IntProperty(
        name = 'Resolution',
        min = 1,
        default = 50,
        update = updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]

    mode: EnumProperty(name='Interpolation mode', default="SPL", items=modes, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.outputs.new('SvCurveSocket', "Curve")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def does_support_draft_mode(self):
        return True

    def draw_label(self):
        label = self.label or self.name
        if self.id_data.sv_draft:
            label = "[D] " + label
        return label

    def process(self):

        if not any((s.is_linked for s in self.outputs)):
            return

        curves_s = self.inputs['Curve'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()

        resolution_s = ensure_nesting_level(resolution_s, 2)
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

        curves_out = []
        for curves, resolutions in zip_long_repeat(curves_s, resolution_s):
            for curve, resolution in zip_long_repeat(curves, resolutions):
                mode = self.mode
                if self.id_data.sv_draft:
                    mode = 'LIN'
                new_curve = SvLengthRebuiltCurve(curve, resolution, mode=mode)
                curves_out.append(new_curve)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvLengthRebuildCurveNode)

def unregister():
    bpy.utils.unregister_class(SvLengthRebuildCurveNode)

