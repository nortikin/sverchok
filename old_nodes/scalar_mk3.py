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

from math import *
from fractions import gcd

import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty

from sverchok.ui.sv_icons import custom_icon
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_itertools import (recurse_fx, recurse_fxy)
# pylint: disable=C0326

# Rules for modification:
#     1) Keep 4 items per column
#     2) only add new function with unique number

func_dict = {
    "---------------OPS" : "#---------------------------------------------------#",
    "ADD":         (0,   lambda x, y: x+y,                ('ss s'), "Add"),
    "SUB":         (1,   lambda x, y: x-y,                ('ss s'), "Sub"),
    "MUL":         (2,   lambda x, y: x*y,                ('ss s'), "Multiply"),
    "DIV":         (3,   lambda x, y: x/y,                ('ss s'), "Divide"),
    "INTDIV":      (4,   lambda x, y: x//y,               ('ss s'), "Int Division"),
    "SQRT":        (10,  lambda x: sqrt(fabs(x)),          ('s s'), "Squareroot"),
    "EXP":         (11,  exp,                              ('s s'), "Exponent"),
    "POW":         (12,  lambda x, y: x**y,               ('ss s'), "Power y"),
    "POW2":        (13,  lambda x: x*x,                    ('s s'), "Power 2"),
    "LN":          (14,  log,                              ('s s'), "log"),
    "LOG10":       (20,  log10,                            ('s s'), "log10"),
    "LOG1P":       (21,  log1p,                            ('s s'), "log1p"),
    "ABS":         (30,  fabs,                             ('s s'), "Absolute"),
    "NEG":         (31,  lambda x: -x,                     ('s s'), "Negate"),
    "CEIL":        (32,  ceil,                             ('s s'), "Ceiling"),
    "FLOOR":       (33,  floor,                            ('s s'), "floor"),
    "MIN":         (40,  min,                             ('ss s'), "min"),
    "MAX":         (42,  max,                             ('ss s'), "max"),
    "ROUND":       (50,  round,                            ('s s'), "Round"),
    "ROUND-N":     (51,  lambda x, y: round(x, int(y)),   ('ss s'), "Round N",),
    "FMOD":        (52,  fmod,                            ('ss s'), "Fmod"),
    "MODULO":      (53,  lambda x, y: (x % y),            ('ss s'), "modulo"),
    "MEAN":        (54,  lambda x, y: 0.5*(x + y),        ('ss s'), "mean"),
    "GCD":         (55,  gcd,                             ('ss s'), "gcd"),
    "--------------TRIG" : "#-------------------------------------------------#",
    "SINCOS":      (60,  lambda x: (sin(x), cos(x)),      ('s ss'), "Sin & Cos"),
    "SINE":        (61,  sin,                              ('s s'), "Sine"),
    "COSINE":      (62,  cos,                              ('s s'), "Cosine"),
    "TANGENT":     (63,  tan,                              ('s s'), "Tangent"),
    "ARCSINE":     (64,  asin,                             ('s s'), "Arcsine"),
    "ARCCOSINE":   (65,  acos,                             ('s s'), "Arccosine"),
    "ARCTANGENT":  (66,  atan,                             ('s s'), "Arctangent"),
    "ACOSH":       (67,  acosh,                            ('s s'), "acosh"),
    "ASINH":       (68,  asinh,                            ('s s'), "asinh"),
    "ATANH":       (69,  atanh,                            ('s s'), "atanh"),
    "COSH":        (70,  cosh,                             ('s s'), "cosh"),
    "SINH":        (71,  sinh,                             ('s s'), "sinh"),
    "TANH":        (72,  tanh,                             ('s s'), "tanh"),
    "ATAN2":       (79,  lambda x, y: atan2(y,x),         ('ss s'), "atan2"),
    "DEGREES":     (80,  degrees,                          ('s s'), "Degrees"),
    "RADIANS":     (82,  radians,                          ('s s'), "Radians"),
    "SINXY":       (83,  lambda x, y: sin(x*y),           ('ss s'), "sin(x*y)"),
    "COSXY":       (84,  lambda x, y: cos(x*y),           ('ss s'), "cos(x*y)"),
    "YSINX":       (85,  lambda x, y: y * sin(x),         ('ss s'), "y * sin(x)"),
    "YCOSX":       (86,  lambda x, y: y * cos(x),         ('ss s'), "y * cos(x)"),
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
    "THETA TAU":   (140, lambda x: pi * 2 * ((x-1) / x),   ('s s'), "tau * (x-1 / x)")
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


class SvScalarMathNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    '''Scalar: Add, Sine... '''
    bl_idname = 'SvScalarMathNodeMK3'
    bl_label = 'Scalar Math'
    sv_icon = 'SV_SCALAR_MATH'
    
    replacement_nodes = [('SvScalarMathNodeMK4', None, None)]
    
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

    def rclick_menu(self, context, layout):
        self.node_replacement_menu(context, layout)
        layout.separator()
        layout.prop_menu_enum(self, "current_op", text="Function")
        layout.prop_menu_enum(self, "input_mode_one", text="Input 1 number type")
        if len(self.inputs) == 2:
            layout.prop_menu_enum(self, "input_mode_two", text="Input 2 number type")
    
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
        signature = (len(self.inputs), len(self.outputs))

        x = self.inputs['x'].sv_get(deepcopy=False)
        if signature == (2, 1):
            y = self.inputs['y'].sv_get(deepcopy=False)

        if self.outputs[0].is_linked:
            result = []
            current_func = func_from_mode(self.current_op)
            if signature == (1, 1):
                result = recurse_fx(x, current_func)
            elif signature == (2, 1):
                result = recurse_fxy(x, y, current_func)
            elif signature == (1, 2):
                # special case at the moment
                result = recurse_fx(x, sin)
                result2 = recurse_fx(x, cos)
                self.outputs[1].sv_set(result2)

            self.outputs[0].sv_set(result)


classes = [SvScalarMathNodeMK3]
register, unregister = bpy.utils.register_classes_factory(classes)
