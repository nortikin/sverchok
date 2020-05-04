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


class SvFormulaDeformMK2Node(bpy.types.Node, SverchCustomTreeNode):
    ''' Deform Verts by Math MK2 '''
    bl_idname = 'SvFormulaDeformMK2Node'
    bl_label = 'Deform by Formula'
    bl_icon = 'MOD_SIMPLEDEFORM'
    sv_icon = 'SV_DEFORM_BY_FORMULA'

    ModeX: StringProperty(name='formulaX', default='x', update=updateNode)
    ModeY: StringProperty(name='formulaY', default='y', update=updateNode)
    ModeZ: StringProperty(name='formulaZ', default='z', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts(xyz)')
        self.inputs.new('SvVerticesSocket', 'Verts(XYZ)')
        self.outputs.new('SvVerticesSocket', 'Verts')

    def draw_buttons(self, context, layout):
        for element in 'XYZ':
            row = layout.row()
            split = row.split(align=True)
            split.split().prop(self, "Mode"+element, text='')

    def process(self):
        Io, Io2 = self.inputs
        Oo = self.outputs[0]
        if Oo.is_linked:
            V = Io.sv_get()
            if Io2.is_linked:
                str = "for Enum,Val2L in zip(enumerate(V), V2): \n    I,L = Enum \n    Pfin = [] \n    for Enum2, vert2 in zip(enumerate(L), safc(L, Val2L)): \n        i, (x, y, z) = Enum2 \n        (X, Y, Z) = vert2 \n        Pfin.append(({n.ModeX},{n.ModeY},{n.ModeZ})) \n    fin.append(Pfin)"
                fin = []
                V2 = Io2.sv_get()
                exec(str.format(n=self))
                Oo.sv_set(fin)
            else:
                exec_string = "Oo.sv_set([[({n.ModeX},{n.ModeY},{n.ModeZ}) for i, (x, y, z) in enumerate(L)] for I, L in enumerate(V)])"
                exec(exec_string.format(n=self))


def register():
    bpy.utils.register_class(SvFormulaDeformMK2Node)


def unregister():
    bpy.utils.unregister_class(SvFormulaDeformMK2Node)
