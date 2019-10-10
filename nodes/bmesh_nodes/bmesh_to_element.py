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
from sverchok.data_structure import updateNode


class SvBMtoElementNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Decompose '''
    bl_idname = 'SvBMtoElementNode'
    bl_label = 'BMesh Elements'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_BMESH_ELEMENTS'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'bmesh_list')
        self.outputs.new('SvStringsSocket', 'BM_verts')
        self.outputs.new('SvStringsSocket', 'BM_edges')
        self.outputs.new('SvStringsSocket', 'BM_faces')

    def process(self):
        bmlist = self.inputs[0]
        if bmlist.is_linked:
            v, e, p = self.outputs
            bml = bmlist.sv_get()
            v.sv_set([i.verts[:] for i in bml])
            e.sv_set([i.edges[:] for i in bml])
            p.sv_set([i.faces[:] for i in bml])


def register():
    bpy.utils.register_class(SvBMtoElementNode)


def unregister():
    bpy.utils.unregister_class(SvBMtoElementNode)
