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
import numpy as np
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)


class SvIndexToMaskNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Create mask list from index '''
    bl_idname = 'SvIndexToMaskNode'
    bl_label = 'SvIndexToMaskNode'
    bl_icon = 'OUTLINER_OB_EMPTY'

    ML = IntProperty(name='Mask_Len', default=10, min=2, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Index')
        self.inputs.new('StringsSocket', 'mask size').prop_name = "ML"
        self.outputs.new('StringsSocket', 'mask')

    def process(self):
        Inds, MaSi = self.inputs
        OM = self.outputs[0]
        if OM.is_linked:
            out = []
            I = Inds.sv_get()
            for Ind, Size in zip(I, safc(I, MaSi.sv_get()[0])):
                Ma = np.zeros(Size)
                Ma[Ind] = 1
                out.append(Ma.tolist())
            OM.sv_set(out)


def register():
    bpy.utils.register_class(SvIndexToMaskNode)


def unregister():
    bpy.utils.unregister_class(SvIndexToMaskNode)
