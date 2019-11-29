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
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvMaskToIndexNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Index list from mask list
    Tooltip: Splits the true and false indices from a mask list
    '''
    bl_idname = 'SvMaskToIndexNode'
    bl_label = 'Mask to Index'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MASK_TO_INDEX'


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Mask")

        self.outputs.new('SvStringsSocket', "True Index")
        self.outputs.new('SvStringsSocket', "False Index")


    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        if not (any(s.is_linked for s in outputs) and inputs[0].is_linked):
            return
        mask = inputs['Mask'].sv_get(default=[[1, 0]])


        if self.outputs['True Index'].is_linked:
            outputs['True Index'].sv_set(self.true_indices(mask))

        if self.outputs['False Index'].is_linked:
            outputs['False Index'].sv_set(self.false_indices(mask))


    def true_indices(self, mask):
        if type(mask[0]) in [list, tuple]:
            return [self.true_indices(m) for m in mask]
        else:
            return [i for i, m in enumerate(mask) if m]

    def false_indices(self, mask):
        if type(mask[0]) in [list, tuple]:
            return [self.false_indices(m) for m in mask]
        else:
            return [i for i, m in enumerate(mask) if not m]



def register():
    bpy.utils.register_class(SvMaskToIndexNode)


def unregister():
    bpy.utils.unregister_class(SvMaskToIndexNode)
