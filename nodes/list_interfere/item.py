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
from sverchok.data_structure import (changable_sockets, repeat_last, updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)




# ListItem2
# Allows a list of items, with both negative and positive index and repeated values
# Other output is not wrapped.
# Based on ListItem
# For now only accepts one list of items
# by Linus Yng


class ListItem2Node(bpy.types.Node, SverchCustomTreeNode):
    ''' List item '''
    bl_idname = 'ListItem2Node'
    bl_label = 'List item'
    bl_icon = 'OUTLINER_OB_EMPTY'

    level = IntProperty(name='level_to_count',
                        default=2, min=0,
                        update=updateNode)
    item = IntProperty(name='item',
                       default=0,
                       update=updateNode)
    typ = StringProperty(name='typ',
                         default='')
    newsock = BoolProperty(name='newsock',
                           default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.inputs.new('StringsSocket', "Item", "Item").prop_name = 'item'
        self.outputs.new('StringsSocket', "Item", "Item")
        self.outputs.new('StringsSocket', "Other", "Other")

    def update(self):
        if 'Data' in self.inputs and len(self.inputs['Data'].links) > 0:
            inputsocketname = 'Data'
            outputsocketname = ['Item', 'Other']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        if 'Item' in self.outputs and self.outputs['Item'].is_linked or \
                'Other' in self.outputs and self.outputs['Other'].is_linked:

            if 'Data' in self.inputs and self.inputs['Data'].is_linked:
                data = SvGetSocketAnyType(self, self.inputs['Data'])

                if 'Item' in self.inputs and self.inputs['Item'].is_linked:
                    items = SvGetSocketAnyType(self, self.inputs['Item'])
                else:
                    items = [[self.item]]

                if 'Item' in self.outputs and self.outputs['Item'].is_linked:
                    if self.level-1:
                        out = self.get(data, self.level-1, items, self.get_items)
                    else:
                        out = self.get_items(data, items[0])
                    SvSetSocketAnyType(self, 'Item', out)
                if 'Other' in self.outputs and self.outputs['Other'].is_linked:
                    if self.level-1:
                        out = self.get(data, self.level-1, items, self.get_other)
                    else:
                        out = self.get_other(data, items[0])
                    SvSetSocketAnyType(self, 'Other', out)

    def get_items(self, data, items):
        if type(data) in [list, tuple]:
            return [data[item] for item in items if item < len(data) and item >= -len(data)]
        else:
            return None

    def get_other(self, data, items):
        is_tuple = False
        if type(data) == tuple:
            data = list(data)
            is_tuple = True
        if type(data) == list:
            m_items = items.copy()
            for idx, item in enumerate(items):
                if item < 0:
                    m_items[idx] = len(data)-abs(item)
            for i in sorted(set(m_items), reverse=True):
                if i < len(data) and i > -1:
                    del data[i]
            if is_tuple:
                return tuple(data)
            else:
                return data
        else:
            return None

    def get(self, data, level, items, f):
        if level == 1:
            item_iter = repeat_last(items)
            return [self.get(obj, level-1, next(item_iter), f) for obj in data]
        elif level:
            return [self.get(obj, level-1, items, f) for obj in data]
        else:
            return f(data, items)

def register():
    bpy.utils.register_class(ListItem2Node)


def unregister():
    bpy.utils.unregister_class(ListItem2Node)
