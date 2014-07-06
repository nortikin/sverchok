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

from copy import copy

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty
from node_tree import SverchCustomTreeNode, StringsSocket
from data_structure import (updateNode, changable_sockets,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class MaskListNode(bpy.types.Node, SverchCustomTreeNode):
    ''' MaskList node '''
    bl_idname = 'MaskListNode'
    bl_label = 'MaskList'
    bl_icon = 'OUTLINER_OB_EMPTY'

    Level = IntProperty(name='Level', description='Choose list level of data (see help)',
                        default=1, min=1, max=10,
                        update=updateNode)

    typ = StringProperty(name='typ',
                         default='')
    newsock = BoolProperty(name='newsock',
                           default=False)

    def init(self, context):
        self.inputs.new('StringsSocket', "data", "data")
        self.inputs.new('StringsSocket', "mask", "mask")

        self.outputs.new('StringsSocket', "mask", "mask")
        self.outputs.new('StringsSocket', "ind_true", "ind_true")
        self.outputs.new('StringsSocket', "ind_false", "ind_false")
        self.outputs.new('StringsSocket', 'dataTrue', 'dataTrue')
        self.outputs.new('StringsSocket', 'dataFalse', 'dataFalse')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Level", text="Level lists")

    def update(self):
        # changable types sockets in output
        # you need the next:
        # typ - needed self value
        # newsocket - needed self value
        # inputsocketname to get one socket to define type
        # outputsocketname to get list of outputs, that will be changed
        inputsocketname = 'data'
        outputsocketname = ['dataTrue', 'dataFalse']
        changable_sockets(self, inputsocketname, outputsocketname)

        # input sockets
        if 'data' not in self.inputs:
            return False
        data = [[]]
        mask = [[1, 0]]

        if self.inputs['data'].links:
            data = SvGetSocketAnyType(self, self.inputs['data'])

        if self.inputs['mask'].links and \
           type(self.inputs['mask'].links[0].from_socket) == StringsSocket:
            mask = SvGetSocketAnyType(self, self.inputs['mask'])

        result = self.getMask(data, mask, self.Level)

        # outupy sockets data
        if 'dataTrue' in self.outputs and self.outputs['dataTrue'].is_linked:
            SvSetSocketAnyType(self, 'dataTrue', result[0])
        else:
            SvSetSocketAnyType(self, 'dataTrue', [[]])
        # print ('всё',result)
        if 'dataFalse' in self.outputs and self.outputs['dataFalse'].is_linked:
            SvSetSocketAnyType(self, 'dataFalse', result[1])
        else:
            SvSetSocketAnyType(self, 'dataFalse', [[]])

        if 'mask' in self.outputs and self.outputs['mask'].is_linked:
            SvSetSocketAnyType(self, 'mask', result[2])
        else:
            SvSetSocketAnyType(self, 'mask', [[]])
        if 'ind_true' in self.outputs and self.outputs['ind_true'].is_linked:
            SvSetSocketAnyType(self, 'ind_true', result[3])
        else:
            SvSetSocketAnyType(self, 'ind_true', [[]])
        if 'ind_false' in self.outputs and self.outputs['ind_false'].is_linked:
            SvSetSocketAnyType(self, 'ind_false', result[4])
        else:
            SvSetSocketAnyType(self, 'ind_false', [[]])

    # working horse
    def getMask(self, list_a, mask_l, level):
        list_b = self.getCurrentLevelList(list_a, level)
        res = list_b
        if list_b:
            res = self.putCurrentLevelList(list_a, list_b, mask_l, level)
        return res

    def putCurrentLevelList(self, list_a, list_b, mask_l, level, idx=0):
        result_t = []
        result_f = []
        mask_out = []
        ind_true = []
        ind_false = []
        if level > 1:
            if type(list_a) in [list, tuple]:
                for idx, l in enumerate(list_a):
                    l2 = self.putCurrentLevelList(l, list_b, mask_l, level-1, idx)
                    result_t.append(l2[0])
                    result_f.append(l2[1])
                    mask_out.append(l2[2])
                    ind_true.append(l2[3])
                    ind_false.append(l2[4])
            else:
                print('AHTUNG!!!')
                return list_a
        else:
            indx = min(len(mask_l)-1, idx)
            mask = mask_l[indx]
            mask_0 = copy(mask)
            while len(mask) < len(list_a):
                if len(mask_0) == 0:
                    mask_0 = [1, 0]
                mask = mask+mask_0

            for idx, l in enumerate(list_a):
                tmp = list_b.pop(0)
                if mask[idx]:
                    result_t.append(tmp)
                    ind_true.append(idx)
                else:
                    result_f.append(tmp)
                    ind_false.append(idx)
            mask_out = mask[:len(list_a)]

        return (result_t, result_f, mask_out, ind_true, ind_false)

    def getCurrentLevelList(self, list_a, level):
        list_b = []
        if level > 1:
            if type(list_a) in [list, tuple]:
                for l in list_a:
                    l2 = self.getCurrentLevelList(l, level-1)
                    if type(l2) in [list, tuple]:
                        list_b.extend(l2)
                    else:
                        return False
            else:
                return False
        else:
            if type(list_a) in [list, tuple]:
                return copy(list_a)
            else:
                return list_a
        return list_b


def register():
    bpy.utils.register_class(MaskListNode)


def unregister():
    bpy.utils.unregister_class(MaskListNode)
