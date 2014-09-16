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

import itertools
from collections import defaultdict

import bpy
import bmesh
from mathutils.geometry import intersect_line_line as LineIntersect

from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, SvGetSocketAnyType
from utils import cad_module as cm

from nodes.modifier_change import edges_intersect as ei
from nodes.modifier_change.edges_intersect import SvIntersectEdgesNode

'''
def order_points(edge, point_list):
def remove_permutations_that_share_a_vertex(bm, permutations):
def get_valid_permutations(bm, edge_indices):
def can_skip(closest_points, vert_vectors):
def get_intersection_dictionary(bm, edge_indices):
def update_mesh(bm, d):
def unselect_nonintersecting(bm, d_edges, edge_indices):
'''


def select_nonintersecting(bm, d_edges):
    for edge in d_edges:
        bm.edges[edge].select = True


class SvNonIntersectEdgesNode(SvIntersectEdgesNode):

    bl_idname = 'SvNonIntersectEdgesNode'
    bl_label = 'Non Intersect Edges Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # def draw_buttons(self, context, layout):
    #     pass

    # def init(self, context):
    #     self.inputs.new('VerticesSocket', 'Verts_in', 'Verts_in')
    #     self.inputs.new('StringsSocket', 'Edges_in', 'Edges_in')

    #     self.outputs.new('VerticesSocket', 'Verts_out', 'Verts_out')
    #     self.outputs.new('StringsSocket', 'Edges_out', 'Edges_out')

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        try:
            verts_in = SvGetSocketAnyType(self, inputs['Verts_in'])[0]
            edges_in = SvGetSocketAnyType(self, inputs['Edges_in'])[0]
            linked = outputs[0].links
        except (IndexError, KeyError) as e:
            return

        bm = bmesh.new()
        [bm.verts.new(co) for co in verts_in]
        bm.normal_update()
        [bm.edges.new((bm.verts[i], bm.verts[j])) for i, j in edges_in]
        bm.normal_update()

        edge_indices = [e.index for e in bm.edges]
        for edge in bm.edges:
            edge.select = False

        d = ei.get_intersection_dictionary(bm, edge_indices)
        select_nonintersecting(bm, d.keys())

        verts_out = [v.co.to_tuple() for v in bm.verts]
        edges_out = [[j.index for j in i.verts] for i in bm.edges if not i.select]

        SvSetSocketAnyType(self, 'Verts_out', [verts_out])
        SvSetSocketAnyType(self, 'Edges_out', [edges_out])

    # def update_socket(self, context):
    #     self.update()


def register():
    bpy.utils.register_class(SvNonIntersectEdgesNode)


def unregister():
    bpy.utils.unregister_class(SvNonIntersectEdgesNode)
