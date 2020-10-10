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
from collections import defaultdict

from sverchok.utils.script_importhelper import safe_names
from sverchok.utils.topo import stable_topo_sort
from sverchok.utils.modules.eval_formula import sv_compile, safe_eval, safe_eval_compiled

class ReferenceCollector(ast.NodeVisitor):
    def __init__(self, row_names, col_names=None):
        self.row_names = row_names
        self.col_names = col_names
        self.references = defaultdict(set)
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

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            name = node.value.id
            if not self.is_local(name) and name in self.row_names:
                if self.col_names is None or node.attr in self.col_names:
                    self.references[name].add(node.attr)
        self.generic_visit(node)

class SvSpreadsheetRowAccessor(object):
    def __init__(self, data, row_name):
        self.data = data
        self.row_name = row_name

    def __getattr__(self, attr_name):
        if self.data is None:
            raise NameError("Input spreadsheet socket is not connected")
        if self.row_name not in self.data:
            raise AttributeError(f"No row named `{self.row_name}' in the input spreadsheet")
        if attr_name not in self.data[self.row_name]:
            raise AttributeError(f"No column named `{attr_name}' in the input spreadsheet")
        return self.data[self.row_name][attr_name]

class SvSpreadsheetAccessor(object):
    def __init__(self, data):
        self.data = data

    def __getattr__(self, attr_name):
        return SvSpreadsheetRowAccessor(self.data, attr_name)

def get_references(string, row_names, col_names=None):
    string = string.strip()
    if not len(string):
        return defaultdict(set)
    root = ast.parse(string, mode='eval')
    visitor = ReferenceCollector(row_names, col_names)
    visitor.visit(root)
    result = visitor.references
    return result

def get_dependencies(src_dict, row_names, col_names):
    items = []
    addresses = []
    edges = []
    from_idx = 0
    rev_idx = dict()
    n_cols = len(col_names)
    for row_name in row_names:
        for col_name in col_names:
            if row_name in src_dict and col_name in src_dict[row_name]:
                string = src_dict[row_name][col_name]
                from_idx = len(items)
                items.append(string)
                addresses.append((row_name, col_name))
                rev_idx[(row_name, col_name)] = from_idx
                #from_idx += 1
                if isinstance(string, str):
                    refs = get_references(string, row_names, col_names)
                    for to_row_name in refs:
                        for to_col_name in refs[to_row_name]:
                            edges.append((from_idx, to_row_name, to_col_name))
    edges_res = []
    for from_idx, to_row_name, to_col_name in edges:
        to_idx = rev_idx[(to_row_name,to_col_name)]
        edges_res.append((to_idx, from_idx))
    return items, addresses, edges_res

def topo_sort_dependencies(src_dict, row_names, col_names):
    items, addresses, edges = get_dependencies(src_dict, row_names, col_names)
    sorted_addresses = stable_topo_sort(addresses, edges)
    return sorted_addresses

def compile_spreadsheet(src_dict, col_names):
    result = src_dict.copy()
    for row_name in src_dict:
        for col_name in col_names:
            if col_name in src_dict[row_name]:
                formula = src_dict[row_name][col_name]
                if formula and isinstance(formula, str):
                    result[row_name][col_name] = sv_compile(formula)
    return result

def eval_compiled_spreadsheet(compiled_src_dict, row_names, order, variables, allowed_names=None):
    result = compiled_src_dict.copy()
    accessors = {name : SvSpreadsheetRowAccessor(result, name) for name in row_names}
    variables = variables.copy()
    variables.update(accessors)
    for row_name, col_name in order:
        compiled = compiled_src_dict[row_name][col_name]
        if compiled:
            value = safe_eval_compiled(compiled, variables, allowed_names)
            result[row_name][col_name] = value
    return result

def eval_spreadsheet(src_dict, row_names, col_names, variables, allowed_names=None):
    order = topo_sort_dependencies(src_dict, row_names, col_names)
    compiled_src_dict = compile_spreadsheet(src_dict, col_names)
    return eval_compiled_spreadsheet(compiled_src_dict, row_names, order, variables, allowed_names)

