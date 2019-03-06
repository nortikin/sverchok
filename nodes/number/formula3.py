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

import ast
from math import *

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntProperty
from mathutils import Vector, Matrix
import json
import io

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import fullList, updateNode, dataCorrect, match_long_repeat

def make_functions_dict(*functions):
    return dict([(function.__name__, function) for function in functions])

# Standard functions which for some reasons are not in the math module
def sign(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    else:
        return 0

# Functions
safe_names = make_functions_dict(
        # From math module
        acos, acosh, asin, asinh, atan, atan2,
        atanh, ceil, copysign, cos, cosh, degrees,
        erf, erfc, exp, expm1, fabs, factorial, floor,
        fmod, frexp, fsum, gamma, hypot, isfinite, isinf,
        isnan, ldexp, lgamma, log, log10, log1p, log2, modf,
        pow, radians, sin, sinh, sqrt, tan, tanh, trunc,
        # Additional functions
        abs, sign,
        # From mathutlis module
        Vector, Matrix,
        # Python type conversions
        tuple, list
    )
# Constants
safe_names['e'] = e
safe_names['pi'] = pi

    
def get_variables(string):
    root = ast.parse(string, mode='eval')
    result = {node.id for node in ast.walk(root) if isinstance(node, ast.Name)}
    return result.difference(safe_names.keys())

# It could be safer...
def safe_eval(string, variables):
    env = dict()
    env.update(safe_names)
    env.update(variables)
    env["__builtins__"] = {}
    root = ast.parse(string, mode='eval')
    return eval(compile(root, "<expression>", 'eval'), env)

class SvFormulaNodeMk3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Formula
    Tooltip: Calculate by custom formula.
    """
    bl_idname = 'SvFormulaNodeMk3'
    bl_label = 'Formula Mk3'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def on_update(self, context):
        self.adjust_sockets()
        updateNode(self, context)

    formula = StringProperty(default = "x+y", update=on_update)

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "x")

        self.outputs.new('StringsSocket', "Result")

    def get_variables(self):
        variables = set()
        if not self.formula:
            return variables

        vs = get_variables(self.formula)
        variables.update(vs)

        return list(sorted(list(variables)))
    
    def adjust_sockets(self):
        variables = self.get_variables()
        #self.debug("adjust_sockets:" + str(variables))
        #self.debug("inputs:" + str(self.inputs.keys()))
        for key in self.inputs.keys():
            if key not in variables:
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('StringsSocket', v)


    def update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        # keeping the file internal for now.
        if not self.formula:
            return

        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        result = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                result[var] = self.inputs[var].sv_get()[0]
                #self.debug("get_input: {} => {}".format(var, result[var]))
        return result

    def process(self):

        if not self.outputs[0].is_linked:
            return

        var_names = self.get_variables()
        inputs = self.get_input()

        results = []

        if var_names:
            input_values = [inputs.get(name, []) for name in var_names]
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[]]]
        for values in zip(*parameters):
            variables = dict(zip(var_names, values))

            value = safe_eval(self.formula, variables)
            results.append(value)

        self.outputs['Result'].sv_set([results])


def register():
    bpy.utils.register_class(SvFormulaNodeMk3)


def unregister():
    bpy.utils.unregister_class(SvFormulaNodeMk3)

