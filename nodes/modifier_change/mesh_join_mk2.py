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
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

def mesh_join(vertices, edges, polygons):
    is_py_input = isinstance(vertices[0], (list, tuple))
    meshes = (meshes_py if is_py_input else meshes_np)(vertices, edges, polygons)
    meshes = join_meshes(meshes)
    out_vertices, out_edges, out_polygons = to_elements(meshes)

    return out_vertices, out_edges, out_polygons

class SvMeshJoinNodeMk2(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    '''
    Triggers: Join Meshes
    Tooltip: Join many mesh into on mesh object
    '''

    bl_idname = 'SvMeshJoinNodeMk2'
    bl_label = 'Mesh Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MESH_JOIN'

    def sv_init(self, context):
        verts = self.inputs.new('SvVerticesSocket', 'Vertices')
        verts.is_mandatory = True
        verts.nesting_level = 3
        verts.default_mode = 'NONE'

        edges = self.inputs.new('SvStringsSocket', 'Edges')
        edges.nesting_level = 3
        edges.default_mode = 'EMPTY_LIST'

        pols = self.inputs.new('SvStringsSocket', 'Polygons')
        pols.nesting_level = 3
        pols.default_mode = 'EMPTY_LIST'

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')

    def migrate_from(self, old_node):
        verts = self.inputs['Vertices']
        verts.is_mandatory = True
        verts.default_mode = 'NONE'

        edges = self.inputs['Edges']
        edges.nesting_level = 3
        edges.default_mode = 'EMPTY_LIST'

        pols = self.inputs['Polygons']
        pols.nesting_level = 3
        pols.default_mode = 'EMPTY_LIST'

    def process_data(self, params):
        return mesh_join(*params)


def register():
    bpy.utils.register_class(SvMeshJoinNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvMeshJoinNodeMk2)
