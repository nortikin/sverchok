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
from bpy.props import EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode

from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)


class SvSetCustomMeshNormals(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' Set custom normals for verts or loops '''
    bl_idname = 'SvSetCustomMeshNormals'
    bl_label = 'Set Custom Normals'
    bl_icon = 'SNAP_NORMAL'
    sv_icon = 'SV_CUSTOM_NORMALS'

    modes = [
        ("per_Vert", "per Vert", "", 1),
        ("per_Loop", "per Loop", "", 2)
        ]

    mode: EnumProperty(items=modes, default='per_Vert', update=updateNode)

    def draw_buttons(self, context, layout):
        self.animatable_buttons(layout, icon_only=True)
        layout.prop(self, "mode", expand=True)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('SvVerticesSocket', 'custom_normal')

    def process(self):
        O, Vnorm = self.inputs
        objml = [ob.data for ob in O.sv_get()]
        if Vnorm.is_linked:
            if self.mode == 'per_Vert':
                for obm, norml in zip(objml, Vnorm.sv_get()):
                    obm.use_auto_smooth = True
                    obm.normals_split_custom_set_from_vertices(safc(obm.vertices[:], norml))
            else:   # per loop
                for obm, norml in zip(objml, Vnorm.sv_get()):
                    obm.use_auto_smooth = True
                    obm.normals_split_custom_set(safc(obm.loops[:], norml))


def register():
    bpy.utils.register_class(SvSetCustomMeshNormals)


def unregister():
    bpy.utils.unregister_class(SvSetCustomMeshNormals)
