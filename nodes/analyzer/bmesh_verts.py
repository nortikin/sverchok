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
        si = self.inputs.new
        si('SvObjectSocket', 'Object')
        si('VerticesSocket', 'Vert')
        si('StringsSocket', 'Edge')
        si('StringsSocket', 'Poly')
        self.outputs.new('StringsSocket', 'Value')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Modes", "Get Verts")

    def process(self):
        Val = []
        siob = self.inputs['Object']
        sive = self.inputs['Vert']
        sied = self.inputs['Edge']
        sipo = self.inputs['Poly']

        if siob.is_linked or siob.object_ref:
            obj = siob.sv_get()
            for OB in obj:
                sm = self.Modes
                bm = bmesh.new()
                bm.from_mesh(OB.data)
                bv = bm.verts
                bv.index_update()
                if sm == 'manifold':
                    Val.append([i.index for i in bv if i.is_manifold])
                elif sm == 'wire':
                    Val.append([i.index for i in bv if i.is_wire])
                elif sm == 'bound':
                    Val.append([i.index for i in bv if i.is_boundary])
                elif sm == 'sel':
                    Val.append([i.index for i in bv if i.select])
                elif sm == 'sharpness':
                    Val.append([i.calc_shell_factor() for i in bv])
                elif sm == 'angle':
                    Val.append([i.calc_vert_angle() for i in bv])
                bm.free()
        if sive.is_linked:
            g = 0
            while g != len(sive.sv_get()):
                bm = bmesh_from_pydata(sive.sv_get()[g],
                                       sied.sv_get()[g] if sied.is_linked else [],
                                       sipo.sv_get()[g] if sipo.is_linked else [])
                bv = bm.verts
                sm = self.Modes
                bv.index_update()
                if sm == 'manifold':
                    Val.append([i.index for i in bv if i.is_manifold])
                elif sm == 'wire':
                    Val.append([i.index for i in bv if i.is_wire])
                elif sm == 'bound':
                    Val.append([i.index for i in bv if i.is_boundary])
                elif sm == 'sel':
                    Val.append([i.index for i in bv if i.select])
                elif sm == 'sharpness':
                    Val.append([i.calc_shell_factor() for i in bv])
                elif sm == 'angle':
                    Val.append([i.calc_vert_angle() for i in bv])
                bm.free()
                g = g+1

        self.outputs['Value'].sv_set(Val)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBMVertsNode)


def unregister():
    bpy.utils.unregister_class(SvBMVertsNode)
