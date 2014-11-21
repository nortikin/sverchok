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
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from sverchok.data_structure import (updateNode)


class SvBMVertsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Verts '''
    bl_idname = 'SvBMVertsNode'
    bl_label = 'bmesh_verts'
    bl_icon = 'OUTLINER_OB_EMPTY'

    invert = BoolProperty(name='invert for props', description='invert output',
                          default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('VerticesSocket', 'Manifold')
        self.outputs.new('VerticesSocket', 'Wire')
        self.outputs.new('VerticesSocket', 'Boundary')
        self.outputs.new('StringsSocket', 'Vertex_Sharpness')

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "invert",   text="Invert")

    def process(self):
        manifold = []
        wire = []
        bound = []
        sharpness = []
        obj = self.inputs['Object'].sv_get()[0]
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.index_update()
        for i in bm.verts:
            if not self.invert:
                if i.is_manifold:
                    manifold.append(i.co[:])
                if i.is_wire:
                    wire.append(i.co[:])
                if i.is_boundary:
                    bound.append(i.co[:])
            else:
                if not i.is_manifold:
                    manifold.append(i.co[:])
                if not i.is_wire:
                    wire.append(i.co[:])
                if not i.is_boundary:
                    bound.append(i.co[:])

            sharpness.append(i.calc_shell_factor())

        bm.free()

        self.outputs['Manifold'].sv_set(manifold)
        self.outputs['Wire'].sv_set(wire)
        self.outputs['Boundary'].sv_set([bound])
        self.outputs['Vertex_Sharpness'].sv_set([sharpness])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBMVertsNode)


def unregister():
    bpy.utils.unregister_class(SvBMVertsNode)
