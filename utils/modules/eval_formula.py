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

from sverchok.utils.script_importhelper import safe_names
from sverchok.utils import logging

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

def sv_compile(string):
    try:
        root = ast.parse(string, mode='eval')
        return compile(root, "<expression>", 'eval')
    except SyntaxError as e:
        logging.exception(e)
        raise Exception("Invalid expression syntax: " + str(e))

def safe_eval_compiled(compiled, variables):
    """
    Evaluate expression, allowing only functions known to be "safe"
    to be used.
    """
    try:
        env = dict()
        env.update(safe_names)
        env.update(variables)
        env["__builtins__"] = {}
        return eval(compiled, env)
    except SyntaxError as e:
        logging.exception(e)
        raise Exception("Invalid expression syntax: " + str(e))

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

