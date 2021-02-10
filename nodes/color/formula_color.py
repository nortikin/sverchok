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
from math import *
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)


class SvFormulaColorNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Change Colors by Math '''
    bl_idname = 'SvFormulaColorNode'
    bl_label = 'Color by formula'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_COLOR_BY_FORMULA'

    ModeR: StringProperty(name='formulaR', default='r', update=updateNode)
    ModeG: StringProperty(name='formulaG', default='g', update=updateNode)
    ModeB: StringProperty(name='formulaB', default='b', update=updateNode)
    ModeA: StringProperty(name='formulaA', default='a', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvColorSocket', 'Colors(rgba)')
        self.inputs.new('SvColorSocket', 'Colors(RGBA)')
        self.outputs.new('SvColorSocket', 'Colors')

    def draw_buttons(self, context, layout):
        for element in 'RGBA':
            row = layout.row()
            split = row.split(align=True)
            split.split().prop(self, "Mode"+element, text='')

    def process(self):
        Io, Io2 = self.inputs
        Oo = self.outputs[0]
        if Oo.is_linked:
            V = Io.sv_get()
            if Io2.is_linked:
                str = "for Enum,Val2L in zip(enumerate(V), V2): \n    I,L = Enum \n    Pfin = [] \n    for Enum2, col2 in zip(enumerate(L), safc(L, Val2L)): \n        i, (r, g, b, a) = Enum2 \n        (R, G, B, A) = col2 \n        Pfin.append(({n.ModeR},{n.ModeG},{n.ModeB},{n.ModeA})) \n    fin.append(Pfin)"
                fin = []
                V2 = Io2.sv_get()
                exec(str.format(n=self))
                Oo.sv_set(fin)
            else:
                exec_string = "Oo.sv_set([[({n.ModeR},{n.ModeG},{n.ModeB},{n.ModeA}) for i, (r, g, b, a) in enumerate(L)] for I, L in enumerate(V)])"
                exec(exec_string.format(n=self))


def register():
    bpy.utils.register_class(SvFormulaColorNode)


def unregister():
    bpy.utils.unregister_class(SvFormulaColorNode)
