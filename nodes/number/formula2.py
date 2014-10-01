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
from bpy.props import BoolProperty, StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import (sv_Vars, updateNode, multi_socket, changable_sockets,
                            dataSpoil, dataCorrect, levelsOflist,
                            SvSetSocketAnyType, SvGetSocketAnyType)
from math import acos, acosh, asin, asinh, atan, atan2, \
                            atanh,ceil,copysign,cos,cosh,degrees,e, \
                            erf,erfc,exp,expm1,fabs,factorial,floor, \
                            fmod,frexp,fsum,gamma,hypot,isfinite,isinf, \
                            isnan,ldexp,lgamma,log,log10,log1p,log2,modf, \
                            pi,pow,radians,sin,sinh,sqrt,tan,tanh,trunc


class Formula2Node(bpy.types.Node, SverchCustomTreeNode):
    ''' Formula2 '''
    bl_idname = 'Formula2Node'
    bl_label = 'Formula2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    formula = StringProperty(name='formula',
                             default='x+n[0]',
                             update=updateNode)
    typ = StringProperty(name='typ',
                         default='')
    newsock = BoolProperty(name='newsock',
                           default=False)

    base_name = 'n'
    multi_socket_type = 'StringsSocket'

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="")

    def init(self, context):
        self.inputs.new('StringsSocket', "X", "X")
        self.inputs.new('StringsSocket', "n[0]", "n[0]")
        self.outputs.new('StringsSocket', "Result", "Result")

    def update(self):
        # inputs
        multi_socket(self, min=2, start=-1, breck=True)

        if 'X' in self.inputs and len(self.inputs['X'].links) > 0:
            # адаптивный сокет
            inputsocketname = 'X'
            outputsocketname = ['Result']
            changable_sockets(self, inputsocketname, outputsocketname)
            vecs = SvGetSocketAnyType(self, self.inputs['X'])
        else:
            vecs = [[0.0]]

        # outputs
        if 'Result' in self.outputs and len(self.outputs['Result'].links) > 0:
            list_mult = []
            if 'n[0]' in self.inputs and len(self.inputs['n[0]'].links) > 0:
                i = 0
                for socket in self.inputs:
                    if socket.links and i != 0:
                        list_mult.append(SvGetSocketAnyType(self, socket))
                    else:
                        i = 1
                #print(list_mult)
            code_formula = parser.expr(self.formula).compile()
            # finding nasty levels, make equal nastyness (canonical 0,1,2,3)
            levels = [levelsOflist(vecs)]
            for n in list_mult:
                levels.append(levelsOflist(n))
            maxlevel = max(max(levels), 3)
            diflevel = maxlevel - levels[0]

            if diflevel:
                vecs_ = dataSpoil([vecs], diflevel-1)
                vecs = dataCorrect(vecs_, nominal_dept=2)
            for i, lev in enumerate(levels):
                if i == 0:
                    continue
                diflevel = maxlevel-lev
                if diflevel:
                    list_temp = dataSpoil([list_mult[i-1]], diflevel-1)
                    list_mult[i-1] = dataCorrect(list_temp, nominal_dept=2)
            #print(list_mult)
            r = self.inte(vecs, code_formula, list_mult, 3)
            result = dataCorrect(r, nominal_dept=min((levels[0]-1), 2))

            SvSetSocketAnyType(self, 'Result', result)

    def inte(self, list_x, formula, list_n, levels, index=0):
        ''' calc lists in formula '''
        out = []
        new_list_n = self.normalize(list_n, list_x)
        for j, x_obj in enumerate(list_x):
            out1 = []
            for k, x_lis in enumerate(x_obj):
                out2 = []
                for q, x in enumerate(x_lis):
                    out2.append(self.calc_item(x, formula, new_list_n, j, k, q))
                out1.append(out2)
            out.append(out1)
        return out

    def calc_item(self, x, formula, nlist, j, k, q):
        X = x
        n = []
        a = []
        list_vars = [w for w in sv_Vars.keys()]
        for v in list_vars:
            if v[:6] == 'sv_typ':
                continue
            abra = sv_Vars[v]
            exec(str(v)+'=[]')
            for i, aa_abra in enumerate(abra):
                eva = str(v)+'.append('+str(aa_abra)+')'
                eval(eva)

        for nitem in nlist:
            n.append(nitem[j][k][q])
        N = n
        return eval(formula)

    def normalize(self, listN, listX):
        Lennox = len(listX)
        new_list_n = []
        for ne in listN:
            Lenin = len(ne)
            equal = Lennox - Lenin
            if equal > 0:
                self.enlarge(ne, equal)
            for i, obj in enumerate(listX):
                Lennox = len(obj)
                Lenin = len(ne[i])
                equal = Lennox - Lenin
                if equal > 0:
                    self.enlarge(ne[i], equal)
                for j, list in enumerate(obj):
                    Lennox = len(list)
                    Lenin = len(ne[i][j])
                    equal = Lennox - Lenin
                    if equal > 0:
                        self.enlarge(ne[i][j], equal)

            new_list_n.append(ne)
        return new_list_n

    def enlarge(self, lst, equal):
        ''' enlarge minor n[i] list to size of x list '''

        lst.extend([lst[-1] for i in range(equal)])
        #return lst


def register():
    bpy.utils.register_class(Formula2Node)


def unregister():
    bpy.utils.unregister_class(Formula2Node)

if __name__ == '__main__':
    register()
