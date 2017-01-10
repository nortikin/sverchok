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
from bpy.props import EnumProperty, BoolProperty, StringProperty
from mathutils import Vector
from mathutils.noise import noise_vector, cell_vector, noise, cell

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, levelsOflist, updateNode)


socket_type = {'s': 'StringsSocket', 'v': 'VerticesSocket'}


func_dict = {
    "DOT":          (lambda u, v: Vector(u).dot(v),                                    ('vv s')),
    "DISTANCE":     (lambda u, v: (Vector(u) - Vector(v)).length,                      ('vv s')),
    "ANGLE RAD":    (lambda u, v: Vector(u).angle(v, 0),                               ('vv s')),
    "ANGLE DEG":    (lambda u, v: degrees(Vector(u).angle(v, 0)),                      ('vv s')),

    "LEN":          (lambda u: sqrt((u[0] * u[0]) + (u[1] * u[1]) + (u[2] * u[2])),    ('v s')),
    "NOISE-S":      (lambda u: noise(Vector(u)),                                       ('v s')),
    "CELL-S":       (lambda u: cell(Vector(u)),                                        ('v s')),

    "CROSS":        (lambda u, v: Vector(u).cross(v)[:],                               ('vv v')),
    "ADD":          (lambda u, v: (u[0]+v[0], u[1]+v[1], u[2]+v[2]),                   ('vv v')),
    "SUB":          (lambda u, v: (u[0]-v[0], u[1]-v[1], u[2]-v[2]),                   ('vv v')),
    "REFLECT":      (lambda u, v: Vector(u).reflect(v)[:],                             ('vv v')),
    "PROJECT":      (lambda u, v: Vector(u).project(v)[:],                             ('vv v')),
    "COMPONENT-WISE":  (lambda u, v: (u[0]*v[0], u[1]*v[1], u[2]*v[2]),                ('vv v')),

    "SCALAR":       (lambda u, s: (u[0]*s, u[1]*s, u[2]*s),                            ('vs v')),
    "1/SCALAR":     (lambda u, s: (u[0]/s, u[1]/s, u[2]/s),                            ('vs v')),
    "ROUND":        (lambda u, s: Vector(u).to_tuple(s),                               ('vs v')),

    "NORMALIZE":    (lambda u: Vector(u).normalized()[:],                              ('v v')),
    "NEG":          (lambda u: (-Vector(u))[:],                                        ('v v')),
    "NOISE-V":      (lambda u: noise_vector(Vector(u))[:],                             ('v v')),
    "CELL-V":       (lambda u: cell_vector(Vector(u))[:],                              ('v v'))
}

# vector math functions
mode_items = [
    ("CROSS",       "Cross product",        "", 0),
    ("DOT",         "Dot product",          "", 1),
    ("ADD",         "Add",                  "", 2),
    ("SUB",         "Sub",                  "", 3),
    ("LEN",         "Length",               "", 4),
    ("DISTANCE",    "Distance",             "", 5),
    ("NORMALIZE",   "Normalize",            "", 6),
    ("NEG",         "Negate",               "", 7),

    ("NOISE-V",     "Noise Vector",         "", 8),
    ("NOISE-S",     "Noise Scalar",         "", 9),
    ("CELL-V",      "Vector Cell noise",    "", 10),
    ("CELL-S",      "Scalar Cell noise",    "", 11),

    ("ANGLE DEG",   "Angle Degrees",        "", 12),
    ("PROJECT",     "Project",              "", 13),
    ("REFLECT",     "Reflect",              "", 14),
    ("SCALAR",      "Multiply Scalar",      "", 15),
    ("1/SCALAR",    "Multiply 1/Scalar",    "", 16),

    ("ANGLE RAD",   "Angle Radians",        "", 17),
    ("ROUND",       "Round s digits",       "", 18),

    ("COMPONENT-WISE", "Component-wise U*V", "", 19)
]


class SvVectorMathNodeMK2(bpy.types.Node, SverchCustomTreeNode):

    ''' VectorMath Node MK2'''
    bl_idname = 'SvVectorMathNodeMK2'
    bl_label = 'Vector Math MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'


    def mode_change(self, context):
        self.update_sockets()
        updateNode(self, context)

    current_op = EnumProperty(
        items=mode_items,
        name="Function",
        description="Function choice",
        default="CROSS",
        update=mode_change)


    def draw_label(self):
        return self.current_op

    def draw_buttons(self, context, layout):
        layout.prop(self, "items_", "Functions:")

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "A")
        self.inputs.new('VerticesSocket', "B")  # will flip to StringsSocket when required
        self.outputs.new('VerticesSocket', "Out")

    def update_sockets(self):
        func, info = func_dict.get(self.current_op)
        t_inputs, t_outputs = info.split(' ')

        self.outputs[0].replace_socket(socket_type.get(t_outputs), "Out")

        if len(t_inputs) > self.inputs:
            self.inputs.new('VerticesSocket', "dummy")
        elif len(t_inputs) < self.inputs:
            self.inputs.remove(self.inputs[-1])

        # with correct input count replace / donothing
        for idx, t_in in enumerate(t_inputs):
            self.inputs[idx].replace_socket(socket_type.get(t_in))
            # set prop_name ?


    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        if not outputs[0].is_linked:
            return
                    
                try:
                    result = self.recurse_fxy(u, b, func, leve - 1)
                except:
                    print(self.name, msg, 'failed')
                    return

            else:
                return  # fail!



                    if isinstance(inputs['V'].links[0].from_socket, VerticesSocket):
                        vector2 = SvGetSocketAnyType(self, inputs['V'], deepcopy=False)
                        result = self.recurse_fxy(u, vector2, func, leve - 1)
                    else:
                        print('socket connected to V is not a vertices socket')
                else:
                    return

            except:
                print('failed scalar out, {} inputs'.format(num_inputs))
                return


    '''
    apply f to all values recursively
    - fx and fxy do full list matching by length
    '''

    # vector -> scalar | vector
    def recurse_fx(self, l, f, leve):
        if not leve:
            return f(l)
        else:
            rfx = self.recurse_fx
            t = [rfx(i, f, leve-1) for i in l]
        return t

    def recurse_fxy(self, l1, l2, f, leve):
        res = []
        res_append = res.append
        # will only be used if lists are of unequal length
        fl = l2[-1] if len(l1) > len(l2) else l1[-1]
        if leve == 1:
            for u, v in zip_longest(l1, l2, fillvalue=fl):
                res_append(f(u, v))
        else:
            for u, v in zip_longest(l1, l2, fillvalue=fl):
                res_append(self.recurse_fxy(u, v, f, leve-1))
        return res


def register():
    bpy.utils.register_class(SvVectorMathNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvVectorMathNodeMK2)
