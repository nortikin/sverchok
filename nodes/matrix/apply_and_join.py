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
from bpy.props import BoolProperty
from mathutils import Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode, VerticesSocket, MatrixSocket
from sverchok.data_structure import (Vector_generate, Vector_degenerate,
                            Matrix_generate, updateNode)
from sverchok.utils.sv_mesh_utils import mesh_join


class SvMatrixApplyJoinNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Multiply vectors on matrices with several objects in output,
        and process edges & faces too '''
    bl_idname = 'SvMatrixApplyJoinNode'
    bl_label = 'Apply matrix to mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'

    do_join = BoolProperty(name='Join',
            description = 'Join resulting meshes to one mesh',
            default=True,
            update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Faces")
        self.inputs.new('MatrixSocket', "Matrices")

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Faces")

    def draw_buttons(self, context, layout):
        layout.prop(self, "do_join")

    def process(self):
        if not self.outputs['Vertices'].is_linked:
            return

        vertices = self.inputs['Vertices'].sv_get()
        vertices = Vector_generate(vertices)
        edges = self.inputs['Edges'].sv_get(default=[[]])
        faces = self.inputs['Faces'].sv_get(default=[[]])

        matrices = self.inputs['Matrices'].sv_get()
        matrices = Matrix_generate(matrices)
        n = len(matrices)

        result_vertices = self.apply(vertices, matrices)
        result_vertices = Vector_degenerate(result_vertices)

        self.outputs['Vertices'].sv_set(result_vertices)

        if self.outputs['Edges'].is_linked or self.outputs['Faces'].is_linked:
            result_edges = edges * n
            result_faces = faces * n

            if self.do_join:
                result_vertices, result_edges, result_faces = mesh_join(result_vertices, result_edges, result_faces)

            if self.outputs['Edges'].is_linked:
                self.outputs['Edges'].sv_set(result_edges)
            if self.outputs['Faces'].is_linked:
                self.outputs['Faces'].sv_set(result_faces)

    def apply(self, vecs, mats):
        out = []
        lengthve = len(vecs)-1
        for i, m in enumerate(mats):
            out_ = []
            k = i
            if k > lengthve:
                k = lengthve
            for v in vecs[k]:
                out_.append(m*v)
            out.append(out_)
        return out

def register():
    bpy.utils.register_class(SvMatrixApplyJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixApplyJoinNode)

