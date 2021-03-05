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

import math

from mathutils import Vector, Matrix

import bpy
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

def calc_mesh_normals(vertices, edges, faces):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    vertex_normals = []
    face_normals = []
    for vertex in bm.verts:
        vertex_normals.append(tuple(vertex.normal))
    for face in bm.faces:
        face_normals.append(tuple(face.normal.normalized()))
    bm.free()
    return face_normals, vertex_normals

class SvGetNormalsNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    ''' Calculate normals of faces and vertices '''
    bl_idname = 'SvGetNormalsNode'
    bl_label = 'Calculate normals2'
    bl_icon = 'SNAP_NORMAL'

    def sv_init(self, context):
        vs = self.inputs.new('SvVerticesSocket', "Vertices")
        vs.is_mandatory = True
        vs.nesting_level = 3
        vs.default_mode = 'NONE'
        
        eds = self.inputs.new('SvStringsSocket', "Edges")
        eds.nesting_level = 3

        pols = self.inputs.new('SvStringsSocket', "Polygons")
        pols.nesting_level = 3


        self.outputs.new('SvVerticesSocket', "FaceNormals")
        self.outputs.new('SvVerticesSocket', "VertexNormals")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'list_match')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def process_data(self, params):
        vertices, edges, faces = params
        verts_normal, faces_normal = [], []
        for v, e, p in zip(vertices, edges, faces):
            f_nor, v_nor = calc_mesh_normals(v, e, p)
            verts_normal.append(v_nor)
            faces_normal.append(f_nor)
        return faces_normal, verts_normal

def register():
    bpy.utils.register_class(SvGetNormalsNode)


def unregister():
    bpy.utils.unregister_class(SvGetNormalsNode)
