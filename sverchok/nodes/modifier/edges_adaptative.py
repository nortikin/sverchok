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
from mathutils import Matrix

from bpy.props import BoolProperty
from node_tree import SverchCustomTreeNode
from data_structure import (Vector_generate,
                            SvSetSocketAnyType, SvGetSocketAnyType,
                            updateNode)


class SvAdaptiveEdgeNode(bpy.types.Node, SverchCustomTreeNode):
    '''Map edge object to recipent edges'''
    bl_idname = 'SvAdaptiveEdgeNode'
    bl_label = 'Adaptive Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mesh_join = BoolProperty(name="Join meshes", default=True,
                            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mesh_join")

    def init(self, context):
        self.inputs.new('VerticesSocket', 'VersR', 'VersR')
        self.inputs.new('StringsSocket', 'EdgeR', 'EdgeR')
        self.inputs.new('VerticesSocket', 'VersD', 'VersD')
        self.inputs.new('StringsSocket', 'EdgeD', 'EdgeD')

        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges', 'Edges')

    def update(self):
        if not 'Edges' in self.outputs:
            return
        if not all((s.links for s in self.inputs)):
            return
        if not any((s.links for s in self.outputs)):
            return

        versR = Vector_generate(SvGetSocketAnyType(self, self.inputs['VersR']))
        versD = Vector_generate(SvGetSocketAnyType(self, self.inputs['VersD']))
        edgeR = SvGetSocketAnyType(self, self.inputs['EdgeR'])
        edgeD = SvGetSocketAnyType(self, self.inputs['EdgeD'])
        verts_out = []
        edges_out = []
        mesh_join = self.mesh_join
        # only first obj
        verD = [v - versD[0][0] for v in versD[0]]
        edgD = edgeD[0]
        d_vector = verD[-1].copy()
        d_scale = d_vector.length
        d_vector.normalize()
        for vc, edg in zip(versR, edgeR):
            if mesh_join:
                v_out = []
                v_out_app = v_out.append
            e_out = []
            e_out_app = e_out.append

            for e in edg:
                if not mesh_join:
                    v_out = []
                    v_out_app = v_out.append
                e_vector = vc[e[1]] - vc[e[0]]
                e_scale = e_vector.length
                e_vector.normalize()
                q1 = d_vector.rotation_difference(e_vector)
                mat_s = Matrix.Scale(e_scale / d_scale, 4)
                mat_r = Matrix.Rotation(q1.angle, 4, q1.axis)
                mat_l = Matrix.Translation(vc[e[0]])
                mat = mat_l * mat_r * mat_s

                offset = len(v_out)
                for v in verD:
                    v_out_app((mat * v)[:])
                if mesh_join:
                    for edge in edgD:
                        e_out_app([i + offset for i in edge])
                else:
                    verts_out.append(v_out)
                    edges_out.append(edgD)
            if mesh_join:
                verts_out.append(v_out)
                edges_out.append(e_out)

        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            SvSetSocketAnyType(self, 'Vertices', verts_out)

        if 'Edges' in self.outputs and self.outputs['Edges'].links:
            SvSetSocketAnyType(self, 'Edges', edges_out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvAdaptiveEdgeNode)


def unregister():
    bpy.utils.unregister_class(SvAdaptiveEdgeNode)
