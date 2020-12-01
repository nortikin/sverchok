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
from sverchok.utils.mesh_functions import meshes_py, join_meshes, meshes_np, to_elements


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

        vertices = self.inputs['Vertices'].sv_get(deepcopy=False)
        edges = []
        polygons = []

        poly_edges = self.inputs['PolyEdge'].sv_get(deepcopy=False, default=[])
        first_elements = [obj[0] for obj in poly_edges]
        if first_elements:
            if all([len(el) == 2 for el in first_elements]):
                edges = poly_edges
            elif all([len(el) != 2 for el in first_elements]):
                polygons = poly_edges
            else:
                raise TypeError('PoyEdge socket should consist either all edges or all faces')  # Sv architecture law

        is_py_input = isinstance(vertices[0], (list, tuple))
        meshes = (meshes_py if is_py_input else meshes_np)(vertices, edges, polygons)
        meshes = join_meshes(meshes)
        out_vertices, out_edges, out_polygons = to_elements(meshes)

        self.outputs['Vertices'].sv_set(out_vertices)
        self.outputs['PolyEdge'].sv_set(out_edges or out_polygons)


def register():
    bpy.utils.register_class(SvMeshJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMeshJoinNode)
