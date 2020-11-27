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
from sverchok.data_structure import updateNode

class SvSeparateMeshNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    '''Separate Loose mesh parts'''
    bl_idname = 'SvSeparateMeshNodeMK2'
    bl_label = 'Separate Loose Parts MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SEPARATE_LOOSE_PARTS'

    join : bpy.props.BoolProperty(
        name = "Flat output",
        description = "If checked, generate one flat list of loose parts for all input meshes; otherwise, generate separate list of loose parts for each input mesh",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'join')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Poly Egde')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Poly Egde')
        self.outputs.new('SvStringsSocket', 'Vert idx')
        self.outputs.new('SvStringsSocket', 'Poly Egde idx')

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        verts = self.inputs['Vertices'].sv_get()
        poly = self.inputs['Poly Egde'].sv_get()
        verts_out = []
        poly_edge_out = []

        vert_index = []
        poly_edge_index = []

        for ve, pe in zip(verts, poly):
            new_verts = []
            new_polys = []
            new_vert_indexes = []
            new_poly_indexes = []

            # build links
            node_links = collections.defaultdict(set)
            for edge_face in pe:
                for i in edge_face:
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
                node_set_list.sort(key=lambda x: min(x))
                for idx, node_set in enumerate(node_set_list):
                    mesh_index = sorted(node_set)
                    vert_dict = {j: i for i, j in enumerate(mesh_index)}
                    new_vert = [ve[i] for i in mesh_index]
                    new_pe = [[vert_dict[n] for n in fe]
                              for fe in pe
                              if fe[0] in node_set]

                    new_verts.append(new_vert)
                    new_polys.append(new_pe)
                    new_vert_indexes.append([idx for i in range(len(new_vert))])
                    new_poly_indexes.append([idx for face in new_pe])
            elif node_set_list:  # no reprocessing needed
                new_verts.append(ve)
                new_polys.append(pe)
                new_vert_indexes.append([0 for i in range(len(ve))])
                new_poly_indexes.append([0 for face in pe])

            if self.join:
                verts_out.extend(new_verts)
                poly_edge_out.extend(new_polys)
                vert_index.extend(new_vert_indexes)
                poly_edge_index.extend(new_poly_indexes)
            else:
                verts_out.append(new_verts)
                poly_edge_out.append(new_polys)
                vert_index.append(new_vert_indexes)
                poly_edge_index.append(new_poly_indexes)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Poly Egde'].sv_set(poly_edge_out)
        self.outputs['Vert idx'].sv_set(vert_index)
        self.outputs['Poly Egde idx'].sv_set(poly_edge_index)


def register():
    bpy.utils.register_class(SvSeparateMeshNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvSeparateMeshNodeMK2)
