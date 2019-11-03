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

from math import sin, pi, fabs
import bpy
from bpy.props import EnumProperty, FloatProperty

from sverchok.ui.sv_icons import custom_icon
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.sv_itertools import (recurse_f_multipar, recurse_f_multipar_const)
from sverchok.utils.geom import LinearSpline


def sine_osc(par):
    val, amplitude, period, phase, offset = par
    return amplitude * sin((val / period + phase) * pi*2) + offset

def math_osc(par, func):
    val, amplitude, period, phase, offset = par
    return amplitude * func((val / period + phase) % 1) + offset

def int_osc(par):
    val, amplitude, period, phase, offset = par
    act_phase = 1 if sin((val / period + phase) *pi*2) > 0 else -1
    return amplitude * act_phase + offset

def saw_osc(par):
    val, amplitude, period, phase, offset = par
    return amplitude - amplitude * (((val / period + phase) * 2) % 2) + offset


def trianglura_osc(par):
    val, amplitude, period, phase, offset = par
    if ((val / period + phase) * 2) % 2 > 1:
        return 2*amplitude * (((val/ period + phase)*2) % 1) + offset - amplitude
    else:
        return amplitude -2* amplitude * (((val/ period + phase)*2) % 1) + offset

def wave_osc(par, spline):
    val, amplitude, period, phase, offset = par
    val = spline.eval([abs(val / period + phase) % 1, 1])

    return amplitude * val[0][1]  + offset


func_dict = {
    "SINE_OSC":     (0,   sine_osc        , "Sine"),
    "INT_OSC":      (1,   int_osc         , "Square"),
    "SAW":          (2,   saw_osc         , "Saw"),
    "TRIANGLE":     (3,   trianglura_osc  , "Triangle"),
    "WAVE":         (4,   wave_osc        , "Wave"),
    "ABS":          (30,  fabs            , "Absolute"),
    "NEG":          (31,  lambda x: -x    , "Negate"),

}

def func_from_mode(mode):
    return func_dict[mode][1]

def generate_node_items():
    prefilter = {k: v for k, v in func_dict.items() if not k.startswith('---')}
    return [(k, descr, '', ident) for k, (ident, _, descr) in sorted(prefilter.items(), key=lambda k: k[1][0])]

mode_items = generate_node_items()



class SvOscillatorNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sine, Saw, Square
    Tooltip: Generate a oscillation signal from a lineal range .
    """
    bl_idname = 'SvOscillatorNode'
    bl_label = 'Oscillator'
    sv_icon = 'SV_OSCILLATOR'

    def mode_change(self, context):
        self.update_sockets()
        updateNode(self, context)


    current_op: EnumProperty(
        name="Function", description="Function choice", default="SINE_OSC",
        items=mode_items, update=mode_change)

    x_: FloatProperty(default=1.0, name='Value', update=updateNode)
    amplitude: FloatProperty(default=1.0, name='Amplitude', update=updateNode)
    period: FloatProperty(default=1.0, name='Period', update=updateNode)
    phase: FloatProperty(default=1.0, name='Phase', update=updateNode)
    addition: FloatProperty(default=1.0, name='Offset', update=updateNode)

    list_match : EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def draw_label(self):
        label = [func_dict[self.current_op][2], "Oscillator"]
        return " ".join(label)

    def draw_buttons(self, ctx, layout):
        row = layout.row(align=True)
        row.prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))

    def draw_buttons_ext(self, ctx, layout):
        layout.row().prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))
        layout.prop(self, "list_match", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "current_op", text="Function")
        layout.prop_menu_enum(self, "list_match", text="List Match")


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "x").prop_name = 'x_'
        self.inputs.new('SvStringsSocket', "Amplitude").prop_name = 'amplitude'
        self.inputs.new('SvStringsSocket', "Period").prop_name = 'period'
        self.inputs.new('SvStringsSocket', "Phase").prop_name = 'phase'
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'addition'
        self.inputs.new('SvVerticesSocket', "Wave")
        self.outputs.new('SvStringsSocket', "Out")
        self.inputs["Wave"].hide_safe = True
    def update_sockets(self):
        if self.current_op == "WAVE":
            if self.inputs["Wave"].hide_safe == True:
                self.inputs["Wave"].hide_safe = False
        else:
            self.inputs["Wave"].hide_safe = True

    def process(self):

        if self.outputs[0].is_linked:
            params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs[:5]]
            current_func = func_from_mode(self.current_op)
            matching_f = list_match_func[self.list_match]
            result = []
            if self.current_op == 'WAVE':
                if self.inputs['Wave'].is_linked:
                    waves = self.inputs['Wave'].sv_get(default=[[]], deepcopy=False)
                    params = [waves] + params
                    params = matching_f(params)
                    for p in zip(*params):
                        spline = LinearSpline(p[0], metric="DISTANCE", is_cyclic=False)
                        result.append(recurse_f_multipar_const(p[1:], spline, wave_osc, matching_f))
            elif self.current_op in ['ABS', 'NEG']:
                result = recurse_f_multipar_const(params, current_func, math_osc, matching_f)
            else:
                result = recurse_f_multipar(params, current_func, matching_f)

            self.outputs[0].sv_set(result)


classes = [SvOscillatorNode]
register, unregister = bpy.utils.register_classes_factory(classes)
