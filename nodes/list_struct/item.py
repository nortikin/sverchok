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
from sverchok.data_structure import (changable_sockets, repeat_last, updateNode)
import numpy as np

# SvListItemNode
# Allows a list of indexes, with both negative and positive index and repeated values
# Other output is not wrapped.
# For now only accepts one list of indexes
# Based on ListItem2 by Linus Yng


class SvListItemNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: List Item Out
    Tooltip: Get elements from list at desired indexes
    '''
    bl_idname = 'SvListItemNode'
    bl_label = 'List Item'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_ITEM'

    level: IntProperty(name='level_to_count', default=2, min=1, update=updateNode)
    index: IntProperty(name='Index', default=0, update=updateNode)
    typ: StringProperty(name='typ', default='')
    newsock: BoolProperty(name='newsock', default=False)

    def draw_buttons(self, context, layout):
        '''draw buttons on the node'''
        layout.prop(self, "level", text="level")

    def sv_init(self, context):
        '''create sockets'''
        self.inputs.new('SvStringsSocket', "Data")
        self.inputs.new('SvStringsSocket', "Index").prop_name = 'index'
        self.outputs.new('SvStringsSocket', "Item")
        self.outputs.new('SvStringsSocket', "Other")

    def migrate_from(self, old_node):
        self.index = old_node.item

    def update(self):
        '''adapt socket type to input type'''
        if 'Data' in self.inputs and self.inputs['Data'].links:
            inputsocketname = 'Data'
            outputsocketname = ['Item', 'Other']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        '''main node function called every update'''
        if self.inputs['Data'].is_linked:
            out_item, out_other = self.outputs
            data = self.inputs['Data'].sv_get()
            indexes = self.inputs['Index'].sv_get([[self.index]])

            if out_item.is_linked:
                if self.level-1:
                    out = self.get(data, self.level-1, indexes, self.get_items)
                else:
                    out = self.get_items(data, indexes[0])
                out_item.sv_set(out)

            if out_other.is_linked:
                if self.level-1:
                    out = self.get(data, self.level-1, indexes, self.get_other)
                else:
                    out = self.get_other(data, indexes[0])
                out_other.sv_set(out)

    def get_items(self, data, indexes):
        '''extract the indexes from the list'''
        if type(data) in [list, tuple]:
            return [data[index] for index in indexes if -len(data) <= index < len(data)]
        elif type(data) == np.ndarray:
            return data[indexes]
        else:
            return None

    def get_other(self, data, indexes):
        '''remove the indexes from the list'''
        if type(data) == np.ndarray:
            mask = np.ones(len(data), bool)
            mask[indexes] = False
            return data[mask]
        is_tuple = False
        if type(data) == tuple:
            data = list(data)
            is_tuple = True
        if type(data) == list:
            m_indexes = indexes.copy()
            for idx, index in enumerate(indexes):
                if index < 0:
                    m_indexes[idx] = len(data)-abs(index)
            for i in sorted(set(m_indexes), reverse=True):
                if -1 < i < len(data):
                    del data[i]
            if is_tuple:
                return tuple(data)
            else:
                return data
        else:
            return None

    def get(self, data, level, indexes, func):
        '''iterative fucntion to get down to the requested level'''
        if level == 1:
            index_iter = repeat_last(indexes)
            return [self.get(obj, level-1, next(index_iter), func) for obj in data]
        elif level:
            return [self.get(obj, level-1, indexes, func) for obj in data]
        else:
            return func(data, indexes)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvListItemNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvListItemNode)
