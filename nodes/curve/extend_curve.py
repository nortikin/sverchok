
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve, SvTaylorCurve, SvLine, SvCircle, SvCurveLengthSolver
from sverchok.utils.curve.algorithms import concatenate_curves, reverse_curve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.extend import extend_curve
from sverchok.utils.geom import circle_by_two_derivatives

class SvExtendCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extend Curve
    Tooltip: Smoothly extend a curve beyond it's range
    """
    bl_idname = 'SvExtendCurveNode'
    bl_label = 'Extend Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTEND_CURVE'

    t_before : FloatProperty(
        name = "Start extension",
        min = 0.0,
        default = 1.0,
        update = updateNode)

    t_after : FloatProperty(
        name = "End extension",
        min = 0.0,
        default = 1.0,
        update = updateNode)

    modes = [
        ('LINE', "1 - Line", "Straight line segment", 0),
        ('ARC', "1 - Arc", "Circular arc", 1),
        ('QUAD', "2 - Smooth - Normal", "Smooth curve", 2),
        ('CUBIC', "3 - Smooth - Curvature", "Smooth curve", 3)
    ]

    mode : EnumProperty(
        name = "Type",
        items = modes,
        default = 'LINE',
        update = updateNode)

    len_modes = [
        ('T', "Curve parameter", "Specify curve parameter extension", 0),
        ('L', "Curve length", "Specify curve length extension", 1)
    ]

    len_mode : EnumProperty(
        name = "Length mode",
        items = len_modes,
        default = 'T',
        update = updateNode)

    len_resolution : IntProperty(
        name = "Length resolution",
        default = 50,
        min = 3,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "StartExt").prop_name = 't_before'
        self.inputs.new('SvStringsSocket', "EndExt").prop_name = 't_after'
        self.outputs.new('SvCurveSocket', "ExtendedCurve")
        self.outputs.new('SvCurveSocket', "StartExtent")
        self.outputs.new('SvCurveSocket', "EndExtent")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text='')
        layout.label(text='Extend by:')
        layout.prop(self, "len_mode", text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.len_mode == 'L':
            layout.prop(self, 'len_resolution')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        t_before_s = self.inputs['StartExt'].sv_get()
        t_after_s = self.inputs['EndExt'].sv_get()

        t_before_s = ensure_nesting_level(t_before_s, 2)
        t_after_s = ensure_nesting_level(t_after_s, 2)
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))

        start_out = []
        end_out = []
        curve_out = []
        for curves, t_before_i, t_after_i in zip_long_repeat(curve_s, t_before_s, t_after_s):
            for curve, t_before, t_after in zip_long_repeat(curves, t_before_i, t_after_i):
                start_extent, end_extent = extend_curve(curve, t_before, t_after,
                                            mode = self.mode,
                                            len_mode = self.len_mode,
                                            len_resolution = self.len_resolution)
                start_out.append(start_extent)
                end_out.append(end_extent)
                curves = []
                if start_extent is not None:
                    curves.append(start_extent)
                curves.append(curve)
                if end_extent is not None:
                    curves.append(end_extent)
                new_curve = concatenate_curves(curves)#, allow_generic=False)
                curve_out.append(new_curve)

        self.outputs['StartExtent'].sv_set(start_out)
        self.outputs['EndExtent'].sv_set(end_out)
        self.outputs['ExtendedCurve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvExtendCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExtendCurveNode)

