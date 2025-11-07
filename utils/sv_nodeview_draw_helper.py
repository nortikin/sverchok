# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import numpy as np
from mathutils import Matrix

from sverchok.utils.decorators_compilation import njit
from sverchok.settings import get_params

# pylint: disable=c0111
# pylint: disable=c0103

def get_xy_for_bgl_drawing(node):
    # adjust proposed text location in case node is framed.
    # take into consideration the hidden state
    _x, _y = node.absolute_location
    ui_scale = bpy.context.preferences.system.ui_scale
    _x, _y = (_x + node.width)*ui_scale + 20, _y*ui_scale

    # this alters location based on DPI/Scale settings.
    return _x * node.location_theta, _y * node.location_theta

class SvNodeViewDrawMixin():

    location_theta: bpy.props.FloatProperty(name="location theta")

    @property
    def xy_offset(self):
        a = self.absolute_location
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
        self.location_theta = multiplier

@njit(cache=True)
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
    add = faces.extend
    pattern = np.array([0, ncx+1, ncx+2, 1])
    for row in range(ncy):
        for col in range(ncx):
            x_offset = ((ncx+1) * row) + col
            quad = (pattern + x_offset)
            add([(quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])])
    return faces

@njit(cache=True)
def get_console_grid(char_width, char_height, num_chars_x, num_chars_y):
    num_verts_x = num_chars_x + 1
    num_verts_y = num_chars_y + 1

    # njit doesn't allow np.tile or np.meshgrid, requiring a short rewrite.
    X = np.linspace(0, num_chars_x*char_width, num_verts_x)
    Y = np.linspace(0, -num_chars_y*char_height, num_verts_y)
    xdir = np.repeat(X, num_verts_y).reshape(-1, num_verts_y).T.flatten()
    ydir = np.repeat(Y, num_verts_x).T
    coords = np.vstack((xdir, ydir)).T

    cfaces = faces_from_xy(num_chars_x, num_chars_y)
    return coords, cfaces
