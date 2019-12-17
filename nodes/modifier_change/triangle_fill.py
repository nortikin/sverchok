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
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

def get_bm_edges(bm, edges, edge_mask):
    good_edges = [set(edge) for edge, mask in zip(edges, edge_mask) if mask]
    return [edge for edge in bm.edges[:] if set([edge.verts[0].index, edge.verts[1].index]) in good_edges]

class SvTriangleFillNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: triangle fill
    Tooltip: Fill edges with triangles
    """
    bl_idname = 'SvTriangleFillNode'
    bl_label = 'Fill with Triangles'
    bl_icon = 'MOD_BEVEL'

    use_beauty : BoolProperty(
        name = "Beauty",
        default = True,
        update = updateNode)

    use_dissolve : BoolProperty(
        name = "Dissolve",
        description = "dissolve resulting faces", 
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "use_beauty", toggle=True)
        col.prop(self, "use_dissolve", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'EdgeMask')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        if not any (socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        masks_s = self.inputs['EdgeMask'].sv_get(default=[[1]])
        has_mask = self.inputs['EdgeMask'].is_linked

        verts_out = []
        edges_out = []
        faces_out = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s])
        for vertices, edges, faces, masks in zip(*meshes):
            fullList(masks, len(edges))

            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
            if has_mask:
                bm_edges = get_bm_edges(bm, edges, masks)
            else:
                bm_edges = bm.edges[:]

            bmesh.ops.triangle_fill(bm,
                    use_beauty = self.use_beauty,
                    use_dissolve = self.use_dissolve,
                    edges = bm_edges)

            new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvTriangleFillNode)


def unregister():
    bpy.utils.unregister_class(SvTriangleFillNode)

