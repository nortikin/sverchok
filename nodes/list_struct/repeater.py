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
from bpy.props import BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, changable_sockets, fixed_iter)


class ListRepeaterNode(bpy.types.Node, SverchCustomTreeNode):
    ''' List repeater
    [[0,1,2,3,]] L=1,*3 => [[ [0,1,2,3], [0,1,2,3], [0,1,2,3] ]]
    '''
    bl_idname = 'ListRepeaterNode'
    bl_label = 'List Repeater'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_REPEATER'

    level: IntProperty(name='level', default=1, min=0, update=updateNode)
    number: IntProperty(name='number', default=1, min=1, update=updateNode)
    unwrap: BoolProperty(name='unwrap', default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self, "unwrap", text="unwrap")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.inputs.new('SvStringsSocket', "Number").prop_name = 'number'
        self.outputs.new('SvStringsSocket', "Data")

    def sv_update(self):
        if self.inputs['Data'].is_linked:
            inputsocketname = 'Data'
            outputsocketname = ['Data', ]
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        data = self.inputs['Data'].sv_get(deepcopy=False, default=[])
        number = self.inputs['Number'].sv_get(deepcopy=False)[0]

        if self.level == 1:  # only for 1 otherwise it changes behaviour dramatically
            obj_num = max(len(data), len(number))
            data = fixed_iter(data, obj_num) if data else []

        out_ = self.count(data, self.level, number)
        if self.unwrap:
            out = []
            if len(out_) > 0:
                for o in out_:
                    out.extend(o)
        else:
            out = out_

        self.outputs['Data'].sv_set(out)

    def count(self, data, level, number, cou=0):
        if level:
            out = []
            for idx, obj in enumerate(data):
                out.append(self.count(obj, level - 1, number, idx))

        else:
            out = []
            indx = min(cou, len(number) - 1)
            for i in range(int(number[indx])):
                out.append(data)
        return out


def register():
    bpy.utils.register_class(ListRepeaterNode)


def unregister():
    bpy.utils.unregister_class(ListRepeaterNode)
