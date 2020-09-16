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
from bpy.props import EnumProperty, BoolProperty
import bmesh

from sverchok.utils.quad_grid import SvQuadGridParser
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, transpose_list

class SvQuadGridSortVertsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: sort vertices quad grid
    Tooltip: Sort vertices from a quad grid (subdivided plane) mesh, row by row
    """
    bl_idname = 'SvQuadGridSortVertsNode'
    bl_label = 'Sort Quad Grid'
    bl_icon = 'MESH_GRID'

    reverse_rows : BoolProperty(
            name = "Reverse rows",
            description = "Reverse order of rows",
            default = False,
            update = updateNode)

    reverse_cols : BoolProperty(
            name = "Reverse columns",
            description = "Reverse order of vertices in each column",
            default = False,
            update = updateNode)

    transpose : BoolProperty(
            name = "Transpose",
            description = "Transpose the list: make rows from columns, and vice versa",
            default = False,
            update = updateNode)
    
    join_rows : BoolProperty(
            name = "Join rows",
            description = "Concatenate all rows (or columns, if `Transpose' is on) into one list",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'reverse_rows')
        layout.prop(self, 'reverse_cols')
        layout.prop(self, 'transpose')
        layout.prop(self, 'join_rows')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Indexes")

    def process(self):
        if not any (socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])

        verts_out = []
        idxs_out = []

        for vertices, edges, faces in zip_long_repeat(vertices_s, edges_s, faces_s):
            bm = bmesh_from_pydata(vertices, edges, faces)
            bm.faces.index_update()

            parser = SvQuadGridParser(bm)
            new_idxs = parser.get_verts_sequence()
            new_verts = parser.get_ordered_verts()
            
            if self.reverse_rows:
                new_idxs = list(reversed(new_idxs))
                new_verts = list(reversed(new_verts))

            if self.reverse_cols:
                new_idxs = [list(reversed(row)) for row in new_idxs]
                new_verts = [list(reversed(row)) for row in new_verts]

            if self.transpose:
                new_idxs = transpose_list(new_idxs)
                new_verts = transpose_list(new_verts)

            if self.join_rows:
                new_idxs = sum(new_idxs, [])
                new_verts = sum(new_verts, [])

            bm.free()

            verts_out.append(new_verts)
            idxs_out.append(new_idxs)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Indexes'].sv_set(idxs_out)

def register():
    bpy.utils.register_class(SvQuadGridSortVertsNode)

def unregister():
    bpy.utils.unregister_class(SvQuadGridSortVertsNode)

