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
from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, SvGetSocketAnyType


class SvDeleteLooseNode(bpy.types.Node, SverchCustomTreeNode):
    '''Delete vertices not used in face or edge'''
    bl_idname = 'SvDeleteLooseNode'
    bl_label = 'Delete Loose'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.inputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')

        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')

    def update(self):

        if 'Vertices' in self.inputs and self.inputs['Vertices'].links and \
           'PolyEdge' in self.inputs and self.inputs['PolyEdge'].links:

            verts = SvGetSocketAnyType(self, self.inputs['Vertices'])
            poly_edge = SvGetSocketAnyType(self, self.inputs['PolyEdge'])
            verts_out = []
            poly_edge_out = []
            for ve, pe in zip(verts, poly_edge):

                # trying to remove indeces of polygons that more that length of
                # vertices list. But it doing wrong, ideces not mutch vertices...
                # what am i doing wrong?
                # i guess, i didn't understood this iterations at all

                delp = []
                for p in pe:
                    deli = []
                    for i in p:
                        if i >= len(ve):
                            deli.append(i)
                    if deli and (len(p)-len(deli)) >= 2:
                        print(deli)
                        for k in deli:
                            p.remove(k)
                    elif (len(p)-len(deli)) <= 1:
                        delp.append(p)
                if delp:
                    for d in delp:
                        pe.remove(d)

                indx = set(chain.from_iterable(pe))
                verts_out.append([v for i, v in enumerate(ve) if i in indx])
                v_index = dict([(j, i) for i, j in enumerate(sorted(indx))])
                poly_edge_out.append([list(map(lambda n:v_index[n], p)) for p in pe])

            if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices', verts_out)

            if 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].links:
                if poly_edge_out:
                    SvSetSocketAnyType(self, 'PolyEdge', poly_edge_out)
                else:
                    SvSetSocketAnyType(self, 'PolyEdge', [[[]]])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvDeleteLooseNode)


def unregister():
    bpy.utils.unregister_class(SvDeleteLooseNode)
