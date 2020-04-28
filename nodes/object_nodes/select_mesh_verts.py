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
import numpy as np
from bpy.props import StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)


class SvSelectMeshVerts(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' Select vertices of mesh objects '''
    bl_idname = 'SvSelectMeshVerts'
    bl_label = 'Select Object Vertices'
    bl_icon = 'EDITMODE_HLT'

    formula: StringProperty(name='formula', default='val == 0', update=updateNode)
    deselect_all: BoolProperty(name='deselect', default=False, update=updateNode)

    modes = [
        ("vertices", "Vert", "", 1),
        ("polygons", "Face", "", 2),
        ("edges", "Edge", "", 3)]

    mode: EnumProperty(items=modes, default='vertices', update=updateNode)

    def draw_buttons(self, context, layout):
        self.animatable_buttons(layout, icon_only=True)
        layout.prop(self, "deselect_all", text="clear selection")
        layout.prop(self, "mode", expand=True)
        if self.inputs[4].is_linked:
            layout.prop(self, "formula", text="")

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('SvStringsSocket', 'element_index')
        self.inputs.new('SvStringsSocket', 'element_mask')
        self.inputs.new('SvStringsSocket', 'edges_polys')
        self.inputs.new('SvStringsSocket', 'floattoboolexpr')
        self.outputs.new('SvStringsSocket', 'selected_indx')
        self.outputs.new('SvStringsSocket', 'selected_mask')
        self.outputs.new('SvObjectSocket', 'Objects')

    def process(self):
        O, Vind, Vmask, edpo, FtoB = self.inputs
        Osvi, Osvmas, OObj = self.outputs
        Prop = self.formula
        objsl = O.sv_get()
        elements = [getattr(ob.data, self.mode) for ob in objsl]
        if self.deselect_all:
            for ob in objsl:    # unfortunately we cant just deselect verts
                for p in ob.data.polygons:
                    p.select = False
                for e in ob.data.edges:
                    e.select = False
                for v in ob.data.vertices:
                    v.select = False
        if Vind.is_linked:
            for omv, ind in zip(elements, Vind.sv_get()):
                for i in ind:
                    omv[i].select = True
        if Vmask.is_linked:
            for obel, ma in zip(elements, Vmask.sv_get()):
                obel.foreach_set('select', safc(obel[:], ma))
        if edpo.is_linked:
            for obj, ind in zip(objsl, edpo.sv_get()):
                omv = obj.data.vertices
                for i in np.unique(ind):
                    omv[i].select = True
        if FtoB.is_linked:
            str = "for val, elem in zip(floats, omv):\n    elem.select="+self.formula
            for omv, floats in zip(elements, FtoB.sv_get()):
                exec(str)
        if Osvi.is_linked:
            Osvi.sv_set([[v.index for v in elem if v.select] for elem in elements])
        if Osvmas.is_linked:
            Osvmas.sv_set([[v.select for v in elem] for elem in elements])
        if OObj.is_linked:
            OObj.sv_set(objsl)


def register():
    bpy.utils.register_class(SvSelectMeshVerts)


def unregister():
    bpy.utils.unregister_class(SvSelectMeshVerts)
