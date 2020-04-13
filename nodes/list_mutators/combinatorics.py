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
from bpy.props import IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttle_node
from sverchok.data_structure import (match_long_repeat, updateNode)

from itertools import (product, permutations, combinations)

operations = {
    "PRODUCT":      (10, lambda s, r: product(*s, repeat=r)),
    "PERMUTATIONS": (20, lambda s, l: permutations(s, l)),
    "COMBINATIONS": (30, lambda s, l: combinations(s, l))
}

operationItems = [(k, k.title(), "", s[0]) for k, s in sorted(operations.items(), key=lambda k: k[1][0])]

ABC = tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')  # input socket labels

multiple_input_operations = {"PRODUCT"}


class SvCombinatoricsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Product, Permutations, Combinations
    Tooltip: Generate various combinatoric operations
    """
    bl_idname = 'SvCombinatoricsNode'
    bl_label = 'Combinatorics'
    sv_icon = 'SV_COMBINATRONICS'

    def update_operation(self, context):
        self.label = self.operation.title()
        self.update_sockets()
        updateNode(self, context)

    operation : EnumProperty(
        name="Operation", items=operationItems,
        description="Operation type", default="PRODUCT",
        update=update_operation)

    repeat : IntProperty(
        name='Repeat', description='Repeat the list inputs this many times',
        default=1, min=1, update=updateNode)

    length : IntProperty(
        name='Length', description='Limit the elements to operate on to this value',
        default=1, min=0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Repeat").prop_name = "repeat"
        self.inputs.new('SvStringsSocket', "Length").prop_name = "length"
        self.inputs.new('SvStringsSocket', "A")
        self.inputs.new('SvStringsSocket', "B")

        self.outputs.new('SvStringsSocket', "Result")

        self.update_operation(context)
    
    def hold_check(self):
        if not 'Result' in self.outputs:
            return True

        # not a multiple input operation ? => no need to update sockets
        if self.operation not in multiple_input_operations:
            return True

    @throttle_node
    def update(self):
        ''' Add/remove sockets as A-Z sockets are connected/disconnected '''

        # get all existing A-Z sockets (connected or not)
        inputs = self.inputs
        inputs_AZ = list(filter(lambda s: s.name in ABC, inputs))

        # last A-Z socket connected ? => add an empty A-Z socket at the end
        if inputs_AZ[-1].links:
            name = ABC[len(inputs_AZ)]  # pick the next letter A to Z
            inputs.new("SvStringsSocket", name)

        else:  # last input disconnected ? => remove all but last unconnected
            while len(inputs_AZ) > 2 and not inputs_AZ[-2].links:
                s = inputs_AZ[-1]
                inputs.remove(s)
                inputs_AZ.remove(s)
    
    def update_sockets(self):
        ''' Update sockets based on selected operation '''

        inputs = self.inputs

        # update the A-Z input sockets
        if self.operation in multiple_input_operations:
            if not "B" in inputs:
                inputs.new("SvStringsSocket", "B")
        else:
            for a in ABC[1:]:  # remove all B-Z inputs (keep A)
                if a in inputs:
                    inputs.remove(inputs[a])

        # update the other sockets
        if self.operation in {"PRODUCT"}:
            if inputs["Repeat"].hide:
                inputs["Repeat"].hide_safe = False
            inputs["Length"].hide_safe = True
        elif self.operation in {"COMBINATIONS", "PERMUTATIONS"}:
            inputs["Repeat"].hide_safe = True
            if inputs["Length"].hide:
                inputs["Length"].hide_safe = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs

        all_AZ_sockets = list(filter(lambda s: s.name in ABC, inputs))
        connected_AZ_sockets = list(filter(lambda s: s.is_linked, all_AZ_sockets))

        # collect the data inputs from all connected AZ sockets
        I = [s.sv_get()[0] for s in connected_AZ_sockets]

        if self.operation == "PRODUCT":
            R = inputs["Repeat"].sv_get()[0]
            R = list(map(lambda x: max(1, int(x)), R))
            parameters = match_long_repeat([[I], R])
        else:  # PERMUTATIONS / COMBINATIONS
            L = inputs["Length"].sv_get()[0]
            L = list(map(lambda x: max(0, int(x)), L))
            parameters = match_long_repeat([I, L])

        function = operations[self.operation][1]

        resultList = []
        for sequence, v in zip(*parameters):
            if self.operation in {"PERMUTATIONS", "COMBINATIONS"}:
                if v == 0 or v > len(sequence):
                    v = len(sequence)
            result = [list(a) for a in function(sequence, v)]
            resultList.append(result)

        outputs["Result"].sv_set(resultList)


def register():
    bpy.utils.register_class(SvCombinatoricsNode)


def unregister():
    bpy.utils.unregister_class(SvCombinatoricsNode)
