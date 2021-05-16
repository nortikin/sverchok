# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

class ShaderLib2D():
    def __init__(self):
        """
        docstring ?
        """
        self.vectors = []
        self.vertex_colors = []
        self.indices = []

    def add_rect(self, x, y, w, h, color):
        addv = self.vectors.extend
        addc = self.vertex_colors.extend
        addi = self.indices.extend
        """
        b - c
        | / |
        a - d
        """
        a = (x, y)
        b = (x, y - h)
        c = (x + w, y - h)
        d = (x + w, y)
        offset = len(self.vectors)
        addv([a, b, c, d])
        addc([color for _ in range(4)])
        addi([[offset + i for i in tri] for tri in [[0, 1, 2], [0, 2, 3]]])

    def compile(self):
        geom = lambda: None
        geom.vectors = self.vectors
        geom.vertex_colors = self.vertex_colors
        geom.indices = self.indices
        return geom
