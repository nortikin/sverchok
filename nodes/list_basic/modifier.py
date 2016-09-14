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

from itertools import accumulate

import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def normalize(a):
    # or numpy version..
    max_value = max(a)
    return [n/max_value for n in a]

def ordered_set(a):
    seen = set()
    b = []
    for x in a:
        if not x in seen:
            b.append(x)
            seen.add(x)
    return b

def unique_consecutives(a):
    prev = ''
    for x in a:
        if not x == prev:
            b.append(x)
            prev = x
    return b

SET = 'Set'
INTX = 'Intersection'
UNION = 'Union'
DIFF = 'Difference'
SYMDIFF = 'Symmetric Diff'
SET_OPS = [SET, INTX, UNION, DIFF, SYMDIFF]


node_item_list = [
    (1, SET, lambda a: set(a)),
    (1, "Ordered Set by input", ordered_set),
    (1, "Unique Consecutives", unique_consecutives),
    (1, "Sequential Set", lambda a: sorted(set(a))),
    (1, "Sequential Set Rev", lambda a: sorted(set(a), reverse=True)),
    (1, "Normalize", normalize),
    (1, "Accumulating Sum", lambda a: list(accumulate(a))),
    (2, INTX, lambda a, b: set(a) & set(b)),
    (2, UNION, lambda a, b: set(a) | set(b)),
    (2, DIFF, lambda a, b: set(a) - set(b)),
    (2, SYMDIFF, lambda a, b: set(a) ^ set(b))
]


func_dict = {k: v for _, k, v in node_item_list}
num_inputs = {k: v for v, k, _ in node_item_list}


class ListModifierNode(bpy.types.Node, SverchCustomTreeNode):
    ''' List Modifier'''
    bl_idname = 'ListModifierNode'
    bl_label = 'List Modifier'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode_items = [(name, name, "", idx) for idx, (_, name, _) in enumerate(node_item_list)

    func_ = EnumProperty(
        name="Modes",
        description="Mode Choices",
        default="AVR", items=mode_items,
        update=updateNode
    )

    listify = BoolProperty(
        default=True,
        description='Output lists or proper sets'
    )


    def draw_buttons(self, context, layout):
        layout.prop(self, "func_")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Data1")
        self.inputs.new('StringsSocket', "Data2")        
        self.outputs.new('StringsSocket', "Result")

    def process(self):

        inputs = self.inputs
        outputs = self.outputs
        func = func_dict[self.func_]

        # if func_ in SET_OPS and self.listify:
        #    maybe define a function to return list only.

        # no logic applied yet
        # data = self.inputs[0].sv_get()
        # def f(d):
        #     if isinstance(d[0], (int, float)):
        #          return operation(d)
        #     else:
        #          return [f(x) for x in d]
        # out = f(data)
        # self.outputs[0].sv_set(data)

        if outputs[0].is_linked:

            if num_inputs[self.func_] == 1:
                data1 = inputs['Data1'].sv_get()
                out = [func(data1)]
            else:
                data1 = inputs['Data1'].sv_get()
                data2 = inputs['Data2'].sv_get()
                out = [func(data1, data2)]

            outputs[0].sv_set([out])


def register():
    bpy.utils.register_class(ListModifierNode)


def unregister():
    bpy.utils.unregister_class(ListModifierNode)
