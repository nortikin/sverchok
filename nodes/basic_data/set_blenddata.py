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
from bpy.props import StringProperty, EnumProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_cycle)


class SvSetDataObjectNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Set Object Props '''
    bl_idname = 'SvSetDataObjectNode'
    bl_label = 'set_dataobject'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def Obm(m):
        m = [(i,i,"") for i in m]
        return m

    M = ['delta_location','delta_rotation_euler','delta_scale','select','parent','name','custom']
    formula = StringProperty(name='formula', default='layers', update=updateNode)
    Modes = EnumProperty(name="property modes", default="select", items=Obm(M), update=updateNode)

    def draw_buttons(self, context, layout):
        if self.Modes == 'custom':
            layout.prop(self,  "formula", text="")
        row = layout.row(align=True)
        layout.prop(self, "Modes", "property")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Objects')
        self.inputs.new('StringsSocket', 'values')
        self.outputs.new('StringsSocket', 'outvalues')

    def process(self):
        objs = self.inputs['Objects'].sv_get()
        va = self.inputs['values']
        Prop = self.Modes if self.Modes != 'custom' else self.formula
        if va.is_linked:
            v = va.sv_get()
            lob = len(objs)
            if isinstance(v[0], list):
                v = v[0]
            if lob > len(v):
                objs, v = match_long_cycle([objs, v])
            g = 0
            while g != lob:
                if objs[g] != None:
                    exec("objs[g]."+Prop+"= v[g]")
                g = g+1
        if self.outputs['outvalues'].is_linked:
            self.outputs['outvalues'].sv_set(eval("[i."+Prop+" for i in objs if i != None]"))


def register():
    bpy.utils.register_class(SvSetDataObjectNode)


def unregister():
    bpy.utils.unregister_class(SvSetDataObjectNode)
