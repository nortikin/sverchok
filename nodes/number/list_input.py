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
from bpy.props import (
    EnumProperty, FloatVectorProperty,
    IntProperty, IntVectorProperty, BoolProperty)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.listutils import (
    listinput_getI_needed, 
    listinput_getF_needed, 
    listinput_drawI,
    listinput_drawF
    )
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties


class SvListInputNode(Show3DProperties, bpy.types.Node, SverchCustomTreeNode):
    ''' Creta a float or int List '''
    bl_idname = 'SvListInputNode'
    bl_label = 'List Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_INPUT'

    defaults = [0 for i in range(32)]

    int_: IntProperty(
        name='int_', description='integer number', default=1, min=1, max=128, update=updateNode)

    v_int: IntProperty(
        name='int_', description='integer number', default=1, min=1, max=10, update=updateNode)

    int_list: IntVectorProperty(
        name='int_list', description="Integer list", default=defaults, size=32,update=updateNode)
    int_list1: IntVectorProperty(
        name='int_list1', description="Integer list", default=defaults, size=32,update=updateNode)
    int_list2: IntVectorProperty(
        name='int_list2', description="Integer list", default=defaults, size=32,update=updateNode)
    int_list3: IntVectorProperty(
        name='int_list3', description="Integer list", default=defaults, size=32,update=updateNode)

    float_list: FloatVectorProperty(
        name='float_list', description="Float list", default=defaults, size=32, update=updateNode)
    float_list1: FloatVectorProperty(
        name='float_list1', description="Float list", default=defaults, size=32, update=updateNode)
    float_list2: FloatVectorProperty(
        name='float_list2', description="Float list", default=defaults, size=32, update=updateNode)
    float_list3: FloatVectorProperty(
        name='float_list3', description="Float list", default=defaults, size=32, update=updateNode)

    vector_list: FloatVectorProperty(
        name='vector_list', description="Vector list", default=defaults, size=32, update=updateNode)

    def changeMode(self, context):
        if self.mode == 'vector':
            if 'Vector List' not in self.outputs:
                self.outputs.remove(self.outputs[0])
                self.outputs.new('SvVerticesSocket', 'Vector List')
                return
        else:
            if 'List' not in self.outputs:
                self.outputs.remove(self.outputs[0])
                self.outputs.new('SvStringsSocket', 'List')
                return

    modes = [
        ("int_list", "Int", "Integer", "", 1),
        ("float_list", "Float", "Float", "", 2),
        ("vector", "Vector", "Vector", "", 3)]

    mode: EnumProperty(items=modes, default='int_list', update=changeMode)

    def sv_init(self, context):
        self.outputs.new('SvStringsSocket', "List")

    def draw_buttons(self, context, layout):
        if self.mode == 'vector':
            layout.prop(self, "v_int", text="List Length")
        else:
            layout.prop(self, "int_", text="List Length")

        layout.prop(self, "mode", expand=True)

        if self.mode == 'vector':
            col = layout.column(align=False)
            for i in range(self.v_int):
                row = col.row(align=True)
                for j in range(3):
                    row.prop(self, 'vector_list', index=i*3+j, text='XYZ'[j])
        elif self.mode == 'int_list':
            col = layout.column(align=True)
            listinput_drawI(self,col)
        else:
            col = layout.column(align=True)
            listinput_drawF(self,col)

    def draw_buttons_3dpanel(self, layout, in_menu=None):
        if not in_menu:
            menu = layout.row(align=True).operator('node.popup_3d_menu', text=f'Show: "{self.label or self.name}"')
            menu.tree_name = self.id_data.name
            menu.node_name = self.name
        else:
            layout.label(text=self.label or self.name)
            if self.mode == 'vector':
                colum_list = layout.column(align=True)
                for i in range(self.v_int):
                    row = colum_list.row(align=True)
                    for j in range(3):
                        row.prop(self, 'vector_list', index=i*3+j, text='XYZ'[j]+(self.label if self.label else self.name))
            else:
                colum_list = layout.column(align=True)
                for i in range(self.int_):
                    row = colum_list.row(align=True)
                    row.prop(self, self.mode, index=i, text=str(i)+(self.label if self.label else self.name))
                    row.scale_x = 0.8

    def process(self):
        if self.outputs[0].is_linked:
            if self.mode == 'int_list':
                data = listinput_getI_needed(self)
                
            elif self.mode == 'float_list':
                data = listinput_getF_needed(self)
            elif self.mode == 'vector':
                c = self.v_int*3
                v_l = list(self.vector_list)
                data = [list(zip(v_l[0:c:3], v_l[1:c:3], v_l[2:c:3]))]
            self.outputs[0].sv_set(data)


def register():
    bpy.utils.register_class(SvListInputNode)


def unregister():
    bpy.utils.unregister_class(SvListInputNode)
