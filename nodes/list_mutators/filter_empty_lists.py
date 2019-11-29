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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvFixEmptyObjectsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' filter out None bpy objects or empty sverchok object level lists '''
    bl_idname = 'SvFixEmptyObjectsNode'
    bl_label = 'fix empty objects'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FIX_EMPTY_OBJECTS'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "data")
        self.outputs.new('SvStringsSocket', "san data")
        self.outputs.new('SvStringsSocket', "mask")
        self.outputs.new('SvStringsSocket', "numpy mask")

    def process(self):
        sd, m, nm = self.outputs
        D = self.inputs[0].sv_get()
        if sd.is_linked:
            sd.sv_set([d for d in D if d])
        if m.is_linked:
            m.sv_set([bool(d) for d in D])
        if nm.is_linked:
            nm.sv_set(np.ma.make_mask(D, copy=False, shrink=False).tolist())


def register():
    bpy.utils.register_class(SvFixEmptyObjectsNode)


def unregister():
    bpy.utils.unregister_class(SvFixEmptyObjectsNode)
