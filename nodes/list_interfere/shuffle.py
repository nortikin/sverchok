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

import random

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty

from sv_node_tree import SverchCustomTreeNode
from sv_data_structure import (updateNode, changable_sockets,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class ListShuffleNode(bpy.types.Node, SverchCustomTreeNode):
    ''' List Shuffle Node '''
    bl_idname = 'ListShuffleNode'
    bl_label = 'List Shuffle'
    bl_icon = 'OUTLINER_OB_EMPTY'

    level = IntProperty(name='level_to_Shuffle',
                        default=2, min=1,
                        update=updateNode)
    seed = IntProperty(name='Seed',
                       default=0,
                       update=updateNode)

    typ = StringProperty(name='typ', default='')
    newsock = BoolProperty(name='newsock', default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'level', text="level")
        if 'seed' not in self.inputs:
            layout.prop(self, 'seed', text="Seed")

    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "seed").prop_name = 'seed'

        self.outputs.new('StringsSocket', 'data', 'data')

    def update(self):
        if 'data' in self.inputs and self.inputs['data'].links:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)

        if 'data' in self.outputs and self.outputs['data'].links:

            if 'seed' not in self.inputs:
                seed = self.seed
            else:
                seed = self.inputs['seed'].sv_get()[0][0]

            random.seed(seed)
            data = SvGetSocketAnyType(self, self.inputs['data'])
            output = self.shuffle(data, self.level)
            SvSetSocketAnyType(self, 'data', output)

    def shuffle(self, lst, level):
        level -= 1
        if level:
            out = []
            for l in lst:
                out.append(self.shuffle(l, level))
            return out
        elif type(lst) in [type([])]:
            l = lst.copy()
            random.shuffle(l)
            return l
        elif type(lst) in [type(tuple())]:
            lst = list(lst)
            random.shuffle(lst)
            return tuple(lst)


def register():
    bpy.utils.register_class(ListShuffleNode)


def unregister():
    bpy.utils.unregister_class(ListShuffleNode)
