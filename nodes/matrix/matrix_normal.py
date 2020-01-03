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
from bpy.props import EnumProperty, BoolProperty
import mathutils
from mathutils import Vector, Matrix
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc, enum_item as e,Vector_generate, match_long_repeat)

def matrix_normal(params, T, U):
    loc, nor = params
    out = []
    nor = safc(loc, nor)
    for V, N in zip(loc, nor):
        n = N.to_track_quat(T, U)
        m = Matrix.Translation(V) @ n.to_matrix().to_4x4()
        out.append(m)
    return out

class SvMatrixNormalNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: M. from Loc & Normal
    Tooltip:  Construct a Matirx from  Location and Normal vectors

    """

    bl_idname = 'SvMatrixNormalNode'
    bl_label = 'Matrix normal'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_NORMAL'

    F = ['X', 'Y', 'Z', '-X', '-Y', '-Z']
    S = ['X', 'Y', 'Z']

    track: EnumProperty(name="track", default=F[4], items=e(F), update=updateNode)
    up: EnumProperty(name="up", default=S[2], items=e(S), update=updateNode)
    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location").use_prop = True
        self.inputs.new('SvVerticesSocket', "Normal").use_prop = True
        self.outputs.new('SvMatrixSocket', "Matrix")

    def draw_buttons(self, context, layout):
        layout.prop(self, "track", text="track")
        layout.prop(self, "up", text="up")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "track", text="track")
        layout.prop(self, "up", text="up")
        self.draw_buttons(context, layout)
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "track", text="Track:")
        layout.prop_menu_enum(self, "up", text="Up:")
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

    def process(self):
        Ma = self.outputs[0]
        if not Ma.is_linked:
            return
        L, N = self.inputs
        T, U = self.track, self.up
        loc = L.sv_get()
        nor = Vector_generate(N.sv_get())
        out = []
        m_add = out.extend if  self.flat_output else out.append
        params = match_long_repeat([loc, nor])

        for par in zip(*params):
            matrixes = matrix_normal(par, T, U)
            m_add(matrixes)
        Ma.sv_set(out)


def register():
    bpy.utils.register_class(SvMatrixNormalNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixNormalNode)
