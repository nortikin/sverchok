# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bmesh

from sverchok.utils.logging import debug, info

class SvQuadGridParser(object):
    """
    Parse a "bmesh" object, which contains a "quad grid", i.e.
    mesh consisting of quads only, in topology similar to subdivided plane (m x n vertices).
    Return vertices ordered row-by-row.
    Raise exception if the given mesh has invalid topology.
    """
    def __init__(self, bm):
        self.bmesh = bm
        self._init_check()
        self._init()

    def _init_check(self):
        # Run some checks that the mesh has correct topology.
        # Not all necessary conditions are checked here, only
        # simplest ones.
        for face in self.bmesh.faces:
            if len(face.verts) != 4:
                raise Exception(f"One of faces has {len(face.verts)} vertices instead of 4")
        corners_cnt = 0
        edges_cnt = 0
        for vert in self.bmesh.verts:
            if vert.is_wire:
                raise Exception("One of verts is a wire")
            k = len(vert.link_edges)
            if k not in {2,3,4}:
                raise Exception(f"One of vertices has {k} adjacent edges instead of 2,3,4")
            if k == 4 and vert.is_boundary:
                raise Exception("Vertex with 4 adjacent edges is boundary")
            if k != 4 and not vert.is_boundary:
                raise Exception(f"Vertex with {k} adjacent edges is not boundary")
            if k == 2:
                corners_cnt += 1
            if k == 3:
                edges_cnt += 1
        if corners_cnt != 4:
            raise Exception(f"Mesh has {corners_cnt} corners instead of 4")
        if edges_cnt % 2 != 0:
            raise Exception("Mesh has {edges_cnt} edge vertices, which does not divide by 2")
        for edge in self.bmesh.edges:
            k = len(edge.link_faces)
            if k not in {1,2}:
                raise Exception(f"One of edges has {k} adjacent faces instead of 1,2")
            if k == 2 and edge.is_boundary:
                raise Exception("Edge with 2 adjacent faces is boundary!?")
            if k == 1 and not edge.is_boundary:
                raise Exception("Edge with 1 adjacent face is not boundary!?")

    def _init(self):
        # Find a corner to start with.
        # We are searching for such a vertex and it's loop,
        # so the edge is pointing in positive X direction.
        # If we can't find such, then search for positive Y...
        self.row_length = None
        self.y_direction = False
        good_x = []
        good_y = []
        for vert in self.bmesh.verts:
            if len(vert.link_edges) == 2:
                for loop in vert.link_loops:
                    other_vert = loop.edge.other_vert(vert)
                    #info(f"V#{vert.index}: x {vert.co.x} => #{other_vert.index} {other_vert.co.x}")
                    if other_vert.co.x > vert.co.x:
                        good_x.append(loop)
                    if other_vert.co.y > vert.co.y:
                        good_y.append(loop)
        
        if good_x:
            loop = good_x[0]
        elif good_y:
            loop = good_y[0]
            self.y_direction = True
        else:
            raise Exception("Could not find a vertex to start from")

        vert = loop.vert
        #info(f"Start with v.{vert.index}, loop {self._show_loop(loop)}")
        self.current_loop = loop
        self.current_vert = vert
        self.start_loop = loop
        self.start_vert = vert

    def _reset(self):
        self.current_loop = self.start_loop
        self.current_vert = self.start_vert

    def _show_loop(self, loop):
        # Debug utility
        vert = loop.vert
        other_vert = loop.edge.other_vert(vert)
        return f"[{vert.index}->{other_vert.index}]({loop.face.index})"

    def _next_loop(self):
        # Find the next loop in "forward" direction
        start_k = len(self.current_vert.link_edges)
        next_loop = self.current_loop.link_loop_next
        k = len(next_loop.vert.link_edges)
        #info(f"> from {self._show_loop(self.current_loop)} => {self._show_loop(next_loop)}, k={k} (for v.{next_loop.vert.index}) of {self.row_start_k}")
        if k == self.row_start_k:
            loop = next_loop
        else:
            loop = next_loop.link_loop_radial_next.link_loop_next
        #info(f"> to {self._show_loop(loop)}")
        return loop

    def _prev_loop(self):
        # Find the next loop in "backward" direction.
        # This method is called only when processing the last row of vertices.
        start_k = len(self.current_vert.link_edges)
        next_loop = self.current_loop.link_loop_prev
        other_vert = next_loop.edge.other_vert(next_loop.vert)
        k = len(other_vert.link_edges)
        #info(f"< from {self._show_loop(self.current_loop)} => {self._show_loop(next_loop)}, k={k} for v.{other_vert.index}")
        if k == 2:
            loop = next_loop
        else:
            loop = next_loop.link_loop_radial_prev.link_loop_prev
        #info(f"< to {self._show_loop(loop)}")
        return loop

    def _step_forward(self):
        # Step to the next loop in row.
        self.current_loop = self._next_loop()
        self.current_vert = self.current_loop.vert

    def _step_backward(self):
        # Step to the previous loop in row.
        # This method is called only when processing the last loop of vertices.
        self.current_loop = self._prev_loop()
        self.current_vert = self.current_loop.vert

    def _walk_row_forward(self):
        # Walk along the row of vertices in "forward" direction.
        self.row_start_loop = self.current_loop
        self.row_start_vert = self.current_vert
        self.row_start_k = len(self.current_vert.link_edges)

        result = [self.current_vert.index]
        while True:
            self._step_forward()
            k = len(self.current_vert.link_edges)
            #info(f"> C: {self.current_vert.index}, k={k}")
            result.append(self.current_vert.index)
            if self.current_vert.is_boundary and k == self.row_start_k:
                break

        n = len(result)
        if self.row_length is None:
            self.row_length = n
        elif self.row_length != n:
            raise Exception(f"Row has length {n} instead of {self.row_length}")
        return result

    def _walk_row_backward(self):
        # Walk along the row of vertices in "backward" direction.
        # This method is called only when processing the last loop of vertices.
        if self.row_length is None:
            raise Exception("_walk_row_backward was called before setting row_length")

        self.row_start_loop = self.current_loop
        self.row_start_vert = self.current_vert
        self.row_start_k = len(self.current_vert.link_edges)

        edge = self.current_loop.edge
        vert = edge.other_vert(self.current_vert)
        result = [vert.index]
        for i in range(self.row_length-1):
            self._step_backward()
            k = len(self.current_vert.link_edges)
            #info(f"< C[{i}]: {self.current_vert.index}, k={k}")
            edge = self.current_loop.edge
            vert = edge.other_vert(self.current_vert)
            result.append(vert.index)

        n = len(result)
        if n == self.row_length - 1:
            result.append(self.current_vert.index)
        elif self.row_length != n:
            raise Exception(f"(Last) Row has length {n} ({result}) instead of {self.row_length}")
        return result

    def _next_row(self):
        # Go to the next row of vertices.
        # Return True if this row is the last one.
        self.current_loop = self.row_start_loop
        start_face_idx = self.current_loop.face.index
        loop = self.current_loop.link_loop_prev.link_loop_prev.link_loop_radial_next
        #info(f"N/: F {loop.face.index}, V {loop.vert.index}, E {self._show_loop(loop)}")
        self.current_loop = loop
        self.current_vert = self.current_loop.vert
        last = loop.face.index == start_face_idx
        return last

    def get_verts_sequence(self, flat=False):
        """
        Return list of lists of vertices indexes,
        sorted row-by-row.
        """
        result = []
        last = False
        while not last:
            row = self._walk_row_forward()
            result.append(row)
            last = self._next_row()

        row = self._walk_row_backward()
        result.append(row)

        if flat:
            result = sum(result, [])
        self._reset()
        return result

    def get_ordered_verts(self, flat=False):
        """
        Return list of lists of vertices coordinates,
        sorted row by row.
        If flat==True, then return flat list of vertices.
        """
        result = []
        for row_idxs in self.get_verts_sequence():
            row = [tuple(self.bmesh.verts[i].co) for i in row_idxs]
            if flat:
                result.extend(row)
            else:
                result.append(row)
        return result

