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
from bpy.props import EnumProperty
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import (updateNode)


class SvBMVertsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Verts '''
    bl_idname = 'SvBMVertsNode'
    bl_label = 'bmesh_verts'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
        ("manifold",   "Manifold",   "", 1),
        ("wire",   "Wire",   "", 2),
        ("bound",   "Boundary",   "", 3),
        ("sel",   "Selected",   "", 4),
        ("sharpness",   "Verts Sharpness",   "", 5),
        ("angle",   "Angle (Two Edges)",   "", 6),
    ]

    Modes = EnumProperty(name="getmodes", description="Get Property modes",
                         default="manifold", items=modes, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('VerticesSocket', 'Vert')
        self.inputs.new('StringsSocket', 'Edge')
        self.inputs.new('StringsSocket', 'Poly')
        self.outputs.new('StringsSocket', 'Value')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        layout.prop(self, "Modes", "Get Verts")

    def process(self):
        Val = []

        if self.inputs['Object'].is_linked or self.inputs['Object'].object_ref:
            obj = self.inputs['Object'].sv_get()
            for OB in obj:
                bm = bmesh.new()
                bm.from_mesh(OB.data)
                bm.verts.index_update()
                if self.Modes == 'manifold':
                    Val.append([i.index for i in bm.verts if i.is_manifold])
                elif self.Modes == 'wire':
                    Val.append([i.index for i in bm.verts if i.is_wire])
                elif self.Modes == 'bound':
                    Val.append([i.index for i in bm.verts if i.is_boundary])
                elif self.Modes == 'sel':
                    Val.append([i.index for i in bm.verts if i.select])
                elif self.Modes == 'sharpness':
                    Val.append([i.calc_shell_factor() for i in bm.verts])
                elif self.Modes == 'angle':
                    Val.append([i.calc_vert_angle() for i in bm.verts])
                bm.free()
        if self.inputs['Vert'].is_linked:
            V = self.inputs['Vert'].sv_get()
            E = self.inputs['Edge'].sv_get() if self.inputs['Edge'].is_linked else [[]]
            P = self.inputs['Poly'].sv_get() if self.inputs['Poly'].is_linked else [[]]
            g = 0
            while g != len(V):
                bm = bmesh_from_pydata(V[g], E[g], P[g])
                bm.verts.index_update()
                if self.Modes == 'manifold':
                    Val.append([i.index for i in bm.verts if i.is_manifold])
                elif self.Modes == 'wire':
                    Val.append([i.index for i in bm.verts if i.is_wire])
                elif self.Modes == 'bound':
                    Val.append([i.index for i in bm.verts if i.is_boundary])
                elif self.Modes == 'sel':
                    Val.append([i.index for i in bm.verts if i.select])
                elif self.Modes == 'sharpness':
                    Val.append([i.calc_shell_factor() for i in bm.verts])
                elif self.Modes == 'angle':
                    Val.append([i.calc_vert_angle() for i in bm.verts])
                bm.free()
                g = g+1

        self.outputs['Value'].sv_set(Val)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBMVertsNode)


def unregister():
    bpy.utils.unregister_class(SvBMVertsNode)
