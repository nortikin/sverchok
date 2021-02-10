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
from sverchok.data_structure import updateNode, changable_sockets, numpy_full_list_cycle
import numpy as np

def mask_list(list_a, mask, flags):
    mask_out, ind_true, ind_false, result_t, result_f = [], [], [], [], []
    if any(flags[:3]):
        mask_out = numpy_full_list_cycle(np.array(mask).astype(bool), len(list_a))

    if flags[1] or flags[2]:
        id_t = np.arange(len(list_a))

        if flags[1]:
            ind_true = id_t[mask_out].tolist()
        if flags[2]:
            ind_false = id_t[np.invert(mask_out)].tolist()
    if flags[3]:
        mask_iter = cycle(mask)
        result_t = [item for item, m in zip(list_a, mask_iter) if m]
    if flags[4]:
        mask_iter = cycle(mask)
        result_f = [item for item, m in zip(list_a, mask_iter) if not m]
    mask_out = mask_out.tolist() if flags[0] else []

    return mask_out, ind_true, ind_false, result_t, result_f

def mask_array(list_a, mask, flags):
    id_t, f_mask = [], []

    mask_out = numpy_full_list_cycle(np.array(mask).astype(bool), len(list_a))
    if flags[1] or flags[2]:
        id_t = np.arange(len(list_a))

    if flags[2] or flags[4]:
        f_mask = np.invert(mask_out)


    return (
        mask_out if flags[0] else [],
        id_t[mask_out] if flags[1] else [],
        id_t[f_mask] if flags[2] else [],
        list_a[mask_out] if flags[3] else [],
        list_a[f_mask] if flags[4] else [])

def mask_data(list_a, mask_l, level, flags, idx=0):

    mask_out, ind_true, ind_false, result_t, result_f = [], [], [], [], []

    if level > 1:
        if isinstance(list_a, (list, tuple, np.ndarray)):
            result = [mask_out, ind_true, ind_false, result_t, result_f]

            for idx, sub_list in enumerate(list_a):

                for i, res in enumerate(mask_data(sub_list, mask_l, level - 1, flags, idx)):
                    result[i].append(res)

    else:
        indx = min(len(mask_l)-1, idx)
        mask = mask_l[indx]

        if type(list_a) == np.ndarray:
            return mask_array(list_a, mask, flags)
        else:
            return mask_list(list_a, mask, flags)


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

    def sv_update(self):
        inputsocketname = 'data'
        outputsocketname = ['dataTrue', 'dataFalse']
        changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        if not any(s.is_linked for s in outputs) and inputs[0].is_linked:
            return
        data = inputs['data'].sv_get(deepcopy=False)
        mask = inputs['mask'].sv_get(default=[[1, 0]],deepcopy=False)
        flags = [s.is_linked for s in outputs]
        result = mask_data(data, mask, self.Level, flags)

        for s, res  in zip(outputs, result):
            if s.is_linked:
                s.sv_set(res)


def register():
    bpy.utils.register_class(MaskListNode)


def unregister():
    bpy.utils.unregister_class(MaskListNode)
