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
from sverchok.data_structure import (changable_sockets, dataCorrect, updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class ListFlipNode(bpy.types.Node, SverchCustomTreeNode):
    ''' ListFlipNode '''
    bl_idname = 'ListFlipNode'
    bl_label = 'List Flip Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    level = IntProperty(name='level_to_count',
                        default=2, min=0, max=3,
                        update=updateNode)
    typ = StringProperty(name='typ',
                         default='')
    newsock = BoolProperty(name='newsock',
                           default=False)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.outputs.new('StringsSocket', 'data', 'data')

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")

    def flip(self, list, level):
        level -= 1
        if level:
            out = []
            for l in list:
                out.extend(self.flip(l, level))
        else:
            out = []
            length = self.maxlen(list)
            for i in range(length):
                out_ = []
                for l in list:
                    try:
                        out_.append(l[i])
                    except:
                        out_.append(l[0])
                out.append(out_)
        return out

    def maxlen(self, list):
        le = []
        for l in list:
            le.append(len(l))
        return max(le)

    def update(self):
        # адаптивный сокет
        inputsocketname = 'data'
        outputsocketname = ['data']
        changable_sockets(self, inputsocketname, outputsocketname)
    
    def process(self):
        if self.inputs['data'].links and self.outputs['data'].links:
            outEval = SvGetSocketAnyType(self, self.inputs['data'])
            outCorr = dataCorrect(outEval)  # this is bullshit, as max 3 in levels
            levels = self.level-1
            out = self.flip(outCorr, levels)
            SvSetSocketAnyType(self, 'data', out)


def register():
    bpy.utils.register_class(ListFlipNode)


def unregister():
    bpy.utils.unregister_class(ListFlipNode)
