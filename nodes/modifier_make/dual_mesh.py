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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (match_long_repeat, updateNode)
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, dual_mesh
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode
from bpy.props import BoolVectorProperty, EnumProperty, BoolProperty, FloatProperty, IntProperty


class SvDualMeshNodeMK2(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Dual Mesh
    Tooltip: Create dual mesh for the given mesh
    """
    bl_idname = 'SvDualMeshNodeMK2'
    bl_label = "Dual Mesh"
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DUAL_MESH'

    keep_boundaries : BoolProperty(
        name = "Keep Boundaries",
        description = "Keep non-manifold boundaries of the mesh in place by avoiding the dual transformation there",
        default = False,
        update = updateNode)  # type: ignore


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket' , 'edges')
        self.inputs.new('SvStringsSocket' , 'polygons')

        self.inputs['vertices'].label = 'Vertices'
        self.inputs['edges']   .label = 'Edges'
        self.inputs['polygons'].label = 'Polygons'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket' , 'edges')
        self.outputs.new('SvStringsSocket' , 'polygons')

        self.outputs['vertices'].label = 'Vertices'
        self.outputs['edges']   .label = 'Edges'
        self.outputs['polygons'].label = 'Polygons'

    @property
    def sv_internal_links(self):
        return [
            (self.inputs[0], self.outputs[0]),
            (self.inputs[2], self.outputs[1]),
        ]
    
    def draw_buttons(self, context, layout):
        col = layout.column()
        col.row().prop(self, 'keep_boundaries')

    def process(self):
        if not any((s.is_linked for s in self.outputs)):
            return

        verts_s = self.inputs['vertices'].sv_get()
        edges_s = self.inputs['edges'].sv_get(default=[[]])
        faces_s = self.inputs['polygons'].sv_get()

        verts_out = []
        edges_out = []
        faces_out = []

        objects = match_long_repeat([verts_s, edges_s, faces_s])
        for verts, edges, faces in zip(*objects):
            bm = bmesh_from_pydata(verts, edges, faces, normal_update=True)
            new_verts, new_edges, new_faces = dual_mesh(bm, keep_boundaries=self.keep_boundaries)
            bm.free()
            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)

        self.outputs['vertices'].sv_set(verts_out)
        self.outputs['edges'].sv_set(edges_out)
        self.outputs['polygons'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvDualMeshNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvDualMeshNodeMK2)

