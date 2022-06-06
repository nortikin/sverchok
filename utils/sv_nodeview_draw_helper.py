# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import re
import numpy as np
from mathutils import Matrix

from sverchok.settings import get_params

# pylint: disable=c0111
# pylint: disable=c0103


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
            quad = (pattern + x_offset).tolist()
            add([(quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])])
    return faces


def get_console_grid(char_width, char_height, num_chars_x, num_chars_y):
    
    num_verts_x = num_chars_x + 1
    num_verts_y = num_chars_y + 1
    X = np.linspace(0, num_chars_x*char_width, num_verts_x)
    Y = np.linspace(0, -num_chars_y*char_height, num_verts_y)
    coords = np.vstack(np.meshgrid(X, Y, 0)).reshape(3, -1).T.tolist()

    cfaces = faces_from_xy(num_chars_x, num_chars_y)
    
    return coords, cfaces
 
def advanced_parse_socket(socket, node):

    out = "...."
    prefix = f"data[{node.element_index}] = "
    if (fulldata := socket.sv_get()):
        if len(fulldata) > 0:
            try:

                # could potentially chop up fulldata here before turning it
                # into nparray. maybe it's faster?

                a = np.array(fulldata[node.element_index])
                str_array = np.array2string(
                    a, 
                    max_line_width=node.line_width, 
                    precision=node.rounding or None, 
                    prefix=prefix, 
                    separator=' ', 
                    threshold=30,
                    edgeitems=10)
                
                if "list" in str_array:
                    str_array = re.sub("list\((?P<list>.+?)\)", "\g<list>", str_array)
                #print(str_array)
                return (prefix + str_array).split("\n")
            except:
                ...
    return out



def find_longest_linelength(lines):
    return len(max(lines, key=len))


def ensure_line_padding(text, filler=" "):
    """ expects a single string, with newlines """
    lines = text.split('\n')
    longest_line = find_longest_linelength(lines)
    
    new_lines = []
    new_line = new_lines.append
    for line in lines:
        new_line(line.ljust(longest_line, filler))
    
    return new_lines, longest_line

def advanced_text_decompose(content):
    """
    input:
        expects to receive a newline separated string, to indicate multiline text
        if anything else is received a "no valid text found..." message is passed.
    return:
        return_str : a list of strings, padded with " " to match the longest line
        dims       : 1. number of lines high, 
                     2. length of longest line (its char count)
    """
    return_str = ""
    if isinstance(content, str):
        return_str, width = ensure_line_padding(content)
    else:
        return_str, width = ensure_line_padding("no valid text found\nfeed it multiline\ntext")

    dims = width, len(return_str)
    return return_str, dims

