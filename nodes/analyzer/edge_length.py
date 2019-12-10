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
from bpy.props import BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

def untangle_edges(orig_edges, bmesh_edges, lengths):
    result = []
    edges = bmesh_edges[:]
    for orig_edge in orig_edges:
        i,e = [(i,e) for i,e in enumerate(edges) if set(v.index for v in e.verts) == set(orig_edge)][0]
        result.append(lengths[i])
    return result

class SvEdgeLengthNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: edge length
    Tooltip: Calculate length of object's edges
    """

    bl_idname = 'SvEdgeLengthNode'
    bl_label = 'Edge Lengths'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ANGLES_AT_EDGES'

    calc_sum : BoolProperty(
            name = "Sum",
            description = "Calculate sum of all edge lengths",
            default = False,
            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "calc_sum")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")

        self.outputs.new('SvStringsSocket', "Length")

    def process(self):

        if not self.outputs['Length'].is_linked:
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])

        result_lengths = []
        meshes = match_long_repeat([vertices_s, edges_s, faces_s])
        for vertices, edges, faces in zip(*meshes):
            new_lengths = []
            length_sum = 0
            bm = bmesh_from_pydata(vertices, edges, faces)
            for edge in bm.edges:
                length = edge.calc_length()
                if self.calc_sum:
                    length_sum += length
                else:
                    new_lengths.append(length)
            if self.calc_sum:
                new_lengths = [length_sum]
            if edges and not self.calc_sum:
                new_lengths = untangle_edges(edges, bm.edges, new_lengths)
            bm.free()

            result_lengths.append(new_lengths)

        self.outputs['Length'].sv_set(result_lengths)

def register():
    bpy.utils.register_class(SvEdgeLengthNode)

def unregister():
    bpy.utils.unregister_class(SvEdgeLengthNode)

