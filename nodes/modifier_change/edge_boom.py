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
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, updateNode
from sverchok.utils.sv_mesh_utils import polygons_to_edges

class SvEdgeBoomNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Edge Boom
    Tooltip: decompose a mesh into list of edge objects
    """
    bl_idname = 'SvEdgeBoomNode'
    bl_label = 'Edge Boom'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXPLODE'

    modes = [
        ('VER', "Vertices", "Output list of first vertices and list of second vertices of each edge", 0),
        ('OBJ', "Objects", "Output list of objects, each consisting of a single edge", 1)
    ]

    @throttled
    def update_sockets(self, context):
        self.outputs['Vertex1'].hide_safe = self.out_mode != 'VER'
        self.outputs['Vertex2'].hide_safe = self.out_mode != 'VER'
        self.outputs['Vertices'].hide_safe = self.out_mode != 'OBJ'
        self.outputs['Edges'].hide_safe = self.out_mode != 'OBJ'

    out_mode : EnumProperty(
        name = "Output mode",
        description = "Output mode",
        default = 'VER',
        items = modes,
        update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvVerticesSocket', 'Vertex1')
        self.outputs.new('SvVerticesSocket', 'Vertex2')
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text="Output mode:")
        layout.prop(self, "out_mode", text="")

    def process(self):
        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get()

        verts1_out = []
        verts2_out = []
        verts_out = []
        edges_out = []
        for vertices, edges, faces in zip_long_repeat(vertices_s, edges_s, faces_s):
            new_verts1 = []
            new_verts2 = []
            if not edges:
                edges = polygons_to_edges([faces], unique_edges=True)[0]
            for i1, i2 in edges:
                new_verts = []
                new_edges = []
                if i1 > i2:
                    i1, i2 = i2, i1
                v1, v2 = vertices[i1], vertices[i2]
                new_verts1.append(v1)
                new_verts2.append(v2)
                new_verts.append(v1)
                new_verts.append(v2)
                new_edges.append([0,1])
                verts_out.append(new_verts)
                edges_out.append(new_edges)

            verts1_out.append(new_verts1)
            verts2_out.append(new_verts2)

        self.outputs['Vertex1'].sv_set(verts1_out)
        self.outputs['Vertex2'].sv_set(verts2_out)
        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)

def register():
    bpy.utils.register_class(SvEdgeBoomNode)

def unregister():
    bpy.utils.unregister_class(SvEdgeBoomNode)

