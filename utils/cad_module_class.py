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

import bmesh

from mathutils import Vector
from mathutils.geometry import intersect_line_line as LineIntersect
from mathutils.geometry import intersect_point_line as PtLineIntersect



class CAD_ops():


    def __init__(self, epsilon=1.0e-5, threshold=0.0001):
        self.VTX_PRECISION = epsilon
        self.VTX_DOUBLES_THRSHLD = threshold


    def point_on_edge(self, p, edge):
        '''
        > p:        vector
        > edge:     tuple of 2 vectors
        < returns:  True / False if a point happens to lie on an edge
        '''
        pt, _percent = PtLineIntersect(p, *edge)
        on_line = (pt-p).length < self.VTX_PRECISION
        return on_line and (0.0 <= _percent <= 1.0)


    def line_from_edge_intersect(self, edge1, edge2):
        '''
        > takes 2 tuples, each tuple contains 2 vectors
        - prepares input for sending to intersect_line_line
        < returns output of intersect_line_line
        '''
        [p1, p2], [p3, p4] = edge1, edge2
        return LineIntersect(p1, p2, p3, p4)


    def get_intersection(self, edge1, edge2):
        '''
        > takes 2 tuples, each tuple contains 2 vectors
        < returns the point halfway on line. See intersect_line_line
        '''
        line = self.line_from_edge_intersect(edge1, edge2)
        return (line[0] + line[1]) / 2


    def get_intersection_from_idxs(self, bm, idx1, idx2):
        '''
        > takes reference to bm and 2 indices
        < returns intersection or None
        '''
        p1, p2 = self.coords_tuple_from_edge_idx(bm, idx1)
        p3, p4 = self.coords_tuple_from_edge_idx(bm, idx2)
        a, b = LineIntersect(p1, p2, p3, p4)
        if (a-b).length < self.VTX_PRECISION:
            return a


    def test_coplanar(self, edge1, edge2):
        '''
        the line that describes the shortest line between the two edges
        would be short if the lines intersect mathematically. If this
        line is longer than the VTX_PRECISION then they are either
        coplanar or parallel.
        '''
        line = self.line_from_edge_intersect(edge1, edge2)
        return (line[0]-line[1]).length < self.VTX_PRECISION


    def closest_idx(self, pt, e):
        '''
        > pt:       vector
        > e:        bmesh edge
        < returns:  returns index of vertex closest to pt.

        if both points in e are equally far from pt, then v1 is returned.
        '''
        if isinstance(e, bmesh.types.BMEdge):
            ev = e.verts
            v1 = ev[0].co
            v2 = ev[1].co
            distance_test = (v1 - pt).length <= (v2 - pt).length
            return ev[0].index if distance_test else ev[1].index

        print("received {0}, check expected input in docstring ".format(e))


    def closest_vector(self, pt, e):
        '''
        > pt:       vector
        > e:        2 vector tuple
        < returns:
        pt, 2 vector tuple: returns closest vector to pt

        if both points in e are equally far from pt, then v1 is returned.
        '''
        if isinstance(e, tuple) and all([isinstance(co, Vector) for co in e]):
            v1, v2 = e
            distance_test = (v1 - pt).length <= (v2 - pt).length
            return v1 if distance_test else v2

        print("received {0}, check expected input in docstring ".format(e))


    def coords_tuple_from_edge_idx(self, bm, idx):
        ''' bm is a bmesh representation '''
        return tuple(v.co for v in bm.edges[idx].verts)


    def vectors_from_indices(self, bm, raw_vert_indices):
        ''' bm is a bmesh representation '''
        return [bm.verts[i].co for i in raw_vert_indices]


    def vertex_indices_from_edges_tuple(self, bm, edge_tuple):
        '''
        > bm:           is a bmesh representation
        > edge_tuple:   contains two edge indices.
        < returns the vertex indices of edge_tuple
        '''
        k = lambda v, w: bm.edges[edge_tuple[v]].verts[w].index
        return [k(i >> 1, i % 2) for i in range(4)]


    def num_edges_point_lies_on(self, pt, edges):
        ''' returns the number of edges that a point lies on. '''
        res = [self.point_on_edge(pt, edge) for edge in [edges[:2], edges[2:]]]
        return len([i for i in res if i])


    def find_intersecting_edges(self, bm, pt, idx1, idx2):
        '''
        > pt:           Vector
        > idx1, ix2:    edge indices,
        < returns the list of edge indices where pt is on those edges
        '''
        idxs = [idx1, idx2]
        edges = [self.coords_tuple_from_edge_idx(bm, idx) for idx in idxs]
        return [idx for edge, idx in zip(edges, idxs) if self.point_on_edge(pt, edge)]


    def duplicates(self, indices):
        return len(set(indices)) < 4


    def vert_idxs_from_edge_idx(self, bm, idx):
        edge = bm.edges[idx]
        return edge.verts[0].index, edge.verts[1].index
