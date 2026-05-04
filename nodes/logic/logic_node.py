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
from collections import namedtuple

import bpy
from bpy.props import EnumProperty, BoolProperty
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, list_match_func, numpy_list_match_modes,
                                     numpy_list_match_func)
from sverchok.utils.sv_itertools import recurse_f_level_control


Item = namedtuple('Item', ['name', 'arg_number', 'func', 'description'])

functions = {
    "AND":     Item("And",   2, lambda x: np.logical_and(x[0], x[1]),                 "True if X and Y are True"),
    "OR":      Item("Or",    2, lambda x: np.logical_or(x[0], x[1]),                  "True if X or Y are True"),
    "IF":      Item("If",    1, lambda x: x[0].astype(bool),                          "True if X is True"),
    "NOT":     Item("Not",   1, lambda x: np.logical_not(x[0]),                       "True if X is False"),
    "NAND":    Item("Nand",  2, lambda x: np.logical_not(np.logical_and(x[0], x[1])), "True if X or Y are False"),
    "NOR":     Item("Nor",   2, lambda x: np.logical_not(np.logical_or(x[0], x[1])),  "True if X and Y are False"),
    "XOR":     Item("Xor",   2, lambda x: np.logical_xor(x[0], x[1]),                 "True if X and Y are opposite"),
    "XNOR":    Item("Xnor",  2, lambda x: np.logical_not(np.logical_xor(x[0], x[1])), "True if X and Y are equals"),
    "LESS":    Item("<",     2, lambda x: x[0] < x[1],                                "True if X < Y"),
    "BIG":     Item(">",     2, lambda x: x[0] > x[1],                                "True if X > Y"),
    "EQUAL":   Item("==",    2, lambda x: x[0] == x[1],                               "True if X = Y"),
    "NOT_EQ":  Item("!=",    2, lambda x: x[0] != x[1],                               "True if X not = Y"),
    "LESS_EQ": Item("<=",    2, lambda x: x[0] <= x[1],                               "True if X <= Y"),
    "BIG_EQ":  Item(">=",    2, lambda x: x[0] >= x[1],                               "True if X >= Y"),
    "TRUE":    Item("True",  0, lambda x: np.array([True]),                           "Result is Always True"),
    "FALSE":   Item("False", 0, lambda x: np.array([False]),                          "Result is Always False"),
}


def logic_numpy(params, constant, matching_f):
    result = []
    func, matching_mode, out_numpy = constant
    params = matching_f(params)
    matching_numpy = numpy_list_match_func[matching_mode]
    for props in zip(*params):

        np_prop = [np.array(prop) for prop in props]

        if len(np_prop) == 1:
            res = func(np_prop[0])
        else:
            regular_prop = matching_numpy(np_prop)
            res = func(regular_prop)

        result.append(res if out_numpy else res.tolist())

    return result


class SvLogicNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    '''And, Or, If, <, >..
    Logic functions: And/Or/If/Not/Nand/Nor/Xor/</>/==/!=/<=/>=/True/False
    In: A, B
    Out: Result (boolean)
    '''
    bl_idname = 'SvLogicNodeMK2'
    bl_label = 'Logic Functions'
    bl_icon = 'NONE' #'LOGIC'
    sv_icon = 'SV_LOGIC'

    func_names = [(n, i.name, i.name+": "+i.description)for n, i in functions.items()]

    def change_function(self, context):
        arg_number = functions[self.function_name].arg_number
        self.inputs[0].enabled = arg_number > 0
        self.inputs[1].enabled = arg_number > 1
        updateNode(self, context)

    function_name: EnumProperty(
        name="Logic Gate",
        description="Logic Gate choice",
        default="AND",
        items=func_names,
        update=change_function)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "function_name", text="")

    def draw_buttons_ext(self, context, layout):
        layout.row().prop(self, 'list_match', expand=False)
        layout.prop(self, "output_numpy", text="Output NumPy")

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "function_name", text="Function:")
        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "output_numpy", expand=False)

    def migrate_from(self, old_node):
        self.function_name = old_node.items_
        self.inputs['A'].default_int_property = old_node.x
        self.inputs['B'].default_int_property = old_node.y
        self.inputs['A'].default_float_property = old_node.i_x
        self.inputs['B'].default_float_property = old_node.i_y
        self.inputs['A'].default_property_type = 'float' if old_node.prop_types[0] else 'int'
        self.inputs['B'].default_property_type = 'float' if old_node.prop_types[1] else 'int'

    def sv_init(self, context):
        a = self.inputs.new('SvStringsSocket', 'A')
        a.use_prop = True
        a.show_property_type = True
        a.default_property_type = 'int'
        b = self.inputs.new('SvStringsSocket', 'B')
        b.use_prop = True
        b.show_property_type = True
        b.default_property_type = 'int'
        self.outputs.new('SvStringsSocket', "Result")

    def draw_label(self):
        return f'{SvLogicNodeMK2.bl_label}: {self.function_name}'

    def process(self):
        current_func = functions[self.function_name].func
        params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]
        matching_f = list_match_func[self.list_match]
        desired_levels = [2 for p in params]
        ops = [current_func, self.list_match, self.output_numpy]
        result = recurse_f_level_control(params, ops, logic_numpy, matching_f, desired_levels)

        self.outputs[0].sv_set(result)


def register():
    bpy.utils.register_class(SvLogicNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvLogicNodeMK2)
