
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvIsoUvCurve, SvConcatCurve
from sverchok.utils.surface import SvSurface

class SvSurfaceBoundaryNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Boundary
    Tooltip: Generate a curve from curve's boundary
    """
    bl_idname = 'SvExSurfaceBoundaryNode'
    bl_label = 'Surface Boundary'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_BOUNDARY'

    modes = [
        ('NO', "Plain", "Non-cyclic surface (similar to plane)", 0),
        ('U', "U Cyclic", "The surface is cyclic in the U direction", 1),
        ('V', "V Cyclic", "The surface is cyclic in the V direction", 2)
    ]

    cyclic_mode : EnumProperty(
        name = "Cyclic surface",
        items = modes,
        default = 'NO',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvCurveSocket', "Boundary")

    def draw_buttons(self, context, layout):
        layout.label(text="Cyclic:")
        layout.prop(self, 'cyclic_mode', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        if isinstance(surface_s[0], SvSurface):
            surface_s = [surface_s]

        curves_out = []
        for surfaces in surface_s:
            for surface in surfaces:
                u_min, u_max = surface.get_u_min(), surface.get_u_max()
                v_min, v_max = surface.get_v_min(), surface.get_v_max()
                if self.cyclic_mode == 'NO':
                    curve1 = SvIsoUvCurve(surface, 'V', v_min, flip=False)
                    curve2 = SvIsoUvCurve(surface, 'U', u_max, flip=False)
                    curve3 = SvIsoUvCurve(surface, 'V', v_max, flip=True)
                    curve4 = SvIsoUvCurve(surface, 'U', u_min, flip=True)
                    new_curves = [SvConcatCurve([curve1, curve2, curve3, curve4])]
                elif self.cyclic_mode == 'U':
                    curve1 = SvIsoUvCurve(surface, 'V', v_max, flip=False)
                    curve2 = SvIsoUvCurve(surface, 'V', v_min, flip=False)
                    new_curves = [curve1, curve2]
                elif self.cyclic_mode == 'V':
                    curve1 = SvIsoUvCurve(surface, 'U', u_max, flip=False)
                    curve2 = SvIsoUvCurve(surface, 'U', u_min, flip=False)
                    new_curves = [curve1, curve2]
                else:
                    raise Exception("Unsupported mode")
                curves_out.append(new_curves)

        self.outputs['Boundary'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvSurfaceBoundaryNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceBoundaryNode)

