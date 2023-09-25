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

import collections

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode
from sverchok.utils.mesh.separate_loose_mesh import separate_loose_mesh


class SvSeparateMeshNode(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    '''Separate Loose mesh parts'''
    bl_idname = 'SvSeparateMeshNode'
    bl_label = 'Separate Loose Parts'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SEPARATE_LOOSE_PARTS'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Poly Egde')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Poly Egde')

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        verts = self.inputs['Vertices'].sv_get(deepcopy=False)
        poly = self.inputs['Poly Egde'].sv_get(deepcopy=False)
        verts_out = []
        poly_edge_out = []
        for ve, pe in zip_long_repeat(verts, poly):
            vo, po, _ = separate_loose_mesh(ve, pe)
            verts_out.extend(vo)
            poly_edge_out.extend(po)
            

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Poly Egde'].sv_set(poly_edge_out)


def register():
    bpy.utils.register_class(SvSeparateMeshNode)


def unregister():
    bpy.utils.unregister_class(SvSeparateMeshNode)
