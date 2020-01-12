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
from collections import defaultdict

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntProperty
import json
import io

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, match_long_repeat, zip_long_repeat
from sverchok.utils import logging
from sverchok.utils.script_importhelper import safe_names

class VariableCollector(ast.NodeVisitor):
    """
    Visitor class to collect free variable names from the expression.
    The problem is that one doesn't just select all names from expression:
    there can be local-only variables.

    For example, in

        [g*g for g in lst]

    only "lst" should be considered as a free variable, "g" should be not,
    as it is bound by list comprehension scope.

    This implementation is not exactly complete (at least, dictionary comprehensions
    are not supported yet). But it works for most cases.

    Please refer to ast.NodeVisitor class documentation for general reference.
    """
    def __init__(self):
        self.variables = set()
        # Stack of local variables
        # It is not enough to track just a plain set of names,
        # since one name can be re-introduced in the nested scope
        self.local_vars = []

    def push(self, local_vars):
        self.local_vars.append(local_vars)

    def pop(self):
        return self.local_vars.pop()

    def is_local(self, name):
        """
        Check if name is local variable
        """

        for stack_frame in self.local_vars:
            if name in stack_frame:
                return True
        return False

    def visit_SetComp(self, node):
        local_vars = set()
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                local_vars.add(generator.target.id)
        self.push(local_vars)
        self.generic_visit(node)
        self.pop()

    def visit_ListComp(self, node):
        local_vars = set()
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                local_vars.add(generator.target.id)
        self.push(local_vars)
        self.generic_visit(node)
        self.pop()

    def visit_Lambda(self, node):
        local_vars = set()
        arguments = node.args
        for arg in arguments.args:
            local_vars.add(arg.id)
        if arguments.vararg:
            local_vars.add(arguments.vararg.arg)
        self.push(local_vars)
        self.generic_visit(node)
        self.pop()

    def visit_Name(self, node):
        name = node.id
        if not self.is_local(name):
            self.variables.add(name)

        self.generic_visit(node)

def get_variables(string):
    """
    Get set of free variables used by formula
    """
    string = string.strip()
    if not len(string):
        return set()
    root = ast.parse(string, mode='eval')
    visitor = VariableCollector()
    visitor.visit(root)
    result = visitor.variables
    return result.difference(safe_names.keys())

# It could be safer...
def safe_eval(string, variables):
    """
    Evaluate expression, allowing only functions known to be "safe"
    to be used.
    """
    try:
        env = dict()
        env.update(safe_names)
        env.update(variables)
        env["__builtins__"] = {}
        root = ast.parse(string, mode='eval')
        return eval(compile(root, "<expression>", 'eval'), env)
    except SyntaxError as e:
        logging.exception(e)
        raise Exception("Invalid expression syntax: " + str(e))

class SvFormulaNodeMk3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Formula
    Tooltip: Calculate by custom formula.
    """
    bl_idname = 'SvFormulaNodeMk3'
    bl_label = 'Formula'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FORMULA'

    @throttled
    def on_update(self, context):
        self.adjust_sockets()

    @throttled
    def on_update_dims(self, context):
        if self.dimensions < 4:
            self.formula4 = ""
        if self.dimensions < 3:
            self.formula3 = ""
        if self.dimensions < 2:
            self.formula2 = ""

        self.adjust_sockets()

    dimensions : IntProperty(name="Dimensions", default=1, min=1, max=4, update=on_update_dims)

    formula1 : StringProperty(default = "x+y", update=on_update)
    formula2 : StringProperty(update=on_update)
    formula3 : StringProperty(update=on_update)
    formula4 : StringProperty(update=on_update)

    separate : BoolProperty(name="Separate", default=False, update=updateNode)
    wrap : BoolProperty(name="Wrap", default=False, update=updateNode)

    def formulas(self):
        return [self.formula1, self.formula2, self.formula3, self.formula4]

    def formula(self, k):
        return self.formulas()[k]

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula1", text="")
        if self.dimensions > 1:
            layout.prop(self, "formula2", text="")
        if self.dimensions > 2:
            layout.prop(self, "formula3", text="")
        if self.dimensions > 3:
            layout.prop(self, "formula4", text="")
        row = layout.row()
        row.prop(self, "separate")
        row.prop(self, "wrap")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "dimensions")
        self.draw_buttons(context, layout)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "x")

        self.outputs.new('SvStringsSocket', "Result")

    def get_variables(self):
        variables = set()

        for formula in self.formulas():
            vs = get_variables(formula)
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
                self.inputs.new('SvStringsSocket', v)

    def update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        if not any(len(formula) for formula in self.formulas()):
            return

        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        inputs = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                inputs[var] = self.inputs[var].sv_get()

#         n_max = max(len(inputs[var]) for var in inputs)
#         result = []
#         for i in range(n_max):
#             item = defaultdict(list)
#             for var in inputs:
#                 value = inputs[var]
#                 if i < len(value):
#                     item[var].append(value[i])
#                 else:
#                     item[var].append(value[-1])
#             result.append(item)

        return inputs

    def migrate_from(self, old_node):
        if old_node.bl_idname == 'Formula2Node':
            formula = old_node.formula
            # Older formula node allowed only fixed set of
            # variables, with names "x", "n[0]" .. "n[100]".
            # Other names could not be considered valid.
            k = -1
            for socket in old_node.inputs:
                name = socket.name
                if k == -1: # First socket name was "x"
                    new_name = name
                else: # Other names was "n[k]", which is syntactically not
                      # a valid python variable name.
                      # So we replace all occurences of "n[0]" in formula
                      # with "n0", and so on.
                    new_name = "n" + str(k)

                logging.info("Replacing %s with %s", name, new_name)
                formula = formula.replace(name, new_name)
                k += 1

            self.formula1 = formula
            self.wrap = True

    def process(self):

        if not self.outputs[0].is_linked:
            return

        var_names = self.get_variables()
        inputs = self.get_input()

        results = []

        if var_names:
            input_values = [inputs.get(name, [[0]]) for name in var_names]
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[]]]
        for objects in zip(*parameters):
            object_results = []
            for values in zip_long_repeat(*objects):
                variables = dict(zip(var_names, values))
                vector = []
                for formula in self.formulas():
                    if formula:
                        value = safe_eval(formula, variables)
                        vector.append(value)
                if self.separate:
                    object_results.append(vector)
                else:
                    object_results.extend(vector)
            results.append(object_results)

        if self.wrap:
            results = [results]

        self.outputs['Result'].sv_set(results)


def register():
    bpy.utils.register_class(SvFormulaNodeMk3)


def unregister():
    bpy.utils.unregister_class(SvFormulaNodeMk3)
