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
from sverchok.utils.sv_mesh_utils import mesh_join


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

            verts = self.inputs['Vertices'].sv_get()
            poly_edge = self.inputs['PolyEdge'].sv_get()

            verts_out, dummy, poly_edge_out = mesh_join(verts, [], poly_edge)

            if 'Vertices' in self.outputs and self.outputs['Vertices'].is_linked:
                self.outputs['Vertices'].sv_set([verts_out])

            if 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].is_linked:
                self.outputs['PolyEdge'].sv_set([poly_edge_out])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvMeshJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMeshJoinNode)
