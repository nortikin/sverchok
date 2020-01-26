# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

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


def triangles_from_quads(faces):
    r"""
    this splits up the quad from geom.grid to triangles

                (ABCD)                   (ABC, ACD)

    go from:    A - - - B           to    A - B            A 
                |       |                  \  |            | \
                |       |                   \ |            |  \
                D - - - C                     C            D - C

    """
    tri_faces = []
    tris_add = tri_faces.extend
    _ = [tris_add(((poly[0], poly[1], poly[2]), (poly[0], poly[2], poly[3]))) for poly in faces]
    return tri_faces


def tri_grid(dim_x=3, dim_y=2, nx=3, ny=3):
    """
    This generates 2d grid, into which we texture each polygon with it's associated character UV

    AA -  -  -AB -  -  -AC -  -  -AD -  -  - n
     | -       | -       | -       |
     |    -    |    -    |    -    |
     |       - |       - |       - |
    BA -  -  -BB -  -  -BC -  - 
     | -       | -
     |    -    |    -
     |       - |       -
    CA -  -  -CB -  -  -
     | -
     |    -
     |       -
    etc

    There's a mapping between int(char) to uv coordinates, charmap will support ascii only.

    """
    neg_y = Matrix(((1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    verts, _, faces = grid(dim_x, dim_y, nx, ny, anchor=7, matrix=neg_y, mode='pydata')
    tri_faces = triangles_from_quads(faces)
    return verts, tri_faces
