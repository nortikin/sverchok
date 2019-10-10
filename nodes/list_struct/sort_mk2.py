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
from bpy.props import BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, changable_sockets,
                                     dataCorrect, levelsOflist)

class ListSortNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' List Sort MK2 '''
    bl_idname = 'ListSortNodeMK2'
    bl_label = 'List Sort'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_SORT'

    level: IntProperty(name='level_to_count', default=2, min=0, update=updateNode)
    typ: StringProperty(name='typ', default='')
    newsock: BoolProperty(name='newsock', default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "data")
        self.inputs.new('SvStringsSocket', "keys")
        self.outputs.new('SvStringsSocket', "data")

    def update(self):
        if 'data' in self.outputs and self.inputs['data'].links:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        if not self.outputs['data'].is_linked:
            return

        data_ = self.inputs['data'].sv_get()
        levelinit = levelsOflist(data_)
        data = dataCorrect(data_, nominal_dept=self.level).copy()
        out_ = []
        if not self.inputs['keys'].is_linked:
            for obj in data:
                out_.append(sorted(obj))
        else:
            keys_ = self.inputs['keys'].sv_get()
            keys = dataCorrect(keys_, nominal_dept=1)
            for d,k in zip(data,keys):
                d.sort(key = lambda x: k.pop(0))
                out_.append(d)
        out = dataCorrect(out_,nominal_dept=levelinit-1)
        self.outputs['data'].sv_set(out)



def register():
    bpy.utils.register_class(ListSortNodeMK2)


def unregister():
    bpy.utils.unregister_class(ListSortNodeMK2)
