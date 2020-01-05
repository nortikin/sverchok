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
from itertools import cycle
import bpy
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, changable_sockets


class MaskListNode(bpy.types.Node, SverchCustomTreeNode):
    ''' MaskList node '''
    bl_idname = 'MaskListNode'
    bl_label = 'List Mask (out)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MASK_OUT'

    Level: IntProperty(
        name='Level', description='Choose list level of data (see help)',
        default=1, min=1, max=10, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "data")
        self.inputs.new('SvStringsSocket', "mask")

        self.outputs.new('SvStringsSocket', "mask")
        self.outputs.new('SvStringsSocket', "ind_true")
        self.outputs.new('SvStringsSocket', "ind_false")
        self.outputs.new('SvStringsSocket', 'dataTrue')
        self.outputs.new('SvStringsSocket', 'dataFalse')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Level", text="Level lists")

    def update(self):
        inputsocketname = 'data'
        outputsocketname = ['dataTrue', 'dataFalse']
        changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        data = inputs['data'].sv_get()
        mask = inputs['mask'].sv_get(default=[[1, 0]])

        result = self.get_mask(data, mask, self.Level)

        if self.outputs['dataTrue'].is_linked:
            outputs['dataTrue'].sv_set(result[0])

        if self.outputs['dataFalse'].is_linked:
            outputs['dataFalse'].sv_set(result[1])

        if self.outputs['mask'].is_linked:
            outputs['mask'].sv_set(result[2])

        if self.outputs['ind_true'].is_linked:
            outputs['ind_true'].sv_set(result[3])

        if self.outputs['ind_false'].is_linked:
            outputs['ind_false'].sv_set(result[4])

    # working horse
    def get_mask(self, list_a, mask_l, level):
        list_b = self.get_current_level_list(list_a, level)
        res = list_b
        if list_b:
            res = self.put_current_level_list(list_a, list_b, mask_l, level)
        return res

    def put_current_level_list(self, list_a, list_b, mask_l, level, idx=0):
        result_t = []
        result_f = []
        mask_out = []
        ind_true = []
        ind_false = []
        if level > 1:
            if isinstance(list_a, (list, tuple)):
                for idx, sub_list in enumerate(list_a):
                    sub_res = self.put_current_level_list(sub_list, list_b, mask_l, level - 1, idx)
                    result_t.append(sub_res[0])
                    result_f.append(sub_res[1])
                    mask_out.append(sub_res[2])
                    ind_true.append(sub_res[3])
                    ind_false.append(sub_res[4])

        else:
            indx = min(len(mask_l)-1, idx)
            mask = mask_l[indx]
            if len(mask) < len(list_a):
                if not mask:
                    mask = [1, 0]
                mask = cycle(mask)
                mask_out = [m for m, l in zip(mask, list_a)]
            else:
                mask_out = mask[:len(list_a)]
            for mask_val, item in zip(mask_out, list_b):
                if mask_val:
                    result_t.append(item)
                    ind_true.append(idx)
                else:
                    result_f.append(item)
                    ind_false.append(idx)

        return (result_t, result_f, mask_out, ind_true, ind_false)

    def get_current_level_list(self, list_a, level):
        list_b = []
        if level > 1:
            if isinstance(list_a, (list, tuple)):
                for sub_list in list_a:
                    sub_res = self.get_current_level_list(sub_list, level-1)
                    if isinstance(sub_res, (list, tuple)):
                        list_b.extend(sub_res)
                    else:
                        return False
            else:
                return False
        else:
            if isinstance(list_a, (list, tuple)):
                return copy(list_a)
            else:
                return list_a
        return list_b


def register():
    bpy.utils.register_class(MaskListNode)


def unregister():
    bpy.utils.unregister_class(MaskListNode)
