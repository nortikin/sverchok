
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvExCurve, SvExCurveOnSurface
from sverchok.utils.surface import SvExSurface

class SvExCurveOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve on Surface
    Tooltip: Generate a curve in UV space of the surface
    """
    bl_idname = 'SvExCurveOnSurfaceNode'
    bl_label = 'Curve on Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_ON_SURFACE'

    planes = [
            ("XY", "XY", "XOY plane", 0),
            ("YZ", "YZ", "YOZ plane", 1),
            ("XZ", "XZ", "XOZ plane", 2)
        ]

    curve_plane: EnumProperty(
        name="Curve plane", description="Curve plane",
        default="XY", items=planes, update=updateNode)

    @property
    def curve_axis(self):
        plane = self.curve_plane
        if plane == 'XY':
            return 2
        elif plane == 'YZ':
            return 0
        else:
            return 1

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', 'Curve')
        self.inputs.new('SvExSurfaceSocket', "Surface")
        self.outputs.new('SvExCurveSocket', "Curve")

    def draw_buttons(self, context, layout):
        layout.label(text="Curve plane:")
        layout.prop(self, 'curve_plane', expand=True)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        surface_s = self.inputs['Surface'].sv_get()

        if isinstance(curve_s[0], SvExCurve):
            curve_s = [curve_s]
        if isinstance(surface_s[0], SvExSurface):
            surface_s = [surface_s]

        curves_out = []
        for curves, surfaces in zip_long_repeat(curve_s, surface_s):
            for curve, surface in zip_long_repeat(curves, surfaces):
                new_curve = SvExCurveOnSurface(curve, surface, self.curve_axis)
                curves_out.append(new_curve)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvExCurveOnSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExCurveOnSurfaceNode)

