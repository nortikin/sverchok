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

import bpy
from bpy.props import (EnumProperty, FloatProperty, BoolProperty,
                       IntProperty, BoolVectorProperty)
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func
from sverchok.utils.sv_itertools import recurse_f_level_control


func_dict = {
    "AND":         (1,  lambda x: np.logical_and(x[0], x[1]),                 ('ii'), "And"),
    "OR":          (2,  lambda x: np.logical_or(x[0], x[1]),                  ('ii'), "Or"),
    "IF":          (3,  lambda x: x.astype(bool),                             ('i'),  "If"),
    "NOT":         (4,  np.logical_not,                                       ('i'),  "Not"),
    "NAND":        (5,  lambda x: np.logical_not(np.logical_and(x[0], x[1])), ('ii'), "Nand"),
    "NOR":         (6,  lambda x: np.logical_not(np.logical_or(x[0], x[1])),  ('ii'), "Nor"),
    "XOR":         (7,  lambda x: np.logical_xor(x[0], x[1]),                 ('ii'), "Xor"),
    "XNOR":        (8,  lambda x: np.logical_not(np.logical_xor(x[0], x[1])), ('ii'), "Xnor"),
    "LESS":        (9,  lambda x: x[0] < x[1],                                ('ff'), "<"),
    "BIG":         (10, lambda x: x[0] > x[1],                                ('ff'), ">"),
    "EQUAL":       (11, lambda x: x[0] == x[1],                               ('ff'), "=="),
    "NOT_EQ":      (12, lambda x: x[0] != x[1],                               ('ff'), "!="),
    "LESS_EQ":     (13, lambda x: x[0] <= x[1],                               ('ff'), "<="),
    "BIG_EQ":      (14, lambda x: x[0] >= x[1],                               ('ff'), ">="),
    "TRUE":        (15, np.array([True]),                                     (''),   "True"),
    "FALSE":       (16, np.array([False]),                                    (''),   "False"),
    }

def func_from_mode(mode):
    return func_dict[mode][1]

def generate_node_items():
    prefilter = {k: v for k, v in func_dict.items() if not k.startswith('---')}
    return [(k, descr, '', ident) for k, (ident, _, _, descr) in sorted(prefilter.items(), key=lambda k: k[1][0])]

mode_items = generate_node_items()

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
class SvLogicNode(bpy.types.Node, SverchCustomTreeNode):
    '''And, Or, If, <, >..'''
    bl_idname = 'SvLogicNode'
    bl_label = 'Logic functions'
    bl_icon = 'NONE' #'LOGIC'
    sv_icon = 'SV_LOGIC'

    @throttled
    def change_type(self, context):
        signature = func_dict[self.items_][2]
        self.set_inputs(len(signature))
        props_names = ['x', 'y']
        for socket, t, n, i in zip(self.inputs, signature, props_names, [0, 1]):
            if t == 'f':
                socket.prop_name = 'i_' + n
                self.prop_types[i] = True
            else:
                socket.prop_name = n
                self.prop_types[i] = False

    def set_inputs(self, num_inputs):
        if num_inputs == len(self.inputs):
            return
        if num_inputs < len(self.inputs):
            while num_inputs < len(self.inputs):
                self.inputs.remove(self.inputs[-1])
        if num_inputs > len(self.inputs):
            if 'X' not in self.inputs:
                self.inputs.new('SvStringsSocket', "X")
            if 'Y' not in self.inputs and num_inputs == 2:
                self.inputs.new('SvStringsSocket', "Y")
            self.change_prop_type(None)

    constant = {
        'FALSE':     False,
        'TRUE':      True,
        }

    x: IntProperty(default=1, name='x', max=1, min=0, update=updateNode)
    y: IntProperty(default=1, name='y', max=1, min=0, update=updateNode)

    i_x: FloatProperty(default=1, name='x', update=updateNode)
    i_y: FloatProperty(default=1, name='y', update=updateNode)

    items_: EnumProperty(
        name="Logic Gate", description="Logic Gate choice", default="AND", items=mode_items, update=change_type)

     # boolvector to control prop type
    def change_prop_type(self, context):
        inputs = self.inputs
        if inputs:
            inputs[0].prop_name = 'i_x' if self.prop_types[0] else 'x'
        if len(inputs) > 1:
            inputs[1].prop_name = 'i_y' if self.prop_types[1] else 'y'


    prop_types: BoolVectorProperty(size=2, default=(False, False), update=change_prop_type)

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
        layout.prop(self, "items_", text="Functions:")


    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "items_", text="Functions:")
        layout.label(text="Change property type")
        for i, socket in enumerate(self.inputs):
            row = layout.row()
            row.label(text=socket.name)
            txt = "To int" if self.prop_types[i] else "To float"
            row.prop(self, "prop_types", index=i, text=txt, toggle=True)
        layout.row().prop(self, 'list_match', expand=False)
        layout.prop(self, "output_numpy", text="Output NumPy")

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "items_", text="Function:")
        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "output_numpy", expand=False)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "X").prop_name = 'x'
        self.inputs.new('SvStringsSocket', "Y").prop_name = 'y'
        self.outputs.new('SvStringsSocket', "Gate")


    def draw_label(self):

        num_inputs = len(self.inputs)
        label = [self.items_]

        if num_inputs:
            x_val = self.i_x if self.prop_types[0] else self.x
            x_label = 'X' if self.inputs[0].links else str(round(x_val, 3))
            label.append(x_label)

        if num_inputs == 2:
            y_val = self.i_y if self.prop_types[1] else self.y
            y_label = 'Y' if self.inputs[1].links else str(round(y_val, 3))
            label.extend((", ", y_label))
        return " ".join(label)


    def process(self):

        if  not self.outputs['Gate'].is_linked:
            return

        if self.items_ in self.constant:
            result = [[self.constant[self.items_]]]
        else:
            current_func = func_from_mode(self.items_)
            params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]
            matching_f = list_match_func[self.list_match]
            desired_levels = [2 for p in params]
            ops = [current_func, self.list_match, self.output_numpy]
            result = recurse_f_level_control(params, ops, logic_numpy, matching_f, desired_levels)

        self.outputs[0].sv_set(result)



def register():
    bpy.utils.register_class(SvLogicNode)


def unregister():
    bpy.utils.unregister_class(SvLogicNode)
