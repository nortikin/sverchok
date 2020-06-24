
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.core.socket_data import SvNoDataError
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvCurveOffsetOnSurface
from sverchok.utils.surface import SvSurface

class SvCurveOffsetOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Offset Curve on Surface
    Tooltip: Offset a Curve along it's normal, while remaining in the surface
    """
    bl_idname = 'SvCurveOffsetOnSurfaceNode'
    bl_label = 'Offset Curve on Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_OFFSET_ON_SURFACE'

    offset : FloatProperty(
            name = "Offset",
            default = 0.1,
            update = updateNode)

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

    offset_types = [
            ('CONST', "Constant", "Specify constant offset by single number", 0),
            ('CURVE', "Variable", "Specify variable offset by providing T -> X curve", 1)
        ]

    offset_curve_types = [
            (SvCurveOffsetOnSurface.BY_PARAMETER, "Curve parameter", "Use offset curve value according to curve's parameter", 0),
            (SvCurveOffsetOnSurface.BY_LENGTH, "Curve length", "Use offset curve value according to curve's length", 1)
        ]

    @throttled
    def update_sockets(self, context):
        self.inputs['OffsetCurve'].hide_safe = self.offset_type == 'CONST'
        self.inputs['Offset'].hide_safe = self.offset_type != 'CONST'

    offset_type : EnumProperty(
            name = "Offset type",
            description = "Specify how the offset values are provided",
            items = offset_types,
            default = 'CONST',
            update = update_sockets)

    offset_curve_type : EnumProperty(
            name = "Offset curve usage",
            description = "How offset curve is evaluated along the curve being offseted",
            items = offset_curve_types,
            default = SvCurveOffsetOnSurface.BY_PARAMETER,
            update = updateNode)

    len_resolution : IntProperty(
        name = "Length resolution",
        default = 50,
        min = 3,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Curve plane:")
        layout.prop(self, 'curve_plane', expand=True)
        layout.prop(self, 'offset_type', expand=True)
        if self.offset_type == 'CURVE':
            layout.label(text="Offset curve use:")
            layout.prop(self, 'offset_curve_type', text='')
            if self.offset_curve_type == SvCurveOffsetOnSurface.BY_LENGTH:
                layout.prop(self, 'len_resolution')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        self.inputs.new('SvCurveSocket', "OffsetCurve")
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvCurveSocket', "UVCurve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        surface_s = self.inputs['Surface'].sv_get()
        offset_s = self.inputs['Offset'].sv_get()
        offset_curve_s = self.inputs['OffsetCurve'].sv_get(default = [[None]])

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        offset_s = ensure_nesting_level(offset_s, 2)
        if self.inputs['OffsetCurve'].is_linked:
            offset_curve_s = ensure_nesting_level(offset_curve_s, 2, data_types=(SvCurve,))

        curves_out = []
        uv_curves_out = []
        for curves, surfaces, offsets, offset_curves in zip_long_repeat(curve_s, surface_s, offset_s, offset_curve_s):
            new_curves = []
            new_uv_curves = []
            for curve, surface, offset, offset_curve in zip_long_repeat(curves, surfaces, offsets, offset_curves):
                if self.offset_type == 'CONST':
                    new_curve = SvCurveOffsetOnSurface(curve, surface, offset=offset,
                                    uv_space=False, axis=self.curve_axis)
                    new_uv_curve = SvCurveOffsetOnSurface(curve, surface, offset=offset,
                                    uv_space=True, axis=self.curve_axis)
                else:
                    if offset_curve is None:
                        raise SvNoDataError(socket=self.inputs['OffsetCurve'], node=self)

                    new_curve = SvCurveOffsetOnSurface(curve, surface,
                                    offset_curve = offset_curve,
                                    offset_curve_type = self.offset_curve_type,
                                    len_resolution = self.len_resolution,
                                    uv_space = False, axis = self.curve_axis)
                    new_uv_curve = SvCurveOffsetOnSurface(curve, surface,
                                    offset_curve = offset_curve,
                                    offset_curve_type = self.offset_curve_type,
                                    len_resolution = self.len_resolution,
                                    uv_space = True, axis = self.curve_axis)

                new_curves.append(new_curve)
                new_uv_curves.append(new_uv_curve)
            curves_out.append(new_curves)
            uv_curves_out.append(new_uv_curves)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['UVCurve'].sv_set(uv_curves_out)

def register():
    bpy.utils.register_class(SvCurveOffsetOnSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvCurveOffsetOnSurfaceNode)

