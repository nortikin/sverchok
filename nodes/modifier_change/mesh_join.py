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

import operator

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import SvSetSocketAnyType, SvGetSocketAnyType


class SvMeshJoinNode(bpy.types.Node, SverchCustomTreeNode):
    '''MeshJoin, join many mesh into on mesh object'''
    bl_idname = 'SvMeshJoinNode'
    bl_label = 'Mesh Join'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.inputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')

        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')

    def process(self):

        if 'Vertices' in self.inputs and self.inputs['Vertices'].is_linked and \
           'PolyEdge' in self.inputs and self.inputs['PolyEdge'].is_linked:

            verts = SvGetSocketAnyType(self, self.inputs['Vertices'])
            poly_edge = SvGetSocketAnyType(self, self.inputs['PolyEdge'])
            verts_out = []
            poly_edge_out = []
            offset = 0
            for obj in zip(verts, poly_edge):
                verts_out.extend(obj[0])
                if offset:
                    res = [list(map(lambda x:operator.add(offset, x), ep)) for ep in obj[1]]
                    poly_edge_out.extend(res)
                else:
                    poly_edge_out.extend(obj[1])
                offset += len(obj[0])

            if 'Vertices' in self.outputs and self.outputs['Vertices'].is_linked:
                SvSetSocketAnyType(self, 'Vertices', [verts_out])

            if 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].is_linked:
                SvSetSocketAnyType(self, 'PolyEdge', [poly_edge_out])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvMeshJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMeshJoinNode)
