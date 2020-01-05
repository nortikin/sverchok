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

from itertools import cycle
import bpy
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, changable_sockets

def mask_data(list_a, mask_l, level, idx=0):

    mask_out, ind_true, ind_false, result_t, result_f = [], [], [], [], []

    if level > 1:
        if isinstance(list_a, (list, tuple)):
            result = [mask_out, ind_true, ind_false, result_t, result_f]

            for idx, sub_list in enumerate(list_a):
                for i, res in enumerate(mask_data(sub_list, mask_l, level - 1, idx)):
                    result[i].append(res)

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
        for mask_val, (id_item, item) in zip(mask_out, enumerate(list_a)):
            if mask_val:
                result_t.append(item)
                ind_true.append(id_item)
            else:
                result_f.append(item)
                ind_false.append(id_item)

    return mask_out, ind_true, ind_false, result_t, result_f

class MaskListNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Split data with Mask
    Tooltip: Filter data with a boolean list ([False, True] or [0,1])
    '''
    bl_idname = 'MaskListNode'
    bl_label = 'List Mask (out)'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MASK_OUT'

    Level: IntProperty(
        name='Level', description='List level to mask (see help)',
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

        result = mask_data(data, mask, self.Level)

        for s, res  in zip(outputs, result):
            if s.is_linked:
                s.sv_set(res)


def register():
    bpy.utils.register_class(MaskListNode)


def unregister():
    bpy.utils.unregister_class(MaskListNode)
