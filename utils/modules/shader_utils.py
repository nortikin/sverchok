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
        self.addv = self.vectors.extend
        self.addc = self.vertex_colors.extend
        self.addi = self.indices.extend

    def add_data(self, new_vectors=None, new_colors=None, new_indices=None):
        """
        input
            see `add_rect` for a reference implementation

            new_vectors:    a list of 2d vectors as lists
            new_colors:     a list of colors of the same length as new_vectors
            new_indices:    a list of indices to make up tri-face toplogy
                            this function automatically offsets the new_indices, so you only have to write
                            topology and such for one instance of your object
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
        a = (x, y)
        b = (x, y - h)
        c = (x + w, y - h)
        d = (x + w, y)

        self.add_data(
            new_vectors=[a, b, c, d], 
            new_colors=[color for _ in range(4)],
            new_indices=[[0, 1, 2], [0, 2, 3]]
        )

    def compile(self):
        geom = lambda: None
        geom.vectors = self.vectors
        geom.vertex_colors = self.vertex_colors
        geom.indices = self.indices
        return geom
