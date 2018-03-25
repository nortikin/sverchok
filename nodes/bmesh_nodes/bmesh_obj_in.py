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
import bmesh
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


class SvBMObjinputNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Object In '''
    bl_idname = 'SvBMObjinputNode'
    bl_label = 'BMesh Obj in'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.outputs.new('StringsSocket', 'bmesh_list')

    def process(self):
        bmL = self.outputs[0]
        if bmL.is_linked:
            Val = []
            obj = self.inputs[0].sv_get()
            for OB in obj:
                bm = bmesh.new()
                bm.from_mesh(OB.data, use_shape_key=False, shape_key_index=0)
                Val.append(bm)
            bmL.sv_set(Val)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBMObjinputNode)


def unregister():
    bpy.utils.unregister_class(SvBMObjinputNode)
