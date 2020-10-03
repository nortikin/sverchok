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
from functools import reduce
from itertools import cycle, chain

import bpy

from sverchok.node_tree import SverchCustomTreeNode
import sverchok.utils.meshes as me


class SvMeshJoinNode(bpy.types.Node, SverchCustomTreeNode):
    '''MeshJoin, join many mesh into on mesh object'''
    bl_idname = 'SvMeshJoinNode'
    bl_label = 'Mesh Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MESH_JOIN'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'PolyEdge')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'PolyEdge')

    def process(self):
        if not self.inputs['Vertices'].is_linked:
            return

        vertices = self.inputs['Vertices'].sv_get(default=[])
        edges = []
        polygons = []

        poly_edges = self.inputs['PolyEdge'].sv_get(default=[])
        first_elements = [obj[0] for obj in poly_edges]
        if first_elements:
            if all([len(el) == 2 for el in first_elements]):
                edges = poly_edges
            elif all([len(el) != 2 for el in first_elements]):
                polygons = poly_edges
            else:
                raise TypeError('PoyEdge socket should consist either all edges or all faces')  # Sv architecture law

        meshes = [me.to_mesh(*m) for m in zip(vertices, chain(edges, cycle([[]])), chain(polygons, cycle([[]])))]
        joined_mesh = reduce(lambda m1, m2: m1.add_mesh(m2), meshes)
        self.outputs['Vertices'].sv_set([joined_mesh.vertices])
        if joined_mesh.edges:
            self.outputs['PolyEdge'].sv_set([joined_mesh.edges])
        if joined_mesh.polygons:
            self.outputs['PolyEdge'].sv_set([joined_mesh.polygons])


def register():
    bpy.utils.register_class(SvMeshJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMeshJoinNode)
