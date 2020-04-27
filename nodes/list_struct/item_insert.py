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
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (changable_sockets, repeat_last, updateNode, list_match_func, list_match_modes)
import numpy as np

# ListItem2
# Allows a list of items, with both negative and positive index and repeated values
# Other output is not wrapped.
# Based on ListItem
# For now only accepts one list of items
# by Linus Yng


class SvListItemInsertNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: List Item In
    Tooltip: Insert elements in list at desired indexes
    '''
    bl_idname = 'SvListItemInsertNode'
    bl_label = 'List Item Insert'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_ITEM_INSERT'

    level: IntProperty(name='level_to_count', default=2, min=0, update=updateNode)
    index: IntProperty(name='index', default=0, update=updateNode)
    replace: BoolProperty(name='Replace', default=False, update=updateNode)
    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths between Index and Item lists",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    typ: StringProperty(name='typ', default='')
    newsock: BoolProperty(name='newsock', default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self, "replace", text="Replace")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "level", text="level")
        layout.prop(self, "replace", text="Replace")
        layout.separator()
        layout.label(text="List Match:")

        layout.prop(self, "list_match_local", text="Item-Index", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop(self, "level", text="level")
        layout.prop(self, "replace", text="Replace")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Item-Index")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.inputs.new('SvStringsSocket', "Item")
        self.inputs.new('SvStringsSocket', "Index").prop_name = 'index'
        self.outputs.new('SvStringsSocket', "Data")


    def sv_update(self):
        if 'Data' in self.inputs and self.inputs['Data'].links:
            inputsocketname = 'Data'
            outputsocketname = ['Data']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        out_socket = self.outputs[0]
        si = self.inputs
        if si['Data'].is_linked and self.inputs['Item'].is_linked and out_socket.is_linked:

            data = si['Data'].sv_get()
            if si['Item'].is_linked:
                new_item = si['Item'].sv_get()
                indexes = si['Index'].sv_get([[self.index]])
                if self.level-1:
                    out = self.get(data, new_item, self.level-1, indexes, self.set_items)
                else:
                    out = self.set_items(data, new_item, indexes[0])
                out_socket.sv_set(out)
            else:
                out_socket.sv_set(data)

    def set_items(self, data, new_items, indexes):
        if type(data) in [list, tuple]:
            params = list_match_func[self.list_match_local]([indexes, new_items])
            for ind, i in zip(*params):
                if self.replace and len(data) > ind:
                    data.pop(ind)
                data.insert(ind, i)
            return data
        elif type(data) == np.ndarray:
            ind, items = list_match_func[self.list_match_local]([indexes, new_items])
            if self.replace:
                data[ind] = items

            else:
                for i, item in zip(ind, items):
                    data = np.concatenate([data[:i], [item], data[i:]])

            return data
        return None

    def get(self, data, new_items, level, items, f):
        if level == 1:
            item_iter = repeat_last(items)
            new_item_iter = repeat_last(new_items)
            return [self.get(obj, next(new_item_iter), level-1, next(item_iter), f) for obj in data]
        elif level:
            return [self.get(obj, new_items, level-1, items, f) for obj in data]
        else:
            return f(data, new_items, items)


def register():
    bpy.utils.register_class(SvListItemInsertNode)


def unregister():
    bpy.utils.unregister_class(SvListItemInsertNode)
