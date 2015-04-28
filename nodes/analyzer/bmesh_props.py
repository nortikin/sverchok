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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


def get_value(self, b, V):
        bv = getattr(b, self.Mod)
        elem = getattr(self, self.Mod)
        V.append(eval("[i."+elem+" for i in bv]"))
        return V


def Obm(m):
        m = [(i,i,"") for i in m]
        return m


class SvBMVertsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Verts '''
    bl_idname = 'SvBMVertsNode'
    bl_label = 'bmesh_props'
    bl_icon = 'OUTLINER_OB_EMPTY'

    Modes = ['verts','faces','edges']
    Mod = EnumProperty(name="getmodes", default="verts", items=Obm(Modes), update=updateNode)
    a = ['hide','select']
    PV = a + ['is_manifold','is_wire','is_boundary','calc_shell_factor()','calc_edge_angle(-1)']
    PF = a + ['calc_area()','calc_perimeter()','material_index','smooth']
    PE = a + ['calc_face_angle()','calc_face_angle_signed()','calc_length()','is_boundary','is_contiguous','is_convex','is_manifold','is_wire','seam']
    verts = EnumProperty(name="Vprop", default="is_manifold", items=Obm(PV), update=updateNode)
    faces = EnumProperty(name="Fprop", default="select", items=Obm(PF), update=updateNode)
    edges = EnumProperty(name="Eprop", default="select", items=Obm(PE), update=updateNode)

    def sv_init(self, context):
        si = self.inputs.new
        si('StringsSocket', 'Objects')
        si('VerticesSocket', 'Vert')
        si('StringsSocket', 'Edge')
        si('StringsSocket', 'Poly')
        self.outputs.new('StringsSocket', 'Value')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Mod", "Get")
        layout.prop(self, self.Mod, "")

    def process(self):
        Val = []
        siob = self.inputs['Objects']
        sive = self.inputs['Vert']
        sied = self.inputs['Edge']
        sipo = self.inputs['Poly']

        if siob.is_linked: # or siob.object_ref:
            obj = siob.sv_get()
            for OB in obj:
                bm = bmesh.new()
                bm.from_mesh(OB.data)
                get_value(self, bm, Val)
                bm.free()
        if sive.is_linked:
            g = 0
            while g != len(sive.sv_get()):
                bm = bmesh_from_pydata(sive.sv_get()[g],
                                       sied.sv_get()[g] if sied.is_linked else [],
                                       sipo.sv_get()[g] if sipo.is_linked else [])
                get_value(self, bm, Val)
                bm.free()
                g = g+1

        self.outputs['Value'].sv_set(Val)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBMVertsNode)


def unregister():
    bpy.utils.unregister_class(SvBMVertsNode)
