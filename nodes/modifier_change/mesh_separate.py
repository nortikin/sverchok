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
from sverchok.data_structure import SvSetSocketAnyType, SvGetSocketAnyType


class SvSeparateMeshNode(bpy.types.Node, SverchCustomTreeNode):
    '''Separate Loose mesh parts'''
    bl_idname = 'SvSeparateMeshNode'
    bl_label = 'Separate Loose'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'Poly Egde')

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Poly Egde')

    def process(self):
        # check that there is atleast one output connected
        if not any((s.links for s in self.outputs)):
            return
        if self.inputs['Vertices'].links and self.inputs['Poly Egde'].links:

            verts = SvGetSocketAnyType(self, self.inputs['Vertices'])
            poly = SvGetSocketAnyType(self, self.inputs['Poly Egde'])
            verts_out = []
            poly_edge_out = []
            for ve, pe in zip(verts, poly):
                # build links
                node_links = {}
                for edge_face in pe:
                    for i in edge_face:
                        if i not in node_links:
                            node_links[i] = set()
                        node_links[i].update(edge_face)

                nodes = set(node_links.keys())
                n = nodes.pop()
                node_set_list = [set([n])]
                node_stack = collections.deque()
                node_stack_append = node_stack.append
                node_stack_pop = node_stack.pop
                node_set = node_set_list[-1]
                # find separate sets
                while nodes:
                    for node in node_links[n]:
                        if node not in node_set:
                            node_stack_append(node)
                    if not node_stack:  # new mesh part
                        n = nodes.pop()
                        node_set_list.append(set([n]))
                        node_set = node_set_list[-1]
                    else:
                        while node_stack and n in node_set:
                            n = node_stack_pop()
                        nodes.discard(n)
                        node_set.add(n)
                # create new meshes from sets, new_pe is the slow line.
                if len(node_set_list) > 1:
                    for node_set in node_set_list:
                        mesh_index = sorted(node_set)
                        vert_dict = {j: i for i, j in enumerate(mesh_index)}
                        new_vert = [ve[i] for i in mesh_index]
                        new_pe = [[vert_dict[n] for n in fe]
                                  for fe in pe
                                  if fe[0] in node_set]
                        verts_out.append(new_vert)
                        poly_edge_out.append(new_pe)
                elif node_set_list:  # no reprocessing needed
                    verts_out.append(ve)
                    poly_edge_out.append(pe)

            if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices', verts_out)

            if 'Poly Egde' in self.outputs and self.outputs['Poly Egde'].links:
                if poly_edge_out:
                    SvSetSocketAnyType(self, 'Poly Egde', poly_edge_out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvSeparateMeshNode)


def unregister():
    bpy.utils.unregister_class(SvSeparateMeshNode)
