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

import parser

import bpy
from bpy.props import StringProperty

from node_tree import SverchCustomTreeNode, StringsSocket
from data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType
from math import cos, sin, pi, tan


class FormulaNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Formula '''
    bl_idname = 'FormulaNode'
    bl_label = 'Formula'
    bl_icon = 'OUTLINER_OB_EMPTY'

    formula = StringProperty(name='formula',
                             default='x*n[0]',
                             update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="formula")

    def init(self, context):
        self.inputs.new('StringsSocket', "X", "X")
        self.inputs.new('StringsSocket', "n[.]", "n[.]")
        self.outputs.new('StringsSocket', "Result", "Result")

    def check_slots(self, num):
        l = []
        if len(self.inputs) < num+1:
            return False
        for i, sl in enumerate(self.inputs[num:]):
            if len(sl.links) == 0:
                l.append(i+num)
        if l:
            return l
        else:
            return False

    def update(self):
        # inputs
        ch = self.check_slots(1)
        if ch:
            for c in ch[:-1]:
                self.inputs.remove(self.inputs[ch[0]])

        if 'X' in self.inputs and self.inputs['X'].links:
            vecs = SvGetSocketAnyType(self, self.inputs['X'])
        else:
            vecs = [[0.0]]

        list_mult = []
        for idx, multi in enumerate(self.inputs[1:]):
            if multi.links and \
               type(multi.links[0].from_socket) == StringsSocket:

                mult = SvGetSocketAnyType(self, multi)
                ch = self.check_slots(2)
                if not ch:
                    self.inputs.new('StringsSocket', 'n[.]', "n[.]")

                list_mult.extend(mult)
        if len(list_mult) == 0:
            list_mult = [[0.0]]

        # outputs
        if 'Result' in self.outputs and self.outputs['Result'].links:

            code_formula = parser.expr(self.formula).compile()
            r_ = []
            result = []
            max_l = 0
            for list_m in list_mult:
                l1 = len(list_m)
                max_l = max(max_l, l1)
            max_l = max(max_l, len(vecs[0]))

            for list_m in list_mult:
                d = max_l - len(list_m)
                if d > 0:
                    for d_ in range(d):
                        list_m.append(list_m[-1])

            lres = []
            for l in range(max_l):
                ltmp = []
                for list_m in list_mult:
                    ltmp.append(list_m[l])
                lres.append(ltmp)

            r = self.inte(vecs, code_formula, lres)

            result.extend(r)
            SvSetSocketAnyType(self, 'Result', result)

    def inte(self, l, formula, list_n, indx=0):
        if type(l) in [int, float]:
            x = X = l

            n = list_n[indx]
            N = n

            t = eval(formula)
        else:
            t = []
            for idx, i in enumerate(l):
                j = self.inte(i, formula, list_n, idx)
                t.append(j)
            if type(l) == tuple:
                t = tuple(t)
        return t


def register():
    bpy.utils.register_class(FormulaNode)


def unregister():
    bpy.utils.unregister_class(FormulaNode)

if __name__ == '__main__':
    register()