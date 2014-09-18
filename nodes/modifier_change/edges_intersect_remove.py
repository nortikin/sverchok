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
from bpy.props import FloatProperty
from mathutils.geometry import intersect_line_line as LineIntersect
from mathutils.kdtree import KDTree

from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, SvGetSocketAnyType, updateNode
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


def make_kdtree(bm):
    size = len(bm.verts)
    kd = KDTree(size)

    for i, vtx in enumerate(bm.verts):
        kd.insert(vtx.co, i)
    kd.balance()
    return kd


def select_non_intersecting(bm, edge_indices, mdist):
    print('start permutation search')
    permutations = ei.get_valid_permutations(bm, edge_indices)
    print('found permutations!')

    # kd = make_kdtree(bm)
    drop_edges = set()

    for edges in permutations:
        '''
        for (co, index, dist) in kd.find_range(vtx, mdist):
            if i == index or (num_edges > 2):
                continue
            e.append([i, index])
        '''
        if set(edges).issubset(drop_edges):
            continue

        vert_indices = cm.vertex_indices_from_edges_tuple(bm, edges)
        v1, v2, v3, v4 = [bm.verts[i].co for i in vert_indices]

        mid_edge1 = (v1+v2) * 0.5
        mid_edge2 = (v3+v4) * 0.5
        distance = (mid_edge1 - mid_edge2).length

        if distance > mdist:
            continue

        # some can be skipped.    (NaN, None, not on both edges)
        points = LineIntersect(v1, v2, v3, v4)
        if not ei.can_skip(points, (v1, v2, v3, v4)):
            bm.edges[edges[0]].select = True
            bm.edges[edges[1]].select = True
            drop_edges.update(set(edges))


class SvNonIntersectEdgesNode(SvIntersectEdgesNode):

    bl_idname = 'SvNonIntersectEdgesNode'
    bl_label = 'Non Intersect Edges Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mdist = FloatProperty(default=0.2, update=updateNode)

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'mdist', text='seek distance')

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        if not (len(outputs) == 2):
            return
        if not outputs['Verts_out'].links:
            return
        if not (inputs['Verts_in'].links and inputs['Edges_in'].links):
            return

        self.process()

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        verts_in = inputs['Verts_in'].sv_get()[0]
        edges_in = inputs['Edges_in'].sv_get()[0]

        if not (verts_in and edges_in):
            return

        bm = self.make_bm(verts_in, edges_in)
        edge_indices = (e.index for e in bm.edges)  # generator expression

        select_non_intersecting(bm, edge_indices, self.mdist)

        verts_out = [v.co[:] for v in bm.verts]
        edges_out = [[j.index for j in i.verts] for i in bm.edges if not i.select]

        outputs['Verts_out'].sv_set([verts_out])
        outputs['Edges_out'].sv_set([edges_out])

    def make_bm(self, verts_in, edges_in):
        bm = bmesh.new()
        [bm.verts.new(co) for co in verts_in]
        bm.normal_update()
        [bm.edges.new((bm.verts[i], bm.verts[j])) for i, j in edges_in]
        bm.normal_update()
        return bm


def register():
    bpy.utils.register_class(SvNonIntersectEdgesNode)


def unregister():
    bpy.utils.unregister_class(SvNonIntersectEdgesNode)
