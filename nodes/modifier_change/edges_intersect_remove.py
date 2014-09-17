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


def get_nonintersection_dictionary(bm, edge_indices):
    permutations = ei.get_valid_permutations(bm, edge_indices)

    k = defaultdict(list)
    d = defaultdict(list)

    for edges in permutations:
        raw_vert_indices = cm.vertex_indices_from_edges_tuple(bm, edges)
        vert_vectors = cm.vectors_from_indices(bm, raw_vert_indices)

        points = LineIntersect(*vert_vectors)

        # some can be skipped.    (NaN, None, not on both edges)
        if ei.can_skip(points, vert_vectors):
            continue

        # reaches this point only when an intersection happens on both edges.
        [k[edge].append(points[0]) for edge in edges]

    # k will contain a dict of edge indices and points found on those edges.
    for edge_idx, unordered_points in k.items():
        tv1, tv2 = bm.edges[edge_idx].verts
        v1 = bm.verts[tv1.index].co
        v2 = bm.verts[tv2.index].co
        ordered_points = ei.order_points((v1, v2), unordered_points)
        d[edge_idx].extend(ordered_points)

    return d


class SvNonIntersectEdgesNode(SvIntersectEdgesNode):

    bl_idname = 'SvNonIntersectEdgesNode'
    bl_label = 'Non Intersect Edges Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        if not (len(outputs) == 2):
            return

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

        d = get_nonintersection_dictionary(bm, edge_indices)
        select_nonintersecting(bm, d.keys())

        verts_out = [v.co.to_tuple() for v in bm.verts]
        edges_out = [[j.index for j in i.verts] for i in bm.edges if not i.select]

        SvSetSocketAnyType(self, 'Verts_out', [verts_out])
        SvSetSocketAnyType(self, 'Edges_out', [edges_out])


def register():
    bpy.utils.register_class(SvNonIntersectEdgesNode)


def unregister():
    bpy.utils.unregister_class(SvNonIntersectEdgesNode)
