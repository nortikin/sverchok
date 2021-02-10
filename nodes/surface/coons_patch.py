
import numpy as np
from math import pi

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, throttle_and_update_node
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface.coons import coons_surface

class SvCoonsPatchNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Coons Patch / Surface form four curves
    Tooltip: Generate a surface (Coons Patch) from four boundary curves
    """
    bl_idname = 'SvCoonsPatchNode'
    bl_label = 'Surface from Four Curves'
    bl_icon = 'SURFACE_DATA'
    sv_icon = 'SV_COONS_PATCH'

    check : BoolProperty(
        name = "Check coincidence",
        default = False,
        update = updateNode)

    max_rho : FloatProperty(
        name = "Max. distance",
        min = 0.0,
        default = 0.001,
        precision = 4,
        update = updateNode)

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['Curves'].hide_safe = self.input_mode != 'LIST'
        self.inputs['Curve1'].hide_safe = self.input_mode == 'LIST'
        self.inputs['Curve2'].hide_safe = self.input_mode == 'LIST'
        self.inputs['Curve3'].hide_safe = self.input_mode == 'LIST'
        self.inputs['Curve4'].hide_safe = self.input_mode == 'LIST'

    modes = [
            ('LIST', "List of curves", "Input is provided as a list of curves, which must have 4 items", 0),
            ('FOUR', "4 curves", "Four separate Curve inputs are provided", 1)
        ]
    
    input_mode : EnumProperty(
            name = "Input",
            items = modes,
            default = 'LIST',
            update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'input_mode', text='')
        layout.prop(self, 'check')
        if self.check:
            layout.prop(self, 'max_rho')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curves")
        self.inputs.new('SvCurveSocket', "Curve1")
        self.inputs.new('SvCurveSocket', "Curve2")
        self.inputs.new('SvCurveSocket', "Curve3")
        self.inputs.new('SvCurveSocket', "Curve4")
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def run_check(self, curves):
        pairs = list(zip(curves, curves[1:]))
        pairs.append((curves[-1], curves[0]))
        for idx, (curve1, curve2) in enumerate(pairs):
            _, t_max_1 = curve1.get_u_bounds()
            t_min_2, _ = curve2.get_u_bounds()
            end1 = curve1.evaluate(t_max_1)
            begin2 = curve2.evaluate(t_min_2)
            distance = np.linalg.norm(begin2 - end1)
            if distance > self.max_rho:
                raise Exception("Distance between the end of {}'th curve and the start of {}'th curve is {} - too much".format(idx, idx+1, distance))

    def get_input(self):
        if self.input_mode == 'LIST':
            curve_list_s = self.inputs['Curves'].sv_get()
            curve_list_s = ensure_nesting_level(curve_list_s, 2, data_types=(SvCurve,))
            for curves in curve_list_s:
                if len(curves) != 4:
                    raise Exception("List of curves must contain exactly 4 curve objects!")
                yield curves
        else:
            curve1_s = self.inputs['Curve1'].sv_get()
            curve2_s = self.inputs['Curve2'].sv_get()
            curve3_s = self.inputs['Curve3'].sv_get()
            curve4_s = self.inputs['Curve4'].sv_get()

            curve1_s = ensure_nesting_level(curve1_s, 1, data_types=(SvCurve,))
            curve2_s = ensure_nesting_level(curve2_s, 1, data_types=(SvCurve,))
            curve3_s = ensure_nesting_level(curve3_s, 1, data_types=(SvCurve,))
            curve4_s = ensure_nesting_level(curve4_s, 1, data_types=(SvCurve,))

            for curve1, curve2, curve3, curve4 in zip_long_repeat(curve1_s, curve2_s, curve3_s, curve4_s):
                yield [curve1, curve2, curve3, curve4]

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_out = []
        for curves in self.get_input():
            if self.check:
                self.run_check(curves)
            surface = coons_surface(*curves)
            surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvCoonsPatchNode)

def unregister():
    bpy.utils.unregister_class(SvCoonsPatchNode)

