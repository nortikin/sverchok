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
import bmesh
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import (updateNode)


class SvBMVertsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Verts '''
    bl_idname = 'SvBMVertsNode'
    bl_label = 'bmesh_verts'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('StringsSocket', 'Manifold')
        self.outputs.new('StringsSocket', 'Wire')
        self.outputs.new('StringsSocket', 'Boundary')
        self.outputs.new('StringsSocket', 'Selected')
        self.outputs.new('StringsSocket', 'Two Edges Angle')
        self.outputs.new('StringsSocket', 'Vertex_Sharpness')

    def process(self):
        manifold = []
        wire = []
        bound = []
        sharpness = []
        sel = []
        angle = []
        obj = self.inputs['Object'].sv_get()
        for OB in obj:
            bm = bmesh.new()
            bm.from_mesh(OB.data)
            bm.verts.index_update()

            manifold.append([i.index for i in bm.verts if i.is_manifold])
            wire.append([i.index for i in bm.verts if i.is_wire])
            bound.append([i.index for i in bm.verts if i.is_boundary])
            sel.append([i.index for i in bm.verts if i.select])
            sharpness.append([i.calc_shell_factor() for i in bm.verts])
            angle.append([i.calc_vert_angle() for i in bm.verts])

            bm.free()

        out = self.outputs
        out['Manifold'].sv_set(manifold)
        out['Wire'].sv_set(wire)
        out['Boundary'].sv_set(bound)
        out['Selected'].sv_set(sel)
        out['Two Edges Angle'].sv_set(angle)
        out['Vertex_Sharpness'].sv_set(sharpness)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBMVertsNode)


def unregister():
    bpy.utils.unregister_class(SvBMVertsNode)
