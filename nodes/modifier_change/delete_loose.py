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

from itertools import chain

import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat


class SvDeleteLooseNode(bpy.types.Node, SverchCustomTreeNode):
    '''Delete vertices not used in face or edge'''

    bl_idname = 'SvDeleteLooseNode'
    bl_label = 'Delete Loose'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DELETE_LOOSE'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'PolyEdge')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'PolyEdge')
        self.outputs.new('SvStringsSocket', 'VertsMask')

    def process(self):
        
        # older versions of this node do not have a vertsmask socket. This upgrades them silently
        if not self.outputs.get('VertsMask'):
            self.outputs.new('SvStringsSocket', 'VertsMask')
        
        if not (all([s.is_linked for s in self.inputs]) and any([s.is_linked for s in self.outputs])):
            return
        verts = self.inputs['Vertices'].sv_get(deepcopy=False)
        poly_edge = self.inputs['PolyEdge'].sv_get(deepcopy=False)
        verts_out = []
        verts_mask_out = []
        poly_edge_out = []
        if len(poly_edge[0]) > 0 and len(poly_edge[0][0]) == 2:
            self.outputs['PolyEdge'].label = "Edges"
        else:
            self.outputs['PolyEdge'].label = "Polygons"

        for ve, pe in zip_long_repeat(verts, poly_edge):

            indx = set(chain.from_iterable(pe))
            verts_out.append([v for i, v in enumerate(ve) if i in indx])
            verts_mask_out.append([True if i in indx else False for i, v in enumerate(ve)])
            v_index = dict([(j, i) for i, j in enumerate(sorted(indx))])
            poly_edge_out.append([list(map(lambda n:v_index[n], p)) for p in pe])

        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(verts_out)
        if poly_edge_out:
            self.outputs['PolyEdge'].sv_set(poly_edge_out)
        if self.outputs['VertsMask'].is_linked:
            self.outputs['VertsMask'].sv_set(verts_mask_out)


def register():
    bpy.utils.register_class(SvDeleteLooseNode)


def unregister():
    bpy.utils.unregister_class(SvDeleteLooseNode)
