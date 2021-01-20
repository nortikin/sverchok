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

    level: IntProperty(name='level_to_count', default=2, min=1, update=updateNode)
    index: IntProperty(name='index', default=1, update=updateNode)
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
        if not (si['Data'].is_linked and si['Item'].is_linked and out_socket.is_linked):
            return

        data = si['Data'].sv_get(deepcopy=False)

        new_item = si['Item'].sv_get(deepcopy=False)
        indexes = si['Index'].sv_get(default=[[self.index]], deepcopy=False)
        if self.level-1:
            out = self.get(data, new_item, self.level-1, indexes, self.set_items)
        else:
            out = self.set_items(data, new_item, indexes[0])
        out_socket.sv_set(out)


    def set_items(self, data, new_items, indexes):
        if type(data) in [list, tuple]:
            data_out = data.copy() if isinstance(data, list) else list(data)
            params = list_match_func[self.list_match_local]([indexes, new_items])
            for ind, i in zip(*params):
                if self.replace and len(data_out) > ind:
                    data_out.pop(ind)
                data_out.insert(ind, i)
            return data_out
        elif type(data) == np.ndarray:
            out_data = np.array(data)
            ind, items = list_match_func[self.list_match_local]([indexes, new_items])
            if self.replace:
                out_data[ind] = items

            else:
                for i, item in zip(ind, items):
                    out_data = np.concatenate([data[:i], [item], data[i:]])

            return out_data
        elif type(data) == str:
            ind, items = list_match_func[self.list_match_local]([indexes, new_items])

            add_one = 1 if self.replace else 0
            out_data = data
            for i, item in zip(ind, items):
                out_data = out_data[:i]+ str(item) + out_data[i+add_one:]
            return out_data
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
