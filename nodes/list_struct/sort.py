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

def sv_sort(data, level):
    if level ==1:
        return sorted(data)
    else:
        out = []
        for d in data:
            out.append(sv_sort(d, level-1))
        return out
def key_sort(data, keys, level, idx):
    if level ==1:
        return [x for _, x in sorted(zip(keys[idx], data))]
    else:
        out = []
        for k_id, d in enumerate(data):
            out.append(key_sort(d, keys, level-1, min(k_id, len(keys)-1)))
        return out

class SvListSortNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Order List Items
    Tooltip: Sort List by value or using custom keys
    """
    bl_idname = 'SvListSortNode'
    bl_label = 'List Sort'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_SORT'

    level: IntProperty(name='level_to_count', default=1, min=1, update=updateNode)
    typ: StringProperty(name='typ', default='')
    newsock: BoolProperty(name='newsock', default=False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "data")
        self.inputs.new('SvStringsSocket', "keys")
        self.outputs.new('SvStringsSocket', "data")

    def sv_update(self):
        if 'data' in self.outputs and self.inputs['data'].links:
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)
            self.newsock = True

    def migrate_from(self, old_node):
        self.level = 4-old_node.level

    def process(self):
        if not self.outputs['data'].is_linked and not self.newsock:
            return
        self.newsock = False

        data_ = self.inputs['data'].sv_get()
        out = []

        input_level = levelsOflist(data_)
        if not self.inputs['keys'].is_linked:

            out = sv_sort(data_, min(self.level, input_level))
        else:
            keys_ = self.inputs['keys'].sv_get()
            out = key_sort(data_, keys_, min(self.level, input_level), 0)

        self.outputs['data'].sv_set(out)



def register():
    bpy.utils.register_class(SvListSortNode)


def unregister():
    bpy.utils.unregister_class(SvListSortNode)
