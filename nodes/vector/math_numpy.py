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

from math import degrees, sqrt
from itertools import zip_longest

import bpy
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import levelsOflist, levels_of_list_or_np, updateNode, list_match_func, list_match_modes, numpy_list_match_modes, numpy_list_match_func

from sverchok.ui.sv_icons import custom_icon
import numpy as np

# pylint: disable=C0326

socket_type = {'s': 'SvStringsSocket', 'v': 'SvVerticesSocket'}
def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.sum(v1_u * v2_u, axis=1), -1.0, 1.0))
# project from https://stackoverflow.com/a/55226228
def reflect(v1,v2):
    mirror = v2/np.linalg.norm(v2, axis=1)
    dot2 = 2 * np.sum(mirror * v1, axis=1)
    return v1 - (dot2[:,np.newaxis] * mirror)
def scale_two_axis(v1,s, axis1, axis2):
    v1[:,axis1]*=s
    v1[:,axis2]*=s
    return v1
func_dict = {
    "DOT":            (1,  lambda u, v: np.sum(u * v, axis=1),                          ('vv s'),        "Dot product"),
    "DISTANCE":       (5,  lambda u, v: np.linalg.norm(u-v, axis=1),            ('vv s'),           "Distance"),
    "ANGLE DEG":      (12, lambda u, v: np.degrees(angle_between(u,v)),            ('vv s'),      "Angle Degrees"),
    "ANGLE RAD":      (17, lambda u, v: angle_between(u,v),                     ('vv s'),      "Angle Radians"),

    "LEN":            (4,  lambda u: np.linalg.norm(u, axis=1),     ('v s'),             "Length"),
    "CROSS":          (0,  lambda u, v: np.cross(u, v),                     ('vv v'),      "Cross product"),
    "ADD":            (2,  lambda u, v: u+v                              ,         ('vv v'),                "Add"),
    "SUB":            (3,  lambda u, v: u-v                              ,         ('vv v'),                "Sub"),
    "PROJECT":        (13, lambda u, v: v * (np.sum(u * v, axis=1)/np.sum(v * v, axis=1))[:,np.newaxis],                   ('vv v'),            "Project"),
    "REFLECT":        (14, lambda u, v: reflect(u,v),                   ('vv v'),            "Reflect"),
    "COMPONENT-WISE": (19, lambda u, v: u*v,         ('vv v'), "Component-wise U*V"),

    "SCALAR":         (15, lambda u, s: u*s,                  ('vs v'),    "Multiply Scalar"),
    "1/SCALAR":       (16, lambda u, s: u/s,                  ('vs v'),  "Multiply 1/Scalar"),
    "ROUND":          (18, lambda u, s: Vector(u).to_tuple(abs(int(s))),           ('vs v'),     "Round s digits"),

    "NORMALIZE":      (6,  lambda u: u/np.linalg.norm(u, axis=1),                     ('v v'),          "Normalize"),
    "NEG":            (7,  lambda u: -u,                               ('v v'),             "Negate"),

    "SCALE XY":       (30, lambda u, s: scale_two_axis(u, s, 0, 1),                    ('vs v'),           "Scale XY"),
    "SCALE XZ":       (31, lambda u, s: scale_two_axis(u, s, 0, 2),                  ('vs v'),           "Scale XZ"),
    "SCALE YZ":       (32, lambda u, s: scale_two_axis(u, s, 1, 2),                  ('vs v'),           "Scale YZ")

}


mode_items = [(k, descr, '', ident) for k, (ident, _, _, descr) in sorted(func_dict.items(), key=lambda k: k[1][0])]


# apply f to all values recursively
# - fx and fxy do full list matching by length

def recurse_fx(l, f, level, out_numpy):
    if level ==1:
        nl= np.array(l)
        return f(nl) if out_numpy else f(nl).tolist()
    else:
        rfx = recurse_fx
        t = [rfx(i, f, level-1, out_numpy) for i in l]
    return t

def recurse_fxy(l1, l2, f, level, out_numpy):
    res = []
    res_append = res.append
    # will only be used if lists are of unequal length
    fl = l2[-1] if len(l1) > len(l2) else l1[-1]
    if level == 1:

        nl1= np.array(l1)
        nl2= np.array(l2)
        nl1, nl2 = numpy_list_match_func['REPEAT']([nl1, nl2])
        res =f(nl1, nl2) if out_numpy else f(nl1, nl2).tolist()
        return res
        # for u, v in zip_longest(l1, l2, fillvalue=fl):
        #     res_append(f(u, v))
    else:

        for u, v in zip_longest(l1, l2, fillvalue=fl):
            res_append(recurse_fxy(u, v, f, level-1, out_numpy))
        return res




class SvVectorMathNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    '''Vector: Add, Dot P..'''
    bl_idname = 'SvVectorMathNodeMK3'
    bl_label = 'Vector Math Numpy'
    bl_icon = 'THREE_DOTS'
    sv_icon = 'SV_VECTOR_MATH'

    def mode_change(self, context):
        self.update_sockets()
        updateNode(self, context)

    current_op: EnumProperty(
        items=mode_items,
        name="Function",
        description="Function choice",
        default="COMPONENT-WISE",
        update=mode_change)

    amount: FloatProperty(default=1.0, name='amount', update=updateNode)
    v3_input_0: FloatVectorProperty(size=3, default=(0,0,0), name='input a', update=updateNode)
    v3_input_1: FloatVectorProperty(size=3, default=(0,0,0), name='input b', update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_label(self):
        text = self.current_op
        if text in {'SCALAR', '1/SCALAR'}:
           text = f'A * {text}'
        return text


    def draw_buttons(self, ctx, layout):
        layout.prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))
        layout.prop(self, "output_numpy")

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "current_op", text="Function")
        #layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "output_numpy", expand=False)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "A").prop_name = 'v3_input_0'
        self.inputs.new('SvVerticesSocket', "B").prop_name = 'v3_input_1'
        self.outputs.new('SvVerticesSocket', "Out")


    def update_sockets(self):
        socket_info = func_dict.get(self.current_op)[2]
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

        func = func_dict.get(self.current_op)[1]
        num_inputs = len(inputs)

        # get either input data, or socket default
        input_one = inputs[0].sv_get(deepcopy=True)

        # level = levelsOflist(input_one) - 1
        level = levels_of_list_or_np(input_one) - 1
        if num_inputs == 1:
            result = recurse_fx(input_one, func, level, self.output_numpy)
        else:
            input_two = inputs[1].sv_get(deepcopy=True)
            result = recurse_fxy(input_one, input_two, func, level, self.output_numpy)

        outputs[0].sv_set(result)



def register():
    bpy.utils.register_class(SvVectorMathNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvVectorMathNodeMK3)
