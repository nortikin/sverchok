# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####

from itertools import zip_longest

import bpy
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import (
    levelsOflist, levels_of_list_or_np, numpy_match_long_repeat, updateNode)

from sverchok.ui.sv_icons import custom_icon
import numpy as np
from sverchok.utils.modules.vector_math_utils import numpy_vector_func_dict, mathutils_vector_func_dict, vector_math_ops


socket_type = {'s': 'SvStringsSocket', 'v': 'SvVerticesSocket'}

# apply f to all values recursively
# - fx and fxy do full list matching by length

def recurse_fx_numpy(l, func, level, out_numpy):
    if level == 1:
        nl = np.array(l)
        return func(nl) if out_numpy else func(nl).tolist()
    else:
        rfx = recurse_fx_numpy
        t = [rfx(i, func, level-1, out_numpy) for i in l]
    return t

def recurse_fxy_numpy(l1, l2, func, level, min_l2_level, out_numpy):
    if level == 1:
        nl1 = np.array(l1)
        nl2 = np.array(l2)
        nl1, nl2 = numpy_match_long_repeat([nl1, nl2])
        res = func(nl1, nl2) if out_numpy else func(nl1, nl2).tolist()
        return res
    else:
        res = []
        res_append = res.append
        if levels_of_list_or_np([l1]) < 4:
            l1 = [l1]
        if levels_of_list_or_np([l2]) < min_l2_level+1:
            l2 = [l2]
        # will only be used if lists are of unequal length
        fl = l2[-1] if len(l1) > len(l2) else l1[-1]
        for u, v in zip_longest(l1, l2, fillvalue=fl):
            res_append(recurse_fxy_numpy(u, v, func, level-1, min_l2_level, out_numpy))
        return res

def recurse_fx(l, func, level):
    if not level:
        return func(l)
    else:
        rfx = recurse_fx
        t = [rfx(i, func, level-1) for i in l]
    return t

def recurse_fxy(l1, l2, func, level, min_l2_level):
    res = []
    res_append = res.append

    if levelsOflist([l1]) < 3:
        l1 = [l1]
    if levelsOflist([l2]) < min_l2_level:
        l2 = [l2]
    # will only be used if lists are of unequal length
    fl = l2[-1] if len(l1) > len(l2) else l1[-1]
    if level == 1:
        for u, v in zip_longest(l1, l2, fillvalue=fl):
            res_append(func(u, v))
    else:
        for u, v in zip_longest(l1, l2, fillvalue=fl):
            res_append(recurse_fxy(u, v, func, level-1, min_l2_level))
    return res


class SvVectorMathNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    '''Vector: Add, Dot P..'''
    bl_idname = 'SvVectorMathNodeMK3'
    bl_label = 'Vector Math'
    bl_icon = 'THREE_DOTS'
    sv_icon = 'SV_VECTOR_MATH'

    @throttled
    def mode_change(self, context):
        self.update_sockets()

    current_op: EnumProperty(
        items=vector_math_ops,
        name="Function",
        description="Function choice",
        default="COMPONENT-WISE",
        update=mode_change)

    amount: FloatProperty(default=1.0, name='amount', update=updateNode)
    v3_input_0: FloatVectorProperty(size=3, default=(0,0,0), name='input a', update=updateNode)
    v3_input_1: FloatVectorProperty(size=3, default=(0,0,0), name='input b', update=updateNode)

    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("MathUtils", "MathUtils", "MathUtils", 1)]

    implementation : EnumProperty(
        name='Implementation', items=implementation_modes,
        description='Choose calculation method',
        default="NumPy", update=updateNode)

    implementation_func_dict ={
        "NumPy": (numpy_vector_func_dict, recurse_fx_numpy, recurse_fxy_numpy),
        "MathUtils": (mathutils_vector_func_dict, recurse_fx, recurse_fxy)
    }

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_label(self):
        text = self.current_op.replace("_", " ")
        if text in {'SCALAR', '1/SCALAR'}:
            text = f'A * {text}'
        return text


    def draw_buttons(self, ctx, layout):
        layout.prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))
        layout.label(text="Implementation:")
        layout.prop(self, "implementation", expand=True)
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "current_op", text="Function")
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "A").prop_name = 'v3_input_0'
        self.inputs.new('SvVerticesSocket', "B").prop_name = 'v3_input_1'
        self.outputs.new('SvVerticesSocket', "Out")

    socket_info: StringProperty(default="vv v")
    def update_sockets(self):
        socket_info = numpy_vector_func_dict.get(self.current_op)[2]
        if socket_info != self.socket_info:
            self.socket_info = socket_info
            t_inputs, t_outputs = socket_info.split(' ')

            self.outputs[0].replace_socket(socket_type.get(t_outputs))

            if len(t_inputs) > len(self.inputs):
                self.inputs.new('SvVerticesSocket', "dummy")
            elif len(t_inputs) < len(self.inputs):
                self.inputs.remove(self.inputs[-1])

            renames = 'AB'
            for idx, t_in in enumerate(t_inputs):
                s = self.inputs[idx].replace_socket(socket_type.get(t_in), renames[idx])
                s.prop_name = f'v3_input_{idx}' if t_in == 'v' else 'amount'

    def process(self):

        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        func = self.implementation_func_dict[self.implementation][0].get(self.current_op)[1]
        num_inputs = len(inputs)

        # get either input data, or socket default
        input_one = inputs[0].sv_get(deepcopy=False)


        level = levels_of_list_or_np(input_one) - 1
        if num_inputs == 1:
            recurse_func = self.implementation_func_dict[self.implementation][1]
            params = [input_one, func, level]
            # result = recurse_func(input_one, func, level, self.output_numpy)
        else:
            input_two = inputs[1].sv_get(deepcopy=False)
            level = max(level, levels_of_list_or_np(input_two) - 1)
            min_l2_level = 3 if inputs[1].bl_idname == "SvVerticesSocket" else 2
            params = [input_one, input_two, func, level, min_l2_level]
            recurse_func = self.implementation_func_dict[self.implementation][2]

        if self.implementation == 'NumPy':
            params.append(self.output_numpy)
        result = recurse_func(*params)
        outputs[0].sv_set(result)



def register():
    bpy.utils.register_class(SvVectorMathNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvVectorMathNodeMK3)
