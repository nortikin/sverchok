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
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)


class SvSelectMeshVerts(bpy.types.Node, SverchCustomTreeNode):
    ''' Select vertices of mesh objects '''
    bl_idname = 'SvSelectMeshVerts'
    bl_label = 'Select Object Vertices'
    bl_icon = 'OUTLINER_OB_EMPTY'

    formula = StringProperty(name='formula', default='v == 0', update=updateNode)
    deselect_all = BoolProperty(name='deselect', default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "deselect_all", text="clear selection")
        if self.inputs[4].is_linked:
            layout.prop(self, "formula", text="")

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('StringsSocket', 'vert_index')
        self.inputs.new('StringsSocket', 'vert_mask')
        self.inputs.new('StringsSocket', 'edges_polys')
        self.inputs.new('StringsSocket', 'floattoboolexpr')
        self.outputs.new('StringsSocket', 'selected_indx')
        self.outputs.new('StringsSocket', 'selected_mask')
        self.outputs.new('SvObjectSocket', 'Objects')

    def process(self):
        O, Vind, Vmask, edpo, FtoB = self.inputs
        Osi, Osmas, OObj = self.outputs
        Prop = self.formula
        objsl = O.sv_get()
        if self.deselect_all:
            for ob in objsl:    # unfortunately we cant just deselect verts
                for p in ob.data.polygons:
                    p.select = False
                for e in ob.data.edges:
                    e.select = False
                for v in ob.data.vertices:
                    v.select = False
            #   ob.data.update()
        if Vind.is_linked:
            INDL = Vind.sv_get()
            for obj, ind in zip(objsl, INDL):
                omv = obj.data.vertices
                for i in ind:
                    omv[i].select = True
        if Vmask.is_linked:
            masL = Vmask.sv_get()
            for obj, ma in zip(objsl, masL):
                obj.data.vertices.foreach_set('select', safc(obj.data.vertices[:], ma))
        if edpo.is_linked:
            topol = edpo.sv_get()
            for obj, ind in zip(objsl, topol):
                omv = obj.data.vertices
                for i in np.unique(ind):
                    omv[i].select = True
        if FtoB.is_linked:
            str = "for v, vert in zip(floats, omv):\n    vert.select="+self.formula
            for obj, floats in zip(objsl, FtoB.sv_get()):
                omv = obj.data.vertices
                exec(str)
        if Osi.is_linked:
            Osi.sv_set([[v.index for v in ob.data.vertices if v.select] for ob in objsl])
        if Osmas.is_linked:
            Osmas.sv_set([[v.select for v in ob.data.vertices] for ob in objsl])
        if OObj.is_linked:
            OObj.sv_set(objsl)


def register():
    bpy.utils.register_class(SvSelectMeshVerts)


def unregister():
    bpy.utils.unregister_class(SvSelectMeshVerts)
