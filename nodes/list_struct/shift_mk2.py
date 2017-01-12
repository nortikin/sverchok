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
import numpy as np

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import (updateNode, changable_sockets)


class ShiftNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Shift node mk2 '''
    bl_idname = 'ShiftNodeMK2'
    bl_label = 'List Shift'
    bl_icon = 'OUTLINER_OB_EMPTY'

    shift_c = IntProperty(name='Shift',
                          default=0,
                          update=updateNode)
    enclose = BoolProperty(name='check_tail',
                           default=True,
                           update=updateNode)
    level = IntProperty(name='level',
                        default=0, min=0,
                        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        #layout.prop(self, "enclose", text="enclose")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "shift", "shift").prop_name = 'shift_c'
        self.outputs.new('StringsSocket', 'data', 'data')

    def update(self):
        if 'data' in self.inputs and self.inputs['data'].links:
            # адаптивный сокет
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        if not self.outputs["data"].is_linked:
            return

        data = self.inputs['data'].sv_get()
        number = self.inputs["shift"].sv_get()[0][0]
        # numpy case:
        dat = np.array(data)
        # levelsOfList replacement:
        depth = dat.ndim #len(np.shape(dat))-1
        # roll with enclose (we need case of declose and vectorization)
        output = np.roll(dat,number,axis=min(self.level,depth)).tolist()

        self.outputs['data'].sv_set(output)


def register():
    bpy.utils.register_class(ShiftNodeMK2)


def unregister():
    bpy.utils.unregister_class(ShiftNodeMK2)

if __name__ == '__main__':
    register()
