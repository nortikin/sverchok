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
    Tooltip: Get elements from list at desired indexes\n\tL=[[5,6,7,8]], i=[0,0,2,1],\n\t\tlvl:2 => item: [[5,5,7,6]], other: [[8]]\n\t\tlvl:1 => item: [[5,6,7,8], [5,6,7,8]], other: []
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

    def sv_update(self):
        """adapt socket type to input type"""
        if self.inputs['Data'].is_linked:
            inputsocketname = 'Data'
            outputsocketname = ['Item', 'Other']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        data = self.inputs['Data'].sv_get(default=[], deepcopy=False)
        indexes = self.inputs['Index'].sv_get(deepcopy=False)

        if self.level-1:
            out = self.get_(data, self.level-1, indexes, self.get_items)
        else:
            out = self.get_items(data, indexes[0])
        self.outputs[0].sv_set(out)

        if self.level-1:
            out = self.get_(data, self.level-1, indexes, self.get_other)
        else:
            out = self.get_other(data, indexes[0])
        self.outputs[1].sv_set(out)

    def get_items(self, data, indexes):
        '''extract the indexes from the list'''
        if type(data) in [list, tuple]:
            return [data[index] for index in indexes if -len(data) <= index < len(data)]
        if type(data) == str:
            return ''.join([data[index] for index in indexes if -len(data) <= index < len(data)])
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
            out_data = data.copy()
            m_indexes = indexes.copy()
            for idx, index in enumerate(indexes):
                if index < 0:
                    m_indexes[idx] = len(out_data)-abs(index)
            for i in sorted(set(m_indexes), reverse=True):
                if -1 < i < len(out_data):
                    del out_data[i]
            if is_tuple:
                return tuple(out_data)
            else:
                return out_data
        if type(data) == str:
            return ''.join([d for idx, d in enumerate(data) if idx not in indexes])
        else:
            return None

    def get_(self, data, level, indexes, func):  # get is build-in method of Node class
        """iterative function to get down to the requested level"""
        if level == 1:
            obj_num = max(len(data), len(indexes))
            index_iter = repeat_last(indexes)
            data_iter = repeat_last(data)
            return [self.get_(next(data_iter), level-1, next(index_iter), func)
                    for _ in range(obj_num)]
        elif level:
            return [self.get_(obj, level-1, indexes, func) for obj in data]
        else:
            return func(data, indexes)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvListItemNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvListItemNode)
