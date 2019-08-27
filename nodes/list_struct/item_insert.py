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

        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop(self, "level", text="level")
        layout.prop(self, "replace", text="Replace")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.inputs.new('SvStringsSocket', "Item")
        self.inputs.new('SvStringsSocket', "Index").prop_name = 'index'
        self.outputs.new('SvStringsSocket', "Data")


    def update(self):
        if 'Data' in self.inputs and self.inputs['Data'].links:
            inputsocketname = 'Data'
            outputsocketname = ['Item']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        if self.inputs['Data'].is_linked:
            OItem = self.outputs[0]
            data = self.inputs['Data'].sv_get()
            new_item = self.inputs['Item'].sv_get()
            indexes = self.inputs['Index'].sv_get([[self.index]])
            if OItem.is_linked:
                # out = self.set_all_items(data, new_item, indexes)
                if self.level-1:
                    out = self.get(data, new_item, self.level-1, indexes, self.set_items)
                else:
                    out = self.set_items(data, new_item, indexes[0])
                OItem.sv_set(out)


    def set_all_items(self, data, new_item, indexes):
        if type(indexes[0]) in [list, tuple]:
            data_iter = repeat_last(data)
            new_item_iter = repeat_last(new_item)
            out = [self.set_all_items(next(data_iter), next(new_item_iter), index) for index in indexes]
        else:
            if self.level-1:
                out = self.get(data, new_item, self.level-1, [indexes], self.set_items)
            else:
                out = self.set_items(data, new_item, indexes)
        return out

    def set_items(self, data, new_items, indexes):
        if type(data) in [list, tuple]:
            params = list_match_func[self.list_match_local]([indexes, new_items])
            for ind, i in zip(*params):
                if self.replace and len(data) > ind:
                    data.pop(ind)
                data.insert(ind, i)
            return data

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
                if -1 < i < len(data):
                    del data[i]
            if is_tuple:
                return tuple(data)
            else:
                return data
        else:
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
