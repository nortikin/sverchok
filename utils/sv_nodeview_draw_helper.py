# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from mathutils import Matrix

from sverchok.settings import get_params
from sverchok.utils.geom import grid

# pylint: disable=c0111
# pylint: disable=c0103


class SvNodeViewDrawMixin():

    @property
    def xy_offset(self):
        a = self.location[:]
        b = int(self.width) + 20
        return int(a[0] + b), int(a[1])

    @staticmethod
    def get_preferences():
        # supplied with default, forces at least one value :)
        props = get_params({
            'render_scale': 1.0,
            'render_location_xy_multiplier': 1.0})
        return props.render_scale, props.render_location_xy_multiplier

    def adjust_position_and_dimensions(self, x, y, width, height):
        scale, multiplier = self.get_preferences()
        x, y = [x * multiplier, y * multiplier]
        width, height = [width * scale, height * scale]
        return x, y, width, height



def faces_from_xy(ncx, ncy):
    r"""
    this splits up the quad from geom.grid to triangles

                (ABCD)                   (ABC, ACD)

    go from:    A - - - D           to    A        A - D 
                |       |                 | \       \  |
                |       |                 |  \       \ |
                B - - - C                 B - C        C

    """
    faces = []
    add = faces.append
    pattern = np.array([0, ncx+1, ncx+2, 1])
    for row in range(ncy):
        for col in range(ncx):
            x_offset = ((ncx+1) * row) + col
            quad = (pattern + x_offset).tolist()
            add((quad[0], quad[1], quad[2]))
            add((quad[0], quad[2], quad[3]))
    return faces

def get_console_grid(char_width, char_height, num_chars_x, num_chars_y):
    num_verts_x = num_chars_x + 1
    num_verts_y = num_chars_y + 1
    
    X = np.linspace(0, num_chars_x*char_width, num_verts_x)
    Y = np.linspace(0, -num_chars_y*char_height, num_verts_y)
    coords = np.vstack(np.meshgrid(X, Y, 0)).reshape(3, -1).T.tolist()
    cfaces = faces_from_xy(num_chars_x, num_chars_y)
    return coords, cfaces
 
