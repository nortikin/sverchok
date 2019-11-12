# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from math import pi
import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty

from sverchok.ui.sv_icons import custom_icon
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.sv_itertools import (recurse_f_level_control)
from sverchok.utils.geom import LinearSpline, CubicSpline
import numpy as np

mode_Items = [
    ("Sine",       "Sine",     "Sinusoidal wave", custom_icon("SV_OSCILLATOR_SINE"), 0),
    ("Square",     "Square",   "Square wave",     custom_icon("SV_OSCILLATOR_INT"),  1),
    ("Saw",        "Saw",      "Saw wave",        custom_icon("SV_OSCILLATOR_SAW"),  2),
    ("Triangular", "Triangle", "Triangular",      custom_icon("SV_OSCILLATOR_TRI"),  3),
    ("Custom",     "Custom",   "Custom wave",     custom_icon("SV_OSCILLATOR_WAVE"), 4),
    ]

def oscillator(params, constant, matching_f):
    result = []
    mode, spline_func, knots, out_numpy = constant
    params = matching_f(params)

    for props in zip(*params):
        regular_prop = matching_f(props[:5])
        wave = props[5]
        val, amplitude, period, phase, offset = [np.array(prop) for prop in regular_prop]

        if mode == 'Sine':
            res = amplitude * np.sin((val / period + phase) * pi*2) + offset

        elif mode == 'Square':
            act_phase = np.ones(amplitude.shape)
            mask = np.sin((val / period + phase) *pi*2) < 0
            act_phase[mask] = -1
            res = amplitude * act_phase + offset

        elif mode == 'Saw':
            res = amplitude - amplitude * (((val / period + phase) * 2) % 2) + offset

        elif mode == 'Triangular':
            mask = ((val / period + phase) * 2) % 2 > 1
            res = 2 * amplitude * (((val / period + phase)*2) % 1) - amplitude
            res[mask] *= -1
            res += offset

        elif mode == 'Custom' and wave:
            spline = spline_func(wave, metric=knots, is_cyclic=False)
            val = spline.eval(np.abs(val / period + phase) % 1)
            res = amplitude * np.array(val)[:, 1]  + offset

        result.append(res if out_numpy else res.tolist())

    return result

class SvOscillatorNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sine, Saw, Square
    Tooltip: Generate a oscillating values from a lineal values .
    """
    bl_idname = 'SvOscillatorNode'
    bl_label = 'Oscillator'
    sv_icon = 'SV_OSCILLATOR'

    def mode_change(self, context):
        self.update_sockets()
        updateNode(self, context)


    current_op: EnumProperty(
        name="Function", description="Function choice", default="Sine",
        items=mode_Items, update=mode_change)

    x_: FloatProperty(default=1.0, name='Value', update=updateNode)
    amplitude: FloatProperty(default=1.0, name='Amplitude', update=updateNode)
    period: FloatProperty(default=1.0, name='Period', update=updateNode)
    phase: FloatProperty(default=1.0, name='Phase', update=updateNode)
    addition: FloatProperty(default=1.0, name='Offset', update=updateNode)


    wave_interp_modes = [('SPL', 'Cubic', "Cubic Spline", 0),
                         ('LIN', 'Linear', "Linear Interpolation", 1)]
    wave_interp_mode: EnumProperty(
        name='Mode', default="LIN",
        items=wave_interp_modes, update=updateNode)

    knot_modes = [('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
                  ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
                  ('POINTS', 'Points', "Points based", 2),
                  ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

    knot_mode: EnumProperty(
        name='Knot Mode', default="DISTANCE",
        items=knot_modes, update=updateNode)

    wave_interp: EnumProperty(
        name="Wave Interpolation",
        description="Behavior on different list lengths",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_label(self):
        label = [self.current_op, "Oscillator"]
        return " ".join(label)

    def draw_buttons(self, ctx, layout):
        row = layout.row(align=True)
        row.prop(self, "current_op", text="")

    def draw_buttons_ext(self, ctx, layout):
        layout.row().prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))
        layout.label(text="Wave interpolation options:")
        if self.current_op == 'Custom':
            layout.row().prop(self, "wave_interp_mode", expand=True)
            layout.row().prop(self, "knot_mode", expand=False)
        layout.prop(self, "list_match", expand=False)
        layout.prop(self, "output_numpy", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "current_op", text="Function")
        if self.current_op == 'Custom':
            layout.prop_menu_enum(self, "wave_interp_mode", text="Wave Interpolation")
            layout.prop_menu_enum(self, "knot_mode", text="Wave knots mode")
        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "output_numpy", expand=False)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'x_'
        self.inputs.new('SvStringsSocket', "Amplitude").prop_name = 'amplitude'
        self.inputs.new('SvStringsSocket', "Period").prop_name = 'period'
        self.inputs.new('SvStringsSocket', "Phase").prop_name = 'phase'
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'addition'
        self.inputs.new('SvVerticesSocket', "Wave")
        self.outputs.new('SvStringsSocket', "Out")
        self.inputs["Wave"].hide_safe = True

    def update_sockets(self):
        if self.current_op == "Custom":
            if self.inputs["Wave"].hide_safe == True:
                self.inputs["Wave"].hide_safe = False
        else:
            self.inputs["Wave"].hide_safe = True



    def process(self):

        if self.outputs[0].is_linked:
            if self.current_op == 'Custom' and not self.inputs["Wave"].is_linked:
                return
            params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs[:6]]
            matching_f = list_match_func[self.list_match]
            spline_func = CubicSpline if self.wave_interp_mode == 'SPL' else LinearSpline
            desired_levels = [2, 2, 2, 2, 2, 3]
            ops = [self.current_op, spline_func, self.knot_mode, self.output_numpy]
            result = recurse_f_level_control(params, ops, oscillator, matching_f, desired_levels)

            self.outputs[0].sv_set(result)


classes = [SvOscillatorNode]
register, unregister = bpy.utils.register_classes_factory(classes)
