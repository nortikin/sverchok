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
from mathutils import Matrix, Vector

from bpy.props import IntProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Vector_generate, updateNode,
                                     match_long_repeat)
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata, dual_mesh

class SvDualMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Trigers: Dual Mesh
    Tooltip: Create dual mesh for the given mesh
    """
    bl_idname = 'SvDualMeshNode'
    bl_label = "Dual Mesh"
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        if not any((s.is_linked for s in self.outputs)):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get()

        verts_out = []
        faces_out = []

        objects = match_long_repeat([verts_s, edges_s, faces_s])
        for verts, edges, faces in zip(*objects):
            bm = bmesh_from_pydata(verts, edges, faces)
            new_verts, new_faces = dual_mesh(bm)
            bm.free()
            new_verts = [tuple(v) for v in new_verts]
            verts_out.append(new_verts)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvDualMeshNode)


def unregister():
    bpy.utils.unregister_class(SvDualMeshNode)

