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

class SvPlanarFacesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: planar faces
    Tooltip: Make Quad/NGon faces planar (flat).
    """
    bl_idname = 'SvPlanarFacesNode'
    bl_label = 'Make Faces Planar'
    bl_icon = 'MOD_BEVEL'

    iterations : IntProperty(
        name = "Iterations",
        description = " Number of times to flatten faces (for when connected faces are used)",
        default = 1, min = 1,
        update = updateNode)

    factor : FloatProperty(
        name = "Factor",
        description = "Influence for making planar each iteration",
        min = 0, max = 1, default = 0.5,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'FaceMask')
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.inputs.new('SvStringsSocket', 'Factor').prop_name = 'factor'

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        if not any (socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        masks_s = self.inputs['FaceMask'].sv_get(default=[[1]])
        factors_s = self.inputs['Factor'].sv_get()
        iterations_s = self.inputs['Iterations'].sv_get()

        verts_out = []
        edges_out = []
        faces_out = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, factors_s, iterations_s])
        for vertices, edges, faces, masks, factor, iterations in zip(*meshes):
            if isinstance(iterations, (list, tuple)):
                iterations = iterations[0]
            if isinstance(factor, (list, tuple)):
                factor = factor[0]
            fullList(masks, len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
            bm_faces = [face for mask, face in zip(masks, bm.faces[:]) if mask]

            bmesh.ops.planar_faces(bm,
                    faces = bm_faces,
                    iterations = iterations,
                    factor = factor)

            new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvPlanarFacesNode)


def unregister():
    bpy.utils.unregister_class(SvPlanarFacesNode)

