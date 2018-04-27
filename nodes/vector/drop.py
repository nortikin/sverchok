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
from mathutils import Matrix
import bmesh
from bmesh.ops import transform
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


class VectorDropNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Drop vertices depending on matrix, as on default rotation, drops to zero matrix '''
    bl_idname = 'VectorDropNode'
    bl_label = 'Vector Drop'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vectors")
        self.inputs.new('MatrixSocket', "Matrixes")
        self.outputs.new('VerticesSocket', "Vectors")

    def process(self):
        if not self.outputs['Vectors'].is_linked:
            return
        vecs = self.inputs['Vectors'].sv_get()
        out = []
        mats = self.inputs['Matrixes'].sv_get([Matrix()])
        for vertl, M in zip(vecs, mats):
            bm = bmesh.new()
            for v in vertl:
                bm.verts.new(v)
            transform(bm, matrix=M, verts=bm.verts)
            out.append([v.co[:] for v in bm.verts])
            bm.free()
        self.outputs['Vectors'].sv_set(out)


def register():
    bpy.utils.register_class(VectorDropNode)


def unregister():
    bpy.utils.unregister_class(VectorDropNode)
