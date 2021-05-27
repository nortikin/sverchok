# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils import Vector

class ShaderLib2D():
    def __init__(self):
        """
        docstring ?
        """
        self.can_use_cache = False
        self.vectors = []
        self.vertex_colors = []
        self.indices = []
        self.addv = self.vectors.extend
        self.addc = self.vertex_colors.extend
        self.addi = self.indices.extend

    def use_cached_canvas(self, geom):
        self.add_data(geom.vectors, geom.vertex_colors, geom.indices)
        self.can_use_cache = True

    def add_data(self, new_vectors=None, new_colors=None, new_indices=None):
        """
        input
            see `add_rect` for a reference implementation

            new_vectors:    a list of 2d vectors as lists
            new_colors:     a list of colors of the same length as new_vectors
            new_indices:    a list of indices to make up tri-face topology
                            this function automatically offsets the new_indices, so you only have to write
                            topology for one instance of your object
        """
        offset = len(self.vectors)
        self.addv(new_vectors)
        self.addc(new_colors)
        self.addi([[offset + i for i in tri] for tri in new_indices])

    def add_rect(self, x, y, w, h, color):
        """
        b - c
        | / |
        a - d
        """
        if self.can_use_cache: return

        a = (x, y)
        b = (x, y - h)
        c = (x + w, y - h)
        d = (x + w, y)

        self.add_data(
            new_vectors=[a, b, c, d], 
            new_colors=[color for _ in range(4)],
            new_indices=[[0, 1, 2], [0, 2, 3]]
        )

    def add_rect_rounded(self, x, y, w, h, color, radius=0, precision=5):
        ...

    def add_line(self, x1, y1, x2, y2, width, color):

        p1 = Vector((x1, y1))
        p2 = Vector((x2, y2))
        v = (p2 - p1).normalized()
        vp = v.orthogonal()
        offset = (width / 2 * vp)
        a = p1 + offset
        b = p1 - offset
        c = p2 - offset
        d = p2 + offset

        self.add_data(
            new_vectors=[a, b, c, d], 
            new_colors=[color for _ in range(4)],
            new_indices=[[0, 1, 2], [0, 2, 3]]
        )

    def add_polyline(self, path, width, color):
        ...

    def add_bezier(self, controls, width, color, samples=20, resampled=False):
        ...

    def add_circle(self, x, y, radius, color, precision=32):
        ...

    def add_arc(self, x, y, start_angle, end_angle, radius, width, color, precision=32):
        ...

    def compile(self):
        geom = lambda: None
        geom.vectors = self.vectors
        geom.vertex_colors = self.vertex_colors
        geom.indices = self.indices
        return geom
