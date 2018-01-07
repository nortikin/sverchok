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
from bpy.props import IntProperty
import bmesh.ops
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


class SvUnsubdivideNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Unsubivide vertices if possible '''
    bl_idname = 'SvUnsubdivideNode'
    bl_label = 'Unsubdivide'
    bl_icon = 'OUTLINER_OB_EMPTY'

    iteration = IntProperty(default=1, min=1, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Verts')
        self.inputs.new('StringsSocket', 'Edges')
        self.inputs.new('StringsSocket', 'Polys')
        self.outputs.new('VerticesSocket', 'Verts')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polys')

    def draw_buttons(self, context, layout):
        layout.prop(self, "iteration")

    def process(self):
        Ve, Ed, Fa = self.inputs
        Ov, Oe, Op = self.outputs
        if Ov.is_linked:
            verts = Ve.sv_get()
            edges = Ed.sv_get([[]])
            faces = Fa.sv_get([[]])
            meshes = match_long_repeat([verts, edges, faces])
            r_verts = []
            r_edges = []
            r_faces = []
            for verts, edges, faces in zip(*meshes):
                bm = bmesh_from_pydata(verts, edges, faces, normal_update=True)
                bmesh.ops.unsubdivide(bm, verts=bm.verts, iterations=self.iteration)
                new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
                bm.free()
                r_verts.append(new_verts)
                r_edges.append(new_edges)
                r_faces.append(new_faces)
            Ov.sv_set(r_verts)
            Oe.sv_set(r_edges)
            Op.sv_set(r_faces)


def register():
    bpy.utils.register_class(SvUnsubdivideNode)


def unregister():
    bpy.utils.unregister_class(SvUnsubdivideNode)
