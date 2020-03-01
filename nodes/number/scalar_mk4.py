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

from math import pi, e
from fractions import gcd

import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty

from sverchok.ui.sv_icons import custom_icon
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func
from sverchok.utils.sv_itertools import (recurse_fx, recurse_fxy, recurse_f_level_control)
import numpy as np
# pylint: disable=C0326

# Rules for modification:
#     1) Keep 4 items per column
#     2) only add new function with unique number

func_dict = {
    "---------------OPS" : "#---------------------------------------------------#",
    "ADD":         (0,   lambda x : x[0]+x[1],              ('ss s'), "Add"),
    "SUB":         (1,   lambda x : x[0]-x[1],             ('ss s'), "Sub"),
    "MUL":         (2,   lambda x: x[0]*x[1],              ('ss s'), "Multiply"),
    "DIV":         (3,   lambda x: x[0]/x[1],              ('ss s'), "Divide"),
    "INTDIV":      (4,   lambda x: x[0]//x[1],             ('ss s'), "Int Division"),
    "SQRT":        (10,  lambda x: np.sqrt(np.fabs(x)),    ('s s'),  "Squareroot"),
    "EXP":         (11,  lambda x: np.exp(x),              ('s s'),  "Exponent"),
    "POW":         (12,  lambda x: x[0]**x[1],             ('ss s'), "Power y"),
    "POW2":        (13,  lambda x: x*x,                    ('s s'),  "Power 2"),
    "LN":          (14,  np.log,                           ('s s'),  "log"),
    "LOG10":       (20,  np.log10,                         ('s s'),  "log10"),
    "LOG1P":       (21,  np.log1p,                         ('s s'),  "log1p"),
    "ABS":         (30,  np.fabs,                          ('s s'),  "Absolute"),
    "NEG":         (31,  lambda x: -x,                     ('s s'),  "Negate"),
    "CEIL":        (32,  np.ceil,                          ('s s'),  "Ceiling"),
    "FLOOR":       (33,  np.floor,                         ('s s'),  "floor"),
    "MIN":         (40,  lambda x: np.minimum(x[0],x[1]),  ('ss s'), "min"),
    "MAX":         (42,  lambda x: np.maximum(x[0],x[1]),  ('ss s'), "max"),
    "ROUND":       (50,  np.round,                         ('s s'),  "Round"),
    "ROUND-N":     (51,  lambda x, y: round(x, int(y)),    ('ss s'), "Round N",),
    "FMOD":        (52,  lambda x: np.fmod(x[0], x[1]),    ('ss s'), "Fmod"),
    "MODULO":      (53,  lambda x: (x[0] % x[1]),          ('ss s'), "modulo"),
    "MEAN":        (54,  lambda x: 0.5*(x[0] + x[1]),      ('ss s'), "mean"),
    "GCD":         (55,  gcd,                              ('ss s'), "gcd"),
    "--------------TRIG" : "#-------------------------------------------------#",
    "SINCOS":      (60,  lambda x: (np.sin(x), np.cos(x)), ('s ss'), "Sin & Cos"),
    "SINE":        (61,  np.sin,                           ('s s'),  "Sine"),
    "COSINE":      (62,  np.cos,                           ('s s'),  "Cosine"),
    "TANGENT":     (63,  np.tan,                           ('s s'),  "Tangent"),
    "ARCSINE":     (64,  np.arcsin,                        ('s s'),  "Arcsine"),
    "ARCCOSINE":   (65,  np.arccos,                        ('s s'),  "Arccosine"),
    "ARCTANGENT":  (66,  np.arctan,                        ('s s'),  "Arctangent"),
    "ACOSH":       (67,  np.arccosh,                       ('s s'),  "acosh"),
    "ASINH":       (68,  np.arcsinh,                       ('s s'),  "asinh"),
    "ATANH":       (69,  np.arctanh,                       ('s s'),  "atanh"),
    "COSH":        (70,  np.cosh,                          ('s s'),  "cosh"),
    "SINH":        (71,  np.sinh,                          ('s s'),  "sinh"),
    "TANH":        (72,  np.tanh,                          ('s s'),  "tanh"),
    "ATAN2":       (79,  lambda x: np.arctan2(x[1],x[0]),  ('ss s'), "atan2"),
    "DEGREES":     (80,  np.degrees,                       ('s s'),  "Degrees"),
    "RADIANS":     (82,  np.radians,                       ('s s'),  "Radians"),
    "SINXY":       (83,  lambda x: np.sin(x[0]*x[1]),      ('ss s'), "sin(x*y)"),
    "COSXY":       (84,  lambda x: np.cos(x[0]*x[1]),      ('ss s'), "cos(x*y)"),
    "YSINX":       (85,  lambda x: x[1] * np.sin(x[0]),    ('ss s'), "y * sin(x)"),
    "YCOSX":       (86,  lambda x: x[1] * np.cos(x[0]),    ('ss s'), "y * cos(x)"),
    "-------------CONST" : "#---------------------------------------------------#",
    "PI":          (90,  lambda x: pi * x,                 ('s s'), "pi * x"),
    "TAU":         (100, lambda x: pi * 2 * x,             ('s s'), "tau * x"),
    "E":           (110, lambda x: e * x,                  ('s s'), "e * x"),
    "PHI":         (120, lambda x: 1.61803398875 * x,      ('s s'), "phi * x"),
    "+1":          (130, lambda x: x + 1,                  ('s s'), "x + 1"),
    "-1":          (131, lambda x: x - 1,                  ('s s'), "x - 1"),
    "*2":          (132, lambda x: x * 2,                  ('s s'), "x * 2"),
    "/2":          (133, lambda x: x / 2,                  ('s s'), "x / 2"),
    "RECIP":       (135, lambda x: 1 / x,                  ('s s'), "1 / x"),
    "THETA_TAU":   (140, lambda x: pi * 2 * ((x-1) / x),   ('s s'), "tau * (x-1 / x)")
}

def func_from_mode(mode):
    return func_dict[mode][1]

def generate_node_items():
    prefilter = {k: v for k, v in func_dict.items() if not k.startswith('---')}
    return [(k, descr, '', ident) for k, (ident, _, _, descr) in sorted(prefilter.items(), key=lambda k: k[1][0])]

mode_items = generate_node_items()


def property_change(node, context, origin):
    if origin == 'input_mode_one':
        node.inputs[0].prop_name = {'Float': 'x_', 'Int': 'xi_'}.get(getattr(node, origin))
    elif origin == 'input_mode_two' and len(node.inputs) == 2:
        node.inputs[1].prop_name = {'Float': 'y_', 'Int': 'yi_'}.get(getattr(node, origin))
    else:
        pass
    updateNode(node, context)

def math_numpy(params, constant, matching_f):
    result = []
    func, matching_mode, out_numpy = constant
    params = matching_f(params)
    matching_numpy = numpy_list_match_func[matching_mode]
    for props in zip(*params):

        np_prop = [np.array(prop) for prop in props]

        if len(np_prop)== 1:
            res = func(np_prop[0])
        else:
            regular_prop = matching_numpy(np_prop)
            res = func(regular_prop)

        result.append(res if out_numpy else res.tolist())

    return result

class SvScalarMathNodeMK4(bpy.types.Node, SverchCustomTreeNode):
    '''Scalar: Add, Sine... '''
    bl_idname = 'SvScalarMathNodeMK4'
    bl_label = 'Scalar Math'
    sv_icon = 'SV_SCALAR_MATH'

    def mode_change(self, context):
        self.update_sockets()
        updateNode(self, context)


    current_op: EnumProperty(
        name="Function", description="Function choice", default="MUL",
        items=mode_items, update=mode_change)

    x_: FloatProperty(default=1.0, name='x', update=updateNode)
    y_: FloatProperty(default=1.0, name='y', update=updateNode)
    xi_: IntProperty(default=1, name='x', update=updateNode)
    yi_: IntProperty(default=1, name='y', update=updateNode)

    mode_options = [(k, k, '', i) for i, k in enumerate(["Float", "Int"])]

    input_mode_one: EnumProperty(
        items=mode_options, description="offers int / float selection for socket 1",
        default="Float", update=lambda s, c: property_change(s, c, 'input_mode_one'))

    input_mode_two: EnumProperty(
        items=mode_options, description="offers int / float selection for socket 2",
        default="Float", update=lambda s, c: property_change(s, c, 'input_mode_two'))

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_label(self):
        num_inputs = len(self.inputs)
        label = [self.current_op]

        if num_inputs > 0:
            x = self.x_ if self.input_mode_one == 'Float' else self.xi_
            x_label = 'X' if self.inputs[0].is_linked else str(round(x, 3))
            label.append(x_label)

        if num_inputs == 2:
            y = self.y_ if self.input_mode_two == 'Float' else self.yi_
            y_label = 'Y' if self.inputs[1].is_linked else str(round(y, 3))
            label.extend([', ', y_label])

        return " ".join(label)

    def draw_buttons(self, ctx, layout):
        row = layout.row(align=True)
        row.prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))


    def draw_buttons_ext(self, ctx, layout):
        layout.row().prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))
        layout.row().prop(self, 'input_mode_one', text="input 1")
        if len(self.inputs) == 2:
            layout.row().prop(self, 'input_mode_two', text="input 2")
        if self.current_op not in ['GCD', 'ROUND-N']:
            layout.row().prop(self, 'list_match', expand=False)
            layout.prop(self, "output_numpy", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "current_op", text="Function")
        layout.prop_menu_enum(self, "input_mode_one", text="Input 1 number type")
        if len(self.inputs) == 2:
            layout.prop_menu_enum(self, "input_mode_two", text="Input 2 number type")
        if self.current_op not in ['GCD', 'ROUND-N']:
            layout.prop_menu_enum(self, "list_match", text="List Match")
            layout.prop(self, "output_numpy", expand=False)

    def migrate_from(self, old_node):
        self.current_op = old_node.current_op

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "x").prop_name = 'x_'
        self.inputs.new('SvStringsSocket', "y").prop_name = 'y_'
        self.outputs.new('SvStringsSocket', "Out")


    def update_sockets(self):
        socket_info = func_dict.get(self.current_op)[2]
        t_inputs, t_outputs = socket_info.split(' ')

        if len(t_inputs) > len(self.inputs):
            new_second_input = self.inputs.new('SvStringsSocket', "y").prop_name = 'y_'
            if self.input_mode_two == 'Int':
                new_second_input.prop_name = 'yi_'
        elif len(t_inputs) < len(self.inputs):
            self.input_mode_two = 'Float'
            self.inputs.remove(self.inputs[-1])

        if len(t_outputs) > len(self.outputs):
            self.outputs.new('SvStringsSocket', "cos( x )")
        elif len(t_outputs) < len(self.outputs):
            self.outputs.remove(self.outputs[-1])

        if len(self.outputs) == 1:
            if not "Out" in self.outputs:
                self.outputs[0].replace_socket("SvStringsSocket", "Out")
        elif len(self.outputs) == 2:
            self.outputs[0].replace_socket("SvStringsSocket", "sin( x )")


    def process(self):

        self.ensure_enums_have_no_space(enums=["current_op"])

        if self.outputs[0].is_linked:
            current_func = func_from_mode(self.current_op)
            params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]
            matching_f = list_match_func[self.list_match]
            desired_levels = [2 for p in params]

            if self.current_op in ['GCD', 'ROUND-N']:
                result = recurse_fxy(params[0], params[1], current_func)
            elif self.current_op  == 'SINCOS':
                ops = [np.sin, self.list_match, self.output_numpy]
                result = recurse_f_level_control(params, ops, math_numpy, matching_f, desired_levels)
                ops2 = [np.cos, self.list_match, self.output_numpy]
                result2 = recurse_f_level_control(params, ops2, math_numpy, matching_f, desired_levels)
                self.outputs[1].sv_set(result2)
            else:
                ops = [current_func, self.list_match, self.output_numpy]
                result = recurse_f_level_control(params, ops, math_numpy, matching_f, desired_levels)

            self.outputs[0].sv_set(result)


classes = [SvScalarMathNodeMK4]
register, unregister = bpy.utils.register_classes_factory(classes)
